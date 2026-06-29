import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
JUDGE_MODEL = "claude-sonnet-4-6"


def recall_at_k(hits: list[dict], arquivo_esperado) -> int:
    aceitos = arquivo_esperado if isinstance(arquivo_esperado, list) else [arquivo_esperado]
    arquivos = [h["metadata"]["arquivo"] for h in hits]
    return 1 if any(a in arquivos for a in aceitos) else 0


def reciprocal_rank(hits: list[dict], arquivo_esperado) -> float:
    aceitos = arquivo_esperado if isinstance(arquivo_esperado, list) else [arquivo_esperado]
    for i, h in enumerate(hits, start=1):
        if h["metadata"]["arquivo"] in aceitos:
            return 1.0 / i
    return 0.0


def faithfulness(pergunta: str, resposta: str, contexto: str) -> str:
    """LLM-as-judge: a resposta se apoia no contexto? 'sim' | 'parcial' | 'nao'."""
    prompt = f"""Você é um avaliador. Sua tarefa é dizer se a RESPOSTA abaixo está
fundamentada no CONTEXTO fornecido, sem inventar FATOS que não estão lá.

CONTEXTO:
{contexto}

PERGUNTA: {pergunta}

RESPOSTA A AVALIAR:
{resposta}

Regra importante: se a pergunta pede para ESCREVER CÓDIGO NOVO, a resposta pode
COMPOR elementos de sintaxe presentes no contexto (estruturas de dados, laços,
definição de função, operadores, cláusulas SQL) para resolver uma tarefa que não
aparece literalmente no contexto. Isso conta como fundamentado ("sim"), não como
"parcial" — desde que nenhum elemento de sintaxe usado seja estranho ao contexto.

Responda com exatamente uma palavra: "sim" (fundamentada, incluindo composição
válida de sintaxe do contexto), "parcial" (usa algum elemento de sintaxe ou fato
que não está no contexto, mas não é grave), ou "nao" (inventou fato ou função que
não existe / não está documentada). Se a resposta corretamente diz que não
encontrou a informação no contexto (recusa), responda "sim".
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

def codigo_executa(pergunta: str, resposta: str, usar_loop: bool) -> dict:
    from src.execution.sandbox import extract_code_blocks, run_snippet
    from src.execution.verify_loop import verify_and_correct

    if not usar_loop:
        blocos = extract_code_blocks(resposta)
        if not blocos:
            return {"sucesso": False, "motivo": "sem_codigo"}
        resultado = run_snippet(blocos[0])
        return {"sucesso": resultado["sucesso"], "motivo": resultado.get("stderr", "")}
    else:
        resultado = verify_and_correct(pergunta, resposta)
        if not resultado["tem_codigo"]:
            return {"sucesso": False, "motivo": "sem_codigo"}
        return {
            "sucesso": resultado["sucesso_final"],
            "motivo": "",
            "tentativas": len(resultado["tentativas"]),
        }