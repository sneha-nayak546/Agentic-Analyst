import os
import json
from typing import List, Dict, Any, Set, Optional

EXPLICIT_FK = "EXPLICIT_FK"
VERIFIED_UNIQUE_KEY = "VERIFIED_UNIQUE_KEY"
LOGICAL_INFERRED = "LOGICAL_INFERRED"

# Static core JGH relationship graph fallback
STATIC_RELATIONSHIP_GRAPH = [
    {"from_table": "users", "from_column": "user_role", "to_table": "role", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "users", "from_column": "state_id", "to_table": "state", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "wallet_transaction", "from_column": "user_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "withdrawal_request", "from_column": "user_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "withdrawal_request", "from_column": "automatic_transaction_id", "to_table": "automatic_transactions", "to_column": "id", "type": "Many-to-One", "origin": LOGICAL_INFERRED},
    {"from_table": "automatic_transactions", "from_column": "user_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "sku_inventories", "from_column": "distributer_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "sku_inventories", "from_column": "status_retailer_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "sku_inventories", "from_column": "status_wholeseller_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "sku_inventories", "from_column": "sku_code", "to_table": "qr_point_map", "to_column": "sku_code", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "sku_inventories", "from_column": "sku_code", "to_table": "sku_qr_points_map", "to_column": "sku_code", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "retailer_distributor_mappings", "from_column": "distributor_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": LOGICAL_INFERRED},
    {"from_table": "retailer_distributor_mappings", "from_column": "retailer_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": LOGICAL_INFERRED},
    {"from_table": "mechanic_details", "from_column": "mechanic_id", "to_table": "users", "to_column": "id", "type": "One-to-One", "origin": EXPLICIT_FK},
    {"from_table": "mechanic_details", "from_column": "company_id", "to_table": "companies", "to_column": "id", "type": "Many-to-One", "origin": EXPLICIT_FK},
    {"from_table": "companies", "from_column": "customer_id", "to_table": "users", "to_column": "id", "type": "Many-to-One", "origin": LOGICAL_INFERRED}
]

_cached_relationship_graph: Optional[List[Dict[str, Any]]] = None

def get_relationship_graph() -> List[Dict[str, Any]]:
    """
    Returns the complete relationship graph across all discoverable ~256 tables.
    Integrates explicit database foreign keys and complete catalog connections.
    """
    global _cached_relationship_graph
    if _cached_relationship_graph is not None:
        return _cached_relationship_graph

    relationships = []
    seen = set()

    def _add_rel(f_tbl, f_col, t_tbl, t_col, origin=EXPLICIT_FK, r_type="Many-to-One"):
        key = (f_tbl.lower(), f_col.lower(), t_tbl.lower(), t_col.lower())
        if key not in seen:
            seen.add(key)
            relationships.append({
                "from_table": f_tbl.lower(),
                "from_column": f_col.lower(),
                "to_table": t_tbl.lower(),
                "to_column": t_col.lower(),
                "type": r_type,
                "origin": origin
            })

    # 1. Ingest connections_knowledge.json (Complete Table Connectivity Catalog for ~238 tables)
    conn_file = "knowledge/connections_knowledge.json"
    if os.path.exists(conn_file):
        try:
            with open(conn_file, "r", encoding="utf-8") as f:
                conn_data = json.load(f)
            for src_tbl, info in conn_data.items():
                for ob in info.get("outbound", []):
                    t_tbl = ob.get("target_table")
                    s_col = ob.get("column")
                    t_col = ob.get("target_column")
                    rel_t = ob.get("type")
                    orig = EXPLICIT_FK if rel_t == "Explicit" else (VERIFIED_UNIQUE_KEY if rel_t == "UniqueKey" else LOGICAL_INFERRED)
                    if t_tbl and s_col and t_col:
                        _add_rel(src_tbl, s_col, t_tbl, t_col, origin=orig)
        except Exception:
            pass

    # 2. Ingest schema_metadata.json foreign keys
    schema_file = "knowledge/schema/schema_metadata.json"
    if os.path.exists(schema_file):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            for tbl, t_info in schema_data.items():
                for fk in t_info.get("foreign_keys", []):
                    ref_tbl = fk.get("referred_table")
                    src_cols = fk.get("constrained_columns", [])
                    ref_cols = fk.get("referred_columns", [])
                    if ref_tbl and src_cols and ref_cols:
                        _add_rel(tbl, src_cols[0], ref_tbl, ref_cols[0], origin=EXPLICIT_FK)
        except Exception:
            pass

    # 3. Always guarantee core domain relationships are present
    for s_rel in STATIC_RELATIONSHIP_GRAPH:
        _add_rel(
            s_rel["from_table"],
            s_rel["from_column"],
            s_rel["to_table"],
            s_rel["to_column"],
            origin=s_rel.get("origin", EXPLICIT_FK),
            r_type=s_rel.get("type", "Many-to-One")
        )

    _cached_relationship_graph = relationships
    return _cached_relationship_graph

def get_relationship_prompt_text(tables: Optional[Set[str]] = None) -> str:
    """Returns formatted join strings for a given subset of tables, prioritizing EXPLICIT_FK over LOGICAL_INFERRED."""
    rels = get_relationship_graph()
    explicit_lines = []
    inferred_lines = []
    seen = set()
    tbls_lower = {t.lower() for t in tables} if tables else None

    for r in rels:
        f_tbl, f_col = r["from_table"], r["from_column"]
        t_tbl, t_col = r["to_table"], r["to_column"]
        if tbls_lower:
            if f_tbl not in tbls_lower and t_tbl not in tbls_lower:
                continue
        origin = r.get("origin", EXPLICIT_FK)
        origin_tag = f"[{origin}]"
        rel_str = f"{f_tbl}.{f_col} = {t_tbl}.{t_col} {origin_tag}"
        if rel_str not in seen:
            seen.add(rel_str)
            if origin == EXPLICIT_FK:
                explicit_lines.append(rel_str)
            else:
                inferred_lines.append(rel_str)

    all_lines = explicit_lines + inferred_lines
    return "\n".join(all_lines) if all_lines else f"sku_inventories.sku_code = qr_point_map.sku_code [{EXPLICIT_FK}]\nwallet_transaction.user_id = users.id [{EXPLICIT_FK}]"



if __name__ == "__main__":
    from app.database.config import get_db_credentials, get_db_engine
    creds = get_db_credentials()
    DB_HOST = creds["host"]
    DB_USER = creds["user"]
    DB_NAME = creds["name"]

    relationships = []
    if all([DB_HOST, DB_USER, DB_NAME]):
        try:
            engine = get_db_engine()
            query = """
            SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = :db AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME;
            """
            with engine.connect() as conn:
                result = conn.execute(text(query), {"db": DB_NAME})
                for row in result.fetchall():
                    if is_allowed_table(row[0]) and is_allowed_table(row[2]):
                        relationships.append({
                            "from_table": row[0],
                            "from_column": row[1],
                            "to_table": row[2],
                            "to_column": row[3]
                        })
        except Exception as e:
            print("Notice:", e)

    # Ensure static relationships for users.user_role and key FKs are included
    for s_rel in STATIC_RELATIONSHIP_GRAPH:
        if s_rel not in relationships:
            relationships.append(s_rel)

    os.makedirs("knowledge/relationships", exist_ok=True)
    with open("knowledge/relationships/relationships.json", "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=4)

    print("Generated relationships.json successfully with user_role relationships.")
