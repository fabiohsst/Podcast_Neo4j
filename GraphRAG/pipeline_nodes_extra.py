# Feature 5: Clarification Node
def clarification_node(inputs):
    """
    Checks if the user query is ambiguous and, if so, returns a clarification prompt.
    Otherwise, passes through the original input.
    """
    user_message = inputs.get('user_message', '')
    # Simple heuristic: if the message is too short or generic, ask for clarification
    if len(user_message.split()) < 3:
        return {'clarification': True, 'clarification_prompt': "Could you please clarify your question?", **inputs}
    return {'clarification': False, **inputs}

# Feature 6: Logging Node
def logging_node(inputs):
    """
    Logs the pipeline state for analytics/debugging.
    """
    import json
    with open("pipeline_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(inputs, ensure_ascii=False) + "\n")
    return inputs

# Feature 9: Citation Node
def citation_node(inputs):
    """
    Parses the LLM response and appends a formatted reference section based on episode_metadata.
    """
    response = inputs.get('llm_response', '')
    episode_metadata = inputs.get('episode_metadata', {})
    # Simple example: append all episode titles/urls as references
    references = "\nReferências:\n"
    for ep, meta in episode_metadata.items():
        if meta.get('url'):
            references += f"- [{meta.get('title', '')}]({meta['url']})\n"
        else:
            references += f"- [{meta.get('title', '')}] (URL not available)\n"
    response += references
    return {**inputs, 'llm_response': response}

# Feature 10: Error Handling Node
def error_handling_node(inputs):
    """
    Catches errors in the pipeline and returns a fallback message if needed.
    """
    if 'llm_response' in inputs and not inputs['llm_response']:
        return {**inputs, 'llm_response': "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente."}
    return inputs

# Feature 11: Language Node
def language_node(inputs):
    """
    Detects or sets the answer language. Optionally translates context or user_message.
    """
    user_message = inputs.get('user_message', '')
    # Simple heuristic: detect Portuguese vs. English
    if any(word in user_message.lower() for word in ['por', 'que', 'as', 'pessoas']):
        language = 'Portuguese'
    else:
        language = 'English'
    return {**inputs, 'language': language}

# Feature 12: Streaming LLM Node (stub)
def streaming_llm_node(inputs):
    """
    Calls the LLM and streams the response (if supported by your LLM provider).
    For now, just calls llm_node as a placeholder.
    """
    from llm_integration import llm_node
    return llm_node(inputs) 