import os
import re
import json
import logging
import time
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from app.llm.llm_config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL as DEFAULT_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_THREAD,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER
)
from app.llm.provider import model_router, GroqProvider, OllamaProvider

_ollama_client = None

def get_ollama_client():
    global _ollama_client
    if _ollama_client is None:
        import ollama
        _ollama_client = ollama.Client(host=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT)
    return _ollama_client

def is_ollama_online_local() -> bool:
    """Check if local Ollama instance is reachable."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/version")
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status == 200
    except Exception:
        return False

def is_llm_online() -> bool:
    """Check if active LLM provider is online."""
    if os.getenv("GEMINI_API_KEY") and model_router.gemini_provider.is_online():
        return True
    if os.getenv("GROQ_API_KEY") and model_router.groq_provider.is_online():
        return True
    return is_ollama_online_local()

is_ollama_online = is_llm_online

def call_ollama(prompt: str, system_prompt: str = "", format_json: bool = False, temperature: float = 0.0, max_tokens: int = 800) -> str:
    """Executes prompt directly against local Ollama Qwen2.5-Coder:7b."""
    return model_router.ollama_provider.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        format_json=format_json,
        temperature=temperature,
        max_tokens=max_tokens
    )

def call_llm(
    prompt: str,
    system_prompt: str = "",
    format_json: bool = False,
    temperature: float = 0.0,
    max_tokens: int = 1200,
    stage: str = "intent"
) -> str:
    """
    Unified LLM dispatcher routed through MultiModelRouter:
    Routes each stage to its configured provider with seamless fallback to local Ollama.
    """
    return model_router.execute_stage(
        stage=stage,
        prompt=prompt,
        system_prompt=system_prompt,
        format_json=format_json,
        temperature=temperature,
        max_tokens=max_tokens
    )

def extract_sql_queries(content: str) -> List[str]:
    """
    Extracts pure SQL query from model output.
    Ensures AST parser receives ONLY valid SQL and strips any conversational filler.
    """
    if not content or not isinstance(content, str):
        return []

    # 0. Strip thinking tags safely
    if "</think>" in content:
        content = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.IGNORECASE).strip()
    elif "<think>" in content:
        m_fence = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", content, flags=re.IGNORECASE)
        if m_fence:
            content = m_fence.group(1).strip()
        else:
            content = re.sub(r"^<think>\s*", "", content, flags=re.IGNORECASE).strip()

    # 1. Match code blocks ```sql ... ``` if model wrapped it despite instructions
    block_match = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", content, flags=re.IGNORECASE)
    if block_match:
        sql_candidate = block_match.group(1).strip()
        lines = sql_candidate.splitlines()
        for idx, line in enumerate(lines):
            l_str = line.strip().upper()
            if l_str.startswith("SELECT") or l_str.startswith("WITH"):
                clean_block = "\n".join(lines[idx:]).strip()
                if ";" in clean_block:
                    clean_block = clean_block.split(";")[0].strip() + ";"
                return [clean_block]
        if any(w in sql_candidate.upper() for w in ["SELECT", "WITH"]):
            return [sql_candidate]

    # 2. If no fence, check for markers like Write: / Query: / SQL:
    marker_match = re.search(r"(?:Write|Query|SQL):\s*([\s\S]+)", content, flags=re.IGNORECASE)
    cleaned = marker_match.group(1).strip() if marker_match else content.strip()
    cleaned = cleaned.replace("```sql", "").replace("```", "").strip()

    # 3. Find the first line starting with SELECT or WITH
    lines = cleaned.splitlines()
    start_line_idx = None
    for idx, line in enumerate(lines):
        l_str = line.strip().upper()
        if l_str.startswith("SELECT ") or l_str.startswith("WITH ") or l_str == "SELECT" or l_str == "WITH":
            start_line_idx = idx
            break

    if start_line_idx is not None:
        sql_text = "\n".join(lines[start_line_idx:]).strip()
        if ";" in sql_text:
            sql_text = sql_text.split(";")[0].strip() + ";"
        return [sql_text]

    # 4. Regex fallback if SELECT or WITH was inline
    m_inline = re.search(r"\b(SELECT\s+[\s\S]+|WITH\s+[a-zA-Z_]\w*\s+AS\s*[\s\S]+)", cleaned, flags=re.IGNORECASE)
    if m_inline:
        sql_text = m_inline.group(1).strip()
        if ";" in sql_text:
            sql_text = sql_text.split(";")[0].strip() + ";"
        return [sql_text]

    return []

def generate_multi_sql(prompt: str, temperature: float = 0.0) -> List[str]:
    """
    Generates MySQL SELECT queries using configured SQL generation model.
    Enforces SQL-ONLY output without markdown fences, explanations, or commentary.
    """
    system_prompt = (
        "You are an expert MySQL Data Analyst.\n"
        "RETURN SQL ONLY.\n\n"
        "DO NOT RETURN:\n"
        "- explanations\n"
        "- reasoning\n"
        "- analysis\n"
        "- comments\n"
        "- markdown\n"
        "- ```sql fences\n"
        "- business-rule explanations\n"
        "- alternative SQL\n"
        "- suggestions\n"
        "- \"maybe\"\n"
        "- natural-language descriptions\n\n"
        "The expected model output must be a single SELECT or WITH statement.\n"
        "Begin your output immediately with SELECT or WITH."
    )
    content = model_router.execute_stage(
        stage="sql",
        prompt=prompt,
        system_prompt=system_prompt,
        format_json=False,
        temperature=temperature,
        max_tokens=950
    )
    queries = extract_sql_queries(content)
    return queries

def generate_sql(prompt: str, model_name: str = None, temperature: float = 0.0, plan: Any = None) -> str:
    """
    Generate ONE SQL query dynamically from prompt using the configured SQL model.
    No hardcoded templates or shortcuts.
    """
    queries = generate_multi_sql(prompt, temperature=temperature)
    if queries:
        return queries[0]
    return ""