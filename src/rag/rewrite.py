import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"


def rewrite_query_with_history(query: str, history: list[dict]) -> str:
    """Transforma uma pergunta de seguimento em uma pergunta autonoma, usando
    as ultimas trocas da conversa. Se nao houver historico, retorna a query original."""
    if not history:
        return query

    # Usa só as últimas 3 trocas (6 mensagens) pra não estourar contexto à toa
    historico_recente = history[-6:]
    historico_texto = "\n".join(
        f"{'Usuário' if h['role'] == 'user' else 'Assistente'}: {h['content'][:300]}"
        for h in historico_recente
    )

    prompt = f"""Dado o histórico de conversa abaixo e a nova pergunta do usuário,
reescreva a nova pergunta como uma pergunta AUTÔNOMA e completa, que faça sentido
sozinha, sem precisar do histórico. Mantenha o idioma português. Se a pergunta já
for autônoma, apenas repita ela sem alterar.

HISTÓRICO:
{historico_texto}

NOVA PERGUNTA: {query}

Responda APENAS com a pergunta reescrita, sem explicações."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()