"""
chatbot_interface.py

A Gradio-based chatbot interface for the Podcast GraphRAG system.
Connects retrieval, context building, and LLM modules for end-to-end Q&A.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import gradio as gr
from retrieval_layer import hybrid_retrieve
from context_builder import build_context
from llm_integration import query_llm, DEFAULT_MODEL
from test_context_llm import get_episode_metadata_neo4j  # Reuse the Neo4j metadata function

# Example episode metadata for demonstration (should be loaded from your DB in production)
EPISODE_METADATA = {
    280: {"title": "Por Que As Pessoas Compartilham Fake News", "url": "https://www.b9.com.br/shows/naruhodo/naruhodo-280-por-que-as-pessoas-compartilham-fake-news"}
}

def chatbot_fn(user_message, chat_history):
    # 1. Retrieve segments for the current user message
    segments = hybrid_retrieve(user_message, top_k=5, expand_depth=1)
    episode_numbers = {seg['episode_number'] for seg in segments}
    episode_metadata = get_episode_metadata_neo4j(episode_numbers)
    context = build_context(segments, episode_metadata, max_tokens=1500, rank_key="similarity", add_urls=True)

    # 2. Build conversation history string
    history_str = ""
    if chat_history:
        for user, assistant in chat_history:
            history_str += f"User: {user}\nAssistant: {assistant}\n"
    # Add the current user message
    history_str += f"User: {user_message}\nAssistant:"

    # 3. Combine context and history for the LLM
    full_prompt = (
        "You are a helpful podcast assistant specialized on the podcast 'Naruhodo'. "
        "Use the provided context and conversation history to answer the user's question.\n\n"
        f"Context:\n{context}\n\n"
        f"Conversation so far:\n{history_str}"
    )

    # 4. Query LLM
    answer = query_llm(context=full_prompt, user_query="", model=DEFAULT_MODEL)
    return answer

with gr.Blocks() as demo:
    gr.Markdown("# Podcast GraphRAG Chatbot\nPergunte sobre episódios, temas ou peça recomendações!")
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Sua pergunta")
    state = gr.State([])  # For chat history

    def respond(user_message, chat_history):
        answer = chatbot_fn(user_message, chat_history)
        chat_history = chat_history + [[user_message, answer]]
        return chat_history, chat_history

    msg.submit(respond, [msg, chatbot], [chatbot, chatbot])

if __name__ == "__main__":
    demo.launch(share=False) 