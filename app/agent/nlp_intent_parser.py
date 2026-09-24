import json
import logging
import re
from typing import Dict, Any, Optional

from app.llm.sql_generator import generate_sql

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
        prompt = self._build_extraction_prompt(question, previous_context)
        try:
            # We use temperature 0 for deterministic JSON extraction
            response = generate_sql(prompt, temperature=0.0)
            
            # Extract JSON block
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                parsed = json.loads(json_match.group(0))
                return parsed
            else:
                logger.error("Failed to extract JSON from LLM response.")
                return self._fallback_plan(question)
        except Exception as e:
            logger.error(f"NLP parsing failed: {e}")
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
