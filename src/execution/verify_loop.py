import os
from anthropic import Anthropic
from dotenv import load_dotenv

from src.execution.sandbox import extract_code_blocks, run_snippet

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"
MAX_TENTATIVAS = 3


def self_correct(pergunta: str, codigo: str, linguagem: str, erro: str) -> str:
    prompt = f"""O código {linguagem} abaixo foi gerado para responder a seguinte pergunta,
mas falhou ao executar.

PERGUNTA ORIGINAL: {pergunta}

CÓDIGO COM ERRO:
```{linguagem}
{codigo}
```

ERRO OBTIDO:
{erro}

Corrija o código. Responda APENAS com o bloco de código corrigido, no formato
```{linguagem}
codigo aqui
```
sem nenhuma explicação antes ou depois.
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = response.content[0].text
    blocos = extract_code_blocks(texto)
    return blocos[0]["codigo"] if blocos else texto.strip()


def verify_and_correct(pergunta: str, resposta: str) -> dict:
    """Extrai codigo da resposta, executa, e autocorrige se falhar. Retorna log completo."""
    blocos = extract_code_blocks(resposta)
    if not blocos:
        return {"tem_codigo": False, "tentativas": [], "sucesso_final": None}

    bloco = blocos[0]  # v1: valida o primeiro bloco de codigo da resposta
    codigo_atual = bloco["codigo"]
    linguagem = bloco["linguagem"]
    tentativas = []

    for i in range(1, MAX_TENTATIVAS + 1):
        resultado = run_snippet({"linguagem": linguagem, "codigo": codigo_atual})
        tentativas.append({
            "numero": i,
            "codigo": codigo_atual,
            "sucesso": resultado["sucesso"],
            "stdout": resultado["stdout"],
            "stderr": resultado["stderr"],
        })

        if resultado["sucesso"]:
            return {"tem_codigo": True, "tentativas": tentativas, "sucesso_final": True, "codigo_final": codigo_atual}

        if i < MAX_TENTATIVAS:
            codigo_atual = self_correct(pergunta, codigo_atual, linguagem, resultado["stderr"])

    return {"tem_codigo": True, "tentativas": tentativas, "sucesso_final": False, "codigo_final": codigo_atual}