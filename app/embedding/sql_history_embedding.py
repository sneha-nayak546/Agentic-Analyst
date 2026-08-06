import json
import chromadb
from sentence_transformers import SentenceTransformer

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Connecting ChromaDB...")

client = chromadb.PersistentClient(
    path="knowledge/chroma_db"
)

# Delete old SQL history collection if exists
try:
    client.delete_collection("sql_history")
except:
    pass

collection = client.create_collection(
    name="sql_history"
)

print("Loading SQL History...")

with open(
    "knowledge/generated/sql_history_chunks.json",
    "r",
    encoding="utf-8"
) as f:
    chunks = json.load(f)

documents = []
embeddings = []
ids = []

for chunk in chunks:

    text = chunk["text"]

    embedding = model.encode(text).tolist()

    documents.append(text)
    embeddings.append(embedding)
    ids.append(chunk["id"])

collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings
)

print("=" * 60)
print("SQL History Embeddings Created")
print("Collection : sql_history")
print(f"Documents  : {len(ids)}")
print("=" * 60)