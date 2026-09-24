"""
Requirement-Grounded Summary Generator for JGH Intelligence Engine.
Provides factual, direct business answers strictly derived from verified MySQL database results.
Does NOT invent generic marketing templates, top contributors, or partner records.
"""

from typing import List, Dict, Any, Optional

def _fmt_curr(val: float) -> str:
    """Formats float into Indian rupee currency string."""
    try:
        return f"₹{val:,.2f}".replace(".00", "")
    except Exception:
        return f"₹{val}"

def generate_natural_summary(
    question: str,
    sql_query: str,
    columns: List[str],
    data: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
    plan: Optional[Any] = None
) -> str:
    """
    Generates a clear natural language summary grounded strictly on verified database data.
    Delegates to the LLM ResponseGenerator or formats exact verified values directly.
    """
    if not data:
        return f"No qualifying records were found in the database for: \"{question}\"."

    # Attempt model-driven generation via ResponseGenerator if plan is available
    if plan is not None:
        try:
            from app.agent.response_generator import response_generator
            exec_res = {"success": True, "columns": columns, "data": data, "row_count": len(data)}
            resp = response_generator.generate_response(plan, exec_res)
            if resp:
                return resp
        except Exception:
            pass

    row_count = len(data)

    # Clean factual fallback formatting
    if row_count == 1:
        first_row = data[0]
        items = []
        for k, v in first_row.items():
            label = k.replace("_", " ").title()
            if isinstance(v, (int, float)):
                if "amount" in k.lower() or "earnings" in k.lower() or "balance" in k.lower():
                    items.append(f"**{label}**: **{_fmt_curr(float(v))}**")
                else:
                    items.append(f"**{label}**: **{v:,}**" if isinstance(v, int) else f"**{label}**: **{v}**")
            elif v is not None:
                items.append(f"**{label}**: **{v}**")
        return f"Verified Database Result for *\"{question}\"*:\n\n• " + "\n• ".join(items)

    return f"Returned **{row_count:,} qualifying records** matching your search criteria."
