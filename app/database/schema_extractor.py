import os
import json
import pymysql
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

from app.database.allowed_tables import TARGET_SCOPE_TABLES

LOOKUP_MASTER_TABLES = {"user_role"}
TRANSACTION_FACT_TABLES = {"wallet_transaction", "withdrawal", "automatic_transaction_bank"}
DIMENSION_TABLES = {"users", "companies", "sku_inventory", "machine_details", "automate"}


def get_table_category(table_name: str) -> str:
    tbl = table_name.lower()
    if tbl in LOOKUP_MASTER_TABLES or tbl.endswith("_role") or tbl.endswith("_master") or tbl.endswith("_type"):
        return "lookup_master_table"
    elif tbl in TRANSACTION_FACT_TABLES or "transaction" in tbl or "request" in tbl:
        return "transaction_fact_table"
    elif tbl in DIMENSION_TABLES:
        return "dimension_table"
    return "master_table"


def extract_db_schema() -> Dict[str, Any]:
    """
    Connects to MySQL database and automatically extracts table metadata,
    columns, data types, nullability, primary keys, foreign keys, table types, and indexes
    strictly for target scope tables using INFORMATION_SCHEMA & metadata commands.
    """
    schema_data = {}

    if not DB_HOST or not DB_USER or not DB_NAME:
        print("[SCHEMA EXTRACTOR WARNING] Missing DB credentials in .env. Returning empty schema.")
        return schema_data

    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )

        with connection.cursor() as cursor:
            # 1. Fetch Column definitions for target tables
            format_strings = ','.join(['%s'] * len(TARGET_SCOPE_TABLES))
            query_columns = f"""
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME IN ({format_strings})
                ORDER BY TABLE_NAME, ORDINAL_POSITION;
            """
            cursor.execute(query_columns, [DB_NAME] + TARGET_SCOPE_TABLES)
            columns_raw = cursor.fetchall()

            for col in columns_raw:
                tbl = col["TABLE_NAME"]
                if tbl not in schema_data:
                    schema_data[tbl] = {
                        "table_name": tbl,
                        "category": get_table_category(tbl),
                        "columns": [],
                        "primary_keys": [],
                        "foreign_keys": [],
                        "indexes": []
                    }

                col_info = {
                    "name": col["COLUMN_NAME"],
                    "datatype": col["DATA_TYPE"],
                    "full_type": col["COLUMN_TYPE"],
                    "nullable": col["IS_NULLABLE"],
                    "key": col["COLUMN_KEY"],
                    "extra": col["EXTRA"],
                    "comment": col["COLUMN_COMMENT"]
                }
                schema_data[tbl]["columns"].append(col_info)
                if col["COLUMN_KEY"] == "PRI":
                    schema_data[tbl]["primary_keys"].append(col["COLUMN_NAME"])

            # 2. Fetch Foreign Key Relationships
            query_fks = f"""
                SELECT 
                    TABLE_NAME, 
                    COLUMN_NAME, 
                    REFERENCED_TABLE_NAME, 
                    REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s 
                  AND REFERENCED_TABLE_NAME IS NOT NULL
                  AND TABLE_NAME IN ({format_strings});
            """
            cursor.execute(query_fks, [DB_NAME] + TARGET_SCOPE_TABLES)
            fks_raw = cursor.fetchall()

            for fk in fks_raw:
                tbl = fk["TABLE_NAME"]
                if tbl in schema_data:
                    schema_data[tbl]["foreign_keys"].append({
                        "column": fk["COLUMN_NAME"],
                        "referenced_table": fk["REFERENCED_TABLE_NAME"],
                        "referenced_column": fk["REFERENCED_COLUMN_NAME"]
                    })

            # 3. Fetch Indexes
            query_indexes = f"""
                SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, NON_UNIQUE
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME IN ({format_strings})
                ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
            """
            cursor.execute(query_indexes, [DB_NAME] + TARGET_SCOPE_TABLES)
            indexes_raw = cursor.fetchall()

            for idx in indexes_raw:
                tbl = idx["TABLE_NAME"]
                if tbl in schema_data:
                    existing_idx = next((i for i in schema_data[tbl]["indexes"] if i["name"] == idx["INDEX_NAME"]), None)
                    if existing_idx:
                        existing_idx["columns"].append(idx["COLUMN_NAME"])
                    else:
                        schema_data[tbl]["indexes"].append({
                            "name": idx["INDEX_NAME"],
                            "is_unique": idx["NON_UNIQUE"] == 0,
                            "columns": [idx["COLUMN_NAME"]]
                        })

        connection.close()



        # Save to knowledge directory
        os.makedirs("knowledge/schema", exist_ok=True)
        schema_file = "knowledge/schema/schema_metadata.json"
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)

        print(f"[SCHEMA EXTRACTOR SUCCESS] Extracted metadata for {len(schema_data)} tables -> {schema_file}")

    except Exception as e:
        print(f"[SCHEMA EXTRACTOR ERROR] Failed to extract database schema: {e}")

    return schema_data


if __name__ == "__main__":
    schema = extract_db_schema()
    print("Extracted Tables:", list(schema.keys()))

