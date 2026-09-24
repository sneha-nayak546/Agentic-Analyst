"""
Deterministic Schema & Column-Existence Validator for JGH Intelligence Engine.
Ensures that all referenced tables and columns in generated SQL queries physically exist
in the active database schema (SQLite / MySQL schema metadata).
Provides high-context, deterministic error reporting on missing columns:
    COLUMN_NOT_FOUND
    table=<tbl>
    column=<col>
"""

import os
import json
import sqlite3
from typing import Dict, Set, List, Optional, Any
import sqlglot
from sqlglot import exp


class SchemaColumnValidationError(Exception):
    """Raised when a query references non-existent tables or columns."""
    def __init__(self, message: str, table: Optional[str] = None, column: Optional[str] = None):
        super().__init__(message)
        self.table = table
        self.column = column


_schema_cache: Optional[Dict[str, Set[str]]] = None


def get_active_schema() -> Dict[str, Set[str]]:
    """
    Loads active database schema from SQLite database.db and schema_metadata.json.
    Returns a dict mapping lowercase table names to sets of lowercase column names.
    """
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

    _schema_cache = schema
    return schema


def get_known_columns_for_table(table_name: str) -> List[str]:
    """Returns sorted list of known valid columns for a given table name."""
    schema = get_active_schema()
    cols = schema.get(table_name.lower(), set())
    return sorted(list(cols))


def validate_schema_columns(query: str, allowed_tables: Optional[List[str]] = None) -> bool:
    """
    Parses the SQL query and deterministically verifies that:
    1. All referenced physical tables exist in the schema.
    2. All referenced columns physically exist in the corresponding tables.
    3. CTE and subquery aliases are handled accurately without false positives.
    """
    if not query or not isinstance(query, str) or not query.strip():
        raise SchemaColumnValidationError("Query is empty.")

    schema = get_active_schema()
    if not schema:
        # No schema metadata available; skip validation
        return True

    try:
        parsed = sqlglot.parse(query, read="mysql")
        if not parsed or not parsed[0]:
            return True
        ast = parsed[0]
    except Exception as e:
        raise SchemaColumnValidationError(f"SQL Syntax Error during schema parsing: {e}")

    # 1. Extract CTE definitions (e.g. WITH my_cte AS (...))
    ctes: Set[str] = set()
    for cte in ast.find_all(exp.CTE):
        if cte.alias_or_name:
            ctes.add(cte.alias_or_name.lower())

    # 2. Extract Subquery aliases (e.g. (SELECT ...) subq)
    subquery_aliases: Set[str] = set()
    for subq in ast.find_all(exp.Subquery):
        if subq.alias:
            subquery_aliases.add(subq.alias.lower())

    # 3. Build alias-to-table mapping for physical tables
    alias_to_table: Dict[str, str] = {}
    referenced_physical_tables: List[str] = []

    for tbl_node in ast.find_all(exp.Table):
        raw_name = tbl_node.name.lower() if tbl_node.name else ""
        if not raw_name:
            continue

        # Skip CTE references
        if raw_name in ctes:
            if tbl_node.alias:
                alias_to_table[tbl_node.alias.lower()] = f"<CTE:{raw_name}>"
            alias_to_table[raw_name] = f"<CTE:{raw_name}>"
            continue

        # Physical table verification
        if raw_name not in schema:
            raise SchemaColumnValidationError(
                f"TABLE_NOT_FOUND\ntable={raw_name}\nTable '{raw_name}' is not allowed or does not exist.",
                table=raw_name
            )

        if allowed_tables:
            allowed_lowers = [t.lower() for t in allowed_tables]
            if raw_name not in allowed_lowers:
                raise SchemaColumnValidationError(
                    f"TABLE_NOT_ALLOWED\ntable={raw_name}\nTable '{raw_name}' is not allowed or does not exist.",
                    table=raw_name
                )

        referenced_physical_tables.append(raw_name)
        alias = tbl_node.alias.lower() if tbl_node.alias else raw_name
        alias_to_table[alias] = raw_name
        alias_to_table[raw_name] = raw_name

    # Map subquery aliases to special markers
    for sq_alias in subquery_aliases:
        alias_to_table[sq_alias] = f"<SUBQUERY:{sq_alias}>"

    # 4. Extract expression aliases defined in SELECT or CTEs (e.g. SELECT x AS my_alias)
    defined_aliases: Set[str] = set()
    for alias_node in ast.find_all(exp.Alias):
        if alias_node.alias:
            defined_aliases.add(alias_node.alias.lower())

    # 5. Validate referenced columns
    for col_node in ast.find_all(exp.Column):
        col_name = col_node.name.lower() if col_node.name else ""
        if not col_name or col_name == "*" or col_name in defined_aliases:
            continue

        # Check if qualified by a table or alias
        if col_node.table:
            tbl_qualifier = col_node.table.lower()

            # If qualified by a CTE or subquery alias, physical column schema doesn't apply
            target_target = alias_to_table.get(tbl_qualifier, tbl_qualifier)
            if (
                tbl_qualifier in ctes
                or tbl_qualifier in subquery_aliases
                or str(target_target).startswith("<CTE:")
                or str(target_target).startswith("<SUBQUERY:")
            ):
                continue

            real_table = target_target
            if real_table in schema:
                if col_name not in schema[real_table]:
                    raise SchemaColumnValidationError(
                        f"COLUMN_NOT_FOUND\ntable={real_table}\ncolumn={col_name}\nColumn '{col_name}' does not exist in table '{real_table}'.",
                        table=real_table,
                        column=col_name
                    )
        else:
            # Unqualified column: must exist in at least one referenced physical table
            if referenced_physical_tables:
                exists_anywhere = any(
                    col_name in schema.get(t, set())
                    for t in referenced_physical_tables
                )
                if not exists_anywhere:
                    primary_tbl = referenced_physical_tables[0]
                    raise SchemaColumnValidationError(
                        f"COLUMN_NOT_FOUND\ntable={primary_tbl}\ncolumn={col_name}\nColumn '{col_name}' does not exist in schema.",
                        table=primary_tbl,
                        column=col_name
                    )

    return True
