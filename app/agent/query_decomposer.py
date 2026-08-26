import re
import json
from openai import OpenAI
import os
from typing import List

DEFAULT_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")

def is_llm_online() -> bool:
    return bool(os.getenv("QWEN_API_KEY")) and bool(os.getenv("QWEN_BASE_URL"))

def decompose_query(question: str) -> List[str]:
    """
    Splits a complex, multi-part question into independent sub-questions.
    If the question is singular, returns a list containing just the original question.
    """
    q_lower = question.lower().strip()
    
    # 1. Quick heuristic bypass for obvious single questions to save LLM latency
    if " and " not in q_lower and " also " not in q_lower and "," not in q_lower and "?" not in q_lower[:-1]:
        return [question]
        
    # 2. LLM Decomposition
    if is_llm_online():
        prompt = (
            "You are an AI query decomposer. The user will provide a sentence. "
            "If the sentence contains multiple DISTINCT questions or tasks (e.g., asking for two separate tables or entirely separate insights), split them into independent, fully-formed sentences. "
            "If the sentence is a single request with multiple conditions, filters, or additional columns requested (e.g., 'Generate a table of X and include a column for Y'), DO NOT split it. Return it as a single item. "
            "Ensure context (like dates, names, or IDs) is carried over to each sub-question if applicable.\n\n"
            "Example 1:\n"
            "User: 'What is the balance of distributor 5997 and list all their retailers'\n"
            'Output: ["What is the balance of distributor 5997?", "List all the retailers for distributor 5997."]\n\n'
            "Example 2:\n"
            "User: 'Show me top 5 retailers in july'\n"
            'Output: ["Show me top 5 retailers in july"]\n\n'
            "Example 3:\n"
            "User: 'Generate a table of retailers linked to distributor 5997, and include a column for their individual total earnings'\n"
            'Output: ["Generate a table of retailers linked to distributor 5997, and include a column for their individual total earnings"]\n\n'
            "Return ONLY a valid JSON array of strings. Do not add markdown blocks or explanations.\n\n"
            f"User: '{question}'\nOutput:"
        )
        
        try:
            client = OpenAI(
                api_key=os.environ.get("QWEN_API_KEY"),
                base_url=os.environ.get("QWEN_BASE_URL"),
            )
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                top_p=0.9,
                max_tokens=150
            )
            content = response.choices[0].message.content.strip()
            
            # Clean markdown if generated
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content).strip()
            
            parsed = json.loads(content)
            if isinstance(parsed, list) and len(parsed) > 0 and all(isinstance(x, str) for x in parsed):
                return parsed
        except Exception as e:
            print(f"[Query Decomposer Error] LLM parsing failed: {e}")
            
    # 3. Fallback Heuristics
    # Split by '?' or ';' if LLM fails, as 'and' is too aggressive for multi-condition single queries
    parts = re.split(r'\?|\;', question)
    parts = [p.strip() for p in parts if p.strip()]
    
    if len(parts) > 1:
        return parts
        
    return [question]
