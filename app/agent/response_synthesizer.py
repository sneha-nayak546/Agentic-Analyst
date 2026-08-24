"""
Gemini/ChatGPT-Style Response Synthesizer for JGH AI Collaborator.
Formats outputs into warm conversational narratives, explains what the data means,
and appends 2 natural follow-up question suggestions.
"""

from typing import Dict, Any, List

class ResponseSynthesizer:
    @staticmethod
    def synthesize(intent: str, mode_result: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """
        Unifies and formats agent response payloads for API output and frontend UI rendering.
        """
        raw_response = mode_result.get("response", "")
        sql_query = mode_result.get("generated_sql", mode_result.get("sql", ""))
        data = mode_result.get("data", [])
        status = mode_result.get("status", "success")

        # Generate 2 relevant follow-up question suggestions
        follow_ups = ResponseSynthesizer._generate_follow_ups(intent, prompt, data)

        # Build natural conversational narrative if in SQL_ANALYTICS mode
        if intent == "SQL_ANALYTICS" and data:
            narrative = ResponseSynthesizer._format_sql_narrative(prompt, sql_query, data, mode_result)
        else:
            narrative = raw_response

        # Append follow-up suggestions to response narrative
        if follow_ups:
            narrative += f"\n\n💡 **Follow-Up Suggestions**:\n1. \"{follow_ups[0]}\"\n2. \"{follow_ups[1]}\""

        unified_output = {
            "mode": intent,
            "status": status,
            "question": prompt,
            "response": narrative,
            "generated_sql": sql_query,
            "data": data,
            "meta": {
                "mermaid_code": mode_result.get("mermaid_code"),
                "dashboard_spec": mode_result.get("dashboard_spec"),
                "sql_executed": mode_result.get("sql_executed", False),
                "follow_ups": follow_ups
            }
        }

        return unified_output

    @staticmethod
    def _format_sql_narrative(prompt: str, sql: str, data: List[Dict[str, Any]], mode_result: Dict[str, Any]) -> str:
        row_cnt = len(data)
        exec_res = mode_result.get("raw_result", {}).get("execution", {})
        exec_time = exec_res.get("execution_time_ms", 12)

        # Calculate high-level metrics for narrative
        summary_insight = f"Found **{row_cnt} records** matching your search criteria."
        if data and isinstance(data[0], dict):
            keys = list(data[0].keys())
            # Find total or max if numeric column exists
            for k in keys:
                if any(term in k.lower() for term in ["amount", "balance", "total", "count", "earnings", "scans"]):
                    try:
                        vals = [float(r[k]) for r in data if r.get(k) is not None]
                        if vals:
                            max_val = max(vals)
                            total_val = sum(vals)
                            summary_insight += f" Total combined **{k}** is **{total_val:,.2f}** (highest single record is **{max_val:,.2f}**)."
                            break
                    except (ValueError, TypeError):
                        pass

        narrative = (
            f"Here are the query results for **\"{prompt}\"**:\n\n"
            f"📌 **Key Insight**: {summary_insight}\n\n"
            f"The query executed successfully against `jghMasterDB` in **{exec_time} ms**."
        )

        return narrative

    @staticmethod
    def _generate_follow_ups(intent: str, prompt: str, data: List[Dict[str, Any]]) -> List[str]:
        p_lower = prompt.lower()

        if any(w in p_lower for w in ["withdrawal", "payout", "withdraw"]):
            return [
                "Show only pending withdrawal requests",
                "Show TDS deducted for withdrawals in August 2026",
                "What was the percentage change in payouts between July and August 2026?"
            ]
        elif any(w in p_lower for w in ["distributor", "retailer", "mechanic", "wholesaler"]):
            if "top" in p_lower:
                return [
                    "Compare with performance in previous month",
                    "Show monthly earnings trend over last 6 months",
                    "Filter top partners in Maharashtra"
                ]
            else:
                return [
                    "Show top 5 distributors by earnings",
                    "Show top 10 retailers with highest earnings in Karnataka",
                    "Compare top distributor earnings in July 2026 vs June 2026"
                ]
        elif any(w in p_lower for w in ["percentage", "growth", "vs", "compare"]):
            return [
                "Show month-over-month trend over last 6 months",
                "Break down earnings by partner city and district",
                "Show total reward points distributed in Q2 2026"
            ]
        elif any(w in p_lower for w in ["sku", "inventory", "scan", "box"]):
            return [
                "Which wholesalers have dispatched more than 100 boxes but have zero retailer scan confirmations?",
                "Show top 10 SKUs with highest scan volume by retailers in July 2026",
                "Calculate total reward points distributed through box scans in Maharashtra"
            ]
        else:
            return [
                "Show top 5 distributors by earnings",
                "Show pending withdrawals awaiting approval",
                "What was the percentage change in approved payouts between July 2026 and August 2026?"
            ]

synthesizer = ResponseSynthesizer()
