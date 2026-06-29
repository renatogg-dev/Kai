import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.retrieve import retrieve

pergunta = "escreva uma query SQL (SQLite) que combine nome e idade de cada pessoa em uma unica coluna de texto, no formato 'Nome - Idade'"

hits = retrieve(pergunta, k=5)
for h in hits:
    print(f"\n--- {h['metadata']['arquivo']} | {h['metadata']['secao']} (dist={h['distance']:.3f}) ---")
    print(h["text"][:400])

# Checagem direta: o operador || aparece em algum chunk do sqlite_select.html no corpus inteiro?
import json
chunks = [json.loads(l) for l in Path("corpus/chunks/chunks.jsonl").read_text(encoding="utf-8").splitlines()]
com_concat = [c for c in chunks if c["arquivo"] == "sqlite_select.html" and "||" in c["text"]]
print(f"\n\nChunks de sqlite_select.html contendo '||': {len(com_concat)}")
for c in com_concat[:3]:
    print(f"  [{c['secao']}] {c['text'][:200]}")