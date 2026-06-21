import chromadb

client = chromadb.PersistentClient(path="store")
collection = client.get_collection("kai_docs")
print(f"Vetores no indice: {collection.count()}")

sample = collection.get(limit=1, include=["documents", "metadatas"])
print("\nAmostra:")
print(sample["documents"][0][:200])
print(sample["metadatas"][0])