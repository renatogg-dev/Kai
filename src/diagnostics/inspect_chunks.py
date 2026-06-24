import json
from collections import Counter
from pathlib import Path

path = Path("corpus/chunks/chunks.jsonl")
lines = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]

print(f"Total de chunks: {len(lines)}\n")

por_arquivo = Counter(c["arquivo"] for c in lines)
print("Chunks por arquivo:")
for arquivo, n in sorted(por_arquivo.items(), key=lambda x: -x[1]):
    print(f"  {arquivo}: {n}")

tamanhos = [len(c["text"]) for c in lines]
curtos = sum(1 for t in tamanhos if t < 60)
print(f"\nTamanho medio: {sum(tamanhos)//len(tamanhos)} chars")
print(f"Chunks muito curtos (<60 chars, suspeitos de lixo): {curtos}")

print("\n--- 3 chunks mais curtos (provaveis lixo) ---")
for c in sorted(lines, key=lambda c: len(c["text"]))[:3]:
    print(f"[{c['arquivo']} | {c['secao']}] {c['text']!r}\n")