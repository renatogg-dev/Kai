import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
JUDGE_MODEL = "claude-sonnet-4-6"


def recall_at_k(hits: list[dict], arquivo_esperado: str) -> int:
    """1 se o arquivo esperado aparece em algum dos hits retornados, senão 0."""
    arquivos = [h["metadata"]["arquivo"] for h in hits]
    return 1 if arquivo_esperado in arquivos else 0


def reciprocal_rank(hits: list[dict], arquivo_esperado: str) -> float:
    """1/posicao do primeiro hit correto (0 se não achou)."""
    for i, h in enumerate(hits, start=1):
        if h["metadata"]["arquivo"] == arquivo_esperado:
            return 1.0 / i
    return 0.0


def faithfulness(pergunta: str, resposta: str, contexto: str) -> str:
    """LLM-as-judge: a resposta se apoia no contexto? 'sim' | 'parcial' | 'nao'."""
    prompt = f"""Você é um avaliador. Sua tarefa é dizer se a RESPOSTA abaixo está
fundamentada APENAS no CONTEXTO fornecido, sem inventar informação externa.

CONTEXTO:
{contexto}

PERGUNTA: {pergunta}

RESPOSTA A AVALIAR:
{resposta}

Responda com exatamente uma palavra: "sim" (totalmente fundamentada no contexto),
"parcial" (mistura contexto com algo não suportado), ou "nao" (não fundamentada
ou inventou informação que não está no contexto). Se a resposta corretamente diz
que não encontrou a informação no contexto (recusa), responda "sim".
"""
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )
    veredito = response.content[0].text.strip().lower()
    if veredito not in ("sim", "parcial", "nao"):
        veredito = "parcial"
    return veredito