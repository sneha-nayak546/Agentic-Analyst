import json
import chromadb
from sentence_transformers import SentenceTransformer
import os


# ------------------------------------
# Load Knowledge Chunks
# ------------------------------------

with open(
    "knowledge/generated/knowledge_chunks.json",
    "r",
    encoding="utf-8"
) as f:

    knowledge_chunks = json.load(f)



# ------------------------------------
# Load Embedding Model
# ------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# ------------------------------------
# Create Chroma Database
# ------------------------------------

client = chromadb.PersistentClient(
    path="knowledge/chroma_db"
)


collection = client.get_or_create_collection(
    name="sql_knowledge"
)



# ------------------------------------
# Insert Embeddings
# ------------------------------------

documents = []
ids = []


for chunk in knowledge_chunks:

    documents.append(
        chunk["text"]
    )

    ids.append(
        chunk["id"]
    )


print(
    "Generating embeddings..."
)


embeddings = model.encode(
    documents,
    show_progress_bar=True
)


collection.add(
    documents=documents,
    embeddings=embeddings.tolist(),
    ids=ids
)



print("==============================")
print("Embedding creation completed")
print("==============================")

print(
    f"Stored {len(ids)} knowledge chunks"
)
