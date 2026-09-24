"""
Deterministic SQL AST Security Validator for JGH Intelligence Engine.
Ensures queries are strictly read-only (SELECT, UNION, JOIN, CTE, Subqueries, Aggregations, Window Functions),
and recursively blocks any destructive AST operations (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE,
CREATE, REPLACE, MERGE, GRANT, REVOKE, CALL, EXECUTE) or multiple statements.
"""

from typing import Optional, Any
import sqlglot
from sqlglot import exp


class SQLASTSecurityError(Exception):
    """Raised when a query violates AST read-only security constraints."""
    pass


# Backward compatibility alias
SQLValidationError = SQLASTSecurityError

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

VALID_DATE_COLUMNS = {
    "created_at",
    "retailer_scanned_at",
    "wholesaler_scanned_at",
    "invoice_date",
    "order_date",
    "updated_at",
}


def validate_ast_security(query: str, plan: Optional[Any] = None) -> bool:
    """
    Validates a SQL query by parsing it into an AST using sqlglot.
    Ensures that only read-only statements (SELECT, UNION, CTE, subqueries) are executed,
    no destructive write/DDL/DCL nodes exist anywhere in the AST, no sensitive columns
    are accessed, and temporal queries contain a timestamp filter.
    """
    if not query or not isinstance(query, str) or not query.strip():
        raise SQLASTSecurityError("LLM generated an empty query. Triggering self-correction retry...")

    try:
        # Parse query with MySQL dialect
        parsed = sqlglot.parse(query, read="mysql")
        if not parsed or not parsed[0]:
            raise SQLASTSecurityError("LLM generated an empty query. Triggering self-correction retry...")

        # 1. Prevent multiple statements (SQL Injection risk)
        if len(parsed) > 1:
            raise SQLASTSecurityError("Multiple SQL statements are not allowed for security reasons.")

        ast = parsed[0]

        # 2. Statement Root must be a read-only Query (Select, Union, Subquery, CTE)
        if ast is None or not isinstance(ast, exp.Query):
            found_type = type(ast).__name__ if ast is not None else "NoneType"
            raise SQLASTSecurityError(f"Only SELECT statements are allowed. Found: {found_type}")

        # 3. Recursively block any write, DDL, DCL, or command operations anywhere in AST
        for node in ast.find_all(*FORBIDDEN_AST_NODES):
            raise SQLASTSecurityError(f"Forbidden operation detected: {type(node).__name__}")

        # 4. Sensitive Column Blacklist Check (Enterprise Security Policy)
        for column in ast.find_all(exp.Column):
            col_name = column.name.lower()
            if col_name in RESTRICTED_SECURITY_COLUMNS:
                raise SQLASTSecurityError(
                    f"Access to sensitive column '{col_name}' is strictly restricted by security policy."
                )

        # 5. Temporal Validation: Ensure queries with time constraints include a timestamp filter
        if plan:
            has_time = False
            if hasattr(plan, "business_requirement"):
                has_time = bool(
                    plan.business_requirement.date_period
                    or plan.business_requirement.relative_dates
                )
            elif isinstance(plan, dict):
                tc = plan.get("time_constraint", {})
                has_time = tc.get("has_time_filter") or (
                    plan.get("time_filter") and plan.get("time_filter") != "None"
                )

            if has_time:
                sql_upper = query.upper()
                has_date_filter = any(
                    col_name.upper() in sql_upper for col_name in VALID_DATE_COLUMNS
                ) or any(
                    col.name.lower() in VALID_DATE_COLUMNS
                    for col in ast.find_all(exp.Column)
                )
                if not has_date_filter:
                    raise SQLASTSecurityError(
                        "Temporal query plan requires a timestamp filter in WHERE clause."
                    )

        return True

    except sqlglot.errors.ParseError as e:
        raise SQLASTSecurityError(f"SQL Syntax Error: {str(e)}")
    except Exception as e:
        if isinstance(e, SQLASTSecurityError):
            raise e
        raise SQLASTSecurityError(f"Validation Error: {str(e)}")


def validate_sql(query: str, allowed_tables: Optional[list] = None, plan: Optional[Any] = None) -> bool:
    """
    Backwards-compatible wrapper for validate_ast_security and schema column validation.
    Runs AST security checks, then runs schema & column existence validation.
    """
    validate_ast_security(query, plan=plan)
    from app.validator.schema_column_validator import validate_schema_columns, SchemaColumnValidationError
    try:
        validate_schema_columns(query, allowed_tables=allowed_tables)
    except SchemaColumnValidationError as e:
        raise SQLASTSecurityError(str(e))
    return True
