"""
chatbot_interface.py

A Gradio-based chatbot interface for the Podcast GraphRAG system.
Connects retrieval, context building, and LLM modules for end-to-end Q&A.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import gradio as gr
from retrieval_layer import hybrid_retrieve, recommend_episodes
from context_builder import build_context
from llm_integration import query_llm, DEFAULT_MODEL
from test_context_llm import get_episode_metadata_neo4j  # Reuse the Neo4j metadata function
import time
import logging
from collections import Counter
import os
import atexit

# Set up logging to file in the absolute logs directory
logging.basicConfig(
    filename=r"G:\My Drive\Projects\naruhodo_references\references_Link\Podcast_Neo4j\GraphRAG\logs\chatbot_latency.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    force=True
)
atexit.register(logging.shutdown)

# Test logging line to verify logging is working
logging.info("Logging test: chatbot_interface.py started")

LANGUAGE_OPTIONS = ["Português", "English"]
LANGUAGE_CODE = {"Português": "Portuguese", "English": "English"}

# Example episode metadata for demonstration (should be loaded from your DB in production)
EPISODE_METADATA = {
    280: {"title": "Por Que As Pessoas Compartilham Fake News", "url": "https://www.b9.com.br/shows/naruhodo/naruhodo-280-por-que-as-pessoas-compartilham-fake-news"}
}

# Language-dependent UI text
UI_TEXT = {
    "title": {"Português": "Naruhodo!", "English": "Naruhodo!"},
    "tagline": {"Português": "O podcast pra quem tem fome de aprender", "English": "The podcast for those who are hungry to learn"},
    "visit_site": {"Português": "Visite o site oficial", "English": "Visit the official website"},
    "chat_header": {"Português": "Pergunte sobre episódios, temas ou peça recomendações!", "English": "Ask about episodes, topics, or request recommendations!"},
    "input_label": {"Português": "Faça uma pergunta", "English": "Make a question"},
    "divider_main": {"Português": "Converse com o Assistente", "English": "Chat with the Assistant"},
    "divider_recs": {"Português": "Episódios Recomendados", "English": "Recommended Episodes"},
    "loading": {"Português": "O assistente está pensando...", "English": "The assistant is thinking..."},
    "presenter": {
        "Português": "Apresentado por Ken Fujioka & Altay de Souza",
        "English": "Hosted by Ken Fujioka & Altay de Souza"
    }
}

def chatbot_fn(user_message, chat_history, language):
    start_time = time.time()
    try:
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
        history_str += f"User: {user_message}\nAssistant:"

        # 3. Combine context and history for the LLM
        system_prompt = (
            f"You are a helpful podcast assistant specialized on the podcast Naruhodo. "
            f"Always answer in {LANGUAGE_CODE[language]}.\n"
            f"At the end of every answer, always include a section titled 'Episódios recomendados:' (if in Portuguese) or 'Recommended Episodes:' (if in English) with the recommended episodes as clickable links.\n"
            f"Do not use the section title 'Fontes' or any other title for sources or references.\n"
            f"Always use ONLY the section title for recommendations as described above.\n"
            f"Format your answer using this template (replace with the correct language):\n"
            f"""
[Your answer here]

Episódios recomendados:
- [Título do episódio 1](URL)
- [Título do episódio 2](URL)
- [Título do episódio 3](URL)
"""
            f"If the user selected English, use 'Recommended Episodes:' instead.\n"
            "Use the provided context and conversation history to answer the user's question.\n\n"
        )
        full_prompt = (
            system_prompt +
            f"Context:\n{context}\n\n"
            f"Conversation so far:\n{history_str}"
        )

        # 4. Query LLM
        answer = query_llm(context=full_prompt, user_query="", model=DEFAULT_MODEL)

        # 5. Log latency and query
        end_time = time.time()
        elapsed = end_time - start_time
        logging.info(f"Query: {user_message} | Language: {language} | Latency: {elapsed:.2f} seconds")

        return answer
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        logging.error(f"Error for query '{user_message}': {str(e)} | Latency: {elapsed:.2f} seconds")
        return (
            "Desculpe, ocorreu um erro ao processar sua pergunta. "
            "Por favor, tente novamente mais tarde ou reformule sua questão.\n\n"
            f"Detalhes técnicos: {str(e)}"
        )

# Place helper functions before Gradio Blocks UI

def render_header(lang, _unused=None):
    return f"""
    <div style='background:#F44336; padding:0; min-height:0;'>
      <div style='max-width:900px; margin:0 auto; display:flex; align-items:flex-end; justify-content:flex-start; padding:8px 0 4px 0;'>
        <div style='flex:0 0 84px; text-align:center; padding:0 18px 0 0;'>
          <img src='https://assets.b9.com.br/wp-content/uploads/2019/08/naruhodo.jpg' alt='Naruhodo! Logo' style='height:72px; width:72px; object-fit:contain; border-radius:8px; display:block; background:#fff;'/>
        </div>
        <div style='flex:1; min-width:220px; text-align:left; display:flex; flex-direction:column; justify-content:flex-end; padding-left:0;'>
          <div style='font-size:2em; color:white; font-weight:bold; letter-spacing:-1px; line-height:1;'>Naruhodo!</div>
          <div style='font-size:1.15em; color:#111; font-family:monospace; font-weight:500; margin:2px 0 2px 0;'>{UI_TEXT['tagline'][lang]}</div>
          <div style='font-size:0.85em; color:white; font-family:monospace; margin:2px 0 0 0;'>{UI_TEXT['presenter'][lang]}</div>
        </div>
      </div>
    </div>
    """

def render_divider(label, color="#F44336"):
    return f"""
    <div style='margin:32px 0 16px 0; display:flex; align-items:center;'>
        <hr style='flex:1; border:none; border-top:2px solid {color}; margin:0 16px;'>
        <span style='font-size:1.1em; color:{color}; font-weight:bold; letter-spacing:1px;'>{label}</span>
        <hr style='flex:1; border:none; border-top:2px solid {color}; margin:0 16px;'>
    </div>
    """

with gr.Blocks() as demo:
    gr.HTML("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
    body, .gradio-container, .gr-block, .gr-box, .gr-markdown, .gr-chatbot, .gr-textbox, .gr-button {
        font-family: 'Montserrat', Arial, sans-serif !important;
    }
    </style>
    """)

    # Header section with dynamic text
    header_md = gr.Markdown(render_header("Português"), elem_id="naruhodo-header")

    # Language selection buttons (Gradio only, with checkmark for selected)
    lang_pt = gr.Button("✔️ Português")
    lang_en = gr.Button("English")
    selected_lang = gr.State("Português")

    # Enable Markdown rendering for answers
    chatbot = gr.Chatbot(type='messages', render_markdown=True)
    msg = gr.Textbox(label=UI_TEXT["input_label"]["Português"], placeholder="")
    state = gr.State([])  # For chat history

    def set_lang_pt(chat_history):
        return (
            render_header("Português"),
            "✔️ Português",
            "English",
            "Português",
            chatbot
        )

    def set_lang_en(chat_history):
        return (
            render_header("English"),
            "Português",
            "✔️ English",
            "English",
            chatbot
        )

    lang_pt.click(set_lang_pt, [chatbot], [header_md, lang_pt, lang_en, selected_lang, chatbot])
    lang_en.click(set_lang_en, [chatbot], [header_md, lang_pt, lang_en, selected_lang, chatbot])

    def respond(user_message, chat_history, language):
        # Convert chat_history to tuples for legacy code
        history_tuples = [(m['content'], a['content']) for m, a in zip(chat_history[::2], chat_history[1::2])] if chat_history else []
        answer = chatbot_fn(user_message, history_tuples, language)
        chat_history_new = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer}
        ]
        return chat_history_new, chat_history_new

    msg.submit(respond, [msg, chatbot, selected_lang], [chatbot, chatbot])

if __name__ == "__main__":
    demo.launch(share=True) 