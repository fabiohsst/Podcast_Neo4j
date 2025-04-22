"""
retrieval_layer.py

This module provides functions to retrieve relevant transcript segments and episodes
from the Neo4j graph for use in a GraphRAG pipeline.

Author: Fabio Tavares
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# --- Load environment variables and connect to Neo4j ---
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- 1. Retrieve Transcript Segments by Keyword ---
def retrieve_segments_by_keyword(keyword, limit=10):
    """
    Retrieve transcript segments containing the given keyword.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (s:TranscriptSegment)
            WHERE toLower(s.text) CONTAINS toLower($keyword)
            RETURN s.episode_number AS episode_number, s.chunk_index AS chunk_index, s.text AS text
            LIMIT $limit
        """, keyword=keyword, limit=limit)
        return [record.data() for record in result]

# --- 2. Retrieve Segments by Embedding Similarity ---
def retrieve_segments_by_embedding(query_embedding, top_k=10):
    """
    Retrieve the top_k transcript segments most similar to the query embedding.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (s:TranscriptSegment)
            RETURN s.episode_number AS episode_number, s.chunk_index AS chunk_index, s.text AS text, s.embedding AS embedding
        """)
        segments = []
        embeddings = []
        for record in result:
            segments.append({
                "episode_number": record["episode_number"],
                "chunk_index": record["chunk_index"],
                "text": record["text"]
            })
            embeddings.append(record["embedding"])
        # Compute cosine similarity
        sim_scores = cosine_similarity([query_embedding], embeddings)[0]
        top_indices = np.argsort(sim_scores)[::-1][:top_k]
        return [segments[i] | {"similarity": float(sim_scores[i])} for i in top_indices]

# --- 3. Expand Context via SIMILAR_TO and REFERENCES ---
def expand_context_from_episode(episode_number, depth=1):
    """
    Retrieve episodes and transcript segments connected to the given episode via
    :SIMILAR_TO and :REFERENCES relationships up to a certain depth.
    """
    with driver.session() as session:
        result = session.run(f"""
            MATCH (e:Episode {{episode_number: $ep}})
            CALL apoc.path.subgraphNodes(e, {{
                relationshipFilter: 'SIMILAR_TO|REFERENCES>',
                minLevel: 1,
                maxLevel: $depth,
                labelFilter: 'Episode|TranscriptSegment'
            }})
            YIELD node
            RETURN node
        """, ep=episode_number, depth=depth)
        return [record["node"] for record in result]

# --- 4. Retrieve Community/Cluster Info (Optional) ---
def get_community_episodes(community_id, limit=20):
    """
    Retrieve episodes belonging to a specific community/cluster.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Episode)
            WHERE e.community = $community_id
            RETURN e.episode_number AS episode_number, e.title AS title
            LIMIT $limit
        """, community_id=community_id, limit=limit)
        return [record.data() for record in result]

# --- Example usage ---
if __name__ == "__main__":
    print("Segments containing 'memória':")
    for seg in retrieve_segments_by_keyword("memória", limit=5):
        print(seg)

    # Example: retrieve_segments_by_embedding(query_embedding, top_k=5)
    # (You need to generate a query_embedding using your embedding model.)

    print("\nEpisodes in community 1:")
    for ep in get_community_episodes(1, limit=5):
        print(ep) 

        