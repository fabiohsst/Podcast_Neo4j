from retrieval_layer import retrieval_node
from context_builder import (
    deduplication_node,
    ranking_node,
    metadata_enrichment_node,
    context_formatting_node
)
from llm_integration import llm_node

# 1. Simulate user input
user_message = "Por que as pessoas compartilham fake news?"

# 2. Retrieval node
retrieval_output = retrieval_node({'user_message': user_message})
print("Retrieval output:", retrieval_output)

# 3. Deduplication node
dedup_output = deduplication_node(retrieval_output)
print("Deduplication output:", dedup_output)

# 4. Ranking node
ranked_output = ranking_node(dedup_output)
print("Ranking output:", ranked_output)

# 5. Metadata enrichment node
metadata_output = metadata_enrichment_node(ranked_output)
print("Metadata enrichment output:", metadata_output)

# 6. Context formatting node
context_output = context_formatting_node(metadata_output)
print("Context formatting output:\n", context_output['context'])

# 7. LLM node
llm_output = llm_node({'context': context_output['context'], 'user_message': user_message})
print("LLM response:\n", llm_output['llm_response']) 