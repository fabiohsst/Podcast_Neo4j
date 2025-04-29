import os
import re
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from neo4j import GraphDatabase

# --- Setup ---
load_dotenv()
# This will always point to the transcripts folder inside Podcast_Neo4j
TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'transcripts')
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
embedding_model = SentenceTransformer(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

CHUNK_SIZE = 300
CHUNK_OVERLAP = 100

# --- Episodes to Skip ---
SKIP_EPISODES = {129, 130, 131, 7, 18, 23, 26, 28, 37, 39, 41, 44, 48, 49, 50, 54, 57, 67, 70, 73, 76, 84, 85, 90, 92, 97, 99, 100, 104, 112}

# --- Checkpointing Utilities ---
PROGRESS_FILE = "processed_episodes.txt"

def load_processed_episodes():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return set(int(line.strip()) for line in f if line.strip().isdigit())
    return set()

def save_processed_episode(ep_num):
    with open(PROGRESS_FILE, "a") as f:
        f.write(f"{ep_num}\n")

# --- Transcript Loader ---
def load_transcript(episode_number):
    # Use regex to match the episode number as a complete token after the underscore
    pattern = re.compile(rf"^Naruhodo _{episode_number}\D")
    transcript_files = [f for f in os.listdir(TRANSCRIPTS_DIR) if pattern.match(f) and f.endswith('.txt')]
    if len(transcript_files) != 1:
        raise FileNotFoundError(f"Expected exactly one transcript file for episode {episode_number}, found: {transcript_files}")
    transcript_path = os.path.join(TRANSCRIPTS_DIR, transcript_files[0])
    print(f"Loading transcript for episode {episode_number}: {transcript_path}")  # Debug print
    segments = []
    timestamp_re = re.compile(r"\[(\d{2}):(\d{2})\] ?(.*)")
    with open(transcript_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            match = timestamp_re.match(line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                text = match.group(3).strip()
                total_seconds = minutes * 60 + seconds
                segments.append((total_seconds, text))
    return segments

# --- Token-based Chunker ---
def chunk_transcript_tokenwise(segments, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP, tokenizer=tokenizer):
    all_text = " ".join([text for _, text in segments])
    tokens = tokenizer(all_text, return_offsets_mapping=True, add_special_tokens=False)
    input_ids = tokens['input_ids']
    offsets = tokens['offset_mapping']
    chunks = []
    chunk_spans = []
    start = 0
    while start < len(input_ids):
        end = min(start + chunk_size, len(input_ids))
        chunk_ids = input_ids[start:end]
        chunk_start_char = offsets[start][0]
        chunk_end_char = offsets[end-1][1] if end-1 < len(offsets) else offsets[-1][1]
        chunk_text = all_text[chunk_start_char:chunk_end_char].strip()
        chunks.append(chunk_text)
        chunk_spans.append((start, end))
        if end == len(input_ids):
            break
        start += chunk_size - overlap
    print(f"Chunked into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
    print("First 3 chunk lengths (tokens):", [e-s for s, e in chunk_spans[:3]])
    return chunks

# --- Embedding ---
def generate_embeddings(text_chunks, batch_size=32):
    return embedding_model.encode(text_chunks, batch_size=batch_size, show_progress_bar=True)

# --- Neo4j Driver ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def delete_segments_for_episode(episode_number):
    with driver.session() as session:
        session.run("""
            MATCH (e:Episode {episode_number: $episode_number})-[:HAS_SEGMENT]->(s:TranscriptSegment)
            DETACH DELETE s
        """, {"episode_number": episode_number})

def import_to_neo4j_with_retries(driver, episode_number, text_chunks, embeddings, retries=3, delay=5):
    for attempt in range(retries):
        try:
            with driver.session() as session:
                session.run(
                    """
                    MERGE (e:Episode {episode_number: $episode_number})
                    """,
                    {"episode_number": episode_number}
                )
                segment_nodes = [
                    {
                        'id': f"{episode_number}_{i}",
                        'episode_number': episode_number,
                        'chunk_index': i,
                        'text': chunk,
                        'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                    }
                    for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings))
                ]
                session.run(
                    """
                    UNWIND $segments AS seg
                    MERGE (s:TranscriptSegment {id: seg.id})
                    SET s.episode_number = seg.episode_number,
                        s.chunk_index = seg.chunk_index,
                        s.text = seg.text,
                        s.embedding = seg.embedding
                    """,
                    {'segments': segment_nodes}
                )
                session.run(
                    """
                    UNWIND $segments AS seg
                    MATCH (e:Episode {episode_number: seg.episode_number})
                    MATCH (s:TranscriptSegment {id: seg.id})
                    MERGE (e)-[:HAS_SEGMENT]->(s)
                    """,
                    {'segments': segment_nodes}
                )
            return True
        except Exception as e:
            print(f"[Retry {attempt+1}/{retries}] Error importing episode {episode_number}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                # Try to reconnect driver if needed
                try:
                    driver.close()
                except Exception:
                    pass
                globals()['driver'] = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            else:
                print(f"Failed to import episode {episode_number} after {retries} attempts.")
                return False

# --- Main Loop ---
# Import all transcripts except those in SKIP_EPISODES and already processed
all_results = []
processed_episodes = load_processed_episodes()
episode_numbers = []
for fname in os.listdir(TRANSCRIPTS_DIR):
    match = re.search(r'Naruhodo _(\d+)', fname)
    if match:
        ep_num = int(match.group(1))
        if ep_num in SKIP_EPISODES or ep_num in processed_episodes:
            print(f"Skipping episode {ep_num} (in skip list or already processed).")
            continue
        if fname.endswith('.txt'):
            episode_numbers.append(ep_num)
episode_numbers = sorted(set(ep_num for ep_num in episode_numbers if ep_num not in processed_episodes))

for episode_number in episode_numbers:
    timings = {}
    print(f"\nProcessing Episode {episode_number}...")
    t0 = time.time()
    segments = load_transcript(episode_number)
    t1 = time.time()
    timings['load'] = t1 - t0

    chunks = chunk_transcript_tokenwise(segments, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP, tokenizer=tokenizer)
    t2 = time.time()
    timings['chunk'] = t2 - t1

    embeddings = generate_embeddings(chunks, batch_size=32)
    t3 = time.time()
    timings['embed'] = t3 - t2

    # Delete segments for this episode before importing
    delete_segments_for_episode(episode_number)
    success = import_to_neo4j_with_retries(driver, episode_number, chunks, embeddings)
    t4 = time.time()
    timings['import'] = t4 - t3

    timings['total'] = t4 - t0
    all_results.append((episode_number, timings))

    if success:
        save_processed_episode(episode_number)

    print(f"  Load:   {timings['load']:.2f}s")
    print(f"  Chunk:  {timings['chunk']:.2f}s")
    print(f"  Embed:  {timings['embed']:.2f}s")
    print(f"  Import: {timings['import']:.2f}s")
    print(f"  Total:  {timings['total']:.2f}s")

print("\n=== All Episode Timing Summary ===")
for ep, timings in all_results:
    print(f"Episode {ep}: {timings['total']:.2f}s (Load: {timings['load']:.2f}s, Chunk: {timings['chunk']:.2f}s, Embed: {timings['embed']:.2f}s, Import: {timings['import']:.2f}s)")

driver.close()