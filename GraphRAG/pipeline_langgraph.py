from langgraph.graph import Graph
from retrieval_layer import retrieval_node
from context_builder import (
    deduplication_node,
    ranking_node,
    metadata_enrichment_node,
    context_formatting_node
)
from pipeline_nodes_extra import (
    clarification_node,
    logging_node,
    citation_node,
    error_handling_node,
    streaming_llm_node
)

# Build the LangGraph pipeline
graph = Graph()
graph.add_node("retrieval", retrieval_node)
graph.add_node("clarification", clarification_node)
graph.add_node("deduplication", deduplication_node)
graph.add_node("ranking", ranking_node)
graph.add_node("metadata", metadata_enrichment_node)
graph.add_node("formatting", context_formatting_node)
graph.add_node("streaming_llm", streaming_llm_node)
graph.add_node("citation", citation_node)
graph.add_node("logging", logging_node)
graph.add_node("error_handling", error_handling_node)

# Define the pipeline flow
graph.add_edge("retrieval", "clarification")
graph.add_edge("clarification", "deduplication")
graph.add_edge("deduplication", "ranking")
graph.add_edge("ranking", "metadata")
graph.add_edge("metadata", "formatting")
graph.add_edge("formatting", "streaming_llm")
graph.add_edge("streaming_llm", "citation")
graph.add_edge("citation", "logging")
graph.add_edge("logging", "error_handling")

def run_pipeline(user_message, language=None, chat_history=None):
    input_dict = {"user_message": user_message}
    if language is not None:
        input_dict["language"] = language
    if chat_history is not None:
        input_dict["chat_history"] = chat_history
    result = graph.invoke(input_dict)
    return result

if __name__ == "__main__":
    user_message = "Por que as pessoas compartilham fake news?"
    result = run_pipeline(user_message, language="Português", chat_history=None)
    print("LLM response:\n", result["llm_response"]) 