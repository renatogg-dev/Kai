import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.retrieve import retrieve
from src.rag.generate import generate
from src.execution.sandbox import extract_code_blocks

PERGUNTAS_PROBLEMATICAS = {
    "g15": "escreva uma função Python que recebe uma string e retorna um dicionário com a frequência de cada palavra",
    "g16": "escreva uma função Python recursiva que calcula o fatorial de um número",
    "g18": "escreva uma query SQL (SQLite) que combine nome e idade de cada pessoa em uma unica coluna de texto, no formato 'Nome - Idade'",
}

for item_id, pergunta in PERGUNTAS_PROBLEMATICAS.items():
    hits = retrieve(pergunta, k=5)
    resposta = generate(pergunta, hits)
    blocos = extract_code_blocks(resposta)

    print(f"\n{'='*60}")
    print(f"[{item_id}] Blocos extraídos: {len(blocos)}")
    print('='*60)
    print(resposta)