"""
retrieval_layer.py

This module provides functions to retrieve relevant transcript segments and episodes
from the Neo4j graph for use in a GraphRAG pipeline.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import logging
import traceback

# --- Set up error logging for problematic segments ---
logging.basicConfig(
    filename="retrieval_layer_errors.log",
    level=logging.ERROR,
    format="%(asctime)s | %(message)s"
)

# --- Load environment variables and connect to Neo4j ---
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# --- Load embedding model (for hybrid retrieval) ---
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Initialize Neo4j driver with connection pooling and error handling
def get_neo4j_driver():
    """Get or create a Neo4j driver with proper error handling"""
    try:
        if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
            raise ValueError("Missing Neo4j connection details in environment variables")
        
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # Test connection
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except Exception as e:
        logging.error(f"Neo4j connection error: {str(e)}")
        raise ConnectionError(f"Failed to connect to Neo4j: {str(e)}")

# Create driver with error handling
try:
    driver = get_neo4j_driver()
except Exception as e:
    logging.error(f"Failed to initialize Neo4j driver: {str(e)}")
    # Set a dummy driver as a fallback for testing purposes
    class DummyDriver:
        def session(self):
            class DummySession:
                def run(self, *args, **kwargs):
                    return []
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return DummySession()
    driver = DummyDriver()
    logging.warning("Using dummy Neo4j driver due to connection failure")

# --- 1. Retrieve Transcript Segments by Keyword ---
def retrieve_segments_by_keyword(keyword, limit=10):
    """
    Retrieve transcript segments containing the given keyword.
    """
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:TranscriptSegment)
                WHERE toLower(s.text) CONTAINS toLower($keyword)
                RETURN s.episode_number AS episode_number, s.chunk_index AS chunk_index, s.text AS text
                LIMIT $limit
            """, keyword=keyword, limit=limit)
            return [record.data() for record in result]
    except Exception as e:
        logging.error(f"Error in keyword search: {str(e)}")
        return []

# --- 2. Retrieve Segments by Embedding Similarity ---
def retrieve_segments_by_embedding(query_embedding, top_k=10):
    """
    Retrieve the top_k transcript segments most similar to the query embedding.
    Ensures all embeddings are valid, 1D, and of the correct length and type.
    Skips any invalid or mismatched embeddings.
    """
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:TranscriptSegment)
                RETURN s.episode_number AS episode_number, s.chunk_index AS chunk_index, s.text AS text, s.embedding AS embedding
            """)
            segments = []
            embeddings = []
            skipped = 0
            for record in result:
                emb = record["embedding"]
                # Ensure embedding is a list/array of the correct length and all elements are floats/ints
                if (
                    emb is not None and
                    isinstance(emb, (list, np.ndarray)) and
                    len(emb) == len(query_embedding) and
                    all(isinstance(x, (float, int, np.floating, np.integer)) for x in emb)
                ):
                    arr = np.array(emb, dtype=np.float32)
                    if arr.ndim == 1:
                        embeddings.append(arr)
                        segments.append({
                            "episode_number": record["episode_number"],
                            "chunk_index": record["chunk_index"],
                            "text": record["text"]
                        })
                    else:
                        skipped += 1
                else:
                    skipped += 1
            if skipped > 0:
                logging.warning(f"Skipped {skipped} transcript segments due to invalid or mismatched embeddings.")
            if not embeddings:
                return []
            sim_scores = cosine_similarity([query_embedding], embeddings)[0]
            top_indices = np.argsort(sim_scores)[::-1][:top_k]
            return [segments[i] | {"similarity": float(sim_scores[i])} for i in top_indices]
    except Exception as e:
        logging.error(f"Error in embedding similarity search: {str(e)}")
        return []

# --- 3. Expand Context via SIMILAR_TO and REFERENCES ---
def expand_context_from_episode(episode_number, depth=1):
    """
    Retrieve episodes and transcript segments connected to the given episode via
    :SIMILAR_TO and :REFERENCES relationships up to a certain depth.
    """
    try:
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
    except Exception as e:
        logging.error(f"Error in context expansion: {str(e)}")
        return []

# --- 5. Hybrid Retrieval Function ---
def hybrid_retrieve_with_fallback(user_message, top_k=5, expand_depth=1):
    """
    Hybrid retrieval with fallback: first uses keyword search and graph expansion.
    If fewer than top_k results are found, uses embedding similarity to fill up to top_k results.
    Returns a deduplicated list of relevant transcript segments.
    """
    try:
        # 1. Keyword search
        keyword_segments = retrieve_segments_by_keyword(user_message, limit=top_k)
        episode_numbers = {seg['episode_number'] for seg in keyword_segments}

        # 2. Graph expansion
        expanded_segments = []
        for ep_num in episode_numbers:
            expanded_nodes = expand_context_from_episode(ep_num, depth=expand_depth)
            expanded_segments.extend([
                node for node in expanded_nodes if isinstance(node, dict) and 'text' in node
            ])

        # Combine and deduplicate
        all_segments = keyword_segments + expanded_segments
        seen = {(seg['episode_number'], seg.get('chunk_index', 0)) for seg in all_segments}

        # 3. Fallback: Embedding similarity if not enough results
        if len(all_segments) < top_k:
            query_embedding = embedding_model.encode([user_message])[0]
            embedding_segments = retrieve_segments_by_embedding(query_embedding, top_k=top_k)
            for seg in embedding_segments:
                key = (seg['episode_number'], seg.get('chunk_index', 0))
                if key not in seen:
                    all_segments.append(seg)
                    seen.add(key)
                if len(all_segments) >= top_k:
                    break

        return all_segments[:top_k]
    except Exception as e:
        logging.error(f"Error in hybrid retrieval: {str(e)}")
        # Provide at least an empty result rather than failing
        return []

# Optionally, you can alias the main hybrid retrieval function to this new approach
hybrid_retrieve = hybrid_retrieve_with_fallback

def recommend_episodes(current_episode, user_history=None, top_n=5):
    """
    Recommend episodes based only on :SIMILAR_TO relationships.
    - current_episode: episode number to base recommendations on
    - user_history: set of episode numbers the user has already seen/listened to
    - top_n: number of recommendations to return
    Returns a list of recommended episode dicts (episode_number, title, score).
    """
    try:
        if user_history is None:
            user_history = set()
        recommendations = []
        with driver.session() as session:
            # Get top similar episodes by :SIMILAR_TO score
            result = session.run("""
                MATCH (e:Episode {episode_number: $ep})- [r:SIMILAR_TO]-> (other:Episode)
                WHERE NOT other.episode_number IN $history
                RETURN other.episode_number AS episode_number, other.title AS title, r.score AS score
                ORDER BY r.score DESC
                LIMIT $top_n
            """, ep=current_episode, history=list(user_history), top_n=top_n*3)  # Fetch extra in case of filtering
            for record in result:
                if record["episode_number"] not in user_history:
                    recommendations.append({
                        "episode_number": record["episode_number"],
                        "title": record["title"],
                        "score": record["score"]
                    })
                if len(recommendations) >= top_n:
                    break
        return recommendations[:top_n]
    except Exception as e:
        logging.error(f"Error in episode recommendations: {str(e)}")
        return []

# --- LangGraph Node: Retrieval ---
# This function is designed to be used as a node in a LangGraph pipeline.
def retrieval_node(state):
    """
    LangGraph retrieval node that handles error cases gracefully.
    Accepts a state dict with 'user_message' or an initial user_message string.
    """
    try:
        print("retrieval_node input:", state)
        
        # Handle different state types
        user_message = None
        if isinstance(state, dict):
            user_message = state.get('user_message')
        elif isinstance(state, str):
            user_message = state
        elif hasattr(state, 'get'):
            # Handle any other object with a get method
            user_message = state.get('user_message')
            
        # Check if we found a user_message
        if not user_message:
            raise ValueError("Input to retrieval_node must include 'user_message'.")
            
        segments = hybrid_retrieve(user_message, top_k=5, expand_depth=1)
        
        # Ensure we have something to work with even if retrieval fails
        if not segments:
            logging.warning(f"No segments found for query: {user_message}")
            # Provide a dummy segment as fallback
            segments = [{
                'episode_number': 0,
                'chunk_index': 0,
                'text': 'No relevant information found in the database.',
                'is_fallback': True
            }]
        
        # Create new state if input was empty
        if isinstance(state, dict) and state:
            # State has content, update it
            result = {**state, 'segments': segments, 'user_message': user_message}
        else:
            # Create new state
            result = {'segments': segments, 'user_message': user_message}
            
        print("retrieval_node output:", result)
        return result
    except Exception as e:
        logging.error(f"Error in retrieval node: {str(e)}")
        traceback.print_exc()
        
        # Create appropriate error state
        if isinstance(state, dict):
            error_state = {
                **state,
                'segments': [],
                'error': f"Retrieval error: {str(e)}",
                'llm_error': f"Failed to retrieve relevant information: {str(e)}"
            }
        else:
            error_state = {
                'segments': [],
                'user_message': str(state) if state else None,
                'error': f"Retrieval error: {str(e)}",
                'llm_error': f"Failed to retrieve relevant information: {str(e)}"
            }
            
        print("retrieval_node error output:", error_state)
        return error_state

# --- Example usage ---
# if __name__ == "__main__":
#     print("Segments containing 'TDAH':")
#     for seg in retrieve_segments_by_keyword("memória", limit=5):
#         print(seg)
#
#     # Example: retrieve_segments_by_embedding(query_embedding, top_k=5)
#     # (You need to generate a query_embedding using your embedding model.)
#
#     # Example: hybrid retrieval
#     print("\nHybrid retrieval for 'fake news':")
#     for seg in hybrid_retrieve("fake news", top_k=3, expand_depth=1):
#         print(seg)
#
#     # Example: recommendations
#     print("\nRecommendations for episode 280, user has seen [280, 42]:")
#     recs = recommend_episodes(280, user_history={280, 42}, top_n=3)
#     for rec in recs:
#         print(rec) 

        