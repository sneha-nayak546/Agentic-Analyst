import os
import re
import json
from openai import OpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")

def is_llm_online() -> bool:
    return bool(os.getenv("QWEN_API_KEY")) and bool(os.getenv("QWEN_BASE_URL"))

def generate_sql(prompt: str, model_name: str = None, temperature: float = 0.0, plan: Dict[str, Any] = None) -> str:
    """
    Generate SQL using the LLM via Cloud Qwen (vLLM) API.
    """
    if is_llm_online():
        model = model_name or DEFAULT_MODEL
        try:
            client = OpenAI(
                api_key=os.environ.get("QWEN_API_KEY"),
                base_url=os.environ.get("QWEN_BASE_URL"),
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert MySQL Data Analyst. Write only valid MySQL SELECT queries. Output the SQL query inside ```sql code blocks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                top_p=0.9,
                max_tokens=300
            )
            content = response.choices[0].message.content.strip()
            
            content = re.sub(r"^```(?:sql)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content).strip()
            if content and ";" in content:
                return content.split(";")[0].strip() + ";"
            if content:
                return content
        except Exception as e:
            print(f"[LLM WARNING] Kimi call failed: {e}")
            raise e
    else:
        raise ConnectionError("KIMI_API_KEY is not set.")

    return ""