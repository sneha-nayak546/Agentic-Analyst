import re
from typing import List, Dict, Any

def generate_natural_summary(question: str, sql_query: str, columns: List[str], data: List[Dict[str, Any]]) -> str:
    """
    Generates a concise natural language summary of SQL query execution results.
    """
    if not data:
        return f"No records found for query: '{question}'."

    row_count = len(data)

    # Detect key metric fields
    numeric_cols = []
    currency_cols = []
    date_cols = []

    for col in columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ["amount", "balance", "price", "total", "cost", "revenue", "paid", "fee"]):
            currency_cols.append(col)
        elif any(keyword in col_lower for keyword in ["count", "quantity", "num", "number", "qty", "items"]):
            numeric_cols.append(col)
        elif any(keyword in col_lower for keyword in ["date", "time", "created", "updated", "month", "year"]):
            date_cols.append(col)

    # Check aggregate calculations
    total_amount = 0.0
    has_amount = False

    if currency_cols:
        primary_curr_col = currency_cols[0]
        try:
            total_amount = sum(float(row[primary_curr_col] or 0) for row in data if row.get(primary_curr_col) is not None)
            has_amount = True
        except (ValueError, TypeError):
            has_amount = False

    # Extract time context from question
    time_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}', question, re.IGNORECASE)
    time_str = f" in {time_match.group(0).title()}" if time_match else ""

    if has_amount and total_amount > 0:
        formatted_amount = f"₹{total_amount:,.2f}".replace(".00", "")
        return f"There were {row_count} transaction{'s' if row_count != 1 else ''}{time_str} with a total amount of {formatted_amount}."

    if row_count == 1:
        first_row = data[0]
        summary_parts = []
        for k, v in list(first_row.items())[:3]:
            if v is not None:
                summary_parts.append(f"{k.replace('_', ' ').title()}: {v}")
        if summary_parts:
            return f"Found 1 record matching your query ({', '.join(summary_parts)})."
        return f"Found 1 matching record{time_str}."

    return f"Retrieved {row_count} record{'s' if row_count != 1 else ''}{time_str}."
