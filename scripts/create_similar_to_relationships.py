"""
create_similar_to_relationships.py

This script:
- Loads episode metadata and computes average transcript embeddings per episode from Neo4j.
- Calculates cosine similarity between all episode pairs.
- Filters pairs by a chosen threshold (default: 0.97).
- Removes all existing :SIMILAR_TO relationships.
- Creates new bidirectional :SIMILAR_TO relationships with the similarity score as a property.
- Provides example Cypher queries for further exploration.

Author: Fabio Tavares
"""

import os
import numpy as np
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

# --- Configuration ---
THRESHOLD = 0.97
BATCH_SIZE = 1000
DATA_DIR = os.path.join('..', 'data', 'processed')  # Adjust if running from a different directory

# --- Load environment variables ---
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# --- Connect to Neo4j ---
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Load episode metadata ---
episodes_df = pd.read_csv(os.path.join(DATA_DIR, 'naruhodo_episodes.csv'))
episode_to_title = pd.Series(
    episodes_df['episode_title'].values,
    index=episodes_df['episode_number']
).to_dict()

# --- Step 1: Extract and aggregate embeddings ---
def get_episode_embeddings(driver):
    """
    For each episode, retrieve all transcript segment embeddings from Neo4j,
    and compute the average embedding for the episode.
    Returns:
        avg_embeddings (dict): {episode_number: np.ndarray (average embedding)}
    """
    episode_embeddings = {}
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Episode)-[:HAS_SEGMENT]->(s:TranscriptSegment)
            RETURN e.episode_number AS episode, s.embedding AS embedding
        """)
        for record in result:
            ep = record['episode']
            emb = record['embedding']
            if emb is not None:
                if ep not in episode_embeddings:
                    episode_embeddings[ep] = []
                episode_embeddings[ep].append(emb)
    avg_embeddings = {}
    for ep, embs in episode_embeddings.items():
        valid_embs = [e for e in embs if e is not None]
        if valid_embs:
            avg_embeddings[ep] = np.mean(np.array(valid_embs), axis=0)
    return avg_embeddings

print("Extracting and aggregating episode embeddings...")
avg_embeddings = get_episode_embeddings(driver)
print(f"Number of episodes with embeddings: {len(avg_embeddings)}")

# --- Step 2: Compute cosine similarity matrix ---
episode_numbers = sorted(avg_embeddings.keys())
embedding_matrix = np.stack([avg_embeddings[ep] for ep in episode_numbers])
similarity_matrix = cosine_similarity(embedding_matrix)

# --- Step 3: Filter episode pairs by threshold ---
similarity_scores = []
num_episodes = len(episode_numbers)
for i in range(num_episodes):
    for j in range(num_episodes):
        if i != j:
            similarity_scores.append((
                episode_numbers[i],
                episode_numbers[j],
                similarity_matrix[i, j]
            ))

selected_pairs = [row for row in similarity_scores if row[2] >= THRESHOLD]
print(f"Number of episode pairs with similarity >= {THRESHOLD}: {len(selected_pairs)}")

# --- Step 4: Remove existing SIMILAR_TO relationships and import new ones ---
with driver.session() as session:
    # Remove all existing SIMILAR_TO relationships
    session.run("MATCH ()-[r:SIMILAR_TO]->() DELETE r")
    print("All existing SIMILAR_TO relationships removed.")

    # Prepare data for both directions
    relationships = []
    for epA, epB, score in selected_pairs:
        relationships.append({'source': epA, 'target': epB, 'score': float(score)})
        relationships.append({'source': epB, 'target': epA, 'score': float(score)})

    # Batch insert new SIMILAR_TO relationships
    for i in range(0, len(relationships), BATCH_SIZE):
        batch = relationships[i:i+BATCH_SIZE]
        session.run("""
            UNWIND $batch AS rel
            MATCH (a:Episode {episode_number: rel.source})
            MATCH (b:Episode {episode_number: rel.target})
            MERGE (a)-[r:SIMILAR_TO]->(b)
            SET r.score = rel.score
        """, batch=batch)
        print(f"Inserted batch {i//BATCH_SIZE + 1} of SIMILAR_TO relationships.")

    # Validate the number of relationships created
    result = session.run("MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) AS rel_count")
    print("Number of SIMILAR_TO relationships in the database:", result.single()["rel_count"])

    # --- Step 5: Run Louvain community detection ---
    print("Running Louvain community detection using GDS...")
    # Required for Neo4j Aura: authenticate GDS usage
    session.run("CALL gds.aura.api.credentials()")
    louvain_result = session.run("""
        CALL gds.louvain.write(
          'Episode',
          {
            relationshipProjection: {
              SIMILAR_TO: {
                type: 'SIMILAR_TO',
                orientation: 'UNDIRECTED',
                properties: {
                  score: {
                    property: 'score',
                    defaultValue: 1.0
                  }
                }
              }
            },
            relationshipWeightProperty: 'score',
            writeProperty: 'community'
          }
        )
        YIELD communityCount, modularity, modularities
    """)
    louvain_stats = louvain_result.single()
    print(f"Louvain community detection complete. Community count: {louvain_stats['communityCount']}, Modularity: {louvain_stats['modularity']}")

driver.close()

# --- Example: How to explore the relationships in Python ---
# def print_most_similar_episodes(target_episode, top_n=10):
#     with driver.session() as session:
#         result = session.run("""
#             MATCH (e:Episode {episode_number: $ep})- [r:SIMILAR_TO]-> (other:Episode)
#             RETURN other.episode_number AS episode_number, other.title AS title, r.score AS score
#             ORDER BY r.score DESC
#             LIMIT $top_n
#         """, ep=target_episode, top_n=top_n)
#         print(f"\nTop {top_n} most similar episodes to {target_episode}:")
#         for record in result:
#             print(record)

# Example usage (uncomment to use):
# print_most_similar_episodes(280, top_n=10)

"""
Documentation:
- This script is intended to be run from the command line or as a batch process.
- It ensures the SIMILAR_TO relationships are always up-to-date and free of duplicates.
- Adjust the THRESHOLD and BATCH_SIZE as needed for your dataset and hardware.
- For further exploration, use the provided function or adapt the Cypher queries from the notebook.
""" 