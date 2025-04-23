"""
test_retrieval.py

Test and debug retrieval functions for the Podcast GraphRAG system.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

from retrieval_layer import (
    retrieve_segments_by_keyword,
    retrieve_segments_by_embedding,
    expand_context_from_episode,
    hybrid_retrieve
)
from sentence_transformers import SentenceTransformer

def print_segments(segments, label):
    print(f"\n--- {label} ---")
    for seg in segments[:5]:
        print(f"Ep {seg['episode_number']} | Chunk {seg.get('chunk_index', '')}: {seg['text'][:80]}...")

# if __name__ == "__main__":
#     query = "TDAH"
#     print("Testing retrieval functions with query:", query)
#
#     # 1. Keyword search
#     keyword_segments = retrieve_segments_by_keyword(query, limit=5)
#     print_segments(keyword_segments, "Keyword Search")
#
#     # 2. Embedding search
#     embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
#     query_embedding = embedding_model.encode([query])[0]
#     embedding_segments = retrieve_segments_by_embedding(query_embedding, top_k=5)
#     print_segments(embedding_segments, "Embedding Search")
#
#     # 3. Graph expansion
#     if keyword_segments:
#         ep_num = keyword_segments[0]['episode_number']
#         expanded_nodes = expand_context_from_episode(ep_num, depth=1)
#         expanded_segments = [node for node in expanded_nodes if isinstance(node, dict) and 'text' in node]
#         print_segments(expanded_segments, "Graph Expansion")
#
#     # 4. Hybrid retrieval
#     hybrid_segments = hybrid_retrieve(query, top_k=5, expand_depth=1)
#     print_segments(hybrid_segments, "Hybrid Retrieval") 