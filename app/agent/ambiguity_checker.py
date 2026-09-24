import os
import json
import re
from typing import Dict, Any, Optional

def load_db_enum_metadata() -> dict:
    meta_path = "knowledge/business_metadata.json"
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def check_ambiguity(question: str, active_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Checks if a user question is ambiguous or underspecified when no previous context exists.
    Returns follow-up clarification details listing exact options if ambiguous, else None.
    """
    if not question or not question.strip():
        return None

    q_clean = question.strip().lower()
    ctx = active_context or {}

    # If the user prompt is a reset or meta command, it's not ambiguous
    if any(k in q_clean for k in ["start a new analysis", "new query", "reset conversation", "ignore previous"]):
        return None

    # Check for Vague / Missing Entity queries like "Show August data.", "Show data for Jan", "Show July 2026 data"
    # only when no entity or metric is present in the question AND none in active context
    vague_data_patterns = [
        r"\b(?:show|get|list|fetch|give\s+me)\s+(?:data|records|info|details|report)?\s*(?:for|in|of)?\s*(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)(?:\s+(20\d{2}))?\s*(?:data|records|info)?\b",
        r"\b(?:show|get|list|fetch)\s+(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)(?:\s+(20\d{2}))?\s+data\b"
    ]

    # Section 4: Bare metric queries without breakdown or entity (e.g. "Show earnings", "earnings")
    bare_earnings_match = bool(re.match(r"^(?:show\s+|get\s+|fetch\s+|display\s+)?(?:the\s+)?earnings\s*[?.!]*$", q_clean))
    if bare_earnings_match and not ctx.get("entity") and not ctx.get("period"):
        return {
            "is_ambiguous": True,
            "clarification": "Do you want total earnings, earnings by retailer, or earnings by month?",
            "options": [
                "Total earnings",
                "Earnings by retailer",
                "Earnings by month"
            ]
        }

    # If query targets an explicit entity ID, it is a specific lookup, not ambiguous
    if re.search(r"\b(?:id\s*=?\s*\d+|#\d+|\b\d{3,}\b)", q_clean):
        return None

    has_entity_in_prompt = any(w in q_clean for w in [
        "user", "users", "distributor", "distributors", "retailer", "retailers", "dealer", "dealers",
        "wholesaler", "wholesalers", "mechanic", "mechanics", "company", "companies",
        "earning", "earnings", "transaction", "transactions", "wallet", "withdrawal",
        "sku", "inventory", "box", "boxes", "balance", "profile", "customer", "account"
    ])

    if not has_entity_in_prompt and not ctx.get("entity") and not ctx.get("metric"):
        if re.search(r"\b(?:show|give|get|display)\s+(?:me\s+)?(?:the\s+)?data\b", q_clean) or any(w in q_clean for w in ["what happened", "show metrics", "give me the details", "show info", "show data", "get data", "details", "show me data"]):
            return {
                "is_ambiguous": True,
                "clarification": f"Your query '{question.strip()}' does not specify which entity or metric you want to view. Please choose an area to analyze:",
                "options": [
                    "Retailers Performance",
                    "Distributors Overview",
                    "Wallet Transactions",
                    "SKU Inventories"
                ]
            }

        for pat in vague_data_patterns:
            m = re.search(pat, q_clean)
            if m:
                month_str = m.group(1).capitalize()
                year_str = m.group(2) or "2026"
                return {
                    "is_ambiguous": True,
                    "clarification": f"What specific business data would you like to see for {month_str} {year_str}?",
                    "options": [
                        f"{month_str} Distributors",
                        f"{month_str} Retailers",
                        f"Distributor Earnings for {month_str}",
                        f"Wallet Transactions in {month_str}"
                    ]
                }

    # Check for Ambiguous "one person" / "single person" without ID, name, or active context

    # Single-word vague inputs like "data", "report", "users" without context
    words = [w for w in q_clean.split() if len(w) > 2]
    if len(words) <= 1 and not ctx.get("entity") and not ctx.get("region"):
        if words and words[0] in ["data", "report", "transactions", "summary", "stats"]:
            return {
                "is_ambiguous": True,
                "clarification": f"Your query '{question.strip()}' is underspecified. Please choose an area to analyze:",
                "options": [
                    "Show Karnataka Distributors",
                    "Distributor Earnings for July 2026",
                    "Retailers Performance",
                    "Recent Wallet Transactions"
                ]
            }

    return None
