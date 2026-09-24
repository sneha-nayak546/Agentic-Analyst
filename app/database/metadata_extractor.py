import os
import json
import traceback
from datetime import datetime
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List
from app.database.config import get_db_engine

EXPLICIT_FK = "EXPLICIT_FK"
VERIFIED_UNIQUE_KEY = "VERIFIED_UNIQUE_KEY"
LOGICAL_INFERRED = "LOGICAL_INFERRED"

def get_engine():
    return get_db_engine()

def safe_execute(conn, query, params=None):
    try:
        if params:
            return conn.execute(text(query), params).fetchall()
        return conn.execute(text(query)).fetchall()
    except SQLAlchemyError as e:
        print(f"Warning: Query execution failed: {e}")
        return []

from app.database.allowed_tables import TARGET_SCOPE_TABLES as TARGET_TABLES

import csv

def ingest_csv_dumps(metadata: Dict[str, Any]) -> Dict[str, Any]:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_mappings = {
        "sku_inventories": os.path.join(root_dir, "Sku_Inventeries_Dump_data.csv"),
        "wallet_transaction": os.path.join(root_dir, "Wallet_Transaction_Dump_Data.csv")
    }

    for tbl_name, csv_path in csv_mappings.items():
        if os.path.exists(csv_path):
            try:
                with open(csv_path, mode="r", encoding="utf-8-sig", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames or []
                    rows = list(reader)
                    
                    if tbl_name not in metadata:
                        metadata[tbl_name] = {
                            "name": tbl_name,
                            "columns": {},
                            "primary_keys": ["id"] if "id" in fieldnames else [],
                            "foreign_keys": [],
                            "indexes": [],
                            "unique_constraints": [],
                            "row_count": len(rows)
                        }
                    
                    existing_cols = metadata[tbl_name].get("columns", {})
                    if not isinstance(existing_cols, dict):
                        existing_cols = {}
                        metadata[tbl_name]["columns"] = existing_cols
                        
                    for col in fieldnames:
                        col_clean = col.strip()
                        if not col_clean:
                            continue
                        
                        vals = [r[col] for r in rows if r.get(col) is not None and str(r.get(col)).strip() != ""]
                        distinct_vals = list(dict.fromkeys([str(v).strip() for v in vals]))
                        
                        if col_clean not in existing_cols:
                            col_type = "VARCHAR(255)"
                            if col_clean in ["id", "user_id", "distributer_id", "product_id", "status_retailer_id", "is_active", "is_offline"]:
                                col_type = "INT"
                            elif col_clean in ["amount", "unit_price", "mrp", "invoiced_quantity", "packed_quantity"]:
                                col_type = "DECIMAL(10,2)"
                            elif "date" in col_clean or "at" in col_clean:
                                col_type = "DATETIME"

                            existing_cols[col_clean] = {
                                "name": col_clean,
                                "type": col_type,
                                "nullable": True,
                                "default": "None",
                                "comment": "",
                                "is_enum": False,
                                "enum_values": []
                            }

                        existing_cols[col_clean]["top_values"] = distinct_vals[:5]
                        existing_cols[col_clean]["distinct_count"] = len(distinct_vals)
                        existing_cols[col_clean]["non_null_count"] = len(vals)
                        existing_cols[col_clean]["null_count"] = len(rows) - len(vals)

                    if tbl_name == "wallet_transaction":
                        if "transaction_type" in existing_cols:
                            enums = list(dict.fromkeys(existing_cols["transaction_type"].get("top_values", []) + ['cash_point', 'referral_earning', 'topup', 'coupon_redeem']))
                            existing_cols["transaction_type"]["is_enum"] = True
                            existing_cols["transaction_type"]["enum_values"] = enums
                        if "reference_type" in existing_cols:
                            enums = list(dict.fromkeys(existing_cols["reference_type"].get("top_values", []) + ['cash_point', 'referral_earning', 'topup', 'coupon_redeem']))
                            existing_cols["reference_type"]["is_enum"] = True
                            existing_cols["reference_type"]["enum_values"] = enums
                            
            except Exception as e:
                print(f"Warning: Failed to process CSV dump {csv_path}: {e}")

    return metadata

def extract_table_metadata(engine=None) -> Dict[str, Any]:
    metadata = {}
    schema_file = "knowledge/schema/schema_metadata.json"
    
    # 1. Attempt Live DB Inspection
    if engine is not None:
        try:
            inspector = inspect(engine)
            db_tables = inspector.get_table_names()
            if db_tables:
                print(f"[METADATA DISCOVERY] Live MySQL online. Discovered {len(db_tables)} tables in database.")
                with engine.connect() as conn:
                    row_counts = {}
                    try:
                        rc_rows = safe_execute(conn, "SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.tables WHERE TABLE_SCHEMA = DATABASE();")
                        for r in rc_rows:
                            row_counts[r[0]] = r[1] or 0
                    except Exception:
                        pass

                    for table_name in db_tables:
                        source_table = table_name
                        try:
                            columns = inspector.get_columns(source_table)
                        except Exception:
                            columns = []

                        table_info = {
                            "name": table_name,
                            "columns": {},
                            "primary_keys": inspector.get_pk_constraint(source_table).get('constrained_columns', []) if columns else [],
                            "foreign_keys": inspector.get_foreign_keys(source_table) if columns else [],
                            "indexes": inspector.get_indexes(source_table) if columns else [],
                            "unique_constraints": inspector.get_unique_constraints(source_table) if columns else [],
                            "row_count": row_counts.get(source_table, 0)
                        }
                        for col in columns:
                            col_name = col['name']
                            col_type = str(col['type'])
                            col_info = {
                                "name": col_name,
                                "type": col_type,
                                "nullable": col['nullable'],
                                "default": str(col.get('default')),
                                "comment": col.get('comment', ''),
                                "is_enum": 'ENUM' in col_type.upper(),
                                "enum_values": []
                            }
                            if col_info["is_enum"]:
                                try:
                                    enum_str = col_type[col_type.find("(")+1:col_type.rfind(")")]
                                    col_info["enum_values"] = [v.strip("'\" ") for v in enum_str.split(",")]
                                except Exception:
                                    pass
                            table_info["columns"][col_name] = col_info
                        metadata[table_name] = table_info
        except Exception as e:
            print(f"[METADATA NOTICE] Live DB extraction unavailable ({e}). Loading complete cached schema metadata.")

    # 2. Fallback / Augmentation from comprehensive schema_metadata.json (~240-256 tables)
    if not metadata and os.path.exists(schema_file):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            for tbl, tbl_info in cached_data.items():
                metadata[tbl] = {
                    "name": tbl,
                    "comment": tbl_info.get("comment", ""),
                    "columns": tbl_info.get("columns", {}),
                    "primary_keys": tbl_info.get("primary_keys", []),
                    "foreign_keys": tbl_info.get("foreign_keys", []),
                    "indexes": tbl_info.get("indexes", []),
                    "unique_constraints": tbl_info.get("unique_constraints", []),
                    "row_count": tbl_info.get("row_count", 0)
                }
            print(f"[METADATA SUCCESS] Loaded {len(metadata)} discoverable tables from complete schema metadata.")
        except Exception as err:
            print(f"[METADATA ERROR] Failed to load schema metadata: {err}")

    # Merge CSV dump columns and enums
    metadata = ingest_csv_dumps(metadata)
    return metadata

def discover_dynamic_relationships(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    relationships = []
    seen = set()
    
    # 1. Formal Foreign Keys from Database Schema (No artificial table filters)
    for table_name, info in metadata.items():
        for fk in info.get("foreign_keys", []):
            ref_tbl = fk.get("referred_table")
            if ref_tbl:
                src_cols = fk.get("constrained_columns", [])
                ref_cols = fk.get("referred_columns", [])
                if src_cols and ref_cols:
                    rel_key = (table_name, src_cols[0], ref_tbl, ref_cols[0])
                    if rel_key not in seen:
                        seen.add(rel_key)
                        relationships.append({
                            "from_table": table_name,
                            "from_column": src_cols[0],
                            "to_table": ref_tbl,
                            "to_column": ref_cols[0],
                            "type": "Many-to-One",
                            "origin": EXPLICIT_FK
                        })

    # 2. Ingest Complete Table Connections Catalog (connections_knowledge.json)
    conn_path = "knowledge/connections_knowledge.json"
    if os.path.exists(conn_path):
        try:
            with open(conn_path, "r", encoding="utf-8") as f:
                conn_data = json.load(f)
            for src_tbl, info in conn_data.items():
                for ob in info.get("outbound", []):
                    target_tbl = ob.get("target_table")
                    src_col = ob.get("column")
                    target_col = ob.get("target_column")
                    rel_type = ob.get("type", "Logical")
                    if target_tbl and src_col and target_col:
                        rel_key = (src_tbl, src_col, target_tbl, target_col)
                        if rel_key not in seen:
                            seen.add(rel_key)
                            origin_val = EXPLICIT_FK if rel_type == "Explicit" else (VERIFIED_UNIQUE_KEY if rel_type == "UniqueKey" else LOGICAL_INFERRED)
                            relationships.append({
                                "from_table": src_tbl,
                                "from_column": src_col,
                                "to_table": target_tbl,
                                "to_column": target_col,
                                "type": "Many-to-One",
                                "origin": origin_val
                            })
        except Exception as e:
            print(f"[RELATIONSHIP NOTICE] Error loading connections_knowledge.json: {e}")

    # 3. Authoritative JGH Business Domain Relationships
    JGH_AUTHORITATIVE_JOINS = [
        ("sku_inventories", "sku_code", "qr_point_map", "sku_code", EXPLICIT_FK),
        ("sku_inventories", "sku_code", "sku_qr_points_map", "sku_code", EXPLICIT_FK),
        ("sku_inventories", "status_retailer_id", "users", "id", EXPLICIT_FK),
        ("sku_inventories", "distributer_id", "users", "id", EXPLICIT_FK),
        ("sku_inventories", "status_wholeseller_id", "users", "id", EXPLICIT_FK),
        ("wallet_transaction", "user_id", "users", "id", EXPLICIT_FK),
        ("users", "state_id", "state", "id", EXPLICIT_FK),
        ("users", "user_role", "role", "id", EXPLICIT_FK),
        ("retailer_distributor_mappings", "distributor_id", "users", "id", LOGICAL_INFERRED),
        ("retailer_distributor_mappings", "retailer_id", "users", "id", LOGICAL_INFERRED),
        ("withdrawal_request", "user_id", "users", "id", EXPLICIT_FK),
        ("companies", "customer_id", "users", "id", LOGICAL_INFERRED),
    ]
    for src_t, src_c, tgt_t, tgt_c, orig in JGH_AUTHORITATIVE_JOINS:
        rel_key = (src_t, src_c, tgt_t, tgt_c)
        if rel_key not in seen:
            seen.add(rel_key)
            relationships.append({
                "from_table": src_t,
                "from_column": src_c,
                "to_table": tgt_t,
                "to_column": tgt_c,
                "type": "Many-to-One",
                "origin": orig
            })

    return relationships

def refresh_database_schema() -> Dict[str, Any]:
    """
    Refreshes the complete database knowledge model:
    1. Discovers ALL ~256 tables.
    2. Discovers ALL columns, data types, nullability, defaults.
    3. Discovers PKs, FKs, and builds complete relationship graph.
    4. Extracts enum and status values.
    5. Updates knowledge graph and RAG semantic index.
    """
    print("[SCHEMA REFRESH] Initiating complete database discovery & relationship mapping...")
    return generate_enterprise_knowledge_base()


def build_join_graph(tables: List[str], relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = list(tables)
    edges = []
    for r in relationships:
        edges.append({
            "source": r["from_table"],
            "target": r["to_table"],
            "source_column": r["from_column"],
            "target_column": r["to_column"],
            "join_clause": f"{r['from_table']}.{r['from_column']} = {r['to_table']}.{r['to_column']}"
        })
    return {"nodes": nodes, "edges": edges}

def extract_business_vocabulary(engine, metadata: Dict[str, Any]) -> Dict[str, Any]:
    business_terminology = {}
    entity_dict = {
        "User": {"table": "users", "description": "Core identity table representing retailers, mechanics, distributors, admins"},
        "Role": {"table": "role", "description": "Lookup table specifying user access levels and roles"},
        "WalletTransaction": {"table": "wallet_transaction", "description": "Loyalty points ledger recording credits, debits, scans"},
        "Company": {"table": "companies", "description": "Registered business units, distributors, brand organizations"},
        "SkuInventory": {"table": "sku_inventories", "description": "Product SKU catalogue, batch details, barcode/LPN codes"},
        "Mechanic": {"table": "mechanic_details", "description": "Profile data for garage owners and mechanics including Aadhaar and bank details"},
        "Withdrawal": {"table": "withdrawal_request", "description": "Redemption and payout requests submitted by users"},
        "AutomaticTransaction": {"table": "automatic_transactions", "description": "Direct bank transfer logs and settlement transaction records"}
    }
    
    try:
        with engine.connect() as conn:
            if "role" in metadata:
                role_rows = safe_execute(conn, "SELECT id, name FROM `role`")
                for r in role_rows:
                    r_id, r_name = r[0], str(r[1]).strip()
                    if r_name:
                        business_terminology[r_name.lower()] = {
                            "table": "role",
                            "column": "id",
                            "value": r_id,
                            "condition": f"users.user_role = {r_id}",
                            "description": f"Users having the '{r_name}' role (role.id = {r_id})"
                        }
                        entity_dict[r_name.title()] = {
                            "table": "users",
                            "filter": f"users.user_role = {r_id}",
                            "description": f"Business entity: {r_name}"
                        }
                        
            if "wallet_transaction" in metadata:
                types = safe_execute(conn, "SELECT DISTINCT transaction_type FROM `wallet_transaction` WHERE transaction_type IS NOT NULL")
                for t in types:
                    t_val = str(t[0]).strip()
                    if t_val:
                        business_terminology[f"{t_val.lower()} transactions"] = {
                            "table": "wallet_transaction",
                            "column": "transaction_type",
                            "value": t_val,
                            "condition": f"wallet_transaction.transaction_type = '{t_val}'",
                            "description": f"Wallet records with type '{t_val}'"
                        }
                        
            if "withdrawal_request" in metadata:
                statuses = safe_execute(conn, "SELECT DISTINCT status FROM `withdrawal_request` WHERE status IS NOT NULL")
                for s in statuses:
                    s_val = str(s[0]).strip()
                    if s_val:
                        business_terminology[f"{s_val.lower()} withdrawals"] = {
                            "table": "withdrawal_request",
                            "column": "status",
                            "value": s_val,
                            "condition": f"withdrawal_request.status = '{s_val}'",
                            "description": f"Withdrawal requests currently '{s_val}'"
                        }
    except Exception as e:
        print(f"[VOCABULARY NOTICE] Live connection unavailable ({e}); using baseline business terminology.")
        business_terminology["retailer"] = {
            "table": "role",
            "column": "id",
            "value": 2,
            "condition": "users.user_role = 2",
            "description": "Users having the 'retailer' role (role.id = 2)"
        }
        business_terminology["distributor"] = {
            "table": "role",
            "column": "id",
            "value": 4,
            "condition": "users.user_role = 4",
            "description": "Users having the 'distributor' role (role.id = 4)"
        }

    return {"business_terminology": business_terminology, "entities": entity_dict}

def generate_enterprise_knowledge_base():
    engine = get_engine()
    metadata = extract_table_metadata(engine)
    relationships = discover_dynamic_relationships(metadata)
    join_graph = build_join_graph(list(metadata.keys()), relationships)
    vocab_res = extract_business_vocabulary(engine, metadata)
    
    os.makedirs("knowledge/schema", exist_ok=True)
    os.makedirs("knowledge/graph", exist_ok=True)
    os.makedirs("knowledge/relationships", exist_ok=True)
    
    # 1. schema_metadata.json
    with open("knowledge/schema/schema_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    # 2. relationship_graph.json & relationship_metadata.json
    with open("knowledge/graph/relationship_graph.json", "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=4)
    with open("knowledge/graph/relationship_metadata.json", "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=4)
    with open("knowledge/relationships/relationships.json", "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=4)
        
    # 3. business_dictionary.json
    existing_terms = {}
    if os.path.exists("knowledge/graph/business_dictionary.json"):
        try:
            with open("knowledge/graph/business_dictionary.json", "r", encoding="utf-8") as f:
                d = json.load(f)
                existing_terms = d.get("business_terminology", {})
        except Exception:
            pass

    merged_terminology = {**vocab_res["business_terminology"], **existing_terms}

    business_dictionary = {
        "business_terminology": merged_terminology,
        "tables": {t: info["row_count"] for t, info in metadata.items()}
    }
    with open("knowledge/graph/business_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(business_dictionary, f, indent=4)
        
    # 4. entity_dictionary.json
    with open("knowledge/graph/entity_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(vocab_res["entities"], f, indent=4)
        
    # 5. enum_dictionary.json
    enum_dict = {}
    for table, info in metadata.items():
        for col_name, col_data in info["columns"].items():
            if col_data.get("enum_values"):
                enum_dict[f"{table}.{col_name}"] = col_data["enum_values"]
    with open("knowledge/schema/enum_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(enum_dict, f, indent=4)
    with open("knowledge/graph/enum_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(enum_dict, f, indent=4)
        
    # 6. join_graph.json
    with open("knowledge/graph/join_graph.json", "w", encoding="utf-8") as f:
        json.dump(join_graph, f, indent=4)
        
    # 7. sample_values.json
    sample_values = {}
    for table, info in metadata.items():
        sample_values[table] = {}
        for col_name, col_data in info["columns"].items():
            if col_data.get("top_values"):
                sample_values[table][col_name] = col_data["top_values"]
    with open("knowledge/schema/sample_values.json", "w", encoding="utf-8") as f:
        json.dump(sample_values, f, indent=4)
    with open("knowledge/graph/sample_values.json", "w", encoding="utf-8") as f:
        json.dump(sample_values, f, indent=4)
        
    # 8. business_rules.json
    business_rules = [
        {"rule": "Read Only", "description": "Always generate SELECT statements only."},
        {"rule": "Default Result Limit", "description": "Limit queries to 500 rows unless computing an aggregate (COUNT, SUM, AVG)."},
        {"rule": "Live Database Execution", "description": "Always execute SQL against the real MySQL database. Never return cached metadata values."},
        {"rule": "Table Scoping", "description": "All ~256 database tables are discoverable and queryable across the enterprise schema."}
    ]
    with open("knowledge/graph/business_rules.json", "w", encoding="utf-8") as f:
        json.dump(business_rules, f, indent=4)
        
    # 9. entity_relationships.json
    entity_relationships = {
        "users_to_role": {"from": "users.user_role", "to": "role.id", "type": "Many-to-One", "description": "Each user is assigned a single role."},
        "users_to_wallet_transaction": {"from": "wallet_transaction.user_id", "to": "users.id", "type": "Many-to-One", "description": "Users have multiple wallet loyalty transactions."},
        "users_to_mechanic_details": {"from": "mechanic_details.mechanic_id", "to": "users.id", "type": "One-to-One", "description": "Mechanics have extended profile data in mechanic_details."},
        "users_to_withdrawal_request": {"from": "withdrawal_request.user_id", "to": "users.id", "type": "Many-to-One", "description": "Users submit multiple withdrawal requests."},
        "users_to_automatic_transactions": {"from": "automatic_transactions.user_id", "to": "users.id", "type": "Many-to-One", "description": "Bank transfer logs map directly to user accounts."},
        "companies_to_users": {"from": "companies.customer_id", "to": "users.id", "type": "Many-to-One", "description": "Companies map to user accounts."},
        "companies_to_mechanic_details": {"from": "mechanic_details.company_id", "to": "companies.id", "type": "Many-to-One", "description": "Mechanics belong to companies/garages."},
        "sku_to_users": {"from": "sku_inventories.distributer_id", "to": "users.id", "type": "Many-to-One", "description": "SKU product inventory is managed by distributors."}
    }
    with open("knowledge/graph/entity_relationships.json", "w", encoding="utf-8") as f:
        json.dump(entity_relationships, f, indent=4)
        
    # 10. query_patterns.json
    query_patterns = [
        {"intent": "List records", "pattern": "SELECT {cols} FROM {table} LIMIT 500;"},
        {"intent": "Count total", "pattern": "SELECT COUNT(*) as total FROM {table};"},
        {"intent": "Top K ordered", "pattern": "SELECT {cols} FROM {table} ORDER BY {sort_col} DESC LIMIT 10;"},
        {"intent": "User Transactions", "pattern": "SELECT u.name, wt.amount, wt.transaction_type FROM wallet_transaction wt JOIN users u ON wt.user_id = u.id LIMIT 500;"},
        {"intent": "Company Overview", "pattern": "SELECT id, name, email, phone FROM companies LIMIT 500;"},
        {"intent": "Withdrawals by Status", "pattern": "SELECT id, user_id, amount, status FROM withdrawal_request WHERE status = '{status}' LIMIT 500;"}
    ]
    with open("knowledge/graph/query_patterns.json", "w", encoding="utf-8") as f:
        json.dump(query_patterns, f, indent=4)
        
    # 11. column_statistics.json
    column_statistics = {}
    for t_name, t_info in metadata.items():
        column_statistics[t_name] = {
            "total_rows": t_info.get("row_count", 0),
            "columns": {
                c_name: {
                    "non_null": c_data.get("non_null_count", 0),
                    "distinct": c_data.get("distinct_count", 0),
                    "nulls": c_data.get("null_count", 0)
                } for c_name, c_data in t_info.get("columns", {}).items()
            }
        }
    with open("knowledge/graph/column_statistics.json", "w", encoding="utf-8") as f:
        json.dump(column_statistics, f, indent=4)
        
    # 12. knowledge_graph.json
    knowledge_graph = {
        "nodes": join_graph["nodes"],
        "edges": join_graph["edges"],
        "entities": vocab_res["entities"],
        "business_terminology": vocab_res["business_terminology"]
    }
    with open("knowledge/graph/knowledge_graph.json", "w", encoding="utf-8") as f:
        json.dump(knowledge_graph, f, indent=4)
        
    # 13. schema_refresh_meta.json (Section 27 Specification)
    db_name = os.getenv("DB_NAME") or "jghMasterDB"
    refresh_meta = {
        "database": db_name,
        "timestamp": datetime.now().isoformat(),
        "table_count": len(metadata),
        "column_count": sum(len(info.get("columns", {})) for info in metadata.values()),
        "relationship_count": len(relationships),
        "relationships_by_origin": {
            "EXPLICIT_FK": sum(1 for r in relationships if r.get("origin") == EXPLICIT_FK),
            "VERIFIED_UNIQUE_KEY": sum(1 for r in relationships if r.get("origin") == VERIFIED_UNIQUE_KEY),
            "LOGICAL_INFERRED": sum(1 for r in relationships if r.get("origin") == LOGICAL_INFERRED)
        }
    }
    with open("knowledge/schema/schema_refresh_meta.json", "w", encoding="utf-8") as f:
        json.dump(refresh_meta, f, indent=4)

    print("\n" + "=" * 60)
    print("ALL 12 ENTERPRISE KNOWLEDGE LAYER ARTIFACTS DYNAMICALLY GENERATED")
    print(f"Database: {db_name} | Tables: {refresh_meta['table_count']} | Columns: {refresh_meta['column_count']} | Relationships: {refresh_meta['relationship_count']}")
    print("=" * 60)
    return {
        "metadata": metadata,
        "relationships": relationships,
        "join_graph": join_graph,
        "vocabulary": vocab_res,
        "refresh_meta": refresh_meta
    }

if __name__ == "__main__":
    generate_enterprise_knowledge_base()