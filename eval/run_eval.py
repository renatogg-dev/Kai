import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.retrieve import retrieve
from src.rag.generate import generate, build_context
from eval.metrics import recall_at_k, reciprocal_rank, faithfulness

GOLDEN_SET_PATH = Path("eval/golden_set.jsonl")
K = 5


def load_golden_set():
    lines = GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines]


def run():
    golden_set = load_golden_set()
    resultados = []

    for item in golden_set:
        hits = retrieve(item["pergunta_pt"], k=K)
        resposta = generate(item["pergunta_pt"], hits)
        contexto = build_context(hits)

        r_at_k = recall_at_k(hits, item["arquivo_esperado"])
        rr = reciprocal_rank(hits, item["arquivo_esperado"])
        faith = faithfulness(item["pergunta_pt"], resposta, contexto)

        resultados.append({
            "id": item["id"],
            "categoria": item["categoria"],
            "tipo": item["tipo"],
            "recall_at_k": r_at_k,
            "reciprocal_rank": rr,
            "faithfulness": faith,
        })
        print(f"[{item['id']}] recall@{K}={r_at_k} MRR={rr:.2f} faithfulness={faith}")

    return resultados


def report(resultados: list[dict]):
    n = len(resultados)
    mean_recall = sum(r["recall_at_k"] for r in resultados) / n
    mean_mrr = sum(r["reciprocal_rank"] for r in resultados) / n
    faith_sim = sum(1 for r in resultados if r["faithfulness"] == "sim") / n

    print("\n" + "=" * 50)
    print("RELATÓRIO GERAL")
    print("=" * 50)
    print(f"Itens avaliados: {n}")
    print(f"Recall@{K} médio: {mean_recall:.2%}")
    print(f"MRR médio: {mean_mrr:.3f}")
    print(f"Faithfulness (% 'sim'): {faith_sim:.2%}")

    print("\nPor categoria:")
    for cat in ("python", "sqlite", "postgresql"):
        subset = [r for r in resultados if r["categoria"] == cat]
        if not subset:
            continue
        cat_recall = sum(r["recall_at_k"] for r in subset) / len(subset)
        cat_mrr = sum(r["reciprocal_rank"] for r in subset) / len(subset)
        print(f"  {cat}: recall@{K}={cat_recall:.2%}  MRR={cat_mrr:.3f}  (n={len(subset)})")


if __name__ == "__main__":
    resultados = run()
    report(resultados)

    out_path = Path("eval/resultados_baseline.json")
    out_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados salvos em {out_path}")