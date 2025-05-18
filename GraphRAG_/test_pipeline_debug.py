"""
Test script for debugging the GraphRAG pipeline.
Provides verbose logging of each step to identify errors.
"""

import logging
import traceback
from pipeline_langgraph import run_pipeline

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("graphrag_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GraphRAG")

def test_simple_pipeline():
    """Test the simplified pipeline implementation"""
    logger.info("Testing simple pipeline implementation...")
    
    # Simple test query
    user_message = "Por que as pessoas compartilham fake news?"
    language = "Português"
    chat_history = None  # Simplified for testing
    
    try:
        logger.info(f"Running pipeline with input: {user_message}")
        result = run_pipeline(user_message, language=language, chat_history=chat_history, use_simple=True)
        
        logger.info("Pipeline execution complete")
        
        # Check result structure
        if result.get('error'):
            logger.error(f"Pipeline reported an error: {result['error']}")
            logger.error(f"Response provided: {result.get('llm_response', 'No response')}")
            return False
            
        logger.info("Pipeline result successful")
        logger.info(f"LLM response: {result.get('llm_response', 'No response')}")
        return True
        
    except Exception as e:
        logger.error(f"Exception in pipeline: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def test_langgraph_pipeline():
    """Test the LangGraph-based pipeline implementation"""
    logger.info("Testing LangGraph pipeline implementation...")
    
    # Simple test query
    user_message = "Por que as pessoas compartilham fake news?"
    language = "Português"
    chat_history = None  # Simplified for testing
    
    try:
        logger.info(f"Running pipeline with input: {user_message}")
        result = run_pipeline(user_message, language=language, chat_history=chat_history, use_simple=False)
        
        logger.info("Pipeline execution complete")
        
        # Check result structure
        if result.get('error'):
            logger.error(f"Pipeline reported an error: {result['error']}")
            logger.error(f"Response provided: {result.get('llm_response', 'No response')}")
            return False
            
        logger.info("Pipeline result successful")
        logger.info(f"LLM response: {result.get('llm_response', 'No response')}")
        return True
        
    except Exception as e:
        logger.error(f"Exception in pipeline: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("==== Testing GraphRAG Simple Pipeline ====")
    simple_success = test_simple_pipeline()
    print(f"Simple Pipeline Test {'succeeded' if simple_success else 'failed'}. See graphrag_debug.log for details.")
    
    print("\n==== Testing GraphRAG LangGraph Pipeline ====")
    langgraph_success = test_langgraph_pipeline()
    print(f"LangGraph Pipeline Test {'succeeded' if langgraph_success else 'failed'}. See graphrag_debug.log for details.") 