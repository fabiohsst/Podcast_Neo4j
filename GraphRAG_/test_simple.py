"""
Simple test script to verify each node in the GraphRAG pipeline individually.
"""

from retrieval_layer import retrieval_node
from context_builder import (
    deduplication_node,
    ranking_node,
    metadata_enrichment_node,
    context_formatting_node
)
from pipeline_nodes_extra import (
    clarification_node,
    language_node,
    streaming_llm_node
)

def test_individual_nodes():
    """Test each node individually with a static input"""
    print("=== Testing Individual Pipeline Nodes ===")
    
    # Initial state
    state = {'user_message': 'Por que as pessoas compartilham fake news?'}
    print("\nInitial State:", state)
    
    # Test retrieval node
    print("\n--- Testing Retrieval Node ---")
    try:
        retrieval_result = retrieval_node(state)
        print("Retrieval Success:", bool(retrieval_result.get('segments')))
        print(f"Retrieved {len(retrieval_result.get('segments', []))} segments")
    except Exception as e:
        print(f"Retrieval Error: {str(e)}")
    
    # Test subsequent nodes if retrieval succeeded
    if retrieval_result and not retrieval_result.get('error'):
        # Test clarification
        print("\n--- Testing Clarification Node ---")
        try:
            clarify_result = clarification_node(retrieval_result)
            print("Clarification needed:", clarify_result.get('clarification', False))
        except Exception as e:
            print(f"Clarification Error: {str(e)}")
            
        # Test language detection
        print("\n--- Testing Language Node ---")
        try:
            lang_result = language_node(clarify_result)
            print("Detected language:", lang_result.get('language'))
        except Exception as e:
            print(f"Language Error: {str(e)}")
            
        # Test deduplication
        print("\n--- Testing Deduplication Node ---")
        try:
            dedup_result = deduplication_node(lang_result)
            print(f"After deduplication: {len(dedup_result.get('segments', []))} segments")
        except Exception as e:
            print(f"Deduplication Error: {str(e)}")
            
        # Test ranking
        print("\n--- Testing Ranking Node ---")
        try:
            ranking_result = ranking_node(dedup_result)
            print("Ranking completed.")
        except Exception as e:
            print(f"Ranking Error: {str(e)}")
            
        # Test metadata enrichment
        print("\n--- Testing Metadata Enrichment Node ---")
        try:
            meta_result = metadata_enrichment_node(ranking_result)
            print(f"Retrieved metadata for {len(meta_result.get('episode_metadata', {}))} episodes")
        except Exception as e:
            print(f"Metadata Error: {str(e)}")
            
        # Test context formatting
        print("\n--- Testing Context Formatting Node ---")
        try:
            ctx_result = context_formatting_node(meta_result)
            context = ctx_result.get('context', '')
            print(f"Generated context with {len(context)} characters")
        except Exception as e:
            print(f"Context Formatting Error: {str(e)}")
            
        # Test LLM
        print("\n--- Testing LLM Node ---")
        try:
            llm_result = streaming_llm_node(ctx_result)
            response = llm_result.get('llm_response')
            error = llm_result.get('llm_error')
            if error:
                print(f"LLM Error: {error}")
            elif response:
                print(f"LLM generated response: {response[:100]}...")
            else:
                print("No response generated.")
        except Exception as e:
            print(f"LLM Error: {str(e)}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_individual_nodes() 