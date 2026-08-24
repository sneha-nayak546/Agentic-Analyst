"""
Clarification Fallback Engine for JGH Intelligence Engine.
Inspects incoming user prompts for unrecognized business terms or ambiguous concepts.
Returns structured clarification prompts listing suggested valid metrics.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.query_logger import query_logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

class PlanValidator:
    def __init__(self):
        self.dict_path = KNOWLEDGE_DIR / "business_dictionary.json"
        self._load_dictionary()

    def _load_dictionary(self):
        self.valid_metrics = [
            "Gross Earnings", "Wallet Balance", "Box Scans",
            "Retailer Scans", "Wholesaler Dispatches", "Withdrawal Requests",
            "Referral Earnings", "Topup Credits"
        ]

    def check_concept_clarification(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Inspects prompt for unrecognized metrics or extreme ambiguities.
        If clarification is needed, logs the query and returns a clarification payload.
        """
        p_lower = prompt.lower()

        # Unmapped metrics detection (e.g. "bitcoin balance", "crypto earnings", "inventory temperature")
        unmapped_terms = ["bitcoin", "crypto", "temperature", "stock price", "employee salary"]
        for term in unmapped_terms:
            if term in p_lower:
                reason = f"Unmapped metric '{term}' referenced in prompt."
                query_logger.log_unmapped_query(prompt, reason, mode="CLARIFICATION")

                clarification_msg = (
                    f"### 🤔 Clarification Required\n\n"
                    f"I couldn't find a direct mapping for **\"{term}\"** in our enterprise database.\n\n"
                    f"💡 **Suggested Valid Enterprise Metrics**:\n"
                    f"- 💰 **Gross Earnings**: Total points/cash credited to mechanics (`wallet_transaction`)\n"
                    f"- 💳 **Wallet Balance**: Current active profile balance (`users.wallet_balance`)\n"
                    f"- 📦 **Box Scans**: Retailer and mechanic QR scans (`sku_inventories`)\n"
                    f"- 🔄 **Payout Withdrawals**: Cash redemptions (`withdrawal_request`)\n\n"
                    f"Please rephrase your question using one of the valid metrics above!"
                )

                return {
                    "status": "CLARIFICATION_REQUIRED",
                    "mode": "CLARIFICATION",
                    "question": prompt,
                    "response": clarification_msg,
                    "suggested_metrics": self.valid_metrics,
                    "sql_executed": False
                }

        return None

plan_validator = PlanValidator()
