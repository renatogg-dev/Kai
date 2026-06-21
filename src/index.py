import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("corpus/chunks/chunks.jsonl")
STORE_DIR = "store"
COLLECTION_NAME = "kai_docs"
BATCH_SIZE = 64

def load_chunks():
    lines = CHUNKS_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines]

def main():
    chunks = load_chunks()
    print(f"Carregados {len(chunks)} chunks.")

    print("Carregando modelo multilingual-e5-base ...")
    model = SentenceTransformer("intfloat/multilingual-e5-base")

    client = chromadb.PersistentClient(path=STORE_DIR)

    # Recria a collection do zero para evitar duplicatas em reindexacoes
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    total = len(chunks)
    for start in range(0, total, BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        texts_prefixed = [f"passage: {c['text']}" for c in batch]
        embeddings = model.encode(texts_prefixed, show_progress_bar=False).tolist()

        collection.add(
            ids=[c["id"] for c in batch],
            embeddings=embeddings,
            documents=[c["text"] for c in batch],
            metadatas=[
                {
                    "arquivo": c["arquivo"],
                    "secao": c["secao"],
                    "source": c["source"],
                    "linguagem": c["metadata"]["linguagem"],
                    "dbms": c["metadata"]["dbms"] or "",
                }
                for c in batch
            ],
        )
        print(f"Indexados {min(start + BATCH_SIZE, total)}/{total}")

    print(f"\nConcluido. Total no indice: {collection.count()}")

if __name__ == "__main__":
    main()