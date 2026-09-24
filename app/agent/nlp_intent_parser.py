import json
import logging
import re
from typing import Dict, Any, Optional

from app.llm.sql_generator import call_llm

logger = logging.getLogger(__name__)

class NLPIntentParser:
    """
    Agentic NLP Intent Parser.
    Extracts a fully structured, relationship-aware execution plan from natural language 
    before ANY SQL generation happens. Replaces legacy regex keyword parsing.
    """

    def _build_extraction_prompt(self, question: str, previous_context: Optional[Dict[str, Any]]) -> str:
        ctx_str = json.dumps(previous_context, indent=2) if previous_context else "None"
        return f"""You are an expert Business Analytics Intent Parser for the JGH Database.
Your task is to analyze the user's question and extract the complete business requirement into a strict JSON object.
DO NOT generate SQL. Only output the JSON.

Rules:
1. Extract the primary intent (e.g., LIST_RELATED_ENTITIES_WITH_METRIC, AGGREGATE, LOOKUP).
2. Identify entities, specific IDs, metrics, grouping, limits, and time boundaries.
3. If a relationship is mentioned (e.g., "retailers linked to distributor 5997"), capture the source entity, target entity, and the relationship logic.
4. For relative dates (e.g., "this month"), set the temporal label clearly (e.g., "current month"). Do not assume a month if not specified.
5. If information is missing that is strictly required, flag it in "missing_information".
6. Inherit context ONLY if the question is an explicit follow-up (using pronouns or modifiers).

Previous Context:
{ctx_str}

User Question:
"{question}"

Output EXACTLY this JSON structure:
{{
  "intent": "string",
  "entities": ["string"],
  "primary_entity": "string",
  "relationships": ["string"],
  "filters": {{"status": "string", "region": "string", "other": []}},
  "specific_id": {{"value": "string", "type": "string"}},
  "metrics": ["string"],
  "aggregation": ["string"],
  "grouping": ["string"],
  "sorting": ["string"],
  "limit": "integer or null",
  "date_boundaries": {{"label": "string", "start": "string", "end": "string"}},
  "missing_information": ["string"],
  "is_follow_up": true/false
}}
"""

    def parse_intent(self, question: str, previous_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from app.agent.nlp_understanding import nlp_agent
            req = nlp_agent.parse_question(question, context=previous_context)
            return {
                "intent": req.intent,
                "entities": req.entities or [],
                "primary_entity": req.entities[0] if req.entities else None,
                "relationships": req.relationships or [],
                "filters": req.filters or {},
                "specific_id": req.specific_ids or {},
                "metrics": req.metrics or [],
                "aggregation": req.aggregation or [],
                "grouping": req.grouping or [],
                "sorting": req.sorting or [],
                "limit": req.limit,
                "date_boundaries": {"label": req.date_period} if req.date_period else {},
                "missing_information": [req.clarification_reason] if req.clarification_required else [],
                "is_follow_up": bool(previous_context and any(w in question.lower() for w in ["what about", "how about", "and"]))
            }
        except Exception as e:
            logger.warning(f"Fast intent parsing fallback: {e}")
            return self._fallback_plan(question)

    def _fallback_plan(self, question: str) -> Dict[str, Any]:
        """Failsafe plan if LLM extraction fails."""
        return {
            "intent": "UNKNOWN",
            "entities": [],
            "primary_entity": None,
            "relationships": [],
            "filters": {},
            "specific_id": {},
            "metrics": [],
            "aggregation": [],
            "grouping": [],
            "sorting": [],
            "limit": None,
            "date_boundaries": {},
            "missing_information": ["Failed to parse intent structure"],
            "is_follow_up": False
        }

nlp_intent_parser = NLPIntentParser()
