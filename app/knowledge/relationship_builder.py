import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from app.database.allowed_tables import is_allowed_table, TARGET_SCOPE_TABLES

# Static relationship graph fallback for 8 target scope tables
# Static relationship graph fallback for 9 target scope tables
STATIC_RELATIONSHIP_GRAPH = [
    {"from_table": "users", "from_column": "user_role", "to_table": "role", "to_column": "id"},
    {"from_table": "wallet_transaction", "from_column": "user_id", "to_table": "users", "to_column": "id"},
    {"from_table": "withdrawal_request", "from_column": "user_id", "to_table": "users", "to_column": "id"},
    {"from_table": "withdrawal_request", "from_column": "automatic_transaction_id", "to_table": "automatic_transactions", "to_column": "id"},
    {"from_table": "automatic_transactions", "from_column": "user_id", "to_table": "users", "to_column": "id"},
    {"from_table": "sku_inventories", "from_column": "distributer_id", "to_table": "users", "to_column": "id"},
    {"from_table": "sku_inventories", "from_column": "status_retailer_id", "to_table": "users", "to_column": "id"},
    {"from_table": "sku_inventories", "from_column": "status_wholeseller_id", "to_table": "users", "to_column": "id"},
    {"from_table": "sku_inventories", "from_column": "sku_code", "to_table": "sku_qr_points_map", "to_column": "sku_code"},
    {"from_table": "sku_qr_points_map", "from_column": "status_wholesaler_id", "to_table": "users", "to_column": "id"},
    {"from_table": "sku_qr_points_map", "from_column": "status_retailer_id", "to_table": "users", "to_column": "id"},
    {"from_table": "mechanic_details", "from_column": "mechanic_id", "to_table": "users", "to_column": "id"},
    {"from_table": "mechanic_details", "from_column": "company_id", "to_table": "companies", "to_column": "id"},
    {"from_table": "companies", "from_column": "customer_id", "to_table": "users", "to_column": "id"}
]

def get_relationship_graph() -> list:
    rel_path = "knowledge/relationships/relationships.json"
    if os.path.exists(rel_path):
        try:
            with open(rel_path, "r", encoding="utf-8") as f:
                rels = json.load(f)
                filtered = [
                    r for r in rels
                    if is_allowed_table(r.get("from_table")) and is_allowed_table(r.get("to_table"))
                ]
                if filtered:
                    # Guarantee user_role relationship is present
                    has_role_rel = any(r.get("from_column") == "user_role" for r in filtered)
                    if not has_role_rel:
                        filtered.append({"from_table": "users", "from_column": "user_role", "to_table": "user_role", "to_column": "id"})
                    return filtered
        except Exception:
            pass
    return STATIC_RELATIONSHIP_GRAPH


def get_relationship_prompt_text(tables: set = None) -> str:
    rels = get_relationship_graph()
    lines = []
    seen = set()
    for r in rels:
        f_tbl, f_col = r["from_table"], r["from_column"]
        t_tbl, t_col = r["to_table"], r["to_column"]
        if tables:
            if f_tbl not in tables and t_tbl not in tables:
                continue
        rel_str = f"{f_tbl}.{f_col} = {t_tbl}.{t_col}"
        if rel_str not in seen:
            seen.add(rel_str)
            lines.append(rel_str)
    return "\n".join(lines) if lines else "users.user_role = user_role.id\nwallet_transaction.user_id = users.id"


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
