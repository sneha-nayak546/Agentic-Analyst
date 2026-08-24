import os
import json
import chromadb
from sentence_transformers import SentenceTransformer


def build_embeddings(model_name: str = "all-MiniLM-L6-v2") -> dict:
    print(f"Loading embedding model ({model_name})...")
    model = SentenceTransformer(model_name)

    db_path = "knowledge/chroma_db"
    os.makedirs(db_path, exist_ok=True)
    client = chromadb.PersistentClient(path=db_path)

    # Clean existing collections
    collection_name = "enterprise_schema"
    existing_collections = [c.name for c in client.list_collections()]
    
    # Try deleting legacy collections to clean up
    for old_col in ["database_schema", "wallet_schema", "user_schema", "withdrawal_schema", "sku_schema", "company_schema", "machine_schema", "automatic_transaction_schema", "automate_schema", collection_name]:
        if old_col in existing_collections:
            try:
                client.delete_collection(old_col)
            except Exception:
                pass

    collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    schema_file = "knowledge/schema/schema_metadata.json"
    if not os.path.exists(schema_file):
        print("Schema metadata not found. Run metadata_extractor.py first.")
        return {"status": "error", "message": "Schema metadata not found"}

    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    docs = []
    ids = []
    metadatas = []

    for tbl_name, info in schema.items():
        ddl_lines = []
        ddl_lines.append(f"CREATE TABLE {tbl_name} (")
        
        raw_cols = info.get("columns", {})
        col_items = raw_cols.items() if isinstance(raw_cols, dict) else ([(c["name"], c) for c in raw_cols if isinstance(c, dict)] if isinstance(raw_cols, list) else [])
        for col_name, col_data in col_items:
            line = f"  {col_name} {col_data.get('type', col_data.get('datatype', 'VARCHAR'))}"
            if not col_data.get('nullable'):
                line += " NOT NULL"
            if col_data.get('default') and col_data.get('default') != 'None':
                line += f" DEFAULT {col_data.get('default')}"
            if col_data.get('comment'):
                line += f" COMMENT '{col_data.get('comment')}'"
            ddl_lines.append(line + ",")
            
        pks = info.get("primary_keys", [])
        if pks:
            ddl_lines.append(f"  PRIMARY KEY ({', '.join(pks)})")
            
        ddl_text = "\n".join(ddl_lines) + "\n);"
        
        card_text = f"TABLE NAME: {tbl_name}\n\nSCHEMA DDL:\n{ddl_text}\n\n"
        
        columns = info.get("columns", {})
        if isinstance(columns, dict):
            for col_name, col_data in columns.items():
                if col_data.get("enum_values"):
                    card_text += (
                        f"- Column {col_name} ENUM values: "
                        f"{', '.join([str(v) for v in col_data['enum_values']])}\n"
                    )
        elif isinstance(columns, list):
            for col_data in columns:
                col_name = col_data.get("name", "")
                enum_values = col_data.get("enum_values") or col_data.get("enums") or []
                if enum_values:
                    card_text += (
                        f"- Column {col_name} ENUM values: "
                        f"{', '.join([str(v) for v in enum_values])}\n"
                    )

        docs.append(card_text)
        ids.append(f"table_{tbl_name}")
        metadatas.append({"table_name": tbl_name})

    if docs:
        embeddings = model.encode(docs).tolist()
        collection.add(
            documents=docs,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully embedded {len(docs)} tables into ChromaDB collection '{collection_name}'.")

    return {"status": "success", "tables_embedded": len(docs), "collection": collection_name}


rebuild_embeddings = build_embeddings

if __name__ == "__main__":
    build_embeddings()