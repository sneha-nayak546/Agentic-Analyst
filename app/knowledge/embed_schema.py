import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

def ingest_schema_to_chroma():
    """
    Reads the dynamically extracted schema_metadata.json and embeds the tables
    into ChromaDB for semantic RAG retrieval.
    """
    schema_path = "knowledge/schema/schema_metadata.json"
    if not os.path.exists(schema_path):
        print("schema_metadata.json not found! Run db_profiler.py first.")
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    db_path = "knowledge/chroma_db"
    os.makedirs(db_path, exist_ok=True)
    
    print("[EMBED] Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("[EMBED] Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    
    # Create or replace collection
    try:
        client.delete_collection("enterprise_schema")
    except:
        pass
        
    collection = client.create_collection("enterprise_schema")
    
    docs = []
    metadatas = []
    ids = []
    embeddings = []
    
    for t_name, t_meta in schema.items():
        # Create a rich text chunk describing the table for the embedding model
        col_names = list(t_meta.get("columns", {}).keys())
        col_desc = " ".join(col_names).replace("_", " ")
        
        t_clean = t_name.replace("_", " ")
        comment = t_meta.get("comment", "")
        
        # e.g., "wallet transaction table. Columns: id user id amount type status. comment: Stores all user transactions."
        doc_text = f"Table {t_clean}. Columns: {col_desc}. {comment}".strip()
        
        docs.append(doc_text)
        metadatas.append({"table_name": t_name, "type": "schema_table"})
        ids.append(f"table_{t_name}")
        embeddings.append(model.encode(doc_text).tolist())

    if docs:
        print(f"[EMBED] Ingesting {len(docs)} tables into ChromaDB...")
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=docs
        )
        print("[EMBED] Success! Schema is now embedded in ChromaDB.")
    else:
        print("[EMBED] No tables to ingest.")

if __name__ == "__main__":
    ingest_schema_to_chroma()
