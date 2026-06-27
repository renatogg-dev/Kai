import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.retrieve import retrieve

CASOS_FALHOS = [
    ("g02", "quais funções de agregação existem no SQLite, tipo soma e média?", "sqlite_aggfunc.html"),
    ("g05", "como funciona a cláusula GROUP BY com funções agregadas no PostgreSQL?", "postgres_aggregate.html"),
    ("g06", "como faço um SELECT com ORDER BY no PostgreSQL?", "postgres_select.html"),
]

for item_id, pergunta, esperado in CASOS_FALHOS:
    print(f"\n{'='*60}")
    print(f"[{item_id}] Pergunta: {pergunta}")
    print(f"Esperado: {esperado}")
    print('='*60)
    hits = retrieve(pergunta, k=5)
    for h in hits:
        marca = " <-- deveria ser este" if h["metadata"]["arquivo"] == esperado else ""
        print(f"  {h['metadata']['arquivo']} (dist={h['distance']:.3f}){marca}")