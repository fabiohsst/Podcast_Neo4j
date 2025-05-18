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