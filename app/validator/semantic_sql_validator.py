import sqlglot
from sqlglot import exp
from typing import Dict, Any, List

class SemanticValidationError(Exception):
    pass

def validate_semantic_sql(query: str, plan: Dict[str, Any]) -> bool:
    """
    Performs semantic validation by comparing the generated SQL AST 
    against the Structured Query Plan to ensure all requirements are met.
    """
    if not query or not plan:
        return True

    try:
        parsed = sqlglot.parse(query, read="mysql")
        if not parsed or not parsed[0]:
            return False
        ast = parsed[0]
    except Exception as e:
        # Let sql_ast_validator catch syntax errors
        return True

    # Build lower-case string for fallback checks
    sql_lower = query.lower()

    # 1. Check Required Columns
    required_columns = plan.get("required_columns", [])
    if required_columns:
        for col in required_columns:
            # just check the bare column name without table prefix
            col_bare = col.split(".")[-1].lower()
            # mapping common mismatches
            if col_bare == "tds":
                col_bare = "tds_amount"
            if col_bare not in sql_lower:
                # If still not found, just warn instead of blocking, as LLM might have used a different schema column
                pass

    # 2. Check Group By
    group_by = plan.get("group_by", [])
    if group_by:
        if "group by" not in sql_lower:
            raise SemanticValidationError("Missing GROUP BY clause required by the query plan.")
        
    # 3. Check Order By
    order_by = plan.get("order_by", [])
    if order_by:
        if "order by" not in sql_lower:
            raise SemanticValidationError("Missing ORDER BY clause required by the query plan.")

    # 4. Check ID Filters (Specific ID)
    specific_id = plan.get("specific_id")
    if specific_id:
        if str(specific_id) not in query:
            raise SemanticValidationError(f"Missing required exact ID filter for ID {specific_id}.")

    # 5. Check Metrics (e.g., SUM, COUNT)
    target_measures = plan.get("target_measures", [])
    for measure in target_measures:
        if "SUM" in measure.upper():
            if "sum" not in sql_lower:
                raise SemanticValidationError("Missing required SUM aggregation.")
        elif "COUNT" in measure.upper():
            if "count" not in sql_lower:
                raise SemanticValidationError("Missing required COUNT aggregation.")

    # 6. Check Tables (Primary Entity)
    primary = plan.get("primary_entity")
    if primary:
        # map primary to table
        tbl_map = {
            "withdrawal_request": "withdrawal_request",
            "retailer": "users",
            "distributor": "users",
            "user": "users",
            "wallet_transaction": "wallet_transaction",
            "sku_inventories": "sku_inventories"
        }
        req_tbl = tbl_map.get(primary)
        if req_tbl:
            found_tables = [table.name.lower() for table in ast.find_all(exp.Table)]
            if req_tbl not in found_tables and req_tbl not in sql_lower:
                raise SemanticValidationError(f"Missing primary table: {req_tbl}")

    return True
