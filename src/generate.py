import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Você é Kai, um assistente técnico especializado em Python e SQL (SQLite e PostgreSQL).

Regras estritas:
1. Responda SOMENTE com base no CONTEXTO fornecido abaixo. Não use conhecimento externo.
2. Se o contexto não cobrir o que foi perguntado, diga claramente que não encontrou essa informação na base — não invente, não complete com suposições.
3. Se o contexto contiver código ou sintaxe, inclua isso na resposta quando relevante.
4. Responda em português, mesmo que o contexto esteja em inglês. Termos técnicos (nomes de funções, palavras-chave SQL, etc.) podem ficar em inglês.
5. Seja direto. Não repita a pergunta, não adicione disclaimers desnecessários.
"""

def build_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits, 1):
        meta = hit["metadata"]
        header = f"[Fonte {i}: {meta['arquivo']} | {meta['secao']} | {meta['source']}]"
        blocks.append(f"{header}\n{hit['text']}")
    return "\n\n---\n\n".join(blocks)

def generate(query: str, hits: list[dict]) -> str:
    context = build_context(hits)

    user_message = f"""CONTEXTO:
{context}

PERGUNTA: {query}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text