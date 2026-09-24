import json
import os
import sys
import sqlite3
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from app.database.config import get_db_engine, get_db_credentials

def audit():
    print("=== DATABASE CONNECTION AUDIT ===")
    creds = get_db_credentials()
    print(f"Target Host: {creds.get('host')}:{creds.get('port')} (Database: {creds.get('name')})")

    actual_tables = []
    actual_cols_count = 0
    fks_count = 0
    raw_fks = []

    try:
        engine = get_db_engine(connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            db_name = conn.execute(text("SELECT DATABASE();")).scalar()
            raw_tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE';")).fetchall()
            actual_tables = [r[0] for r in raw_tables]
            actual_cols_count = conn.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE();")).scalar()
            fks_count = conn.execute(text("SELECT COUNT(*) FROM information_schema.table_constraints WHERE table_schema = DATABASE() AND constraint_type = 'FOREIGN KEY';")).scalar()
            raw_fks = conn.execute(text("""
                SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL;
            """)).fetchall()

        print(f"[OK] Connected Successfully to MySQL Database: {db_name}")
        print(f"Actual Base Tables  : {len(actual_tables)}")
        print(f"Actual Columns      : {actual_cols_count}")
        print(f"Foreign Keys (DB)   : {fks_count}")
        print(f"Foreign Key Usages  : {len(raw_fks)}")
    except Exception as e:
        print(f"[!] MySQL Connection Failed ({type(e).__name__}): {e}")

    # Check local SQLite database.db
    if os.path.exists("database.db"):
        conn_sq = sqlite3.connect("database.db")
        cur_sq = conn_sq.cursor()
        cur_sq.execute("SELECT name FROM sqlite_master WHERE type='table';")
        sq_tables = [r[0] for r in cur_sq.fetchall()]
        print(f"\n=== LOCAL SQLITE (database.db) AUDIT ===")
        print(f"SQLite Tables Count : {len(sq_tables)}")
        if not actual_tables:
            actual_tables = sq_tables

    # Check knowledge/schema/schema_metadata.json
    schema_path = "knowledge/schema/schema_metadata.json"
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta_tables = meta.get("tables", {}) if isinstance(meta, dict) else meta
        indexed_cols = sum(len(t_info.get("columns", {})) for t_info in meta_tables.values()) if isinstance(meta_tables, dict) else 0
        print(f"\n=== SCHEMA METADATA JSON AUDIT ===")
        print(f"Indexed Tables in JSON  : {len(meta_tables)}")
        print(f"Indexed Columns in JSON : {indexed_cols}")
        if actual_tables:
            coverage = (len(meta_tables) / len(actual_tables)) * 100 if len(actual_tables) > 0 else 0
            print(f"Schema Coverage         : {coverage:.2f}% ({len(meta_tables)}/{len(actual_tables)})")
            missing_in_json = set(actual_tables) - set(meta_tables.keys())
            print(f"Tables missing in JSON  : {len(missing_in_json)}")
            if missing_in_json:
                print(f"Sample missing tables   : {list(missing_in_json)[:10]}")
    else:
        print(f"[!] {schema_path} does not exist!")

    # Check ChromaDB Collections
    chroma_dir = "knowledge/chroma_db"
    print(f"\n=== CHROMADB AUDIT ===")
    if os.path.exists(chroma_dir):
        try:
            import chromadb
            client = chromadb.PersistentClient(path=chroma_dir)
            collections = client.list_collections()
            print(f"ChromaDB Collections Found: {len(collections)}")
            for col in collections:
                print(f"  • {col.name} (Items: {col.count()})")
        except Exception as e:
            print(f"ChromaDB read error: {e}")
    else:
        print(f"ChromaDB dir '{chroma_dir}' not found.")

    # Check Relationship files
    rel_path = "knowledge/relationships"
    print(f"\n=== RELATIONSHIPS AUDIT ===")
    if os.path.exists(rel_path):
        rel_files = os.listdir(rel_path)
        print(f"Relationship files: {rel_files}")
        for rf in rel_files:
            fp = os.path.join(rel_path, rf)
            if os.path.isfile(fp):
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    print(f"  • {rf}: {len(data) if isinstance(data, (list, dict)) else type(data)}")
                except Exception as e:
                    print(f"  • {rf}: error reading ({e})")
    
    # Check Business Rules
    br_path = "knowledge/business_rules"
    print(f"\n=== BUSINESS RULES AUDIT ===")
    if os.path.exists(br_path):
        br_files = os.listdir(br_path)
        print(f"Business rule files: {br_files}")

if __name__ == "__main__":
    audit()
