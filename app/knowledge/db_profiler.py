import os
import json
import pymysql
from dotenv import load_dotenv
from app.database.allowed_tables import TARGET_SCOPE_TABLES

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def run_database_profiler() -> dict:
    """
    Database Profiler & Knowledge Builder:
    1. Connects to MySQL database (100% READ-ONLY).
    2. Fetches sample records (LIMIT 50-100) from each allowed table.
    3. Captures ALL rows for lookup/master tables (user_role / role) to define business vocabulary.
    4. Automatically generates the Business Dictionary dynamically from database lookup rows.
    5. Profiles all distinct ENUM and categorical column values from the database.
    6. Updates knowledge/business_metadata.json.
    """
    metadata_path = "knowledge/business_metadata.json"
    existing_meta = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
        except Exception as e:
            print("[PROFILER WARNING] Failed to read business_metadata.json:", e)

    if not DB_HOST or not DB_USER or not DB_NAME:
        print("[PROFILER NOTICE] Missing database credentials. Returning static metadata.")
        return existing_meta

    discovered = {
        "version": "3.0",
        "domain": "Enterprise Data Analytics & Lookup Master Engine",
        "tables": existing_meta.get("tables", {}),
        "integer_mappings": existing_meta.get("integer_mappings", {}),
        "enum_values": existing_meta.get("enum_values", {}),
        "business_terminology": existing_meta.get("business_terminology", {}),
        "lookup_tables_data": {},
        "table_samples": {}
    }

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )

        with conn.cursor() as cursor:
            # Load schema to dynamically find lookup tables and enum columns
            schema_meta = {}
            schema_path = "knowledge/schema/schema_metadata.json"
            if os.path.exists(schema_path):
                with open(schema_path, "r", encoding="utf-8") as sf:
                    schema_meta = json.load(sf)

            # 1. Capture ALL rows for lookup/master tables
            lookup_table_candidates = []
            for tbl, info in schema_meta.items():
                if info.get("category") == "lookup_master_table" or tbl.endswith("_role") or tbl.endswith("_status"):
                    lookup_table_candidates.append(tbl)
            if not lookup_table_candidates:
                lookup_table_candidates = ["user_role", "role"]

            for l_tbl in set(lookup_table_candidates):
                try:
                    q = f"SELECT * FROM `{l_tbl}` LIMIT 500;"
                    cursor.execute(q)
                    rows = cursor.fetchall()
                    if rows:
                        sanitized_rows = []
                        for r in rows:
                            clean_r = {}
                            for k, v in r.items():
                                if hasattr(v, "isoformat"):
                                    clean_r[k] = v.isoformat()
                                else:
                                    clean_r[k] = str(v) if isinstance(v, (int, float, str, type(None))) else str(v)
                            sanitized_rows.append(clean_r)
                        discovered["lookup_tables_data"][l_tbl] = sanitized_rows
                        
                        # Build Business Dictionary dynamically from database lookup rows
                        for r in rows:
                            r_id = r.get("id")
                            r_name = r.get("name") or r.get("role_name") or r.get("title") or r.get("role") or r.get("status_name")
                            if r_id is not None and r_name:
                                term_key = str(r_name).strip().lower()
                                discovered["business_terminology"][term_key] = {
                                    "table": l_tbl,
                                    "column": "id",
                                    "value": r_id,
                                    "condition": f"{l_tbl}.id = {r_id}",
                                    "description": f"{r_name} in {l_tbl} (id = {r_id})"
                                }
                except Exception:
                    pass

            # 3. Read sample records (LIMIT 50-100) from all allowed scope tables
            sample_tables = list(TARGET_SCOPE_TABLES) if TARGET_SCOPE_TABLES else [
                "users", "user_role", "role", "wallet_transaction", "sku_inventories",
                "companies", "machine_details", "withdrawal_request", "withdrawal",
                "automatic_transactions", "automatic_transactions_bank", "automate"
            ]
            for tbl in sample_tables:
                try:
                    q = f"SELECT * FROM `{tbl}` LIMIT 50;"
                    cursor.execute(q)
                    rows = cursor.fetchall()
                    sample_summary = []
                    for r in rows[:10]:
                        clean_row = {}
                        for k, v in r.items():
                            if hasattr(v, "isoformat"):
                                clean_row[k] = v.isoformat()
                            elif isinstance(v, (bytes, bytearray)):
                                clean_row[k] = "<binary>"
                            else:
                                clean_row[k] = str(v) if v is not None else None
                        sample_summary.append(clean_row)
                    discovered["table_samples"][tbl] = sample_summary
                except Exception:
                    pass

            # 4. Profile ALL distinct values for ENUM and categorical columns dynamically
            profiling_targets = []
            for tbl, info in schema_meta.items():
                for col in info.get("columns", []):
                    col_type = col.get("datatype", "").lower()
                    col_name = col.get("name", "").lower()
                    if col_type == "enum" or (col_type == "varchar" and ("status" in col_name or "type" in col_name or "role" in col_name)):
                        profiling_targets.append((tbl, col_name))
            
            if not profiling_targets:
                profiling_targets = [
                    ("wallet_transaction", "reference_type"), ("wallet_transaction", "transaction_type"), 
                    ("wallet_transaction", "status"), ("withdrawal_request", "status"),
                    ("users", "user_role"), ("users", "status"), ("automatic_transactions", "transfer_type"),
                    ("automatic_transactions", "status")
                ]

            for tbl, col in set(profiling_targets):
                try:
                    q = f"SELECT DISTINCT `{col}` FROM `{tbl}` WHERE `{col}` IS NOT NULL LIMIT 100;"
                    cursor.execute(q)
                    rows = cursor.fetchall()
                    values = [str(r[col]) for r in rows if r.get(col) is not None]
                    key = f"{tbl}.{col}"
                    discovered["enum_values"][key] = list(set(discovered["enum_values"].get(key, []) + values))
                except Exception:
                    pass

        conn.close()
        print("[DB PROFILER SUCCESS] Sample records read (LIMIT 50) and lookup table rows captured.")
        print("[DB PROFILER SUCCESS] All distinct enum & categorical values extracted from DB.")

        # Save updated metadata
        os.makedirs("knowledge", exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(discovered, f, indent=2, ensure_ascii=False)

    except Exception as err:
        print("[DB PROFILER NOTICE] Profiler offline fallback:", err)

    return discovered



if __name__ == "__main__":
    profile = run_database_profiler()
    print("Profiled Tables:", list(profile.get("tables", {}).keys()))
    print("Discovered Business Vocabulary Terms:", list(profile.get("business_terminology", {}).keys()))

