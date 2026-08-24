"""
Intent Router Module for JGH AI Collaborator.
Classifies user prompts into 1 of 5 operational modes:
  1. TUTOR_QA        - Database Tutor & Onboarding Coach ("teach me", "explain", "what is", "tell me about")
  2. ERD_GEN         - Visual ER Diagram & Architecture Generator ("ER diagram", "draw architecture")
  3. DASHBOARD_GEN   - Dynamic Dashboard Spec Builder ("build dashboard", "analytics panel")
  4. BUSINESS_STORY  - Executive Business Storyteller ("what happened this month", "simple words")
  5. SQL_ANALYTICS   - Tested v2.0 Text-to-SQL Execution Pipeline (Default data queries)
"""

import re
from typing import Dict, Any

class IntentRouter:
    @staticmethod
    def classify(prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            return "SQL_ANALYTICS"

        p_lower = prompt.lower().strip()

        # 0. Conversational Greetings, Help & Courtesies
        greeting_patterns = [
            r"^(hi|hii|hiii|hello|hey|heyy|howdy|hola|namaste|greetings|good\s+(?:morning|afternoon|evening|day))[\s!.,?]*$",
            r"^(what\s+can\s+you\s+do|who\s+are\s+you|help|how\s+to\s+use|what\s+can\s+i\s+ask|capabilities)[\s!.,?]*$",
            r"^(thanks|thank\s+you|ok|okay|cool|great|awesome|bye|goodbye)[\s!.,?]*$"
        ]
        if any(re.search(pat, p_lower) for pat in greeting_patterns):
            return "GREETING"

        # 1. ERD & Visual Architecture Generator
        erd_patterns = [
            r"\berd\b", r"\ber diagram\b", r"\bschema visual\b", r"\btable relationships?\b",
            r"\bdraw architecture\b", r"\brelationship graph\b", r"\bdiagram for\b", r"\bvisualize schema\b"
        ]
        if any(re.search(pat, p_lower) for pat in erd_patterns):
            return "ERD_GEN"

        # 2. Dynamic Dashboard Spec Builder
        dashboard_patterns = [
            r"\bbuild dashboard\b", r"\bcreate dashboard\b", r"\bdashboard for\b",
            r"\banalytics panel\b", r"\bdashboard spec\b", r"\bvisual dashboard\b", r"\bmetrics panel\b"
        ]
        if any(re.search(pat, p_lower) for pat in dashboard_patterns):
            return "DASHBOARD_GEN"

        # 3. Executive Business Storyteller
        story_patterns = [
            r"\bwhat happened this month\b", r"\bin simple words\b", r"\bbusiness trends\b",
            r"\bexecutive summary\b", r"\bmonthly story\b", r"\bperformance breakdown\b",
            r"\bsummary in simple words\b", r"\btell a story\b", r"\bexecutive story\b",
            r"\bstory of\b"
        ]
        if any(re.search(pat, p_lower) for pat in story_patterns):
            return "BUSINESS_STORY"

        # 4. Database Tutor & Onboarding Coach
        # Guard: If query is asking for data/numbers/entities/metrics or follow-up references, keep as SQL
        is_data_query = bool(re.search(
            r"\b(top\s*\d+|highest|lowest|sum|count|total\s+amount|how\s+many|show\s+me\s+top|list\s+all|"
            r"earning|earnings|earned|revenue|sales|balance|wallet|withdraw|withdrawal|withdrawals|payout|"
            r"distributor|distributors|retailer|retailers|wholesaler|wholesalers|mechanic|mechanics|"
            r"company|companies|inventory|sku|transaction|transactions|box|boxes|"
            r"their|them|these|those|which\s+one|who\s+has|who\s+earned|how\s+much|approved|pending|status|\bid\b|\b\d{4,6}\b)\b",
            p_lower
        ))
        
        tutor_patterns = [
            r"\bteach me\b", r"\bexplain\s+to\s+me\b", r"\bexplain\s+how\b", r"\bexplain\s+about\b",
            r"\bhow does\s+\w+\s+work\b", r"\bhow do\s+\w+\s+work\b", r"\btell me about\s+(?:the\s+)?(?:system|database|schema|architecture|table|roles)\b",
            r"\bhow are roles\b", r"\bexplain the schema\b", r"\bwhat do roles mean\b", r"\bhow do roles work\b",
            r"\bexplain difference between\b", r"\bwhat is the difference\b", r"\bmeaning of\b",
            r"\bguide on\b", r"\boverview of the database\b", r"\bwhat does\s+\w+\s+mean\b",
            r"^(?:what is|what are)\s+(?:a\s+|an\s+|the\s+)?(?:role|user_role|distributor|retailer|wholesaler|mechanic|tds|wallet_balance|sku_inventories|database|schema)[\s?]*$"
        ]
        if any(re.search(pat, p_lower) for pat in tutor_patterns) and not is_data_query:
            return "TUTOR_QA"

        # 5. Default: Tested v2.0 SQL Analytics Pipeline
        return "SQL_ANALYTICS"

def route_intent(prompt: str) -> str:
    return IntentRouter.classify(prompt)
