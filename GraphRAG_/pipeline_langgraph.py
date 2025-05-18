from langgraph.graph import StateGraph, END
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
    streaming_llm_node,
    language_node
)

def create_simple_pipeline():
    """
    Creates a simplified version of the GraphRAG pipeline with manual processing.
    """
    def process_query(user_message, language=None, chat_history=None):
        """Process a query through all pipeline steps manually"""
        try:
            # Start with initial state
            state = {'user_message': user_message}
            if language:
                state['language'] = language
            if chat_history:
                state['chat_history'] = chat_history
                
            # Run through each node in sequence
            state = retrieval_node(state)
            
            # Check if needs clarification
            clarify_state = clarification_node(state)
            if clarify_state.get('clarification') is True:
                return clarify_state
            
            # Continue with pipeline
            state = language_node(clarify_state)
            state = deduplication_node(state)
            state = ranking_node(state)
            state = metadata_enrichment_node(state)
            state = context_formatting_node(state)
            state = streaming_llm_node(state)
            state = citation_node(state)
            state = logging_node(state)
            state = error_handling_node(state)
            
            return state
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'llm_response': f'Error: {str(e)}',
                'error': str(e),
                'user_message': user_message
            }
    
    return process_query

def create_pipeline():
    """
    Creates and configures the LangGraph pipeline with proper error handling.
    """
    # Build the LangGraph pipeline
    class GraphState(dict):
        """State for the graph."""
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
    
    graph = StateGraph(GraphState)

    # Add all nodes
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("language", language_node)
    graph.add_node("deduplication", deduplication_node)
    graph.add_node("ranking", ranking_node)
    graph.add_node("metadata", metadata_enrichment_node)
    graph.add_node("formatting", context_formatting_node)
    graph.add_node("streaming_llm", streaming_llm_node)
    graph.add_node("citation", citation_node)
    graph.add_node("logging", logging_node)
    graph.add_node("error_handling", error_handling_node)

    # Define the pipeline flow
    graph.set_entry_point("retrieval")
    
    # Define the edges
    graph.add_edge("retrieval", "clarification")
    
    # Add conditional edge based on clarification flag
    def needs_clarification(state):
        if state.get("clarification") is True:
            return "end"
        return "language"
    
    graph.add_conditional_edges(
        "clarification",
        needs_clarification,
        {
            "language": "language",
            "end": END
        }
    )
    
    graph.add_edge("language", "deduplication")
    graph.add_edge("deduplication", "ranking")
    graph.add_edge("ranking", "metadata")
    graph.add_edge("metadata", "formatting")
    graph.add_edge("formatting", "streaming_llm")
    graph.add_edge("streaming_llm", "citation")
    graph.add_edge("citation", "logging")
    graph.add_edge("logging", "error_handling")
    graph.add_edge("error_handling", END)

    return graph.compile()

# Create a singleton pipeline instance
_pipeline = None
_simple_pipeline = None

def get_pipeline(use_simple=True):
    """
    Gets or creates the pipeline instance.
    """
    global _pipeline, _simple_pipeline
    
    if use_simple:
        if _simple_pipeline is None:
            _simple_pipeline = create_simple_pipeline()
        return _simple_pipeline
    else:
        if _pipeline is None:
            _pipeline = create_pipeline()
        return _pipeline

def validate_result(result):
    """
    Validates the pipeline result and ensures it contains required fields.
    """
    if result is None:
        return {
            'llm_response': 'Error: Pipeline returned no result.',
            'error': 'Pipeline execution failed'
        }
    
    if not isinstance(result, dict):
        return {
            'llm_response': 'Error: Invalid pipeline result format.',
            'error': f'Expected dict, got {type(result)}'
        }
    
    # Handle clarification case
    if result.get('clarification') is True:
        return {
            'llm_response': result.get('clarification_prompt', 'Could you please clarify your question?'),
            'clarification': True,
            'user_message': result.get('user_message')
        }
    
    # Ensure we have either a valid response or an error message
    if not result.get('llm_response') and not result.get('llm_error'):
        result['llm_response'] = 'Error: No response generated'
        result['error'] = 'Missing response and error fields'
    
    return result

def run_pipeline(user_message, language=None, chat_history=None, use_simple=True):
    """
    Runs the GraphRAG pipeline with proper error handling and result validation.
    """
    print("run_pipeline input user_message:", user_message)
    
    try:
        # Get pipeline instance
        pipeline = get_pipeline(use_simple=use_simple)
        
        if use_simple:
            # Run simple pipeline directly
            result = pipeline(user_message, language, chat_history)
        else:
            # Prepare input for LangGraph pipeline
            input_dict = {"user_message": user_message}
            if language is not None:
                input_dict["language"] = language
            if chat_history is not None:
                input_dict["chat_history"] = chat_history
            
            # Run LangGraph pipeline
            raw_result = pipeline.invoke(input_dict)
            
            # Check if result is None
            if raw_result is None:
                error_result = {
                    'llm_response': 'Error: Pipeline returned no result.',
                    'error': 'Pipeline execution failed',
                    'user_message': user_message
                }
                print("Pipeline error:", error_result)
                return error_result
            
            # Extract the final state
            result = {}
            for key, value in raw_result.items():
                if key != "__end__" and not key.startswith("__"):  # Skip special keys
                    result[key] = value
        
        # Validate and normalize result
        validated_result = validate_result(result)
        
        print("Pipeline result:", validated_result)
        return validated_result

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_result = {
            'llm_response': f'Error: {str(e)}',
            'error': str(e),
            'user_message': user_message
        }
        print("Pipeline error:", error_result)
        return error_result

if __name__ == "__main__":
    user_message = "Por que as pessoas compartilham fake news?"
    result = run_pipeline(user_message, language="Português", chat_history=None, use_simple=True)
    if result.get('clarification'):
        print("Clarification needed:", result['llm_response'])
    elif result.get('error'):
        print("Error:", result['error'])
    else:
        print("LLM response:\n", result["llm_response"]) 