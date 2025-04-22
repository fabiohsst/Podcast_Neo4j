"""
context_builder.py

Aggregates and formats transcript segments and episode metadata for LLM input.

Author: [Your Name]
"""

import tiktoken  # For token counting with OpenAI models

def count_tokens(text, model_name="gpt-4o-mini-2024-07-18"):
    """
    Count tokens in a string using tiktoken (for OpenAI models).
    """
    enc = tiktoken.encoding_for_model(model_name)
    return len(enc.encode(text))

def build_context(segments, episode_metadata=None, max_tokens=2000, model_name="gpt-4o-mini-2024-07-18"):
    """
    Build a context string for the LLM from transcript segments and optional metadata.
    Segments should be a list of dicts with 'text', 'episode_number', etc.
    """
    context_parts = []
    total_tokens = 0

    # Optionally, sort or rank segments by relevance/score
    # segments = sorted(segments, key=lambda x: -x.get('similarity', 0))

    for seg in segments:
        ep_info = ""
        if episode_metadata:
            meta = episode_metadata.get(seg['episode_number'])
            if meta:
                ep_info = f"Episode {seg['episode_number']}: {meta['title']}\n"
        chunk = f"{ep_info}Segment {seg.get('chunk_index', '')}: {seg['text']}\n"
        chunk_tokens = count_tokens(chunk, model_name)
        if total_tokens + chunk_tokens > max_tokens:
            break
        context_parts.append(chunk)
        total_tokens += chunk_tokens

    context = "\n".join(context_parts)
    return context

# Example usage
if __name__ == "__main__":
    # Example segments for episode 280
    segments = [
        {"episode_number": 280, "chunk_index": 1, "text": "Por que as pessoas compartilham fake news?"},
        {"episode_number": 280, "chunk_index": 2, "text": "Discussão sobre psicologia das redes sociais."},
        {"episode_number": 280, "chunk_index": 3, "text": "Impacto das fake news na sociedade moderna."},
    ]
    # Example metadata for episode 280
    episode_metadata = {
        280: {"title": "Por Que As Pessoas Compartilham Fake News"}
    }
    context = build_context(segments, episode_metadata, max_tokens=200)
    print(context) 