import sys
from retrieve import retrieve
from generate import generate

def ask(query: str, k: int = 5, dbms: str | None = None) -> dict:
    hits = retrieve(query, k=k, dbms=dbms)
    answer = generate(query, hits)
    return {"query": query, "hits": hits, "answer": answer}

def print_result(result: dict):
    print(f"\nPERGUNTA: {result['query']}\n")
    print(f"RESPOSTA:\n{result['answer']}\n")
    print("FONTES USADAS:")
    for hit in result["hits"]:
        meta = hit["metadata"]
        print(f"  - {meta['arquivo']} | {meta['secao']} (dist={hit['distance']:.3f})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = ask(query)
        print_result(result)
    else:
        print("Kai — RAG Python/SQL. Digite 'sair' para encerrar.\n")
        while True:
            query = input("Pergunta: ").strip()
            if query.lower() in ("sair", "exit", "quit"):
                break
            if not query:
                continue
            result = ask(query)
            print_result(result)
            print()