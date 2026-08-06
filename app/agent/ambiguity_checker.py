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

def check_ambiguity(question: str) -> Optional[Dict[str, Any]]:
    """
    Checks if a user question is ambiguous, underspecified, or requires database value clarification.
    Returns follow-up clarification details listing exact DB options if ambiguous, else None.
    """
    if not question or not question.strip():
        return None

    q_clean = question.strip().lower()
    words = [w for w in q_clean.split() if len(w) > 2]

    # Database-Driven Ambiguity Check against discovered Enum & Distinct Values
    metadata = load_db_enum_metadata()
    enum_values = metadata.get("enum_values", {})
    business_terms = metadata.get("business_terminology", {})
    
    # Collect all valid DB terms
    all_db_terms = set()
    for term in business_terms:
        all_db_terms.add(term.lower())
    for col, vals in enum_values.items():
        for v in vals:
            all_db_terms.add(str(v).lower())
            
    # Check for partial matches that might need clarification
    for w in words:
        if w in ["transaction", "transactions", "report", "reports", "user", "users", "show", "list", "get", "all"]:
            continue
            
        if w not in all_db_terms:
            # Check if it's a partial match for any DB term
            partial_matches = [t for t in all_db_terms if w in t]
            # Exclude very short matches
            partial_matches = [t for t in partial_matches if len(t) > 3 and abs(len(t) - len(w)) < 10]
            
            if partial_matches and len(partial_matches) > 1:
                # E.g., user said "scan" but DB has "scan_reward"
                options = [f"Did you mean '{pm}'?" for pm in partial_matches[:4]]
                return {
                    "is_ambiguous": True,
                    "clarification": f"I found multiple database values matching '{w}'. Please clarify:",
                    "options": options
                }

    # Single-word vague inputs
    if len(words) <= 2 and any(w in ["transaction", "transactions", "report", "reports", "user", "users"] for w in words):
        return {
            "is_ambiguous": True,
            "clarification": f"Your prompt '{question.strip()}' is underspecified. Please clarify your request or select an option:",
            "options": [
                "Today's Transactions",
                "Last 7 days Transactions",
                "Last 30 days Transactions",
                "Show Wallet Transactions",
                "Show Withdrawal Requests"
            ]
        }

    return None
