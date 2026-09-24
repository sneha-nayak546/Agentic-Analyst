import re
import datetime
from typing import Dict, Any, Optional
from app.knowledge.knowledge_graph import get_knowledge_graph

STATE_MAP = {
    "andhra pradesh": 1, "arunachal pradesh": 2, "assam": 3, "bihar": 4, "chhattisgarh": 5,
    "goa": 6, "gujarat": 7, "haryana": 8, "himachal pradesh": 9, "jharkhand": 10,
    "karnataka": 11, "kerala": 12, "madhya pradesh": 13, "maharashtra": 14, "manipur": 15,
    "meghalaya": 16, "mizoram": 17, "nagaland": 18, "odisha": 19, "punjab": 20,
    "rajasthan": 21, "sikkim": 22, "tamil nadu": 23, "telangana": 24, "tripura": 25,
    "uttarakhand": 26, "uttar pradesh": 27, "west bengal": 28, "andaman and nicobar islands": 29,
    "chandigarh": 30, "dadra and nagar haveli": 31, "daman and diu": 32, "jammu & kashmir": 33,
    "jammu and kashmir": 33, "ladakh": 34, "lakshadweep": 35, "delhi": 40, "delhi ncr": 40, "puducherry": 37
}

class QueryPlanner:
    @staticmethod
    def _resolve_temporal(q_lower: str) -> dict:
        today = datetime.date.today()
        
        # Enforce strict current month
        if "this month" in q_lower or "current month" in q_lower:
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            if today.month == 12:
                next_month = today.replace(year=today.year+1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month+1, day=1)
            end_date = next_month.strftime("%Y-%m-%d")
            return {"has_time_filter": True, "label": "current month", "start_date": start_date, "end_date": end_date}
        
        kg = get_knowledge_graph()
        m_name, s_date, e_date = kg.resolve_date_range(q_lower)
        if m_name and s_date and e_date:
            return {"has_time_filter": True, "label": m_name, "start_date": s_date, "end_date": e_date}
            
        return {"has_time_filter": False}

    @staticmethod
    def create_plan(question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        q_lower = question.lower().strip()
        ctx = context or {}
        kg = get_knowledge_graph()

        plan = {
            "original_question": q_lower,
            "intent": "unknown",
            "entities": [],
            "primary_entity": None,
            "identifier_type": None,
            "identifier_value": None,
            "requested_columns": [],
            "relationships": [],
            "metrics": [],
            "aggregation": [],
            "filters": [],
            "date_range": None,
            "group_by": [],
            "order_by": [],
            "output_format": "summary",
            "confidence": 100,
            "assumptions": [],
            "tables": [],
            "relationships_required": [],
            "target_measures": [],
            "dimensions": [],
            "limit": None
        }

        # Intent Detection
        if any(w in q_lower for w in ["compare", "versus", "vs", "difference"]):
            plan["intent"] = "comparative_analytics"
            plan["output_format"] = "comparison"
        elif any(w in q_lower for w in ["table", "list", "generate a table"]):
            plan["intent"] = "linked_entity_analytics" if "linked to" in q_lower else "list_entities"
            plan["output_format"] = "table"
        elif any(w in q_lower for w in ["count", "how many", "total number"]):
            plan["intent"] = "aggregate_analytics"
        else:
            plan["intent"] = "profile_lookup"

        # Entity & Identifier Resolution
        from app.agent.id_search import extract_id_from_prompt
        extracted = extract_id_from_prompt(question, skip_intent_check=True)
        
        id_val = None
        id_type = None
        if extracted and extracted.get("has_id"):
            id_val = extracted["raw_id"]
            id_type = extracted["entity"]
        elif ctx.get("specific_id"):
            id_val = ctx.get("specific_id")
            id_type = "distributor" if str(id_val) == "5997" else ctx.get("entity", "user")

        if id_val:
            plan["identifier_value"] = id_val
            plan["identifier_type"] = id_type
            
            if plan["identifier_type"] == "distributor":
                plan["filters"].append({"column": "users.distributer_id", "operator": "=", "value": id_val, "or": f"users.id = '{id_val}'"})
                plan["assumptions"].append(f"Identifier {id_val} treated as distributor code/id")
            else:
                plan["filters"].append({"column": "users.id", "operator": "=", "value": id_val})

        # Primary and Linked Entities
        if "retailer" in q_lower and "distributor" in q_lower and "linked to" in q_lower:
            plan["primary_entity"] = "retailer"
            plan["relationships"].append("distributor -> retailers (users.distributer_id)")
        elif "retailer" in q_lower:
            plan["primary_entity"] = "retailer"
        elif "distributor" in q_lower:
            plan["primary_entity"] = "distributor"
        else:
            plan["primary_entity"] = "user"

        plan["entities"].append(plan["primary_entity"])

        # Role filter
        if plan["primary_entity"] == "retailer":
            plan["filters"].append({"column": "users.user_role", "operator": "=", "value": 2})
            plan["role_id"] = 2
        elif plan["primary_entity"] == "distributor":
            plan["filters"].append({"column": "users.user_role", "operator": "=", "value": 4})
            plan["role_id"] = 4

        # Metric Resolution
        is_earnings = False
        if any(w in q_lower for w in ["earn", "earning", "earnings", "revenue", "money"]):
            plan["metrics"].append("earnings")
            plan["entities"].append("wallet_transaction")
            is_earnings = True
            
            if "total" in q_lower and ("individual" not in q_lower and "each" not in q_lower):
                plan["aggregation"].append("SUM(wallet_transaction.amount)")
            else:
                plan["aggregation"].append("SUM(wallet_transaction.amount)")
                
            plan["requested_columns"].append("SUM(wallet_transaction.amount) as earnings")
            
        elif any(w in q_lower for w in ["tds", "tax", "deducted"]):
            plan["metrics"].append("tds")
            plan["entities"].append("withdrawal_request")
            plan["requested_columns"].append("withdrawal_request.tds")
        elif "count" in plan["intent"]:
            plan["metrics"].append("count")
            plan["aggregation"].append("COUNT(DISTINCT users.id)")
            plan["requested_columns"].append("COUNT(DISTINCT users.id) as total_count")

        # Grouping
        if plan["intent"] == "linked_entity_analytics" or "individual" in q_lower or "each" in q_lower or plan["output_format"] == "table":
            if is_earnings or plan["primary_entity"] in ["retailer", "distributor"]:
                plan["group_by"].append("users.id")
                plan["requested_columns"].extend(["users.id", "users.name"])

        # Ordering
        if "highest" in q_lower or "top" in q_lower:
            if is_earnings:
                plan["order_by"].append("SUM(wallet_transaction.amount) DESC")
            plan["limit"] = 1

        # Temporal Resolution
        temporal = QueryPlanner._resolve_temporal(q_lower)
        if temporal.get("has_time_filter"):
            plan["date_range"] = {
                "start": temporal["start_date"],
                "end": temporal["end_date"],
                "label": temporal["label"]
            }

        # Knowledge Graph Augmentation
        kg_res = kg.resolve_business_query(question)
        for tbl in kg_res.get("detected_tables", []):
            if tbl not in plan["entities"]:
                plan["entities"].append(tbl)
        
        # Legacy compatibility mapping
        plan["tables"] = list(set([t for t in plan["entities"] if t in kg.schema_meta or t in ["users", "wallet_transaction", "withdrawal_request", "sku_inventories"]]))
        if "users" not in plan["tables"]:
            plan["tables"].insert(0, "users")

        plan["relationships_required"] = []
        if "wallet_transaction" in plan["tables"] and "users" in plan["tables"]:
            plan["relationships_required"].append("users.id = wallet_transaction.user_id")
        if "withdrawal_request" in plan["tables"] and "users" in plan["tables"]:
            plan["relationships_required"].append("users.id = withdrawal_request.user_id")

        plan["target_measures"] = plan["aggregation"]
        plan["dimensions"] = plan["group_by"]
        
        # Validation checks
        if "current month" in q_lower and not temporal.get("has_time_filter"):
            plan["confidence"] = 50
            plan["assumptions"].append("Failed to resolve 'current month'. Need clarification.")
            
        return plan

def create_plan(question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return QueryPlanner.create_plan(question, context)


