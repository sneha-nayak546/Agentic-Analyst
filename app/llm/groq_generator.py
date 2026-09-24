import os
import json
import logging
import urllib.request
import urllib.error
import time
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_groq_key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip("\"'")

def get_groq_model() -> str:
    return os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip("\"'")

GROQ_API_KEY = get_groq_key()
GROQ_MODEL = get_groq_model()

def is_groq_online(api_key: Optional[str] = None) -> bool:
    """Verifies that Groq API is reachable."""
    key = api_key or os.getenv("GROQ_API_KEY", "").strip("\"'")
    if not key:
        return False
    try:
        url = "https://api.groq.com/openai/v1/models"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False

def call_groq(
    prompt: str,
    system_prompt: str = "",
    format_json: bool = False,
    temperature: float = 0.0,
    max_tokens: int = 500,
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Executes prompt against Groq Cloud LPUs (~0.5s latency).
    """
    key = api_key or os.getenv("GROQ_API_KEY", "").strip("\"'")
    if not key:
        raise ValueError("GROQ_API_KEY is not configured in .env")

    selected_model = model or os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip("\"'")
    url = "https://api.groq.com/openai/v1/chat/completions"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens if max_tokens and max_tokens > 0 else 600,
    }
    if format_json:
        body["response_format"] = {"type": "json_object"}

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            elapsed = round(time.time() - t0, 2)
            res = json.loads(resp.read().decode("utf-8"))
            content = res["choices"][0]["message"]["content"].strip()
            logger.info(f"[GROQ SUCCESS]: Received {len(content)} chars in {elapsed}s using {selected_model}")
            return content
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        logger.error(f"[GROQ ERROR after {elapsed}s]: {type(e).__name__}: {e}")
        raise e
