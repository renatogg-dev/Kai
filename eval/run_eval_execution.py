import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.retrieve import retrieve
from src.rag.generate import generate
from eval.metrics import codigo_executa

GOLDEN_SET_PATH = Path("eval/golden_set.jsonl")
K = 5


def load_golden_set():
    lines = GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines()
    itens = [json.loads(l) for l in lines]
    return [i for i in itens if i["tipo"] == "codigo"]


def run():
    itens = load_golden_set()
    print(f"DEBUG: {len(itens)} itens carregados", flush=True)
    resultados = []

    for item in itens:
        print(f"DEBUG: processando {item['id']}", flush=True)
        hits = retrieve(item["pergunta_pt"], k=K)
        resposta = generate(item["pergunta_pt"], hits)

        sem_loop = codigo_executa(item["pergunta_pt"], resposta, usar_loop=False)
        com_loop = codigo_executa(item["pergunta_pt"], resposta, usar_loop=True)

        from src.execution.sandbox import extract_code_blocks
        blocos = extract_code_blocks(resposta)
        codigo_original = blocos[0]["codigo"] if blocos else None

        resultados.append({
            "id": item["id"],
            "categoria": item["categoria"],
            "sem_loop_sucesso": sem_loop["sucesso"],
            "com_loop_sucesso": com_loop["sucesso"],
            "tentativas_com_loop": com_loop.get("tentativas", 1),
            "codigo_original": codigo_original,
            "corrigido": com_loop.get("tentativas", 1) > 1,
        })

        print(f"[{item['id']}] sem_loop={sem_loop['sucesso']}  com_loop={com_loop['sucesso']} (tentativas={com_loop.get('tentativas', 1)})")

    return resultados


def report(resultados: list[dict]):
    n = len(resultados)
    taxa_sem = sum(r["sem_loop_sucesso"] for r in resultados) / n
    taxa_com = sum(r["com_loop_sucesso"] for r in resultados) / n
    corrigidos = sum(1 for r in resultados if r["corrigido"])

    print("\n" + "=" * 50)
    print("COMPARATIVO: EXECUTION LOOP")
    print("=" * 50)
    print(f"Itens de código avaliados: {n}")
    print(f"Taxa de sucesso SEM loop: {taxa_sem:.1%}")
    print(f"Taxa de sucesso COM loop: {taxa_com:.1%}")
    print(f"Ganho: {(taxa_com - taxa_sem):+.1%}")
    print(f"Casos onde o loop precisou corrigir algo: {corrigidos}/{n}")

    print("\nPor categoria:")
    for cat in ("python", "sqlite"):
        subset = [r for r in resultados if r["categoria"] == cat]
        if not subset:
            continue
        cat_sem = sum(r["sem_loop_sucesso"] for r in subset) / len(subset)
        cat_com = sum(r["com_loop_sucesso"] for r in subset) / len(subset)
        print(f"  {cat}: sem_loop={cat_sem:.1%}  com_loop={cat_com:.1%}  (n={len(subset)})")

    print("\nDistribuição de tentativas (com loop):")
    from collections import Counter
    dist = Counter(r["tentativas_com_loop"] for r in resultados)
    for n_tentativas in sorted(dist):
        print(f"  {n_tentativas} tentativa(s): {dist[n_tentativas]} caso(s)")
    
if __name__ == "__main__":
    resultados = run()
    report(resultados)

    out_path = Path("eval/resultados_execution.json")
    out_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados salvos em {out_path}")