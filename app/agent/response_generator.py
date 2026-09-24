import re
from typing import Dict, Any, List

class ResponseGenerator:
    """
    Agentic Response Generator.
    Formats verified database results into a natural, business-friendly response.
    Ensures IDs are NOT formatted with commas.
    Ensures calculations and comparisons are explained.
    """

    def generate_response(self, plan: Dict[str, Any], execution_result: Dict[str, Any]) -> str:
        """
        Generates the final natural language answer based on the structured plan and execution results.
        """
        rows = execution_result.get("data", [])
        columns = execution_result.get("columns", [])
        intent = plan.get("intent", "").lower()
        metrics = plan.get("metrics", [])
        
        if not execution_result.get("success"):
            return f"Error executing query: {execution_result.get('error', 'Unknown Error')}"

        if not rows:
            # Handle empty results gracefully with explicit ID/relationship contexts
            specific_id = plan.get("specific_id", {})
            id_val = specific_id.get("value")
            id_type = specific_id.get("type", "entity")
            target = plan.get("target_entity", plan.get("primary_entity", "records"))
            
            if id_val:
                return f"I found the {id_type} (ID: {id_val}), but no {target} were found matching your requested filters."
            return f"No {target} matching the exact requirements were found."

        # Calculations / Percentages
        if "percentage" in intent or "percent" in intent:
            if rows and len(columns) == 1:
                val = rows[0].get(columns[0])
                return f"The requested percentage is {val}%."
        
        # Single Aggregate / Count
        if len(rows) == 1 and (len(columns) == 1 or len(columns) == 2):
            val = rows[0].get(columns[-1])
            if "count" in metrics or "total" in intent:
                return f"The total count is {self._format_value(val)}."
            elif "earnings" in metrics:
                return f"The total earnings amount to {self._format_currency(val)}."

        # Table formatting for general queries
        response = "Here are the verified results:\n\n"
        
        # Format Header
        response += "| " + " | ".join(self._clean_col_names(columns)) + " |\n"
        response += "|" + "|".join(["---"] * len(columns)) + "|\n"
        
        # Format Rows (prevent commas in IDs)
        for row in rows[:15]:  # Limit output in text response
            formatted_row = []
            for col in columns:
                val = row.get(col)
                if "id" in col.lower() or col.lower().endswith("_code"):
                    formatted_row.append(str(val)) # No formatting for IDs
                elif "amount" in col.lower() or "earning" in col.lower() or "tds" in col.lower():
                    formatted_row.append(self._format_currency(val))
                else:
                    formatted_row.append(str(val))
            response += "| " + " | ".join(formatted_row) + " |\n"
            
        if len(rows) > 15:
            response += f"\n*(Showing top 15 out of {len(rows)} records)*"

        return response

    def _format_value(self, val: Any) -> str:
        if val is None: return "0"
        try:
            return f"{int(val):,}"
        except:
            return str(val)

    def _format_currency(self, val: Any) -> str:
        if val is None: return "₹0.00"
        try:
            return f"₹{float(val):,.2f}"
        except:
            return str(val)
            
    def _clean_col_names(self, cols: List[str]) -> List[str]:
        return [c.replace("_", " ").title() for c in cols]

response_generator = ResponseGenerator()
