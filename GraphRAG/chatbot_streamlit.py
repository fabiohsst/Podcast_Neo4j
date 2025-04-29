import sys
import streamlit as st
from retrieval_layer import hybrid_retrieve, recommend_episodes
from context_builder import build_context
from llm_integration import query_llm, DEFAULT_MODEL
from test_context_llm import get_episode_metadata_neo4j
import time

def chatbot_fn(user_message, chat_history, language):
    LANGUAGE_CODE = {"Português": "Portuguese", "English": "English"}
    start_time = time.time()
    try:
        segments = hybrid_retrieve(user_message, top_k=5, expand_depth=1)
        episode_numbers = {seg['episode_number'] for seg in segments}
        episode_metadata = get_episode_metadata_neo4j(episode_numbers)
        context = build_context(segments, episode_metadata, max_tokens=2000, rank_key="similarity", add_urls=True)

        history_str = ""
        if chat_history:
            for user, assistant in chat_history:
                history_str += f"User: {user}\nAssistant: {assistant}\n"
        history_str += f"User: {user_message}\nAssistant:"

        system_prompt = (
            f"You are a highly knowledgeable and friendly assistant specialized in the Naruhodo podcast. "
            f"Your role is to help users deeply understand the topics discussed in the episodes, using a clear, engaging, and conversational style. "
            f"Always answer in {LANGUAGE_CODE[language]}.\n"
            f"Discuss the subject of the user's question, making fluid connections between insights from different episodes, and reference episodes inline as citations (e.g., [Ep. 123]). "
            f"At the end of your answer, provide a section titled 'Referências' (if in Portuguese) or 'References' (if in English), listing all episodes you cited, as clickable links using the provided URLs from the context. "
            f"Only include episodes in the references section if you have a valid URL for them (provided in the context).\n"
            f"If you mention an episode in your answer but do not have a URL for it, write: "(URL not available)" instead of a link.\n"
            f"Never invent or guess URLs. Never repeat references from previous answers unless they are relevant to the current user question.\n"
            f"Format your answer using this template (replace with the correct language and number of episodes):\n"
            f"""
[Your answer here, making fluid connections between episode insights and referencing episodes inline, e.g., ... [Ep. 123].]

Referências:
- [Título do episódio 1](URL)
- [Título do episódio 2](URL)
- [Título do episódio 3] (URL not available)
"""
            "Use the provided context and conversation history to answer the user's question.\n\n"
        )
        full_prompt = (
            system_prompt +
            f"Context:\n{context}\n\n" +
            f"Conversation so far:\n{history_str}"
        )
        answer = query_llm(context=full_prompt, user_query="", model=DEFAULT_MODEL)
        return answer
    except Exception as e:
        return (
            "Desculpe, ocorreu um erro ao processar sua pergunta. "
            "Por favor, tente novamente mais tarde ou reformule sua questão.\n\n"
            f"Detalhes técnicos: {str(e)}"
        )

def main():
    st.set_page_config(page_title="Naruhodo! Chatbot", page_icon="🎙️", layout="centered")
    # Custom CSS for Montserrat font and sidebar color
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
        html, body, [class*='css']  {
            font-family: 'Montserrat', Arial, sans-serif !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #F44336 !important;
            color: white !important;
        }
        .sidebar-title {
            color: white !important;
            font-size: 2em;
            font-weight: bold;
        }
        .sidebar-tagline {
            color: #111 !important;
            font-size: 0.85em !important;
            font-family: monospace;
            font-weight: 500;
            margin-bottom: 0.2em;
            line-height: 1.1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .sidebar-presenter {
            color: #222 !important;
            font-size: 0.62em !important; /* 4pt less than tagline */
            font-family: monospace;
            margin-bottom: 1em;
            line-height: 1.1;
        }
        .sidebar-btn {
            background: #111 !important;
            color: black !important;
            border: none;
            border-radius: 6px;
            padding: 0.5em 1.2em;
            margin-right: 0.5em;
            font-weight: bold;
            font-size: 1em;
            cursor: pointer;
        }
        .sidebar-btn.selected {
            background: #111 !important;
            color: black !important;
            border: 2px solid white !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    LANGUAGE_OPTIONS = ["Português", "English"]
    UI_TEXT = {
        "title": {"Português": "Naruhodo!", "English": "Naruhodo!"},
        "tagline": {"Português": "O podcast pra quem tem fome de aprender", "English": "The podcast for those who are hungry to learn"},
        "presenter": {
            "Português": "Apresentado por Ken Fujioka & Altay de Souza",
            "English": "Hosted by Ken Fujioka & Altay de Souza"
        },
        "input_label": {"Português": "Faça uma pergunta", "English": "Make a question"},
        "references": {"Português": "Referências", "English": "References"},
        "chat_header": {"Português": "Converse com o Assistente", "English": "Chat with the Assistant"},
    }

    # Sidebar with color and language buttons
    with st.sidebar:
        st.markdown(f"<div class='sidebar-title'>{UI_TEXT['title']['Português']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-tagline'>{UI_TEXT['tagline']['Português']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sidebar-presenter'>{UI_TEXT['presenter']['Português']}</div>", unsafe_allow_html=True)
        language = st.selectbox("Idioma / Language", LANGUAGE_OPTIONS, index=0)
        st.markdown(f"<div style='margin-top:1em;'><a style='color:white;' href='https://github.com/fabiohsst/Podcast_Neo4j/blob/main/GraphRAG/chatbot_streamlit.py' target='_blank'>Ver código fonte</a></div>", unsafe_allow_html=True)

    # No header or divider in main area

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Como posso ajudar?" if language == "Português" else "How can I help you?"}
        ]

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input(UI_TEXT["input_label"][language]):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        chat_history = []
        for i in range(0, len(st.session_state["messages"]) - 1, 2):
            user_msg = st.session_state["messages"][i]["content"]
            assistant_msg = st.session_state["messages"][i+1]["content"] if i+1 < len(st.session_state["messages"]) else ""
            chat_history.append((user_msg, assistant_msg))

        with st.spinner("O assistente está pensando..." if language == "Português" else "The assistant is thinking..."):
            answer = chatbot_fn(prompt, chat_history, language)

        st.session_state["messages"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)

if __name__ == "__main__":
    main() 