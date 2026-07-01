import sys
from src.rag.retrieve import retrieve
from src.rag.generate import generate
from src.rag.rewrite import rewrite_query_with_history

def ask(query: str, k: int = 5, dbms: str | None = None, history: list[dict] | None = None) -> dict:
    history = history or []
    retrieval_query = rewrite_query_with_history(query, history)
    hits = retrieve(retrieval_query, k=k, dbms=dbms)
    answer = generate(query, hits, history=history)
    return {
        "query": query,
        "retrieval_query": retrieval_query,
        "hits": hits,
        "answer": answer,
    }

def print_result(result: dict):
    print(f"\nPERGUNTA: {result['query']}")
    if result["retrieval_query"] != result["query"]:
        print(f"(interpretada para busca como: {result['retrieval_query']})")
    print(f"\nRESPOSTA:\n{result['answer']}\n")
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
        historico = []
        while True:
            query = input("Pergunta: ").strip()
            if query.lower() in ("sair", "exit", "quit"):
                break
            if not query:
                continue
            result = ask(query, history=historico)
            print_result(result)
            historico.append({"role": "user", "content": query})
            historico.append({"role": "assistant", "content": result["answer"]})
            print()