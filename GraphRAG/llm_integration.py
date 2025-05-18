"""
llm_integration.py

Sends context and user queries to the OpenAI API using the gpt-4o-mini-2024-07-18 model.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import os
import openai
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"

# Create OpenAI client (for openai>=1.0.0)
client = openai.Client(api_key=OPENAI_API_KEY)

def query_llm(prompt, model=DEFAULT_MODEL, max_tokens=512, temperature=0.2):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()

# --- LangGraph Node: LLM ---
def llm_node(inputs):
    """
    LangGraph node for LLM call. Expects a dict with 'context' (and optionally 'user_message' and 'chat_history').
    Returns a dict with 'llm_response', 'context', and 'user_message'.
    """
    context = inputs.get('context', '')
    user_message = inputs.get('user_message', None)
    chat_history = inputs.get('chat_history', None)
    # Format chat history if present
    history_str = ""
    if chat_history:
        for user, assistant in chat_history:
            history_str += f"User: {user}\nAssistant: {assistant}\n"
    # Build the prompt
    prompt = context
    if history_str:
        prompt += f"\nConversation so far:\n{history_str}"
    if user_message:
        prompt += f"User: {user_message}\nAssistant:"
    response = query_llm(prompt)
    return {
        'llm_response': response,
        'context': context,
        'user_message': user_message
    }

# Example usage
# if __name__ == "__main__":
#     # Example context and user query
#     context = (
#         "Episode 280: Por Que As Pessoas Compartilham Fake News\n"
#         "Segment 1: Por que as pessoas compartilham fake news?\n"
#         "Segment 2: Discussão sobre psicologia das redes sociais.\n"
#         "Segment 3: Impacto das fake news na sociedade moderna.\n"
#     )
#     user_query = "Por que as pessoas tendem a compartilhar notícias falsas nas redes sociais?"
#     answer = query_llm(context, user_query)
#     print("LLM Response:\n", answer) 