# Feature 5: Clarification Node
def clarification_node(inputs):
    """
    Checks if the user query is ambiguous and, if so, returns a clarification prompt.
    Otherwise, passes through the original input.
    """
    print("clarification_node input:", inputs)
    user_message = inputs.get('user_message', '')
    
    # Simple heuristic: if the message is too short or generic, ask for clarification
    if len(user_message.split()) < 3:
        # Return early with clarification request
        return {
            **inputs,
            'clarification': True,
            'clarification_prompt': "Could you please clarify your question?",
            'user_message': user_message,
            'llm_response': "Could you please clarify your question?"  # Add this for consistent output
        }
    
    # Continue with pipeline if no clarification needed
    return {
        **inputs, 
        'clarification': False
    }

# Feature 6: Logging Node
def logging_node(inputs):
    """
    Logs the pipeline state for analytics/debugging.
    """
    print("logging_node input:", inputs)
    import json
    import os
    
    # Determine the correct log file path
    log_file = "pipeline_log.jsonl"
    if os.path.exists("Podcast_Neo4j/pipeline_log.jsonl"):
        log_file = "Podcast_Neo4j/pipeline_log.jsonl"
    elif os.path.exists("GraphRAG/logs/pipeline_log.jsonl"):
        log_file = "GraphRAG/logs/pipeline_log.jsonl"
    
    try:
        # Create a simplified log entry
        log_entry = {
            'user_message': inputs.get('user_message'),
            'llm_response': inputs.get('llm_response'),
            'error': inputs.get('error') or inputs.get('llm_error'),
            'context_length': len(inputs.get('context', '')) if 'context' in inputs else None,
            'segments_count': len(inputs.get('segments', [])) if 'segments' in inputs else None
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[Warning] Failed to log pipeline state: {e}")
    return inputs

# Feature 9: Citation Node
def citation_node(inputs):
    """
    Parses the LLM response and appends a formatted reference section based on episode_metadata.
    """
    print("citation_node input:", inputs)
    response = inputs.get('llm_response', '')
    episode_metadata = inputs.get('episode_metadata', {})
    if not isinstance(episode_metadata, dict):
        episode_metadata = {}
    references = "\nReferências:\n"
    for ep, meta in episode_metadata.items():
        if isinstance(meta, dict) and meta.get('url'):
            references += f"- [{meta.get('title', '')}]({meta['url']})\n"
        elif isinstance(meta, dict):
            references += f"- [{meta.get('title', '')}] (URL not available)\n"
        else:
            references += f"- [Unknown episode] (URL not available)\n"
    response += references
    return {**inputs, 'llm_response': response}

# Feature 10: Error Handling Node
def error_handling_node(inputs):
    """
    Catches errors in the pipeline and returns a fallback message if needed.
    """
    print("error_handling_node input:", inputs)
    
    # Check for explicit LLM errors first
    if inputs.get('llm_error'):
        return {
            **inputs,
            'llm_response': f"Desculpe, ocorreu um erro ao processar sua pergunta: {inputs['llm_error']}",
            'error': inputs['llm_error']
        }
    
    # Check for missing or empty LLM response
    if not inputs.get('llm_response'):
        return {
            **inputs,
            'llm_response': "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.",
            'error': 'No LLM response generated'
        }
    
    # If we have a valid response, pass through all inputs
    return inputs

# Feature 11: Language Node
def language_node(inputs):
    """
    Detects or sets the answer language. Optionally translates context or user_message.
    """
    print("language_node input:", inputs)
    user_message = inputs.get('user_message', '')
    # Use provided language if available, otherwise detect
    language = inputs.get('language')
    if not language:
        # Simple heuristic: detect Portuguese vs. English
        if any(word in user_message.lower() for word in ['por', 'que', 'as', 'pessoas']):
            language = 'Portuguese'
        else:
            language = 'English'
    return {**inputs, 'language': language}

# Feature 12: Streaming LLM Node
def streaming_llm_node(inputs):
    """
    Calls the LLM and streams the response (if supported by your LLM provider).
    For now, just calls llm_node as a placeholder.
    """
    print("streaming_llm_node input:", inputs)
    from llm_integration import llm_node
    
    try:
        output = llm_node(inputs)
        if output.get('llm_error'):
            return {
                **inputs,
                'llm_response': None,
                'llm_error': output['llm_error']
            }
        if not output.get('llm_response'):
            return {
                **inputs,
                'llm_response': None,
                'llm_error': 'No response from LLM'
            }
        return {**inputs, **output}
    except Exception as e:
        return {
            **inputs,
            'llm_response': None,
            'llm_error': str(e)
        } 