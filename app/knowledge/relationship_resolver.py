import json
import logging
import os
from typing import Dict, Any, List
from openai import OpenAI

from app.agent.business_requirement import BusinessRequirement
from app.agent.execution_plan import ExecutionPlan
from app.retriever.retriever import retrieve_schema

logger = logging.getLogger(__name__)

# Try importing, fallback if missing
try:
    from app.llm.sql_generator import is_llm_online, DEFAULT_MODEL
except ImportError:
    DEFAULT_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
    def is_llm_online() -> bool:
        return bool(os.getenv("QWEN_API_KEY")) and bool(os.getenv("QWEN_BASE_URL"))

class RelationshipResolver:
    """
    Verifies and resolves business relationships between entities before SQL generation.
    Uses LLM reasoning against the database schema to dynamically discover relationships.
    """

    def resolve(self, req: BusinessRequirement) -> ExecutionPlan:
        plan = ExecutionPlan(business_requirement=req)
        
        # Build a prompt to map entities and relationships to schema
        entities = req.entities + ([req.intent] if req.intent else [])
        if req.specific_ids:
            entities.extend(req.specific_ids.keys())
            
        context = retrieve_schema(" ".join(entities), k=3)
        plan.rag_evidence = context
        
        if not is_llm_online():
            logger.warning("LLM offline, skipping generic relationship resolution.")
            return plan

        prompt = f"""You are the Relationship Resolution module of the JGH Intelligence Engine.
Your task is to map the requested business entities to actual database tables, and identify the required SQL joins based strictly on the provided schema context.

User's Original Question: {req.original_question}
Entities Extracted: {req.entities}
Relationships Mentioned: {req.relationships}

Schema Context:
{context}

Respond ONLY with a JSON object in this exact format, with no markdown formatting:
{{
  "relevant_tables": ["table1", "table2"],
  "required_joins": ["table1 JOIN table2 ON table1.id = table2.table1_id"],
  "resolved_entities": ["entity mapped to table"],
  "missing_information": ["List any relationships that cannot be resolved via schema, or leave empty"]
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
            plan.relevant_tables = data.get("relevant_tables", [])
            plan.required_joins = data.get("required_joins", [])
            plan.resolved_entities = data.get("resolved_entities", [])
            plan.missing_information = data.get("missing_information", [])
            
        except Exception as e:
            logger.error(f"Relationship resolution failed: {e}")
            plan.missing_information.append(f"Relationship resolution error: {e}")

        return plan

relationship_resolver = RelationshipResolver()
