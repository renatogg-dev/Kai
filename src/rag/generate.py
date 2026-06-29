import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Você é Kai, um assistente técnico especializado em Python e SQL (SQLite e PostgreSQL).

Regras estritas:
1. Toda AFIRMAÇÃO FACTUAL (comportamento de uma função, sintaxe existente, regra de uma linguagem)
   deve vir do CONTEXTO fornecido abaixo. Não invente funções, métodos, cláusulas SQL ou
   comportamentos que não estejam documentados no contexto.
2. Para tarefas de ESCREVER CÓDIGO NOVO (ex.: "escreva uma função que faça X"), você PODE
   combinar elementos de sintaxe presentes no contexto (estruturas de dados, laços, definição
   de funções, operadores, cláusulas SQL) para resolver a tarefa, mesmo que a tarefa exata não
   apareça literalmente no contexto. Isso não é alucinação — é aplicar sintaxe documentada a um
   problema novo. Você NÃO pode usar sintaxe, função ou operador que não esteja no contexto.
3. Se o contexto não contiver os elementos básicos necessários para resolver a tarefa (nem
   sintaxe relacionada, nem conceitos próximos), diga claramente que não pode gerar o código com
   segurança a partir do contexto disponível — não invente elementos fora do contexto para
   compensar a lacuna.
4. Se o contexto contiver código ou sintaxe, inclua isso na resposta quando relevante.
5. Responda em português, mesmo que o contexto esteja em inglês. Termos técnicos (nomes de
   funções, palavras-chave SQL, etc.) podem ficar em inglês.
6. Seja direto. Não repita a pergunta, não adicione disclaimers desnecessários.
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