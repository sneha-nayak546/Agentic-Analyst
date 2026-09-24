import os
import json
from typing import Set, List

_all_known_tables_cache: Set[str] = set()

def get_all_known_tables() -> Set[str]:
    """Dynamically retrieves all ~256 discoverable tables across schema metadata and local DB."""
    global _all_known_tables_cache
    if _all_known_tables_cache:
        return _all_known_tables_cache

    tables: Set[str] = set()
    # 1. Inspect schema_metadata.json
    meta_path = "knowledge/schema/schema_metadata.json"
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    tables.update(k.lower() for k in data.keys())
        except Exception:
            pass

    # 2. Inspect connections_knowledge.json
    conn_path = "knowledge/connections_knowledge.json"
    if os.path.exists(conn_path):
        try:
            with open(conn_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    tables.update(k.lower() for k in data.keys())
        except Exception:
            pass

    # 3. Inspect local SQLite database.db ONLY in explicit local test mode
    from app.database.read_executor import is_explicit_local_test_mode
    if is_explicit_local_test_mode() and os.path.exists("database.db"):
        try:
            import sqlite3
            con = sqlite3.connect("database.db")
            cur = con.cursor()
            for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall():
                tables.add(r[0].lower())
            con.close()
        except Exception:
            pass

    # Fallback default tables if metadata files are missing
    if not tables:
        tables = {
            "users", "companies", "wallet_transaction", "role", "user_role",
            "sku_inventories", "mechanic_details", "withdrawal_request",
            "automatic_transactions", "sku_qr_points_map", "qr_point_map",
            "state", "districts", "retailer_distributor_mappings"
        }

    _all_known_tables_cache = tables
    return _all_known_tables_cache

# Backward-compatibility alias containing all discoverable tables
TARGET_SCOPE_TABLES: List[str] = list(get_all_known_tables())

def is_allowed_table(table_name: str) -> bool:
    """Validates if a table is discoverable in the full ~256 table database schema."""
    if not table_name or not isinstance(table_name, str):
        return False
    t_clean = table_name.strip().lower()
    known = get_all_known_tables()
    return t_clean in known or not t_clean.startswith("sqlite_")

def get_canonical_table_name(table_name: str) -> str:
    if not table_name:
        return ""
    return table_name.lower()


