import os
import json
import logging
import urllib.request
import urllib.error
import time
from typing import Optional

from app.llm.llm_config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

def is_gemini_online(api_key: Optional[str] = None) -> bool:
    """Verifies that the Gemini API endpoint is reachable with the provided API key."""
    key = api_key or GEMINI_API_KEY
    if not key:
        return False
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        logger.warning(f"[GEMINI CONNECTIVITY CHECK FAILED]: {e}")
        return False

def call_gemini(
    prompt: str,
    system_prompt: str = "",
    format_json: bool = False,
    temperature: float = 0.0,
    max_tokens: int = 500,
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Executes prompt against Google Generative Language API (Gemini 2.5 Flash)
    using native HTTPS requests with sub-2s response latency.
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY is not configured in .env")

    selected_model = model or GEMINI_MODEL or "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={key}"

    # Build Generation Config
    generation_config = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens if max_tokens and max_tokens > 0 else 1000,
        "thinkingConfig": {"thinkingBudget": 0}  # Ultra-fast mode without latent reasoning overhead
    }
    if format_json:
        generation_config["responseMimeType"] = "application/json"

    # Build Payload
    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": generation_config
    }

    if system_prompt:
        body["systemInstruction"] = {
            "parts": [{"text": system_prompt}]
        }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    max_retries = 2
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                elapsed = round(time.time() - t0, 2)
                res = json.loads(resp.read().decode("utf-8"))
                
                candidates = res.get("candidates", [])
                if not candidates:
                    raise ValueError(f"Gemini API returned no candidates: {res}")
                
                content_obj = candidates[0].get("content", {})
                parts = content_obj.get("parts", [])
                if not parts:
                    raise ValueError("Gemini API candidate has no content parts")
                
                text_output = parts[0].get("text", "").strip()
                logger.info(f"[GEMINI SUCCESS]: Received {len(text_output)} chars in {elapsed}s using {selected_model}")
                return text_output

        except urllib.error.HTTPError as e:
            elapsed = round(time.time() - t0, 2)
            err_body = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                if "quota" in err_body.lower() or "resource_exhausted" in err_body.lower():
                    logger.warning(f"[GEMINI QUOTA EXHAUSTED]: Daily free-tier limit exceeded. Routing to alternative provider immediately.")
                    raise RuntimeError(f"Gemini Quota Exhausted: {err_body}") from e
                if attempt < max_retries:
                    retry_wait = 2 * (attempt + 1)
                    logger.warning(f"[GEMINI RATE LIMIT]: 429 received. Backing off for {retry_wait}s before retry ({attempt+1}/{max_retries})...")
                    time.sleep(retry_wait)
                    continue
            logger.error(f"[GEMINI HTTP ERROR {e.code} after {elapsed}s]: {err_body}")
            raise RuntimeError(f"Gemini API Error {e.code}: {err_body}") from e
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            logger.error(f"[GEMINI NETWORK ERROR after {elapsed}s]: {type(e).__name__}: {e}")
            raise e

