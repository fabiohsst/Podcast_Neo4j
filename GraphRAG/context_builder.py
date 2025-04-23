"""
context_builder.py

Aggregates and formats transcript segments and episode metadata for LLM input.

Author: Fabio Tavares
GitHub: https://github.com/fabiohsst
LinkedIn: https://www.linkedin.com/in/fabiohsst/
"""

import tiktoken  # For token counting with OpenAI models

def count_tokens(text, model_name="gpt-4o-mini-2024-07-18"):
    """
    Count tokens in a string using tiktoken (for OpenAI models).
    """
    enc = tiktoken.encoding_for_model(model_name)
    return len(enc.encode(text))

def build_context(segments, episode_metadata=None, max_tokens=2000, model_name="gpt-4o-mini-2024-07-18", rank_key=None, add_urls=False, summarize_if_too_long=False):
    """
    Build a context string for the LLM from transcript segments and optional metadata.
    - segments: list of dicts with 'text', 'episode_number', etc.
    - episode_metadata: dict mapping episode_number to metadata (title, url, ...)
    - rank_key: optional key to sort segments by (e.g., 'similarity')
    - add_urls: if True, include episode URLs in the context
    - summarize_if_too_long: if True, add a placeholder for future summarization logic
    """
    # Deduplicate segments by (episode_number, chunk_index)
    unique_segments = { (seg['episode_number'], seg.get('chunk_index', 0)): seg for seg in segments }
    segments = list(unique_segments.values())

    # Optionally, sort or rank segments by relevance/score
    if rank_key:
        segments = sorted(segments, key=lambda x: -x.get(rank_key, 0))

    context_parts = []
    total_tokens = 0

    for seg in segments:
        ep_info = ""
        if episode_metadata:
            meta = episode_metadata.get(seg['episode_number'])
            if meta:
                ep_info = f"Episode {seg['episode_number']}: {meta.get('title', '')}"
                if add_urls and meta.get('url'):
                    ep_info += f" ({meta['url']})"
                ep_info += "\n"
        chunk = f"{ep_info}Segment {seg.get('chunk_index', '')}: {seg['text']}\n"
        chunk_tokens = count_tokens(chunk, model_name)
        if total_tokens + chunk_tokens > max_tokens:
            if summarize_if_too_long:
                context_parts.append("[Context truncated. Summarization needed.]")
            break
        context_parts.append(chunk)
        total_tokens += chunk_tokens

    context = "\n".join(context_parts)
    return context

# Example usage
# if __name__ == "__main__":
#     # Example segments for episode 280
#     segments = [
#         {"episode_number": 280, "chunk_index": 1, "text": "Por que as pessoas compartilham fake news?", "similarity": 0.98},
#         {"episode_number": 280, "chunk_index": 2, "text": "Discussão sobre psicologia das redes sociais.", "similarity": 0.95},
#         {"episode_number": 280, "chunk_index": 3, "text": "Impacto das fake news na sociedade moderna.", "similarity": 0.93},
#     ]
#     # Example metadata for episode 280
#     episode_metadata = {
#         280: {"title": "Por Que As Pessoas Compartilham Fake News", "url": "https://www.b9.com.br/shows/naruhodo/naruhodo-280-por-que-as-pessoas-compartilham-fake-news"}
#     }
#     context = build_context(segments, episode_metadata, max_tokens=200, rank_key="similarity", add_urls=True)
#     print(context) 