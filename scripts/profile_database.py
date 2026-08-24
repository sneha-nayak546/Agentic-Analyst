"""
Phase 0 Database Profiling Script for JGH Intelligence Engine.
Introspects MySQL database (jghMasterDB) using SQLAlchemy/PyMySQL configuration,
profiles low-cardinality enums, identifies restricted/sensitive columns, and maps implicit relationships.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.database.config import get_db_engine

def run_database_profiling():
    print("=" * 60)
    print(" 🔍 JGH Intelligence Engine - Phase 0 Database Profiler")
    print("=" * 60)

    engine = get_db_engine()
    knowledge_dir = PROJECT_ROOT / "knowledge"
    schema_dir = knowledge_dir / "schema"

    knowledge_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)

    with engine.connect() as conn:
        db_name = conn.execute(text("SELECT DATABASE()")).scalar() or "jghMasterDB"
        print(f"[+] Connected to MySQL database: {db_name}")

        # ----------------------------------------------------------------------
        # 1. SCHEMA STRUCTURE INTROSPECTION
        # ----------------------------------------------------------------------
        print("\n[1/4] Introspecting Schema Structure from INFORMATION_SCHEMA...")

        columns_sql = text("""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """)
        col_rows = conn.execute(columns_sql, {"db_name": db_name}).fetchall()

        fk_sql = text("""
            SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, CONSTRAINT_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = :db_name AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        fk_rows = conn.execute(fk_sql, {"db_name": db_name}).fetchall()

        # Group foreign keys
        fk_map = defaultdict(list)
        for r in fk_rows:
            fk_map[r.TABLE_NAME].append({
                "column": r.COLUMN_NAME,
                "referenced_table": r.REFERENCED_TABLE_NAME,
                "referenced_column": r.REFERENCED_COLUMN_NAME,
                "constraint_name": r.CONSTRAINT_NAME
            })

        tables_meta = defaultdict(lambda: {"columns": [], "primary_keys": [], "foreign_keys": []})

        for r in col_rows:
            tbl = r.TABLE_NAME
            cname = r.COLUMN_NAME
            is_pk = (r.COLUMN_KEY == "PRI")

            col_meta = {
                "name": cname,
                "data_type": r.DATA_TYPE,
                "column_type": r.COLUMN_TYPE,
                "is_nullable": r.IS_NULLABLE,
                "default": r.COLUMN_DEFAULT,
                "primary_key": is_pk,
                "extra": r.EXTRA
            }

            tables_meta[tbl]["columns"].append(col_meta)
            if is_pk:
                tables_meta[tbl]["primary_keys"].append(cname)

        for tbl, fks in fk_map.items():
            tables_meta[tbl]["foreign_keys"] = fks

        schema_metadata = {
            "database_name": db_name,
            "generated_at": datetime.now().isoformat(),
            "total_tables": len(tables_meta),
            "tables": dict(tables_meta)
        }

        draft_schema_path = schema_dir / "draft_schema_metadata.json"
        with open(draft_schema_path, "w", encoding="utf-8") as f:
            json.dump(schema_metadata, f, indent=2, default=str)
        print(f"[OK] Saved schema metadata ({len(tables_meta)} tables) to {draft_schema_path.relative_to(PROJECT_ROOT)}")

        # ----------------------------------------------------------------------
        # 2. LOW-CARDINALITY ENUM PROFILING
        # ----------------------------------------------------------------------
        print("\n[2/4] Profiling Low-Cardinality Enums across all tables...")

        # Fast single query for estimated table row counts from INFORMATION_SCHEMA.TABLES
        tbl_rows_sql = text("SELECT TABLE_NAME, TABLE_ROWS FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = :db_name")
        tbl_rows_res = conn.execute(tbl_rows_sql, {"db_name": db_name}).fetchall()
        tbl_row_counts = {r.TABLE_NAME: (r.TABLE_ROWS if r.TABLE_ROWS is not None else 0) for r in tbl_rows_res}

        low_cardinality_profile = {}
        target_columns = {
            ("users", "user_role"),
            ("wallet_transaction", "reference_type"),
            ("wallet_transaction", "status"),
            ("sku_inventories", "order_type"),
            ("sku_inventories", "sources"),
            ("sku_qr_points_map", "gride_type"),
            ("sku_qr_points_map", "uom"),
            ("sku_qr_points_maps", "gride_type"),
            ("sku_qr_points_maps", "uom"),
        }

        targeted_enums = {}

        # Column name keywords for candidate enums
        enum_keywords = ["status", "type", "role", "mode", "category", "gride", "uom", "source", "action", "level", "tier", "flag", "active", "is_"]
        skip_keywords = ["password", "hash", "token", "secret", "address", "description", "email", "url", "image", "file", "path", "comment", "json", "payload", "created_at", "updated_at", "deleted_at"]

        for tbl, meta in tables_meta.items():
            est_rows = tbl_row_counts.get(tbl, 0)

            for col_info in meta["columns"]:
                cname = col_info["name"]
                cname_lower = cname.lower()
                dtype = col_info["data_type"].lower()
                is_target = (tbl, cname) in target_columns

                # Filter out non-enums unless explicitly targeted
                if not is_target:
                    if col_info.get("primary_key") or cname_lower == "id" or cname_lower.endswith("_id"):
                        continue
                    if any(sk in cname_lower for sk in skip_keywords):
                        continue
                    if "text" in dtype or "blob" in dtype or "date" in dtype or "time" in dtype:
                        continue

                    is_candidate = (
                        "enum" in dtype or "set" in dtype or "tinyint" in dtype or
                        any(kw in cname_lower for kw in enum_keywords) or
                        ("char" in dtype and not cname_lower.endswith("_id"))
                    )

                    if not is_candidate:
                        continue

                try:
                    # Optimized profiling query using LIMIT subquery sampling for large tables (>50,000 estimated rows)
                    if est_rows > 50000:
                        sample_q = f"SELECT `{cname}`, COUNT(*) as count FROM (SELECT `{cname}` FROM `{tbl}` LIMIT 100000) as t GROUP BY `{cname}` ORDER BY count DESC LIMIT 51"
                    else:
                        sample_q = f"SELECT `{cname}`, COUNT(*) as count FROM `{tbl}` GROUP BY `{cname}` ORDER BY count DESC LIMIT 51"

                    rows = conn.execute(text(sample_q)).fetchall()
                    unique_count = len(rows)

                    if unique_count <= 50 or is_target:
                        val_counts = []
                        for r in rows:
                            val = r[0]
                            cnt = r[1]
                            val_counts.append({"value": val, "count": cnt})

                        key_name = f"{tbl}.{cname}"
                        profile_entry = {
                            "table_name": tbl,
                            "column_name": cname,
                            "data_type": col_info["data_type"],
                            "estimated_total_rows": est_rows,
                            "unique_values_count": unique_count if unique_count <= 50 else f">50 (Sampled {len(rows)})",
                            "distinct_values": val_counts
                        }
                        low_cardinality_profile[key_name] = profile_entry

                        if is_target:
                            targeted_enums[key_name] = profile_entry
                except Exception:
                    pass

        db_profile_data = {
            "generated_at": datetime.now().isoformat(),
            "description": "Low-cardinality enum values and row counts across database tables",
            "targeted_columns": targeted_enums,
            "all_low_cardinality_columns": low_cardinality_profile
        }

        draft_profile_path = knowledge_dir / "draft_db_profile.json"
        with open(draft_profile_path, "w", encoding="utf-8") as f:
            json.dump(db_profile_data, f, indent=2, default=str)
        print(f"[OK] Saved low-cardinality profile ({len(low_cardinality_profile)} columns profiled) to {draft_profile_path.relative_to(PROJECT_ROOT)}")

        # ----------------------------------------------------------------------
        # 3. SENSITIVE & RESTRICTED COLUMN DETECTION
        # ----------------------------------------------------------------------
        print("\n[3/4] Scanning for Sensitive & Restricted Columns...")
        security_keywords = ["password", "hash", "token", "secret", "auth", "reset", "key"]

        restricted_columns = []
        for tbl, meta in tables_meta.items():
            for col in meta["columns"]:
                cname = col["name"]
                cname_lower = cname.lower()

                matched_keywords = [kw for kw in security_keywords if kw in cname_lower]
                if matched_keywords:
                    restricted_columns.append({
                        "table_name": tbl,
                        "column_name": cname,
                        "data_type": col["data_type"],
                        "matched_keywords": matched_keywords,
                        "recommendation": "RESTRICT_FROM_PROMPTS_AND_EXCLUDE_FROM_LLM_OUTPUT"
                    })

        restricted_data = {
            "generated_at": datetime.now().isoformat(),
            "total_restricted_columns": len(restricted_columns),
            "security_keywords": security_keywords,
            "restricted_columns": restricted_columns
        }

        draft_restricted_path = knowledge_dir / "draft_restricted_columns.json"
        with open(draft_restricted_path, "w", encoding="utf-8") as f:
            json.dump(restricted_data, f, indent=2, default=str)
        print(f"[OK] Saved restricted column map ({len(restricted_columns)} columns) to {draft_restricted_path.relative_to(PROJECT_ROOT)}")

        # ----------------------------------------------------------------------
        # 4. IMPLICIT RELATIONSHIP CANDIDATE MAPPER
        # ----------------------------------------------------------------------
        print("\n[4/4] Mapping Implicit Foreign Key / Join Candidate Relationships...")

        # Group tables by column names
        col_to_tables = defaultdict(list)
        for tbl, meta in tables_meta.items():
            for col in meta["columns"]:
                cname = col["name"]
                col_to_tables[cname].append((tbl, col))

        candidate_edges = []
        for cname, tbl_cols in col_to_tables.items():
            if len(tbl_cols) < 2:
                continue

            cname_lower = cname.lower()
            # Focus on key/id/code columns shared across tables
            is_key_like = (
                cname_lower.endswith("_id") or
                cname_lower.endswith("_code") or
                cname_lower in ["id", "sku_code", "status_retailer_id", "status_wholeseller_id", "user_id", "distributer_id", "distributor_id", "company_id", "product_id"]
            )

            if not is_key_like:
                continue

            # Generate candidate edges between table pairs
            for i in range(len(tbl_cols)):
                for j in range(i + 1, len(tbl_cols)):
                    tbl_a, col_a = tbl_cols[i]
                    tbl_b, col_b = tbl_cols[j]

                    candidate_edges.append({
                        "source_table": tbl_a,
                        "source_column": cname,
                        "target_table": tbl_b,
                        "target_column": cname,
                        "join_condition": f"{tbl_a}.{cname} = {tbl_b}.{cname}",
                        "data_type": col_a["data_type"],
                        "confidence": "HIGH" if cname in ["user_id", "sku_code", "distributer_id", "status_retailer_id", "status_wholeseller_id"] else "MEDIUM"
                    })

        relationship_data = {
            "generated_at": datetime.now().isoformat(),
            "total_candidate_edges": len(candidate_edges),
            "candidate_edges": candidate_edges
        }

        draft_graph_path = knowledge_dir / "draft_relationship_graph.json"
        with open(draft_graph_path, "w", encoding="utf-8") as f:
            json.dump(relationship_data, f, indent=2, default=str)
        print(f"[OK] Saved candidate relationship graph ({len(candidate_edges)} edges) to {draft_graph_path.relative_to(PROJECT_ROOT)}")

    print("\n" + "=" * 60)
    print(" ✅ Database Profiling Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    run_database_profiling()
