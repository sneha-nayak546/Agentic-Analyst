"""
Value Linker for JGH Intelligence Engine.
Distinguishes between:
  concept, entity, database value, date, status, ID, metric.
Maps natural language values to verified database column values and constants.
"""

import re
from typing import Dict, Any, Optional, List

# Verified Geography IDs
STATE_NAME_TO_ID = {
    "karnataka": 11,
    "kerala": 12,
    "tamil nadu": 13,
    "maharashtra": 14,
    "delhi": 15,
    "punjab": 16,
    "haryana": 17,
    "andhra pradesh": 18,
    "telangana": 19,
    "gujarat": 20,
    "rajasthan": 21,
    "uttar pradesh": 22
}

CITY_TO_STATE = {
    "bengaluru": ("Karnataka", 11),
    "bangalore": ("Karnataka", 11),
    "mysuru": ("Karnataka", 11),
    "hubli": ("Karnataka", 11),
    "kochi": ("Kerala", 12),
    "ernakulam": ("Kerala", 12),
    "pune": ("Maharashtra", 14),
    "mumbai": ("Maharashtra", 14),
    "delhi": ("Delhi", 15)
}

# Verified User Roles
ROLE_NAME_TO_ID = {
    "retailer": 2,
    "retailers": 2,
    "mechanic": 3,
    "mechanics": 3,
    "distributor": 4,
    "distributors": 4,
    "wholesaler": 5,
    "wholesalers": 5,
    "company": 1,
    "admin": 1
}

# Verified Transaction Types in wallet_transaction
TRANSACTION_TYPES = {
    "earnings": 1,      # Credit / Scan Earning
    "earning": 1,
    "credit": 1,
    "topup": 1,
    "topups": 1,
    "debit": 2,         # Debit / Withdrawal
    "withdrawal": 2,
    "redemption": 2
}

class ValueLinker:
    def link_values(self, question: str, entities: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extracts and links real database values from question text.
        Returns a dictionary of resolved database bindings.
        """
        q_lower = question.lower()
        linked = {
            "resolved_filters": [],
            "exact_ids": {},
            "state_id": None,
            "role_id": None,
            "transaction_type": None,
            "date_range": None
        }

        # 1. Exact ID Extraction (e.g. "distributor 5997", "id 12345", "user 50225")
        id_matches = re.findall(r"\b(distributor|retailer|user|company|id)\s*#?\s*(\d{3,10})\b", q_lower)
        for ent, val in id_matches:
            val_int = int(val)
            if ent in ["distributor", "distributer"]:
                linked["exact_ids"]["distributor_id"] = val_int
                linked["resolved_filters"].append({"column": "distributor_id", "operator": "=", "value": val_int})
            elif ent in ["retailer", "user", "id"]:
                linked["exact_ids"]["user_id"] = val_int
                linked["resolved_filters"].append({"column": "id", "operator": "=", "value": val_int})

        # 2. State & City Mapping
        for city, (st_name, st_id) in CITY_TO_STATE.items():
            if re.search(rf"\b{re.escape(city)}\b", q_lower):
                linked["city"] = city.title()
                linked["state_id"] = st_id
                linked["state_name"] = st_name
                linked["resolved_filters"].append({"column": "city", "operator": "=", "value": city.title()})
                break

        if not linked.get("state_id"):
            for st_name, st_id in STATE_NAME_TO_ID.items():
                if re.search(rf"\b{re.escape(st_name)}\b", q_lower):
                    linked["state_id"] = st_id
                    linked["state_name"] = st_name.title()
                    linked["resolved_filters"].append({"column": "state_id", "operator": "=", "value": st_id})
                    break

        # 3. Role Mapping
        for role_kw, role_num in ROLE_NAME_TO_ID.items():
            if re.search(rf"\b{re.escape(role_kw)}\b", q_lower):
                linked["role_id"] = role_num
                linked["resolved_filters"].append({"column": "user_role", "operator": "=", "value": role_num})
                break

        # 4. Transaction Type Mapping
        for tx_kw, tx_type in TRANSACTION_TYPES.items():
            if re.search(rf"\b{re.escape(tx_kw)}\b", q_lower):
                linked["transaction_type"] = tx_type
                linked["resolved_filters"].append({"column": "transaction_type", "operator": "=", "value": tx_type})
                break

        # 5. Verified Date Ranges (e.g. July 2026, June 2026, etc.)
        from app.utils.date_parser import parse_temporal_expressions
        temp = parse_temporal_expressions(question)
        if temp and temp.get("start_date") and temp.get("end_date"):
            linked["date_range"] = {
                "start": temp["start_date"],
                "end": temp["end_date"],
                "condition": temp.get("sql_condition", "")
            }

        return linked

value_linker = ValueLinker()
