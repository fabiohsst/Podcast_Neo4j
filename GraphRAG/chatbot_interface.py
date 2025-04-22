"""
chatbot_interface.py

A Gradio-based chatbot interface for the Podcast GraphRAG system.
Connects retrieval, context building, and LLM modules for end-to-end Q&A.

Author: [Your Name]
"""

import gradio as gr
from retrieval_layer import retrieve_segments_by_keyword  # or your full pipeline
from context_builder import build_context
from llm_integration import query_llm

# Example episode metadata for demonstration
EPISODE_METADATA = {
    280: {"title": "Por Que As Pessoas Compartilham Fake News"}
}

def chatbot_fn(user_message, history):
    # Retrieve segments by keyword (replace with your full retrieval pipeline as needed)
    segments = retrieve_segments_by_keyword(user_message, limit=5)
    context = build_context(segments, EPISODE_METADATA, max_tokens=1500)
    answer = query_llm(context, user_message)
    return answer

iface = gr.ChatInterface(
    chatbot_fn,
    title="Podcast GraphRAG Chatbot",
    description="Ask about podcast episodes, topics, or get recommendations!"
)

if __name__ == "__main__":
    iface.launch() 