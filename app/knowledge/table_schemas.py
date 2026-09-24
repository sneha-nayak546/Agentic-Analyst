import os
import json
from typing import List, Dict, Any, Optional, Set

_schema_cache: Optional[Dict[str, Any]] = None

def get_full_schema_metadata() -> Dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        schema_file = "knowledge/schema/schema_metadata.json"
        if os.path.exists(schema_file):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    _schema_cache = json.load(f)
            except Exception:
                _schema_cache = {}
        else:
            _schema_cache = {}
    return _schema_cache

IGNORED_COLUMNS = {
    "password", "two_factor_secret", "two_factor_recovery_codes", "remember_token",
    "fcm_token", "device_id", "deleted_at", "email_verified_at"
}

import sqlite3
from app.database.read_executor import is_explicit_local_test_mode

_actual_db_cols_cache: Dict[str, Set[str]] = {}

def get_actual_db_columns(table_name: str) -> Optional[Set[str]]:
    global _actual_db_cols_cache
    if not is_explicit_local_test_mode():
        # In production mode, do not restrict schema columns using local SQLite replica
        return None

    if table_name in _actual_db_cols_cache:
        return _actual_db_cols_cache[table_name]
    if os.path.exists("database.db"):
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            cols = {row[1] for row in c.execute(f"PRAGMA table_info({table_name});").fetchall()}
            conn.close()
            if cols:
                _actual_db_cols_cache[table_name] = cols
                return cols
        except Exception:
            pass
    return None

def get_selective_schema_context(tables: List[str]) -> str:
    """
    Returns a compact, targeted schema definition containing ONLY the tables
    and columns necessary for the detected query tables, strictly grounded to
    columns that physically exist in the database.
    """
    if not tables:
        tables = ["users"]

    full_schema = get_full_schema_metadata()
    lines = []
    
    relevant_joins = []
    tbl_set = set(tables)

    for tbl in tables:
        tbl_clean = tbl.strip()
        actual_cols = get_actual_db_columns(tbl_clean)
        if tbl_clean in full_schema:
            tbl_info = full_schema[tbl_clean]
            summary = tbl_info.get("comment", "")
            lines.append(f"TABLE `{tbl_clean}`" + (f" ({summary})" if summary else "") + ":")

            cols = tbl_info.get("columns", {})
            col_entries = []
            cols_iterable = cols.values() if isinstance(cols, dict) else (cols if isinstance(cols, list) else [])
            for c in cols_iterable:
                c_name = c.get("name", "")
                if c_name in IGNORED_COLUMNS:
                    continue
                if actual_cols and c_name not in actual_cols:
                    continue
                c_type = c.get("datatype", "")
                
                # Dynamic Foreign Key Joins
                if c.get("foreign_key"):
                    fk_tbl = c["foreign_key"].get("table")
                    fk_col = c["foreign_key"].get("column")
                    if fk_tbl in tbl_set and fk_tbl != tbl_clean:
                        relevant_joins.append(f"{tbl_clean}.{c_name} = {fk_tbl}.{fk_col}")

                if c.get("is_enum") and c.get("enum_values"):
                    enums = ", ".join([f"'{v}'" for v in c["enum_values"][:6]])
                    col_entries.append(f"{c_name} ({c_type}: {enums})")
                else:
                    col_entries.append(f"{c_name} ({c_type})")
            lines.append(f"  Columns: " + ", ".join(col_entries))
        else:
            lines.append(f"TABLE `{tbl_clean}`:\n  - (Standard table schema applies)")

        lines.append("")

    # Ingest dynamic relationships from Complete Relationship Graph
    try:
        from app.knowledge.relationship_builder import get_relationship_graph
        all_rels = get_relationship_graph()
        for r in all_rels:
            f_tbl = r.get("from_table", "").lower()
            t_tbl = r.get("to_table", "").lower()
            if f_tbl in tbl_set and t_tbl in tbl_set and f_tbl != t_tbl:
                f_col = r.get("from_column")
                t_col = r.get("to_column")
                tag = "[Explicit DB FK]" if r.get("origin") == "database_foreign_key" else "[Inferred Logical]"
                relevant_joins.append(f"{f_tbl}.{f_col} = {t_tbl}.{t_col} {tag}")
    except Exception:
        pass

    # Explicit Canonical Business Relationships for JGH
    KNOWN_BUSINESS_JOINS = [
        ("sku_inventories", "qr_point_map", "sku_inventories.sku_code = qr_point_map.sku_code (Box scan calculation: SUM(qr_point_map.box_calulation_um)) [Explicit DB FK]"),
        ("sku_inventories", "users", "sku_inventories.status_retailer_id = users.id (when joining Retailer, users.user_role = 2) [Explicit DB FK]"),
        ("sku_inventories", "users", "sku_inventories.distributer_id = users.id (when joining Distributor, users.user_role = 4) [Explicit DB FK]"),
        ("sku_inventories", "retailer_distributor_mappings", "sku_inventories.status_retailer_id = retailer_distributor_mappings.retailer_id [Inferred Logical]"),
        ("retailer_distributor_mappings", "users", "retailer_distributor_mappings.distributor_id = users.id (Distributor) [Inferred Logical]"),
        ("retailer_distributor_mappings", "users", "retailer_distributor_mappings.retailer_id = users.id (Retailer) [Inferred Logical]"),
        ("wallet_transaction", "users", "wallet_transaction.user_id = users.id [Explicit DB FK]"),
        ("withdrawal_request", "users", "withdrawal_request.user_id = users.id [Explicit DB FK]"),
        ("users", "state", "users.state_id = state.id (Select state.sname AS state_name) [Explicit DB FK]"),
        ("users", "states", "users.state_id = states.id (Select states.name AS state_name) [Explicit DB FK]"),
    ]
    for t1, t2, j_str in KNOWN_BUSINESS_JOINS:
        if t1 in tbl_set and t2 in tbl_set:
            relevant_joins.append(j_str)

    if relevant_joins:
        lines.append("RELEVANT DYNAMIC JOINS:")
        lines.extend([f"- {j}" for j in sorted(list(set(relevant_joins)))])

    return "\n".join(lines).strip()

