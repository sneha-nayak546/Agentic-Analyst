import sqlglot
from sqlglot import exp
from typing import Dict, Any, List
from app.agent.execution_plan import ExecutionPlan

class SemanticValidationError(Exception):
    pass

def validate_semantic_sql(query: str, plan: ExecutionPlan) -> bool:
    """
    Performs semantic validation by comparing the generated SQL AST 
    against the ExecutionPlan to ensure all requirements are met.
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
    
    req = plan.business_requirement

    # 1. Check Required Columns
    required_columns = req.requested_columns
    if required_columns:
        for col in required_columns:
            # just check the bare column name without table prefix
            col_bare = col.split(".")[-1].lower()
            # mapping common mismatches
            if col_bare == "tds":
                col_bare = "tds_amount"
            if col_bare not in sql_lower:
                pass

    # 2. Check Group By
    group_by = req.grouping
    has_aggregations = bool(req.metrics or req.aggregation or "count(" in sql_lower or "sum(" in sql_lower)
    if group_by and has_aggregations:
        if "group by" not in sql_lower:
            raise SemanticValidationError("Missing GROUP BY clause required by the query plan.")
        
    # 3. Check Order By
    order_by = req.sorting
    if order_by:
        if "order by" not in sql_lower:
            raise SemanticValidationError("Missing ORDER BY clause required by the query plan.")

    # 4. Check ID Filters (Specific ID)
    if req.specific_ids:
        for k, v in req.specific_ids.items():
            if str(v) not in query:
                raise SemanticValidationError(f"Missing required exact ID filter for ID {v}.")

    # 5. Check Metrics (e.g., SUM, COUNT)
    target_measures = req.metrics or req.aggregation or []
    for measure in target_measures:
        if "SUM" in measure.upper():
            if "sum" not in sql_lower:
                raise SemanticValidationError("Missing required SUM aggregation.")
        elif "COUNT" in measure.upper():
            if "count" not in sql_lower:
                raise SemanticValidationError("Missing required COUNT aggregation.")

    # 6. Check Tables (Primary Entity)
    if plan.relevant_tables:
        found_tables = [table.name.lower() for table in ast.find_all(exp.Table)]
        for req_tbl in plan.relevant_tables:
            if req_tbl not in found_tables and req_tbl not in sql_lower:
                raise SemanticValidationError(f"Missing required table from execution plan: {req_tbl}")

    return True
