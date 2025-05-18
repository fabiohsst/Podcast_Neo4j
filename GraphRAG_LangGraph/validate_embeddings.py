"""
validate_embeddings.py

Checks all TranscriptSegment embeddings in Neo4j for consistency and validity.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import numpy as np
from collections import Counter

# --- Load environment variables and connect to Neo4j ---
load_dotenv()
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

EXPECTED_LENGTH = 384  # Change to your embedding model's output size

def validate_embeddings(expected_length=EXPECTED_LENGTH, auto_fix=False, delete_invalid=False):
    valid = 0
    invalid = 0
    length_counter = Counter()
    issues = []
    to_delete = []
    with driver.session() as session:
        result = session.run("""
            MATCH (s:TranscriptSegment)
            RETURN s.id AS id, s.episode_number AS episode_number, s.chunk_index AS chunk_index, s.embedding AS embedding
        """)
        for record in result:
            node_id = record["id"]
            ep = record["episode_number"]
            idx = record["chunk_index"]
            emb = record["embedding"]
            reason = None
            if emb is None:
                reason = "None"
            elif not isinstance(emb, (list, np.ndarray)):
                reason = "Not a list/array"
            elif not all(isinstance(x, (float, int, np.floating, np.integer)) for x in emb):
                reason = "Non-numeric element"
            elif np.array(emb).ndim != 1:
                reason = "Not 1D"
            else:
                length = len(emb)
                length_counter[length] += 1
                if length != expected_length:
                    reason = f"Length {length} != expected {expected_length}"
            if reason:
                invalid += 1
                issues.append((ep, idx, reason, node_id))
                if auto_fix and delete_invalid:
                    to_delete.append(node_id)
            else:
                valid += 1
    print(f"Valid embeddings: {valid}")
    print(f"Invalid embeddings: {invalid}")
    print("Embedding length distribution:", dict(length_counter))
    if issues:
        print("Examples of invalid embeddings:")
        for ep, idx, reason, node_id in issues[:10]:
            print(f"Episode {ep}, chunk {idx}, id {node_id}: {reason}")
    if auto_fix and delete_invalid and to_delete:
        print(f"Deleting {len(to_delete)} invalid TranscriptSegment nodes...")
        with driver.session() as session:
            for node_id in to_delete:
                session.run("""
                    MATCH (s:TranscriptSegment {id: $id}) DETACH DELETE s
                """, id=node_id)
        print("Invalid nodes deleted.")

# if __name__ == "__main__":
#     # Set auto_fix=True and delete_invalid=True to remove invalid nodes
#     validate_embeddings(auto_fix=True, delete_invalid=True)
#     print("\nAuto-fix complete. Rerun this script to verify all embeddings are now valid.") 
    