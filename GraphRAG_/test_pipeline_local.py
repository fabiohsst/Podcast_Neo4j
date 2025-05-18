"""
Test script for running the LangGraph pipeline locally.
"""

import logging
import traceback
from pipeline_langgraph import run_pipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline_local_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LocalTest")

if __name__ == "__main__":
    print("=== Testing GraphRAG Pipeline Locally ===")
    
    # Test queries
    test_queries = [
        "Por que as pessoas compartilham fake news?",
        "What causes people to share misinformation?",
        "Como evitar a desinformação nas redes sociais?"
    ]
    
    # Chat history for context
    chat_history = [
        ("O que é fake news?", "Fake news são notícias falsas divulgadas como se fossem verdadeiras."),
        ("Como identificar fake news?", "É importante checar fontes e buscar informações em veículos confiáveis.")
    ]
    
    # Run tests
    for i, query in enumerate(test_queries):
        print(f"\n\nTest {i+1}: {query}")
        language = "Português" if any(word in query.lower() for word in ['por', 'que', 'como']) else "English"
        
        try:
            logger.info(f"Running pipeline with query: {query}")
            result = run_pipeline(query, language=language, chat_history=chat_history)
            
            if result.get('error'):
                print(f"⚠️ Error: {result['error']}")
                logger.error(f"Pipeline error: {result['error']}")
            else:
                print("✅ Success!")
                print("-" * 40)
                print(result["llm_response"])
                print("-" * 40)
                logger.info(f"Response: {result['llm_response'][:100]}...")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            logger.error(f"Exception in test {i+1}: {str(e)}")
            logger.error(traceback.format_exc())
    
    print("\n=== Test Complete ===")
    print("See pipeline_local_test.log for details") 