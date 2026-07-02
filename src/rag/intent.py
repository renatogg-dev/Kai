import re

VERBOS_GERACAO = [
    "escreva", "escreve", "crie", "crie uma", "gere", "gera",
    "implemente", "implementa", "construa", "constrói", "constroi",
    "desenvolva", "desenvolve", "monte", "monta", "programe", "programa",
    "faça uma função", "faca uma funcao", "faça uma query", "faca uma query",
    "me dá um código", "me da um codigo", "me dá o código", "me da o codigo",
    "me dá um exemplo de código", "me da um exemplo de codigo",
]


def is_code_generation_request(query: str) -> bool:
    """Heuristica: a pergunta esta pedindo para GERAR codigo novo (deve
    disparar o execution loop) ou e uma pergunta conceitual/explicativa
    (nao deve, mesmo que a resposta contenha blocos de exemplo ilustrativo)?"""
    texto = query.lower().strip()
    return any(verbo in texto for verbo in VERBOS_GERACAO)