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

from app.database.allowed_tables import TARGET_SCOPE_TABLES

def validate_sql(query: str, allowed_tables: list = None) -> bool:
    """
    Validates a SQL query by parsing it into an AST using sqlglot.
    Ensures that only SELECT statements are executed, no malicious nodes exist,
    and all referenced tables are within the allowed list (if provided).
    """
    if allowed_tables is None:
        allowed_tables = TARGET_SCOPE_TABLES

    try:
        # Parse query, assuming MySQL dialect
        parsed = sqlglot.parse(query, read="mysql")
        if not parsed:
            raise SQLValidationError("Empty or invalid query.")
            
        ast = parsed[0]
        
        # 1. Root must be SELECT
        if not isinstance(ast, exp.Select):
            raise SQLValidationError(f"Only SELECT statements are allowed. Found: {type(ast).__name__}")
            
        # 2. Prevent write operations
        forbidden_node_types = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, 
            exp.Create, exp.Commit, exp.Rollback, exp.Execute,
            exp.Command
        )
        for node in ast.find_all(*forbidden_node_types):
            raise SQLValidationError(f"Forbidden operation detected: {type(node).__name__}")
            
        # 3. Validate tables if a list is provided
        if allowed_tables is not None:
            referenced_tables = [table.name.lower() for table in ast.find_all(exp.Table)]
            for t in referenced_tables:
                if t not in allowed_tables:
                    raise SQLValidationError(f"Table '{t}' is not allowed or does not exist.")
                    
            # 4. Validate columns
            schema = _get_schema_metadata()
            if schema:
                valid_columns = set()
                table_to_cols = {}
                for t in referenced_tables:
                    if t in schema:
                        cols = [c.lower() for c in schema[t].get("columns", {}).keys()]
                        table_to_cols[t] = cols
                        valid_columns.update(cols)
                
                for column in ast.find_all(exp.Column):
                    col_name = column.name.lower()
                    if col_name == "*":
                        continue
                        
                    if column.table:
                        tbl = column.table.lower()
                        if tbl in table_to_cols and col_name not in table_to_cols[tbl]:
                            raise SQLValidationError(f"Column '{col_name}' does not exist in table '{tbl}'.")
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
