import re
import json
import logging
from typing import List, Dict, Any
from app.llm.sql_generator import call_llm, is_llm_online

logger = logging.getLogger(__name__)

def decompose_query(question: str) -> List[str]:
    """
    Splits a complex, multi-part question into independent sub-questions.
    If the question is singular or a table request with columns/filters, returns [question].
    Preserves entities, shared filters, dates, and IDs across each sub-question.
    """
    q_lower = question.lower().strip()

    # 1. Fast heuristics for obvious single queries
    if " and " not in q_lower and " also " not in q_lower and ";" not in q_lower and "?" not in q_lower[:-1] and " compare " not in q_lower:
        return [question]

    # Don't split queries that are single requests asking to include a column, aggregate, or comparison
    if "include a column" in q_lower or "with a column" in q_lower or "along with their" in q_lower or q_lower.startswith("compare ") or " compare " in q_lower:
        return [question]

    # Deterministic split on conjoined imperative tasks (e.g. "Show X and list Y", "Which X and which Y", "Show top X and top Y")
    imperative_match = re.split(r"\s*,?\s+and\s+(?=(?:list|show|give|tell|find|what|which|total|top\b))", question, flags=re.IGNORECASE)
    if len(imperative_match) > 1:
        parts = []
        for p in imperative_match:
            p_str = p.strip()
            if not p_str.endswith("?") and not p_str.endswith("."):
                p_str += "?"
            parts.append(p_str[0].upper() + p_str[1:])
        return parts

    # 2. Local Ollama Qwen Decomposition
    prompt = f"""You are an expert query decomposer for the JGH Intelligence Engine.
Your job is to analyze the user request and determine if it contains multiple independent tasks.

Rules:
1. If the sentence contains multiple DISTINCT questions or comparative requests (e.g. "Give total wallet amount for July, compare it with June, and show the top 5 distributors by increase"), split them into independent, self-contained sub-questions:
   Example output: ["Total wallet amount for July", "Total wallet amount for June", "Top 5 distributors by increase in wallet amount between July and June"]
2. If the request is a single coherent request with multiple conditions or columns (e.g. "Generate a table of retailers linked to distributor 5997, and include a column for their individual total earnings"), DO NOT split it. Return only ["{question}"].

User Question: "{question}"

Respond ONLY with a JSON array of strings.
"""
    system_prompt = "You are a query decomposer. Always respond with pure valid JSON array of strings."

    try:
        content = call_llm(prompt=prompt, system_prompt=system_prompt, format_json=False, temperature=0.0, max_tokens=150)
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)

        content = re.sub(r"\s*```$", "", content).strip()
        parsed = json.loads(content)
        if isinstance(parsed, list) and len(parsed) > 0 and all(isinstance(x, str) for x in parsed):
            return parsed
    except Exception as e:
        logger.warning(f"[QUERY DECOMPOSER NOTICE] Local LLM decomposition fallback: {e}")

    # 3. Fallback Heuristics
    parts = [p.strip() for p in re.split(r'\?|\;', question) if p.strip()]
    if len(parts) > 1:
        return parts

    return [question]

def decompose_to_atomic_tasks(question: str) -> List[Dict[str, Any]]:
    """
    Decomposes a question into structured atomic task dictionaries.
    Each atomic task preserves shared entities, filters, and dates.
    """
    sub_questions = decompose_query(question)
    tasks = []
    for i, sub_q in enumerate(sub_questions):
        tasks.append({
            "task_id": i + 1,
            "description": sub_q,
            "is_standalone": len(sub_questions) == 1
        })
    return tasks
