import json
import logging
import re
import os
from typing import Dict, Any, List
from openai import OpenAI

from app.agent.business_requirement import BusinessRequirement
try:
    from app.llm.sql_generator import is_llm_online, DEFAULT_MODEL
except ImportError:
    DEFAULT_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
    def is_llm_online() -> bool:
        return bool(os.getenv("QWEN_API_KEY")) and bool(os.getenv("QWEN_BASE_URL"))

logger = logging.getLogger(__name__)

class NLPUnderstanding:
    """
    NLP module to extract intent, entities, specific IDs, dates, and relationships
    from a user's natural language question.
    """

    def parse_question(self, question: str, context: str = "") -> BusinessRequirement:
        if not is_llm_online():
            # Basic fallback when offline
            return BusinessRequirement(
                original_question=question,
                intent="DATA_RETRIEVAL",
                entities=["table"]
            )

        prompt = f"""You are the NLP Understanding module of the JGH Intelligence Engine.
Analyze the user's question and extract relevant business requirements.

Context Schema: {context}
User Question: {question}

Extract and map the following:
1. Intent (e.g., DATA_RETRIEVAL, AGGREGATION, COMPARISON)
2. Entities (tables or core business concepts mentioned)
3. Specific IDs (any specific user IDs, product IDs, etc. formatted as {{"entity_name": [id1, id2]}})
4. Date Range (if mentioned, e.g. "July 2026", map to start and end dates)
5. Relationships (how entities connect, if specified)

Respond ONLY with a JSON object in this exact format, with no markdown formatting:
{{
  "intent": "DATA_RETRIEVAL",
  "entities": ["users", "wallet_transaction"],
  "specific_ids": {{"distributor_id": [5997]}},
  "date_range": "2026-07-01 to 2026-07-31",
  "relationships": ["users to wallet_transaction via user_id"]
}}
"""
        try:
            client = OpenAI(
                api_key=os.environ.get("QWEN_API_KEY"),
                base_url=os.environ.get("QWEN_BASE_URL"),
            )
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            
            # Map fields safely
            return BusinessRequirement(
                original_question=question,
                intent=data.get("intent", "UNKNOWN"),
                entities=data.get("entities", []),
                specific_ids=data.get("specific_ids", {}),
                date_period=str(data.get("date_range")) if data.get("date_range") else None,
                relationships=data.get("relationships", [])
            )
            
        except Exception as e:
            logger.error(f"[NLP ERROR] LLM call failed: {e}")
            raise e

nlp_agent = NLPUnderstanding()
