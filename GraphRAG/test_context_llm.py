"""
test_context_llm.py

Test context construction and LLM integration for the Podcast GraphRAG system.
Always uses the gpt-4o-mini-2024-07-18 model.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import argparse
from retrieval_layer import hybrid_retrieve
from context_builder import build_context
from llm_integration import query_llm, DEFAULT_MODEL
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Function to fetch episode metadata from Neo4j
def get_episode_metadata_neo4j(episode_numbers):
    """
    Given a set of episode_numbers, return a dict mapping episode_number to metadata (title, url) from Neo4j.
    """
    load_dotenv()
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USER = os.getenv('NEO4J_USER')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    meta = {}
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Episode)
            WHERE e.episode_number IN $ep_nums
            RETURN e.episode_number AS episode_number, e.title AS title, e.url AS url
            """,
            ep_nums=list(episode_numbers)
        )
        for record in result:
            meta[record['episode_number']] = {
                "title": record['title'],
                "url": record['url']
            }
    driver.close()
    return meta

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test context and LLM integration for Podcast GraphRAG.")
    parser.add_argument("user_query", type=str, nargs="?", help="The user query to test")
    args = parser.parse_args()
    user_query = args.user_query or input("Enter your query: ")
    print("Testing context and LLM integration with query:", user_query)

    # 1. Retrieve segments
    segments = hybrid_retrieve(user_query, top_k=5, expand_depth=1)
    print(f"Retrieved {len(segments)} segments.")

    # 2. Dynamically gather metadata for all relevant episodes from Neo4j
    episode_numbers = {seg['episode_number'] for seg in segments}
    EPISODE_METADATA = get_episode_metadata_neo4j(episode_numbers)

    # 3. Build context
    context = build_context(segments, EPISODE_METADATA, max_tokens=1500, rank_key="similarity", add_urls=True)
    print("\n--- Context Sent to LLM ---\n")
    print(context[:1000] + ("..." if len(context) > 1000 else ""))  # Print first 1000 chars

    # 4. Call LLM
    answer = query_llm(context, user_query, model=DEFAULT_MODEL)
    print("\n--- LLM Response ---\n")
    print(answer) 