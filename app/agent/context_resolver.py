"""
Context Resolver for JGH Intelligence Engine.
Implements structured conversational context extraction, inheritance, replacement,
correction, and reset:
  Final Context = (Previous Context - Explicitly Overridden Fields) + New Information
Ensures filters (e.g. region, month, ID, role) are ONLY inherited when the user
asks a contextual follow-up or modifier.
"""

import re
from typing import Dict, Any, Optional
from app.utils.date_parser import parse_temporal_expressions, MONTH_NAME_TO_NUM, MONTH_NUM_TO_NAME, DEFAULT_YEAR

# Known Geographies (States, Cities, Districts)
KNOWN_REGIONS = [
    "karnataka", "kerala", "tamil nadu", "maharashtra", "delhi", "delhi ncr",
    "lucknow", "bangalore", "bengaluru", "mumbai", "pune", "una", "karnal",
    "nagpur", "amravati", "sangli", "nashik", "kannur", "punjab", "haryana", "jharkhand",
    "andhra pradesh", "telangana", "gujarat", "rajasthan", "uttar pradesh"
]

# Reset trigger phrases
RESET_PATTERNS = [
    r"\b(?:start\s+a\s+new\s+analysis|new\s+analysis)\b",
    r"\b(?:ignore\s+previous\s+context|ignore\s+context)\b",
    r"\b(?:new\s+query|new\s+chat|start\s+fresh|fresh\s+session)\b",
    r"\b(?:reset\s+conversation|reset\s+context|clear\s+context|clear\s+memory)\b"
]

# Anaphoric / Follow-up References that indicate the user wants to continue the previous entity/context
FOLLOW_UP_PATTERNS = [
    r"\b(?:in\s+that\s+region|in\s+that\s+state|in\s+that\s+city|in\s+the\s+same\s+region)\b",
    r"\b(?:(?:in|from|over|around)\s+there)\b",
    r"^(?:what\s+about|show\s+me|compare|how\s+about|and|also)\s+(?:their|them|these|those)\b",
    r"\b(?:among\s+them|of\s+them)\b",
    r"\b(?:what\s+about\s+their|show\s+their|compare\s+their|how\s+about\s+their|what\s+are\s+their|tell\s+me\s+their)\b",
    r"\b(?:and\s+their|with\s+their|also\s+for\s+them)\b",
    r"\b(?:that\s+person|that\s+single\s+person|that\s+user|that\s+retailer|that\s+distributor)\b",
    r"\b(?:who\s+is\s+(?:the|that)\s+one\s+person|single\s+person\s+details|that\s+single\s+person\s+details)\b",
    r"\b(?:the\s+one\s+person|the\s+single\s+person|top\s+1|first\s+one|the\s+top\s+one|the\s+highest\s+one)\b",
    # Superlatives / ranking on previous result
    r"\b(?:which\s+one|which\s+one\s+is|which\s+one\s+has|who\s+has\s+the\s+highest|who\s+earned\s+the\s+most|who\s+is\s+(?:the\s+)?highest|highest\s+among\s+them|which\s+of\s+them)\b",
    # Elliptical / modifier questions
    r"^(?:what\s+about|how\s+about|and\s+in|and\s+for|what\s+of)\s+(?:january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec|q[1-4]|today|yesterday|last\s+month|this\s+month|\d{4})",
    r"^(?:what\s+about|how\s+about|and\s+in)\s+(?:karnataka|kerala|tamil\s+nadu|maharashtra|delhi|lucknow|pune|mumbai|bangalore)",
    r"\b(?:how\s+many\s+were\s+approved|how\s+many\s+were\s+pending|how\s+many\s+were\s+rejected|how\s+many\s+were\s+paid|how\s+many\s+are\s+approved|how\s+many\s+are\s+pending|how\s+many\s+are\s+active)\b",
    r"\b(?:approved\s+ones|pending\s+ones|rejected\s+ones|only\s+approved|only\s+pending)\b"
]

class ContextResolver:
    def is_reset_command(self, prompt: str) -> bool:
        """Checks if the user prompt is an explicit context reset command."""
        p_lower = prompt.lower().strip()
        for pattern in RESET_PATTERNS:
            if re.search(pattern, p_lower):
                return True
        return False

    def classify_context(self, prompt: str, previous_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Classifies turn into:
          NEW_QUERY, FOLLOW_UP, REFINEMENT, CORRECTION, MULTI_PART, CLARIFICATION
        """
        p_lower = prompt.lower().strip()
        if self.is_reset_command(prompt):
            return "NEW_QUERY"

        from app.agent.query_decomposer import decompose_query
        parts = decompose_query(prompt)
        if len(parts) > 1:
            return "MULTI_PART"

        # Check for correction
        if any(re.search(pat, p_lower) for pat in [r"\b(?:no\b|sorry\b|actually\b|i meant\b|not that\b|change to\b)"]):
            return "CORRECTION"

        if not previous_context:
            return "NEW_QUERY"

        # Check for follow-up or refinement
        if self.is_explicit_follow_up(prompt, previous_context=previous_context):
            if any(re.search(pat, p_lower) for pat in [r"\bonly\b", r"\bfilter by\b", r"\bjust the\b", r"\blimit to\b"]):
                return "REFINEMENT"
            return "FOLLOW_UP"

        return "NEW_QUERY"

    def is_explicit_follow_up(self, prompt: str, previous_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determines whether the prompt is a contextual follow-up to previous conversation:
          - Contains anaphoric pronoun/reference ("their", "them", "which one", "who has highest")
          - Is an elliptical / fragment modifier ("What about July?", "How many were approved?")
          - Missing standalone entity while previous context has an active entity
        """
        p_lower = prompt.lower().strip()

        # Check explicit follow-up regex patterns
        if any(re.search(pat, p_lower) for pat in FOLLOW_UP_PATTERNS):
            return True

        # Check elliptical phrases like "what about", "now filter by", "limit to"
        if re.search(r"^(?:what\s+about|how\s+about|now\s+filter|filter\s+by|limit\s+to|show\s+only|only\s+in|and\s+their|and\s+for)\b", p_lower):
            return True

        if not previous_context:
            return False

        has_prev_entity = bool(previous_context.get("entity") or previous_context.get("specific_id"))
        if not has_prev_entity:
            return False

        # If current prompt has NO explicit standalone entity mentioned, but has a modifier/question
        has_new_entity = any(w in p_lower for w in [
            "retailer", "retailers", "dealer", "dealers", "shop owner", "shop owners", "shopkeeper",
            "distributor", "distributors", "wholesaler", "wholesalers", "mechanic", "mechanics",
            "company", "companies", "withdrawal", "withdrawals", "payout", "payouts",
            "sku", "inventory", "inventories", "automatic transaction", "automatic_transaction"
        ])

        # If prompt starts with modifier phrases like "what about", "how about", "which", "how many", "and", "show"
        if not has_new_entity:
            if re.search(r"^(?:what\s+about|how\s+about|which\s+one|which|how\s+many|and\s+|also\s+|show\s+only|only\s+)\b", p_lower):
                return True
            if any(w in p_lower for w in ["highest earnings", "top earnings", "lowest earnings", "highest balance", "were approved", "were rejected", "were pending", "are active"]):
                return True

        return False

    def extract_attributes(self, prompt: str, inherited_year: Optional[int] = None) -> Dict[str, Any]:
        """Extracts structured entities, filters, metrics, status, and temporal metadata from a single prompt."""
        p_lower = prompt.lower().strip()
        extracted = {}

        # 1. Geographic Regions
        for loc in KNOWN_REGIONS:
            if re.search(rf"\b{re.escape(loc)}\b", p_lower):
                extracted["region"] = loc.title()
                break

        # 2. Roles & Entities
        if any(w in p_lower for w in ["retailer", "retailers", "retailor", "retailors", "dealer", "dealers", "shop owner", "shop owners", "shopkeeper"]):
            extracted["entity"] = "retailer"
            extracted["role_id"] = 2
        elif any(w in p_lower for w in ["distributor", "distributors", "distributer", "distributers", "distribtor", "distribtors"]):
            extracted["entity"] = "distributor"
            extracted["role_id"] = 4
        elif any(w in p_lower for w in ["wholesaler", "wholesalers"]):
            extracted["entity"] = "wholesaler"
            extracted["role_id"] = 5
        elif any(w in p_lower for w in ["mechanic", "mechanics"]):
            extracted["entity"] = "mechanic"
            extracted["role_id"] = 3
        elif any(w in p_lower for w in ["company", "companies"]):
            extracted["entity"] = "company"
        elif any(w in p_lower for w in ["withdrawal", "withdrawals", "payout", "payouts"]):
            extracted["entity"] = "withdrawal_request"
        elif any(w in p_lower for w in ["sku", "inventory", "inventories", "box scan", "boxes"]):
            extracted["entity"] = "sku_inventories"
        elif "automatic transaction" in p_lower or "automatic_transaction" in p_lower:
            extracted["entity"] = "automatic_transactions"
        elif any(w in p_lower for w in ["transaction", "transactions", "wallet"]):
            extracted["entity"] = "wallet_transaction"

        # 3. Business Metrics / Measures
        if any(w in p_lower for w in ["earning", "earnings", "earned", "revenue", "sales", "sales amount", "how much"]):
            extracted["metric"] = "earnings"
        elif any(w in p_lower for w in ["wallet balance", "current balance", "balance", "total balance"]):
            extracted["metric"] = "balance"
        elif any(w in p_lower for w in ["count", "total count", "number of", "how many"]):
            extracted["metric"] = "count"
        elif any(w in p_lower for w in ["scanned box", "scanned boxes", "boxes scanned", "scan count"]):
            extracted["metric"] = "scanned_boxes"
        elif any(w in p_lower for w in ["withdrawal", "withdrawals"]):
            extracted["metric"] = "withdrawals"

        # 4. Status Filter
        if any(w in p_lower for w in [
            "only active", "active ones", "active only", "active retailers", "active distributors",
            "active users", "status active", "are active"
        ]):
            extracted["status_filter"] = "active"
        elif any(w in p_lower for w in [
            "approved only", "only approved", "approved retailers", "approved distributors",
            "status approved", "were approved", "are approved", "approved ones", "how many approved"
        ]):
            extracted["status_filter"] = "approved"
        elif any(w in p_lower for w in [
            "pending only", "only pending", "pending status", "were pending", "are pending", "pending ones"
        ]):
            extracted["status_filter"] = "pending"
        elif any(w in p_lower for w in [
            "inactive", "blocked", "blacklisted", "were rejected", "are rejected", "rejected ones", "only rejected"
        ]):
            extracted["status_filter"] = "rejected" if "reject" in p_lower else "inactive"

        # 5. Temporal Period and Comparison
        temporal = parse_temporal_expressions(prompt, inherited_year=inherited_year)
        if temporal.get("has_time_filter"):
            extracted["period"] = temporal.get("label")
            extracted["month"] = temporal.get("month")
            extracted["year"] = temporal.get("year")
            extracted["time_condition"] = temporal.get("condition")
            extracted["start_date"] = temporal.get("start_date")
            extracted["end_date"] = temporal.get("end_date")

        if temporal.get("comparison"):
            extracted["comparison"] = temporal["comparison"]
            extracted["comparison_label"] = temporal["comparison"].get("compare_label")

        # 6. Limits and Ranking Quantifiers
        limit_m = re.search(r"\b(?:top|first|highest|lowest|limit)\s*(\d+)\b", p_lower)
        if limit_m:
            extracted["limit"] = int(limit_m.group(1))
        elif any(w in p_lower for w in [
            "which one has the highest", "which one is the highest", "who has the highest",
            "which one has highest", "which one", "who earned the most", "the top one", "top 1",
            "highest 1", "single person", "the one person", "that one person", "1 person",
            "single retailer", "single distributor", "single user", "that single person"
        ]):
            extracted["limit"] = 1

        # 7. Specific ID Extraction
        from app.agent.id_search import extract_id_from_prompt
        id_info = extract_id_from_prompt(prompt, skip_intent_check=True)
        if id_info:
            extracted["specific_id"] = id_info.get("raw_id")
            extracted["id_type"] = id_info.get("entity")
            if not extracted.get("entity") and id_info.get("entity") != "user":
                extracted["entity"] = id_info.get("entity")
                if extracted["entity"] == "distributor":
                    extracted["role_id"] = 4
                elif extracted["entity"] == "retailer":
                    extracted["role_id"] = 2
                elif extracted["entity"] == "wholesaler":
                    extracted["role_id"] = 5
                elif extracted["entity"] == "mechanic":
                    extracted["role_id"] = 3

        return extracted

    def resolve(self, current_prompt: str, previous_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Resolves prompt into a single clean structured context:
          - Explicit follow-up:
              Final Context = Previous Context merged with New Attributes
          - Standalone question:
              Final Context = ONLY New Attributes (previous context cleared)
        Never leaks old location, month, ID, or entity into a new question.
        """
        if self.is_reset_command(current_prompt):
            return {
                "is_reset": True,
                "understanding_summary": "Started a new fresh analysis session. Context reset.",
                "resolved_prompt": current_prompt
            }

        prev = (previous_context or {}).copy()
        is_follow_up = self.is_explicit_follow_up(current_prompt, previous_context=prev)

        inherited_year = prev.get("year", DEFAULT_YEAR) if is_follow_up else DEFAULT_YEAR
        new_attrs = self.extract_attributes(current_prompt, inherited_year=inherited_year)

        if is_follow_up:
            resolved = prev.copy()
            # Clear comparison unless re-requested
            for k in ["comparison", "comparison_label"]:
                resolved.pop(k, None)

            # If user provides a new entity, clear previous specific_id if it was for a different entity
            if new_attrs.get("entity") and new_attrs.get("entity") != prev.get("entity"):
                # Do not drop if the previous entity is a logical parent (like distributor/company) 
                # and the new entity is a child (like retailer/mechanic). This allows queries like 
                # "show their retailers" after querying a distributor ID.
                prev_ent = prev.get("entity", "")
                new_ent = new_attrs.get("entity", "")
                is_parent_child = prev_ent in ["distributor", "company", "wholesaler"] and new_ent in ["retailer", "mechanic", "user", "withdrawal_request", "wallet_transaction"]
                
                if not is_parent_child:
                    resolved.pop("specific_id", None)
                    resolved.pop("id_type", None)

            # If new query provides a new region or date, replace it
            for time_k in ["period", "month", "year", "time_condition", "start_date", "end_date"]:
                if time_k in new_attrs:
                    resolved[time_k] = new_attrs[time_k]

            for k, v in new_attrs.items():
                if v is not None:
                    resolved[k] = v
        else:
            # Standalone question: start fresh — do NOT inherit stale context
            resolved = {}
            for k, v in new_attrs.items():
                if v is not None:
                    resolved[k] = v

        resolved["is_explicit_follow_up"] = is_follow_up

        if resolved.get("region"):
            resolved["location"] = resolved["region"]
        if resolved.get("entity"):
            resolved["role"] = resolved["entity"]

        # Build clean understanding indicator for UI and summaries
        parts = []
        if resolved.get("specific_id"):
            parts.append(f"ID #{resolved['specific_id']}")
        if resolved.get("region"):
            parts.append(resolved["region"])
        if resolved.get("entity"):
            ent_name = resolved["entity"].capitalize()
            if not ent_name.endswith("s"):
                ent_name += "s"
            parts.append(ent_name)
        if resolved.get("status_filter"):
            parts.append(f"({resolved['status_filter'].capitalize()} status)")
        if resolved.get("metric"):
            parts.append(resolved["metric"].capitalize())
        if resolved.get("period"):
            parts.append(resolved["period"])
        if resolved.get("comparison_label"):
            parts.append(f"vs {resolved['comparison_label']}")
        if resolved.get("limit") and resolved.get("limit") != 500:
            parts.append(f"Top {resolved['limit']}")

        understanding_str = " • ".join(parts) if parts else "Enterprise Analytics"
        resolved["understanding_summary"] = understanding_str
        resolved["resolved_prompt"] = self.build_augmented_prompt(current_prompt, resolved)
        return resolved

    def build_augmented_prompt(self, original_prompt: str, ctx: Dict[str, Any]) -> str:
        """
        Builds a natural language prompt. For standalone queries, returns the original
        prompt to avoid injecting stale context. For follow-ups, enriches with inherited context.
        """
        if not ctx.get("is_explicit_follow_up"):
            return original_prompt

        clauses = []
        entity = ctx.get("entity", "users")
        region = ctx.get("region")
        metric = ctx.get("metric")
        status = ctx.get("status_filter")
        period = ctx.get("period")
        comparison = ctx.get("comparison_label")
        limit = ctx.get("limit")
        specific_id = ctx.get("specific_id") or ctx.get("distributor_id")

        if specific_id and entity == "retailer":
            clauses.append(f"retailers linked to distributor {specific_id}")
        elif specific_id:
            clauses.append(f"ID {specific_id}")

        if not (specific_id and entity == "retailer"):
            if region and entity:
                clauses.append(f"{region} {entity}s")
            elif entity:
                clauses.append(f"{entity}s")
            elif region:
                clauses.append(f"data in {region}")

        if metric:
            clauses.append(f"with {metric}")
        if period:
            clauses.append(f"for {period}")
        if comparison:
            clauses.append(f"compared with {comparison}")

        augmented = " ".join(clauses).strip()
        return augmented if augmented else original_prompt

context_resolver = ContextResolver()
