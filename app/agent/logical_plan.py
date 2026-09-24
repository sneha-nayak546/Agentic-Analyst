"""
Logical Query Planner for JGH Intelligence Engine.
Builds an intermediate structured logical query plan before SQL generation:
  task, tables, columns, joins, filters, metric, group_by, order_by, limit.
The LLM SQL generator generates SQL directly from this grounded plan rather
than guessing raw text.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LogicalQueryPlan(BaseModel):
    """
    Intermediate logical plan describing the target SQL operation.
    """
    task: str = Field(..., description="High-level description of what the query calculates.")
    tables: List[str] = Field(default_factory=list, description="Target database tables.")
    columns: List[str] = Field(default_factory=list, description="Target database columns (table.column).")
    joins: List[str] = Field(default_factory=list, description="Explicit verified join conditions.")
    filters: List[str] = Field(default_factory=list, description="Explicit filter conditions.")
    metric: Optional[str] = Field(None, description="Aggregation or computed metric (e.g. SUM(amount)).")
    group_by: List[str] = Field(default_factory=list, description="Grouping columns.")
    order_by: Optional[str] = Field(None, description="Sorting specification.")
    limit: Optional[int] = Field(None, description="Row limit.")
    atomic_tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Sub-tasks if multi-part.")

def build_logical_query_plan(
    requirement: Any,
    relevant_tables: List[str],
    required_joins: List[str],
    linked_values: Dict[str, Any]
) -> LogicalQueryPlan:
    """
    Constructs a deterministic LogicalQueryPlan by integrating the business requirement,
    verified joins, and linked database values.
    """
    task_name = f"{requirement.intent}_{'_'.join(requirement.entities)}"
    columns = list(requirement.requested_columns)
    filters = []

    # Map verified linked filters with proper table qualification
    tbl_set = set(relevant_tables)
    if linked_values.get("resolved_filters"):
        for rf in linked_values["resolved_filters"]:
            col = rf["column"]
            op = rf["operator"]
            val = rf["value"]

            # Table qualification to prevent ambiguous columns
            if col in ["user_role", "city", "district", "state_id", "status"] and "users" in tbl_set:
                col = f"users.{col}"
            elif col in ["transaction_type"] and "wallet_transaction" in tbl_set:
                col = f"wallet_transaction.{col}"
            elif col == "id" and "users" in tbl_set:
                col = f"users.id"

            if isinstance(val, str):
                filters.append(f"{col} {op} '{val}'")
            else:
                filters.append(f"{col} {op} {val}")

    # Map dates with event table qualification
    if linked_values.get("date_range"):
        dr = linked_values["date_range"]
        if "wallet_transaction" in tbl_set:
            date_col = "wallet_transaction.created_at"
        elif "sku_inventories" in tbl_set:
            date_col = "sku_inventories.retailer_scanned_at"
        elif "users" in tbl_set and len(tbl_set) == 1:
            date_col = "users.created_at"
        else:
            date_col = "created_at"
        filters.append(f"{date_col} >= '{dr['start']}' AND {date_col} < '{dr['end']}'")

    # Map metrics, aggregations, and earnings condition
    metric_expr = None
    req_metrics_lower = [m.lower() for m in requirement.metrics]
    req_ents_lower = [e.lower() for e in requirement.entities]
    is_earnings = any("earning" in m for m in req_metrics_lower)
    q_lower = getattr(requirement, "original_question", "").lower()
    is_active = "active" in q_lower or any("active" in str(c).lower() for c in requirement.conditions)

    if is_active and "wallet_transaction" in tbl_set and ("users" in tbl_set or any(e in ["retailer", "distributor", "user"] for e in req_ents_lower)):
        metric_expr = "COUNT(DISTINCT users.id)"
        columns = ["COUNT(DISTINCT users.id) AS active_retailers" if "retailer" in req_ents_lower else "COUNT(DISTINCT users.id) AS active_users"]
    elif is_earnings:
        metric_expr = "SUM(wallet_transaction.amount)"
        if "wallet_transaction" in tbl_set:
            if not any("amount > 0" in f for f in filters):
                filters.append("wallet_transaction.amount > 0")
            if not any("transaction_type" in f for f in filters):
                filters.append("wallet_transaction.transaction_type = 1")
        if not columns:
            columns = ["SUM(wallet_transaction.amount) AS total_earnings"]
    elif requirement.metrics and requirement.aggregation:
        metric_expr = f"{requirement.aggregation[0]}({requirement.metrics[0]})"
        if not columns:
            columns = [f"{metric_expr} AS {requirement.metrics[0]}"]
    elif "wallet_balance" in req_metrics_lower:
        metric_expr = "wallet_balance"

    # Grouping
    group_by_cols = list(requirement.grouping)
    is_ranking = bool(requirement.ranking or requirement.intent in ["ranking", "top_n"])
    q_lower = getattr(requirement, "original_question", "").lower()
    if is_ranking or (requirement.limit and is_earnings):
        if not group_by_cols and ("users" in tbl_set or any(e in ["retailer", "distributor", "user"] for e in requirement.entities)):
            group_by_cols = ["users.id", "users.name"]

    # Sorting
    order_by = None
    if requirement.sorting:
        order_by = requirement.sorting[0]
    elif is_ranking:
        direction = "ASC" if any(w in q_lower for w in ["bottom", "lowest", "least", "worst"]) else "DESC"
        order_by = f"{metric_expr or 'id'} {direction}"

    return LogicalQueryPlan(
        task=task_name,
        tables=relevant_tables,
        columns=columns,
        joins=required_joins,
        filters=filters,
        metric=metric_expr,
        group_by=group_by_cols,
        order_by=order_by,
        limit=requirement.limit
    )
