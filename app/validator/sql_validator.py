import os
import json
import re
import sqlglot
from sqlglot import exp
from app.validator.sql_optimizer import optimize_sql

BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "TRUNCATE", "CREATE", "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL"
]

FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop,
    exp.Create, exp.Alter
)

_schema_cache = None
def get_schema_metadata():
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = {}
        path = "knowledge/schema/schema_metadata.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _schema_cache = json.load(f)
            except Exception:
                pass
    return _schema_cache

_rel_cache = None
def get_relationships():
    global _rel_cache
    if _rel_cache is None:
        _rel_cache = []
        path = "knowledge/relationships/relationships.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _rel_cache = json.load(f)
            except Exception:
                pass
    return _rel_cache

def validate_sql(sql: str) -> dict:
    if not sql or not sql.strip():
        return {
            "status": "BLOCKED",
            "reason": "SQL query is empty",
            "sql": sql,
            "affected_tables": []
        }

    cleaned_sql = sql.strip().rstrip(";")

    # 1. Pre-filter regex check for forbidden write keywords
    sql_upper = cleaned_sql.upper()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", sql_upper):
            return {
                "status": "BLOCKED",
                "reason": f"Forbidden keyword '{kw}' detected",
                "sql": cleaned_sql,
                "affected_tables": []
            }

    # 2. AST Parsing with sqlglot (MySQL dialect)
    try:
        parsed_expressions = sqlglot.parse(cleaned_sql, read="mysql")
        if not parsed_expressions or parsed_expressions[0] is None:
            return {
                "status": "BLOCKED",
                "reason": "Failed to parse SQL AST",
                "sql": cleaned_sql,
                "affected_tables": []
            }
        ast = parsed_expressions[0]
    except Exception as parse_err:
        if cleaned_sql.upper().startswith("SELECT"):
            optimized_fallback = optimize_sql(cleaned_sql)
            return {
                "status": "APPROVED",
                "reason": "Safe SELECT query (Fallback parse)",
                "sql": optimized_fallback,
                "affected_tables": []
            }
        return {
            "status": "BLOCKED",
            "reason": f"SQL Syntax Error: {str(parse_err)}",
            "sql": cleaned_sql,
            "affected_tables": []
        }

    # 3. Ensure root statement is SELECT, SHOW, DESCRIBE, or EXPLAIN
    if not sql_upper.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN")):
        return {
            "status": "BLOCKED",
            "reason": "Only SELECT, SHOW, DESCRIBE, and EXPLAIN queries are allowed",
            "sql": cleaned_sql,
            "affected_tables": []
        }

    # 4. Check for forbidden expression nodes anywhere in AST
    for node in ast.walk():
        if isinstance(node, FORBIDDEN_NODES):
            return {
                "status": "BLOCKED",
                "reason": f"Forbidden AST operation: {type(node).__name__}",
                "sql": cleaned_sql,
                "affected_tables": []
            }

    # 5. Extract and validate referenced table names and columns against schema metadata
    schema_meta = get_schema_metadata()
    if not schema_meta:
        optimized_sql = optimize_sql(cleaned_sql)
        return {
            "status": "APPROVED",
            "reason": "Safe SELECT (No schema available for validation)",
            "sql": optimized_sql,
            "affected_tables": []
        }

    tables_in_query = list(set([table.name.lower() for table in ast.find_all(exp.Table) if table.name]))
    
    invalid_tables = []
    valid_tables = []
    for t in tables_in_query:
        if t not in schema_meta:
            invalid_tables.append(t)
        else:
            valid_tables.append(t)

    if invalid_tables:
        return {
            "status": "BLOCKED",
            "reason": f"Hallucinated Tables Detected: {', '.join(invalid_tables)}. These tables do not exist in the database.",
            "sql": cleaned_sql,
            "affected_tables": valid_tables
        }

    # 5.5 Validate Joins against Relationship Graph
    rels = get_relationships()
    if rels:
        valid_join_edges = set()
        for r in rels:
            edge1 = f"{r['from_table']}.{r['from_column']}={r['to_table']}.{r['to_column']}"
            edge2 = f"{r['to_table']}.{r['to_column']}={r['from_table']}.{r['from_column']}"
            valid_join_edges.add(edge1)
            valid_join_edges.add(edge2)

        alias_map = {}
        for table in ast.find_all(exp.Table):
            if table.name:
                t_name = table.name.lower()
                alias = table.alias.lower() if table.alias else t_name
                alias_map[alias] = t_name

        for join in ast.find_all(exp.Join):
            if join.args.get("on"):
                on_clause = join.args["on"]
                for eq in on_clause.find_all(exp.EQ):
                    if isinstance(eq.left, exp.Column) and isinstance(eq.right, exp.Column):
                        l_table = alias_map.get(eq.left.table.lower() if eq.left.table else "", "")
                        l_col = eq.left.name.lower()
                        r_table = alias_map.get(eq.right.table.lower() if eq.right.table else "", "")
                        r_col = eq.right.name.lower()
                        
                        if l_table and r_table:
                            edge = f"{l_table}.{l_col}={r_table}.{r_col}"
                            if edge not in valid_join_edges:
                                return {
                                    "status": "BLOCKED",
                                    "reason": f"Hallucinated Join Detected: {edge}. This relationship does not exist in the database.",
                                    "sql": cleaned_sql,
                                    "affected_tables": valid_tables
                                }

    # 6. Run SQL optimization pass
    optimized_sql = optimize_sql(cleaned_sql)

    return {
        "status": "APPROVED",
        "reason": "Safe and valid SELECT query",
        "sql": optimized_sql,
        "affected_tables": valid_tables
    }