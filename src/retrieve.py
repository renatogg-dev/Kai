import chromadb
from sentence_transformers import SentenceTransformer

STORE_DIR = "store"
COLLECTION_NAME = "kai_docs"

_model = None
_collection = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-base")
    return _model

def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=STORE_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection

def retrieve(query: str, k: int = 5, dbms: str | None = None):
    model = _get_model()
    collection = _get_collection()

    query_prefixed = f"query: {query}"
    query_embedding = model.encode([query_prefixed]).tolist()

    where = {"dbms": dbms} if dbms else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        where=where,
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return hits

if __name__ == "__main__":
    perguntas_teste = [
        "como faço um JOIN no SQLite?",
        "como criar uma classe em Python?",
        "como lidar com exceções em Python?",
    ]

    for pergunta in perguntas_teste:
        print(f"\n{'='*60}")
        print(f"PERGUNTA: {pergunta}")
        print('='*60)
        for hit in retrieve(pergunta, k=3):
            print(f"\n[{hit['metadata']['arquivo']} | {hit['metadata']['secao']}] (dist={hit['distance']:.3f})")
            print(hit["text"][:200])