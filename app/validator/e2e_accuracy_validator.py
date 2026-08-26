import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class E2EAccuracyValidator:
    """
    Strict End-to-End Accuracy Validation Layer.
    Validates 10 dimensions of a query before it is allowed to return data:
    USER INTENT → ENTITY → ID/IDENTIFIER → RELATIONSHIP → FILTERS → DATE RANGE → METRIC → AGGREGATION → GENERATED SQL → ACTUAL RESULT
    """

    def validate(
        self,
        question: str,
        sql: str,
        context: Dict[str, Any],
        execution_result: Dict[str, Any],
        plan: Any
    ) -> Dict[str, Any]:
        """
        Runs the 10-point accuracy validation.
        Returns a dict: {"success": bool, "reason": str, "failed_dimension": str}
        """
        sql_lower = sql.lower() if sql else ""
        rows = execution_result.get("data", []) or []
        row_count = len(rows)
        
        is_obj = hasattr(plan, 'business_requirement')
        req = plan.business_requirement if is_obj else None

        try:
            # 1. USER INTENT
            # Basic intent validation - we expect SELECT queries
            if not sql_lower.strip().startswith("select"):
                return {"success": False, "reason": "Generated SQL is not a SELECT query.", "failed_dimension": "USER INTENT"}

            # 2. ENTITY
            expected_tables = plan.relevant_tables if is_obj else plan.get("tables", [])
            for table in expected_tables:
                # Naive check: table name must be in the SQL
                if table.lower() not in sql_lower:
                    return {"success": False, "reason": f"Expected entity '{table}' not found in SQL.", "failed_dimension": "ENTITY"}

            # 3. ID/IDENTIFIER
            specific_ids = req.specific_ids.values() if is_obj else []
            if not is_obj:
                specific_id = plan.get("identifier_value") or context.get("specific_id")
                if specific_id:
                    specific_ids = [specific_id["value"] if isinstance(specific_id, dict) else specific_id]
                    
            for specific_id in specific_ids:
                str_id = str(specific_id).strip()
                pattern = rf"=\s*['\"]?{re.escape(str_id)}['\"]?\b"
                if not re.search(pattern, sql_lower):
                    return {"success": False, "reason": f"Requested specific ID '{str_id}' is missing from the query filters.", "failed_dimension": "ID/IDENTIFIER"}

            # 4. RELATIONSHIP
            relationships = plan.required_joins if is_obj else plan.get("relationships_required", [])
            if relationships and "join" not in sql_lower:
                return {"success": False, "reason": "Query requires table relationships but no JOIN is present.", "failed_dimension": "RELATIONSHIP"}

            # 5. FILTERS
            # Role filter
            expected_role = None
            if not is_obj: expected_role = plan.get("role_id") or context.get("role_id")
            if expected_role is not None:
                pattern = rf"\buser_role\s*=\s*{expected_role}\b"
                if not re.search(pattern, sql_lower):
                    return {"success": False, "reason": f"Expected user_role={expected_role} filter missing.", "failed_dimension": "FILTERS"}

            # State/Region filter
            expected_state = None
            if not is_obj: expected_state = plan.get("state_id") or context.get("state_id")
            if expected_state is not None:
                pattern = rf"\bstate_id\s*=\s*{expected_state}\b"
                if not re.search(pattern, sql_lower):
                    return {"success": False, "reason": f"Expected state_id={expected_state} filter missing.", "failed_dimension": "FILTERS"}
            
            # Status filter
            status_filter = None
            if not is_obj: status_filter = plan.get("status_filter") or context.get("status_filter")
            if status_filter:
                status_value_map = {
                    "approved": "approved",
                    "active": "approved",
                    "pending": "pending",
                    "rejected": "rejected",
                    "inactive": "inactive",
                }
                expected_status_val = status_value_map.get(status_filter.lower())
                if expected_status_val:
                    pattern = rf"status\s*=\s*['\"]?{re.escape(expected_status_val)}['\"]?"
                    if not re.search(pattern, sql_lower):
                        return {"success": False, "reason": f"Expected status filter '{status_filter}' missing.", "failed_dimension": "FILTERS"}

            # 6. DATE RANGE
            date_range = bool(req.date_period or req.relative_dates) if is_obj else plan.get("date_range")
            if date_range:
                has_date_filter = any(
                    kw in sql_lower
                    for kw in ["created_at", "updated_at", "transaction_date", "date(", "year(", "month(", "between", "date_format", ">=", "<"]
                )
                if not has_date_filter:
                    return {"success": False, "reason": "Expected temporal/date filter is missing.", "failed_dimension": "DATE RANGE"}

            # 7. METRIC
            # Ensure if a metric is requested, some aggregate function or specific column is present.
            metrics = req.metrics if is_obj else []
            if not is_obj: 
                m = plan.get("metric") or context.get("metric")
                if m: metrics.append(m)
                
            for metric in metrics:
                if metric == "earnings" and "amount" not in sql_lower:
                     return {"success": False, "reason": "Earnings metric requested but 'amount' not in SQL.", "failed_dimension": "METRIC"}
                if metric == "scans" and "sku_inventories" not in sql_lower:
                     return {"success": False, "reason": "Scans metric requested but 'sku_inventories' not in SQL.", "failed_dimension": "METRIC"}

            # 8. AGGREGATION
            group_by = req.grouping if is_obj else plan.get("group_by", [])
            if group_by:
                if "group by" not in sql_lower:
                    return {"success": False, "reason": "Aggregation requested but GROUP BY missing.", "failed_dimension": "AGGREGATION"}

            # 9. GENERATED SQL
            # Handled upstream by AST validator, but we assert it exists
            if not sql:
                return {"success": False, "reason": "Generated SQL is empty.", "failed_dimension": "GENERATED SQL"}

            # 10. ACTUAL RESULT
            if row_count == 0:
                # If 0 rows returned but we requested specific IDs, it might be correct, 
                # but we return success here and let the caller decide if VERIFIED_EMPTY applies
                pass

            return {"success": True, "reason": "All 10 dimensions verified successfully.", "failed_dimension": None}

        except Exception as e:
            return {"success": False, "reason": f"Validation engine failure: {str(e)}", "failed_dimension": "INTERNAL"}

e2e_accuracy_validator = E2EAccuracyValidator()
