"""
context_builder.py

Aggregates and formats transcript segments and episode metadata for LLM input.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import tiktoken  # For token counting with OpenAI models
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def count_tokens(text, model_name=None):
    """
    Count tokens in a string using tiktoken (for OpenAI models).
    Model name can be set via the TOKEN_COUNT_MODEL environment variable.
    """
    if model_name is None:
        model_name = os.getenv("TOKEN_COUNT_MODEL", "gpt-4o-mini-2024-07-18")
    enc = tiktoken.encoding_for_model(model_name)
    return len(enc.encode(text))

def build_context(segments, episode_metadata=None, max_tokens=2000, model_name=None, add_urls=False, summarize_if_too_long=False):
    """
    Build a context string for the LLM from transcript segments and optional metadata.
    - segments: list of dicts with 'text', 'episode_number', etc.
    - episode_metadata: dict mapping episode_number to metadata (title, url, ...)
    - add_urls: if True, include episode URLs in the context
    - summarize_if_too_long: if True, add a placeholder for future summarization logic
    """
    # Assume segments are already deduplicated and ranked

    context_parts = []
    total_tokens = 0

    for seg in segments:
        ep_info = ""
        if episode_metadata:
            meta = episode_metadata.get(seg['episode_number'])
            if meta:
                ep_info = f"Episode {seg['episode_number']}: {meta.get('title', '')}"
                if add_urls and meta.get('url'):
                    ep_info += f" ({meta['url']})"
                ep_info += "\n"
        chunk = f"{ep_info}Segment {seg.get('chunk_index', '')}: {seg['text']}\n"
        chunk_tokens = count_tokens(chunk, model_name)
        if total_tokens + chunk_tokens > max_tokens:
            if summarize_if_too_long:
                context_parts.append("[Context truncated. Summarization needed.]")
            break
        context_parts.append(chunk)
        total_tokens += chunk_tokens

    context = "\n".join(context_parts)
    return context

# --- LangGraph Node: Deduplication ---
def deduplication_node(inputs):
    print("deduplication_node input:", inputs)
    segments = inputs.get('segments', [])
    unique_segments = { (seg['episode_number'], seg.get('chunk_index', 0)): seg for seg in segments }
    deduped_segments = list(unique_segments.values())
    output = {**inputs, 'segments': deduped_segments}
    print("deduplication_node output:", output)
    return output

# --- LangGraph Node: Ranking (by similarity) ---
def ranking_node(inputs):
    print("ranking_node input:", inputs)
    segments = inputs.get('segments', [])
    if any('similarity' in seg for seg in segments):
        ranked_segments = sorted(segments, key=lambda x: -x.get('similarity', 0))
    else:
        ranked_segments = segments
    output = {**inputs, 'segments': ranked_segments}
    print("ranking_node output:", output)
    return output

# --- Metadata Retrieval Function ---
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise EnvironmentError("Missing Neo4j connection details in environment variables.")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_episode_metadata_neo4j(episode_numbers):
    """
    Fetch metadata (title, url) for a set of episode_numbers from Neo4j.
    Returns a dict: {episode_number: {'title': ..., 'url': ...}, ...}
    """
    if not episode_numbers:
        return {}
    metadata = {}
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Episode)
            WHERE e.episode_number IN $eps
            RETURN e.episode_number AS episode_number, e.title AS title, e.url AS url
            """,
            eps=list(episode_numbers)
        )
        for record in result:
            metadata[record['episode_number']] = {
                'title': record['title'],
                'url': record['url']
            }
    return metadata

# --- LangGraph Node: Metadata Enrichment ---
def metadata_enrichment_node(inputs):
    print("metadata_enrichment_node input:", inputs)
    segments = inputs.get('segments', [])
    episode_numbers = {seg['episode_number'] for seg in segments}
    episode_metadata = get_episode_metadata_neo4j(episode_numbers)
    output = {**inputs, 'episode_metadata': episode_metadata}
    print("metadata_enrichment_node output:", output)
    return output

# --- LangGraph Node: Context Formatting ---
def context_formatting_node(inputs):
    print("context_formatting_node input:", inputs)
    segments = inputs.get('segments', [])
    episode_metadata = inputs.get('episode_metadata', {})
    context = build_context(segments, episode_metadata, max_tokens=2000, add_urls=True)
    output = {**inputs, 'context': context}
    print("context_formatting_node output:", output)
    return output 