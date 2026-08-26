import os
import json
import pymysql
from app.database.config import get_db_credentials

def run_database_profiler() -> dict:
    """
    Database Profiler & Knowledge Builder:
    1. Connects to MySQL database (100% READ-ONLY).
    2. Queries INFORMATION_SCHEMA to dynamically extract ALL tables and views.
    3. Extracts columns, data types, primary keys, and column comments.
    4. Extracts foreign key relationships via KEY_COLUMN_USAGE.
    5. Profiles ENUM and categorical columns for distinct values.
    6. Samples basic lookup tables for business terminology.
    7. Saves all extracted metadata into knowledge/schema/schema_metadata.json and knowledge/business_metadata.json.
    """
    metadata_path = "knowledge/business_metadata.json"
    schema_path = "knowledge/schema/schema_metadata.json"
    
    os.makedirs("knowledge/schema", exist_ok=True)
    
    existing_meta = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
        except Exception as e:
            print("[PROFILER WARNING] Failed to read business_metadata.json:", e)

    creds = get_db_credentials()
    db_host = creds["host"]
    db_port = int(creds["port"]) if creds["port"] else 3306
    db_user = creds["user"]
    db_password = creds["password"]
    db_name = creds["name"]

    if not db_host or not db_user or not db_name:
        print("[PROFILER NOTICE] Missing database credentials. Returning empty metadata.")
        return {}

    schema_metadata = {}
    discovered = {
        "version": "4.0",
        "domain": "Full Database Intelligence",
        "enum_values": existing_meta.get("enum_values", {}),
        "business_terminology": existing_meta.get("business_terminology", {}),
        "relationships": [],
        "table_samples": {}
    }

    try:
        conn = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            ssl={}
        )

        with conn.cursor() as cursor:
            # 1. Fetch All Tables & Views
            print("[DB PROFILER] Fetching all tables and views...")
            cursor.execute(f"""
                SELECT TABLE_NAME, TABLE_TYPE, TABLE_COMMENT 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = '{db_name}'
            """)
            tables_result = cursor.fetchall()
            
            for t in tables_result:
                t_name = t["TABLE_NAME"]
                schema_metadata[t_name] = {
                    "type": t["TABLE_TYPE"],
                    "comment": t["TABLE_COMMENT"] or "",
                    "columns": {}
                }

            # 2. Fetch Columns
            print("[DB PROFILER] Fetching column definitions...")
            cursor.execute(f"""
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, 
                       IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA, COLUMN_COMMENT 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = '{db_name}'
            """)
            columns_result = cursor.fetchall()
            
            for c in columns_result:
                t_name = c["TABLE_NAME"]
                c_name = c["COLUMN_NAME"]
                if t_name in schema_metadata:
                    c_type = c["COLUMN_TYPE"]
                    is_enum = c_type.lower().startswith("enum")
                    enum_vals = []
                    if is_enum:
                        try:
                            val_str = c_type[5:-1] # enum('a','b') -> 'a','b'
                            enum_vals = [v.strip("'") for v in val_str.split(",")]
                        except:
                            pass
                            
                    schema_metadata[t_name]["columns"][c_name] = {
                        "name": c_name,
                        "datatype": c["DATA_TYPE"],
                        "full_type": c_type,
                        "is_nullable": c["IS_NULLABLE"] == "YES",
                        "default": c["COLUMN_DEFAULT"],
                        "is_primary": c["COLUMN_KEY"] == "PRI",
                        "is_auto_increment": "auto_increment" in c["EXTRA"],
                        "comment": c["COLUMN_COMMENT"] or "",
                        "is_enum": is_enum,
                        "enum_values": enum_vals
                    }

            # 3. Fetch Foreign Keys (Relationships)
            print("[DB PROFILER] Fetching foreign key relationships...")
            cursor.execute(f"""
                SELECT 
                    TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, 
                    REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = '{db_name}' 
                  AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            fk_result = cursor.fetchall()
            
            relationships = []
            for fk in fk_result:
                rel = {
                    "table": fk["TABLE_NAME"],
                    "column": fk["COLUMN_NAME"],
                    "referenced_table": fk["REFERENCED_TABLE_NAME"],
                    "referenced_column": fk["REFERENCED_COLUMN_NAME"],
                    "constraint_name": fk["CONSTRAINT_NAME"]
                }
                relationships.append(rel)
                
                # Attach FK info to schema
                if fk["TABLE_NAME"] in schema_metadata and fk["COLUMN_NAME"] in schema_metadata[fk["TABLE_NAME"]]["columns"]:
                    schema_metadata[fk["TABLE_NAME"]]["columns"][fk["COLUMN_NAME"]]["foreign_key"] = {
                        "table": fk["REFERENCED_TABLE_NAME"],
                        "column": fk["REFERENCED_COLUMN_NAME"]
                    }
                    
            discovered["relationships"] = relationships

            # 4. Profile ENUM and Categorical Distinct Values (Limit 50 rows to avoid full table scans on large tables)
            print("[DB PROFILER] Profiling categorical distinct values...")
            for t_name, t_meta in schema_metadata.items():
                for c_name, c_meta in t_meta["columns"].items():
                    if c_meta["is_enum"] or (c_meta["datatype"] == "varchar" and any(x in c_name.lower() for x in ["status", "type", "role", "category"])):
                        try:
                            # Only profile if table is small or we sample it
                            q = f"SELECT DISTINCT `{c_name}` FROM `{t_name}` WHERE `{c_name}` IS NOT NULL LIMIT 50;"
                            cursor.execute(q)
                            rows = cursor.fetchall()
                            values = [str(r[c_name]) for r in rows if r.get(c_name) is not None]
                            key = f"{t_name}.{c_name}"
                            discovered["enum_values"][key] = list(set(discovered["enum_values"].get(key, []) + values))
                        except Exception:
                            pass

            # 5. Extract Lookup Vocabulary for NLP mapping (e.g., tables ending with _role or containing names)
            print("[DB PROFILER] Sampling lookup tables...")
            for t_name in schema_metadata.keys():
                if "role" in t_name.lower() or "status" in t_name.lower() or "category" in t_name.lower() or t_name in ["users", "companies"]:
                    try:
                        cursor.execute(f"SELECT * FROM `{t_name}` LIMIT 10;")
                        rows = cursor.fetchall()
                        sanitized = []
                        for r in rows:
                            clean_r = {}
                            r_id = None
                            r_name = None
                            for k, v in r.items():
                                val = v.isoformat() if hasattr(v, "isoformat") else str(v)
                                clean_r[k] = val
                                if k.lower() == "id": r_id = val
                                if k.lower() in ["name", "title", "role_name", "status_name", "type_name"]: r_name = val
                                
                            sanitized.append(clean_r)
                            
                            # Add to terminology
                            if r_id and r_name:
                                term_key = str(r_name).strip().lower()
                                discovered["business_terminology"][term_key] = {
                                    "table": t_name,
                                    "column": "id",
                                    "value": r_id,
                                    "description": f"{r_name} in {t_name} (id={r_id})"
                                }
                        discovered["table_samples"][t_name] = sanitized
                    except Exception:
                        pass

        conn.close()
        
        # Save output
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema_metadata, f, indent=2, ensure_ascii=False)
            
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(discovered, f, indent=2, ensure_ascii=False)
            
        print(f"[DB PROFILER SUCCESS] Profiled {len(schema_metadata)} tables and {len(relationships)} relationships.")
        
    except Exception as err:
        print(f"[DB PROFILER ERROR] Failed to run database profiler: {err}")

    return discovered

if __name__ == "__main__":
    profile = run_database_profiler()

