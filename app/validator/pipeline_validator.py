"""
Authoritative SQL Validation and Safety Gate for JGH Intelligence Engine.
Enforces:
  1. AST Read-Only Security (SELECT, WITH, UNION only; no mutation or DDL).
  2. Single Statement (Injection prevention).
  3. Table Existence (against physical schema).
  4. Column Existence (against referenced physical tables).
  5. Basic Semantic Consistency:
     - Box scans must query sku_inventories, never wallet_transaction or users alone.
     - Earnings must query wallet_transaction with amount > 0.
     - Timestamps: retailer_scanned_at for box scans, created_at for wallet transactions.
"""

import re
import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Set
import sqlglot
from sqlglot import exp

FORBIDDEN_AST_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.TruncateTable,
    exp.Create,
    exp.Command,
    exp.Execute,
    exp.Commit,
    exp.Rollback,
    exp.Merge,
    exp.Grant,
    exp.Revoke,
    exp.Replace,
)

RESTRICTED_SECURITY_COLUMNS = {
    "password",
    "secret",
    "token",
    "master_key",
    "auth_token",
    "private_key",
    "password_hash",
}

_schema_cache: Optional[Dict[str, Set[str]]] = None

def get_active_schema() -> Dict[str, Set[str]]:
    """Loads active database schema mapping lowercase table names to sets of lowercase column names."""
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache

    schema: Dict[str, Set[str]] = {}

    from app.database.read_executor import is_explicit_local_test_mode

    # 1. Inspect local SQLite database.db ONLY if in explicit local test mode
    if is_explicit_local_test_mode():
        db_path = "database.db"
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
                for tbl in tables:
                    cols = {row[1].lower() for row in cursor.execute(f"PRAGMA table_info('{tbl}');").fetchall()}
                    schema[tbl.lower()] = cols
                conn.close()
            except Exception:
                pass

    # 2. Production schema source: schema_metadata.json
    meta_path = "knowledge/schema/schema_metadata.json"
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            for tbl, tbl_info in metadata.items():
                t_lower = tbl.lower()
                raw_cols = tbl_info.get("columns", {})
                json_cols = set()
                if isinstance(raw_cols, dict):
                    json_cols = {k.lower() for k in raw_cols.keys()}
                elif isinstance(raw_cols, list):
                    json_cols = {
                        c["name"].lower() if isinstance(c, dict) else str(c).lower()
                        for c in raw_cols
                    }
                if t_lower in schema:
                    schema[t_lower].update(json_cols)
                else:
                    schema[t_lower] = json_cols
        except Exception:
            pass

    # 3. Ensure sku_qr_points_maps and qr_point_map alias parity and column variations
    if "sku_qr_points_maps" in schema:
        schema["sku_qr_points_maps"].add("box_calculation_uom")
        schema["sku_qr_points_maps"].add("box_calulation_um")
        schema["sku_qr_points_map"] = set(schema["sku_qr_points_maps"])
        schema["qr_point_map"] = set(schema["sku_qr_points_maps"])
    elif "qr_point_map" in schema:
        schema["qr_point_map"].add("box_calculation_uom")
        schema["qr_point_map"].add("box_calulation_um")
        schema["sku_qr_points_maps"] = set(schema["qr_point_map"])
        schema["sku_qr_points_map"] = set(schema["qr_point_map"])

    _schema_cache = schema
    return schema


def validate_generated_sql(sql: str, question: str = "") -> Dict[str, Any]:
    """
    Validates the generated SQL against AST read-only rules, physical schema, and semantic consistency.
    Returns {"is_valid": bool, "error": Optional[str], "sql": str}.
    """
    if not sql or not isinstance(sql, str) or not sql.strip():
        return {
            "is_valid": False,
            "error": "The generated SQL is empty.",
            "category": "EMPTY_SQL"
        }

    clean_sql_str = sql.strip().strip(";").strip()
    
    # 1. Parse AST
    try:
        parsed = sqlglot.parse(clean_sql_str, read="mysql")
    except Exception as parse_err:
        return {
            "is_valid": False,
            "error": f"SQL Syntax Error: {parse_err}",
            "category": "SYNTAX_ERROR"
        }

    if not parsed or not parsed[0]:
        return {
            "is_valid": False,
            "error": "Could not parse SQL query into a valid AST.",
            "category": "SYNTAX_ERROR"
        }

    if len(parsed) > 1:
        return {
            "is_valid": False,
            "error": "Multiple SQL statements detected. Only a single SELECT query is permitted.",
            "category": "MULTIPLE_STATEMENTS"
        }

    ast = parsed[0]

    # 2. Read-Only Root Check
    if not isinstance(ast, exp.Query):
        return {
            "is_valid": False,
            "error": f"Only SELECT/read-only queries are permitted. Found: {type(ast).__name__}",
            "category": "NON_READ_ONLY"
        }

    # 3. Forbid write / DDL / DCL nodes
    for node in ast.find_all(*FORBIDDEN_AST_NODES):
        return {
            "is_valid": False,
            "error": f"Dangerous or write operation detected: {type(node).__name__}",
            "category": "FORBIDDEN_OPERATION"
        }

    # 4. Sensitive Column Check
    for column in ast.find_all(exp.Column):
        col_name = column.name.lower()
        if col_name in RESTRICTED_SECURITY_COLUMNS:
            return {
                "is_valid": False,
                "error": f"Access to sensitive security column '{col_name}' is prohibited.",
                "category": "SECURITY_POLICY_VIOLATION"
            }

    # 5. Schema & Table Existence
    schema = get_active_schema()
    referenced_tables: Dict[str, str] = {} # alias/name -> physical table name or CTE name
    cte_definitions: Dict[str, Set[str]] = {} # cte_name -> set of output column names

    # Extract all CTE definitions and their projected output column aliases
    for with_node in ast.find_all(exp.With):
        for cte in with_node.expressions:
            cte_name = cte.alias_or_name.lower()
            cte_cols = set()
            cte_query = cte.this
            if isinstance(cte_query, exp.Query):
                for select_expr in cte_query.expressions:
                    if hasattr(select_expr, "output_name") and select_expr.output_name:
                        cte_cols.add(select_expr.output_name.lower())
                    elif isinstance(select_expr, exp.Column):
                        cte_cols.add(select_expr.name.lower())
            cte_definitions[cte_name] = cte_cols
            referenced_tables[cte_name] = cte_name

    # Register subquery aliases
    for subquery in ast.find_all(exp.Subquery):
        sub_alias = subquery.alias_or_name.lower()
        if sub_alias:
            referenced_tables[sub_alias] = "__subquery__"

    # Register all FROM and JOIN tables
    for table_node in ast.find_all(exp.Table):
        t_name = table_node.name.lower()
        if not t_name:
            continue
        
        alias = table_node.alias_or_name.lower()

        # If it's a CTE reference
        if t_name in cte_definitions:
            referenced_tables[alias] = t_name
            referenced_tables[t_name] = t_name
            continue

        if schema and t_name not in schema:
            return {
                "is_valid": False,
                "error": f"Table '{t_name}' does not exist in the database schema.",
                "category": "TABLE_NOT_FOUND"
            }
        
        referenced_tables[alias] = t_name
        referenced_tables[t_name] = t_name

    # 6. Column Existence in Referenced Tables
    # For qualified columns (e.g. u.id, si.retailer_scanned_at, rs.retailer_id)
    for column in ast.find_all(exp.Column):
        col_name = column.name.lower()
        tbl_ref = column.table.lower() if column.table else None

        if tbl_ref:
            if tbl_ref not in referenced_tables:
                return {
                    "is_valid": False,
                    "error": f"Table alias '{tbl_ref}' referenced in '{tbl_ref}.{col_name}' is not defined or joined in FROM/JOIN clauses.",
                    "category": "UNKNOWN_TABLE_ALIAS"
                }
            phys_tbl = referenced_tables[tbl_ref]
            
            # If referencing a CTE
            if phys_tbl in cte_definitions:
                known_cte_cols = cte_definitions[phys_tbl]
                if known_cte_cols and col_name not in known_cte_cols and col_name != "*":
                    # CTE columns are known and column doesn't match
                    return {
                        "is_valid": False,
                        "error": f"Column '{col_name}' does not exist in CTE '{phys_tbl}'. Projected columns: {', '.join(sorted(known_cte_cols))}",
                        "category": "COLUMN_NOT_FOUND"
                    }
            elif phys_tbl == "__subquery__":
                pass
            elif phys_tbl in schema and col_name not in schema[phys_tbl] and col_name != "*":
                valid_cols = sorted(list(schema[phys_tbl]))[:10]
                return {
                    "is_valid": False,
                    "error": f"Column '{col_name}' does not exist in table '{phys_tbl}'. Valid columns include: {', '.join(valid_cols)}",
                    "category": "COLUMN_NOT_FOUND"
                }

    # Verify GROUP BY expressions
    select_aliases = {
        expr.output_name.lower()
        for s in ast.find_all(exp.Select)
        for expr in s.expressions
        if getattr(expr, "output_name", None)
    }
    all_table_cols = set().union(*[schema.get(t, set()) for t in referenced_tables.values() if t in schema])
    all_table_cols.update(*[cte_definitions.get(t, set()) for t in referenced_tables.values() if t in cte_definitions])

    for group_node in ast.find_all(exp.Group):
        for g_expr in group_node.expressions:
            if isinstance(g_expr, exp.Column):
                g_col = g_expr.name.lower()
                g_tbl = g_expr.table.lower() if g_expr.table else None
                if not g_tbl and g_col not in all_table_cols and g_col not in select_aliases:
                    return {
                        "is_valid": False,
                        "error": f"Column or alias '{g_col}' in GROUP BY does not exist in joined tables or SELECT projection.",
                        "category": "COLUMN_NOT_FOUND"
                    }

    # 7. Basic Semantic Consistency
    q_lower = question.lower()
    sql_lower = clean_sql_str.lower()
    sql_upper = clean_sql_str.upper()

    has_scan_terms = any(w in q_lower for w in ["box scan", "box scans", "boxes scanned", "scanned box", "scanned boxes", "scan count", "box", "boxes", "scan", "scans"])
    has_earnings_terms = any(w in q_lower for w in ["earning", "earnings", "earned", "revenue", "points earned", "loyalty earning"])

    is_box_scan = has_scan_terms
    is_earnings = has_earnings_terms

    # Box scan metric source check
    if is_box_scan:
        if "sku_inventories" not in sql_lower:
            return {
                "is_valid": False,
                "error": "METRIC_SOURCE_MISMATCH: Box scan questions must query 'sku_inventories' joined with 'qr_point_map'. Do not query 'users' alone.",
                "category": "METRIC_SOURCE_MISMATCH"
            }
        # Only forbid wallet_transaction if earnings was NOT requested
        if not has_earnings_terms and "wallet_transaction" in sql_lower:
            return {
                "is_valid": False,
                "error": "METRIC_SOURCE_MISMATCH: Box scans must not query 'wallet_transaction'. Use 'sku_inventories' joined with 'qr_point_map'.",
                "category": "METRIC_SOURCE_MISMATCH"
            }
        if any(c in sql_upper for c in ["COUNT(SI.ID)", "COUNT(SKU_INVENTORIES.ID)", "COUNT( SI.ID )", "COUNT( SKU_INVENTORIES.ID )"]):
            return {
                "is_valid": False,
                "error": "BUSINESS_RULE_MISMATCH: Authoritative JGH box quantity is SUM(qr_point_map.box_calulation_um), NEVER COUNT(sku_inventories.id). COUNT(si.id) counts database records, not actual box quantity.",
                "category": "BUSINESS_RULE_MISMATCH"
            }
        if (
            "qr_point_map" not in sql_lower
            and "sku_qr_points_map" not in sql_lower
            and "sku_qr_points_maps" not in sql_lower
            and "box_calulation_um" not in sql_lower
            and "box_calculation_uom" not in sql_lower
        ):
            return {
                "is_valid": False,
                "error": "METRIC_SOURCE_MISMATCH: Box scans must join 'sku_qr_points_maps' on sku_code and calculate SUM(qpm.box_calculation_uom).",
                "category": "METRIC_SOURCE_MISMATCH"
            }
        # Box scan timestamp check
        if any(w in q_lower for w in ["this month", "last month", "july", "june", "today", "2026"]):
            if "retailer_scanned_at" not in sql_lower and "wholesaler_scanned_at" not in sql_lower:
                if "created_at" in sql_lower and "sku_inventories" in sql_lower:
                    return {
                        "is_valid": False,
                        "error": "TEMPORAL_COLUMN_MISMATCH: For box scans, filter by 'sku_inventories.retailer_scanned_at', NOT 'users.created_at'.",
                        "category": "TEMPORAL_COLUMN_MISMATCH"
                    }

    # Earnings metric source check
    if is_earnings:
        if "wallet_transaction" not in sql_lower:
            return {
                "is_valid": False,
                "error": "METRIC_SOURCE_MISMATCH: Earnings queries must query 'wallet_transaction' using SUM(wt.amount).",
                "category": "METRIC_SOURCE_MISMATCH"
            }
        if "amount" in sql_lower and not any(f in sql_upper for f in ["AMOUNT > 0", "AMOUNT>0"]):
            return {
                "is_valid": False,
                "error": "BUSINESS_RULE_MISMATCH: Earnings queries must filter positive amounts (e.g. WHERE wt.amount > 0).",
                "category": "BUSINESS_RULE_MISMATCH"
            }
        if "reference_type" not in sql_lower and not any(f in sql_lower for f in ["topup", "cash_point", "referral_earning", "coupon_redeem"]):
            return {
                "is_valid": False,
                "error": "BUSINESS_RULE_MISMATCH: Earnings queries must filter reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem').",
                "category": "BUSINESS_RULE_MISMATCH"
            }

    # 8. Ranking Semantics Check
    if any(w in q_lower for w in ["highest", "most", "maximum", "best"]):
        if "order by" in sql_lower and " desc" not in sql_lower:
            if " asc" in sql_lower:
                return {
                    "is_valid": False,
                    "error": "RANKING_SEMANTICS_MISMATCH: Questions asking for 'highest' or 'most' must ORDER BY metric DESC (found ASC).",
                    "category": "RANKING_SEMANTICS_MISMATCH"
                }

    if any(w in q_lower for w in ["lowest", "least", "minimum", "worst"]):
        if "order by" in sql_lower and " asc" not in sql_lower:
            if " desc" in sql_lower:
                return {
                    "is_valid": False,
                    "error": "RANKING_SEMANTICS_MISMATCH: Questions asking for 'lowest' or 'least' must ORDER BY metric ASC (found DESC).",
                    "category": "RANKING_SEMANTICS_MISMATCH"
                }

    # Single ranking limit check
    if any(p in q_lower for p in ["which distributor has the highest", "which retailer", "which state has the highest", "which category has the lowest"]):
        if "order by" in sql_lower and "limit" not in sql_lower:
            return {
                "is_valid": False,
                "error": "RANKING_SEMANTICS_MISMATCH: Questions asking for a single highest/lowest entity must include LIMIT 1.",
                "category": "RANKING_SEMANTICS_MISMATCH"
            }

    return {
        "is_valid": True,
        "error": None,
        "sql": clean_sql_str
    }

