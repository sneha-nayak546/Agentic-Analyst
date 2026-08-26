import json
import logging
import os
from typing import Dict, Any
from openai import OpenAI

# Try importing, fallback if missing
try:
    from app.llm.sql_generator import is_llm_online, DEFAULT_MODEL
except ImportError:
    DEFAULT_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
    def is_llm_online() -> bool:
        return bool(os.getenv("QWEN_API_KEY")) and bool(os.getenv("QWEN_BASE_URL"))

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Agentic Response Generator.
    Formats verified database results into a natural, business-friendly response using LLM.
    """

    def generate_response(self, plan: Dict[str, Any], execution_result: Dict[str, Any]) -> str:
        """
        Generates the final natural language answer based on the structured plan and execution results via LLM.
        """
        if not execution_result.get("success"):
            return f"Error executing query: {execution_result.get('error', 'Unknown Error')}"
            
        rows = execution_result.get("data", [])
        if hasattr(plan, 'business_requirement'):
            question = plan.business_requirement.original_question
        else:
            question = plan.get("original_question", plan.get("intent", "Data Request"))
        
        # If no LLM available, use simple fallback
        if not is_llm_online():
            if not rows:
                return "No records matching the exact requirements were found."
            return f"Found {len(rows)} matching records. (LLM unavailable for summarization)"

        # Cap rows to prevent context window explosion
        is_truncated = len(rows) > 15
        display_rows = rows[:15]
        
        prompt = f"""You are an expert Data Analyst providing a business-friendly response to the user.
User Question: "{question}"

Database Execution Result:
Success: True
Total Rows Found: {len(rows)}
Sample Data (Top {len(display_rows)}):
{json.dumps(display_rows, indent=2, default=str)}

Instructions:
1. Provide a natural, concise answer to the user's question based on the Data provided.
2. If there are multiple rows, format them into a clean markdown table.
3. If IDs are returned, do NOT format them with commas (e.g. 5997 not 5,997).
4. If currency is returned, format it properly (e.g. ₹).
5. If the result is empty, politely explain that no records match the criteria.
"""
        if is_truncated:
            prompt += "\n6. Mention that these are the top 15 results out of a larger dataset."

        try:
            client = OpenAI(
                api_key=os.environ.get("QWEN_API_KEY"),
                base_url=os.environ.get("QWEN_BASE_URL"),
            )
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                top_p=0.9
            )
            content = response.choices[0].message.content.strip()
            return content if content else "Could not generate a response."
        except Exception as e:
            print(f"[LLM WARNING] Response generation failed: {e}")
            if not rows:
                return "No records matching the exact requirements were found."
            return f"Found {len(rows)} matching records. (LLM summarization failed)"

response_generator = ResponseGenerator()
