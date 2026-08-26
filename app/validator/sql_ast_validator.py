import sqlglot
from sqlglot import exp

class SQLValidationError(Exception):
    pass

import os
import json

def _get_schema_metadata():
    schema_file = "knowledge/schema/schema_metadata.json"
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def validate_sql(query: str, allowed_tables: list = None, plan: dict = None) -> bool:
    """
    Validates a SQL query by parsing it into an AST using sqlglot.
    Ensures that only SELECT statements are executed, no malicious nodes exist,
    all referenced tables are within the allowed list (if provided), and
    temporal queries contain a created_at timestamp filter.
    """
    if not query or not isinstance(query, str) or not query.strip():
        raise SQLValidationError("LLM generated an empty query. Triggering self-correction retry...")

    schema = _get_schema_metadata()
    if allowed_tables is None:
        allowed_tables = list(schema.keys())

    try:
        # Parse query, assuming MySQL dialect
        parsed = sqlglot.parse(query, read="mysql")
        if not parsed or not parsed[0]:
            raise SQLValidationError("LLM generated an empty query. Triggering self-correction retry...")
            
        # Prevent multiple statements (SQL Injection risk)
        if len(parsed) > 1:
            raise SQLValidationError("Multiple SQL statements are not allowed for security reasons.")
            
        ast = parsed[0]
        
        # 1. Root must be SELECT
        if ast is None or not isinstance(ast, exp.Select):
            found_type = type(ast).__name__ if ast is not None else "NoneType"
            raise SQLValidationError(f"Only SELECT statements are allowed. Found: {found_type}")
            
        # 1b. Temporal Validation: Ensure queries with time constraints include a valid timestamp filter
        if plan:
            has_time = False
            if hasattr(plan, 'business_requirement'):
                has_time = bool(plan.business_requirement.date_period or plan.business_requirement.relative_dates)
            else:
                tc = plan.get("time_constraint", {})
                has_time = tc.get("has_time_filter") or (plan.get("time_filter") and plan.get("time_filter") != "None")
                
            if has_time:
                sql_upper = query.upper()
                valid_date_cols = ["CREATED_AT", "RETAILER_SCANNED_AT", "WHOLESALER_SCANNED_AT", "INVOICE_DATE", "ORDER_DATE", "UPDATED_AT"]
                has_date_filter = any(col_name in sql_upper for col_name in valid_date_cols) or any(col.name.lower() in [c.lower() for c in valid_date_cols] for col in ast.find_all(exp.Column))
                if not has_date_filter:
                    raise SQLValidationError("Temporal query plan requires a timestamp filter in WHERE clause.")
            
        # 2. Prevent write operations & command nodes
        forbidden_node_types = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, 
            exp.Create, exp.Commit, exp.Rollback, exp.Execute,
            exp.Command
        )
        for node in ast.find_all(*forbidden_node_types):
            raise SQLValidationError(f"Forbidden operation detected: {type(node).__name__}")

        # 2b. Sensitive Column Blacklist Check (Security Requirement)
        restricted_columns = {"password", "secret", "token", "master_key", "auth_token", "private_key", "password_hash"}
        for column in ast.find_all(exp.Column):
            col_name = column.name.lower()
            if col_name in restricted_columns:
                raise SQLValidationError(f"Access to sensitive column '{col_name}' is strictly restricted by security policy.")
            
        # 3. Validate tables if a list is provided
        if allowed_tables is not None:
            referenced_tables = [table.name.lower() for table in ast.find_all(exp.Table)]
            for t in referenced_tables:
                if t not in allowed_tables:
                    raise SQLValidationError(f"Table '{t}' is not allowed or does not exist.")
                    
            # Build table alias mapping (e.g. 'wt' -> 'wallet_transaction', 'u' -> 'users')
            alias_to_table = {}
            for table in ast.find_all(exp.Table):
                real_tbl = table.name.lower()
                alias = table.alias.lower() if table.alias else real_tbl
                alias_to_table[alias] = real_tbl
                alias_to_table[real_tbl] = real_tbl

            # 4. Validate columns against schema metadata
            schema = _get_schema_metadata()
            if schema:
                valid_columns = set()
                table_to_cols = {}
                for t in referenced_tables:
                    if t in schema:
                        raw_cols = schema[t].get("columns", {})
                        if isinstance(raw_cols, dict):
                            cols = [c.lower() for c in raw_cols.keys()]
                        elif isinstance(raw_cols, list):
                            cols = [c["name"].lower() if isinstance(c, dict) else str(c).lower() for c in raw_cols]
                        else:
                            cols = []
                        table_to_cols[t] = cols
                        valid_columns.update(cols)

                # Extract aliases defined in SELECT (e.g., AS cash_point_earning)
                select_aliases = set()
                for alias_node in ast.find_all(exp.Alias):
                    select_aliases.add(alias_node.alias.lower())

                for column in ast.find_all(exp.Column):
                    col_name = column.name.lower()
                    if col_name == "*" or col_name in select_aliases:
                        continue
                        
                    if column.table:
                        raw_tbl = column.table.lower()
                        real_tbl = alias_to_table.get(raw_tbl, raw_tbl)
                        if real_tbl in table_to_cols:
                            if col_name not in table_to_cols[real_tbl]:
                                raise SQLValidationError(f"Column '{col_name}' does not exist in table '{real_tbl}'.")
                        else:
                            if valid_columns and col_name not in valid_columns:
                                raise SQLValidationError(f"Column '{col_name}' does not exist in schema.")
                    else:
                        if valid_columns and col_name not in valid_columns:
                            raise SQLValidationError(f"Column '{col_name}' does not exist in any of the referenced tables.")
                            
        return True
        
    except sqlglot.errors.ParseError as e:
        raise SQLValidationError(f"SQL Syntax Error: {str(e)}")
    except Exception as e:
        if isinstance(e, SQLValidationError):
            raise e
        raise SQLValidationError(f"Validation Error: {str(e)}")
