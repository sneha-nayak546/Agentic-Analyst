import os
import json
import logging
import urllib.request
import urllib.error
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from app.llm.llm_config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_THREAD,
    INTENT_PROVIDER,
    INTENT_MODEL,
    SQL_PROVIDER,
    SQL_MODEL,
    SQL_VERIFIER_PROVIDER,
    SQL_VERIFIER_MODEL,
    ANSWER_PROVIDER,
    ANSWER_MODEL,
)

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base interface for all LLM providers (Gemini, Groq, Ollama)."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        format_json: bool = False,
        temperature: float = 0.0,
        max_tokens: int = 600,
        model: Optional[str] = None
    ) -> str:
        pass

    @abstractmethod
    def is_online(self) -> bool:
        pass


class GeminiProvider(LLMProvider):
    """
    Google Gemini Provider via Google AI Studio API.
    Fast, highly capable cloud reasoning model.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)).strip("\"'")
        self.default_model = default_model or os.getenv("GEMINI_MODEL", GEMINI_MODEL)

    def is_online(self) -> bool:
        key = self.api_key or os.getenv("GEMINI_API_KEY", "").strip("\"'")
        if not key:
            return False
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        format_json: bool = False,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        key = self.api_key or os.getenv("GEMINI_API_KEY", "").strip("\"'")
        if not key:
            raise ValueError("GEMINI_API_KEY is not configured in environment")

        selected_model = model or self.default_model or "gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={key}"

        generation_config = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens if max_tokens and max_tokens > 0 else 1000,
        }
        if format_json:
            generation_config["responseMimeType"] = "application/json"

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                elapsed = round(time.time() - t0, 2)
                res = json.loads(resp.read().decode("utf-8"))
                candidates = res.get("candidates", [])
                if not candidates:
                    raise ValueError(f"Gemini returned no candidates")
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise ValueError("Gemini candidate content is empty")
                text_out = parts[0].get("text", "").strip()
                logger.info(f"[GEMINI SUCCESS]: {len(text_out)} chars in {elapsed}s using {selected_model}")
                return text_out
        except urllib.error.HTTPError as e:
            elapsed = round(time.time() - t0, 2)
            err_body = e.read().decode("utf-8", errors="replace")
            logger.error(f"[GEMINI HTTP ERROR {e.code} after {elapsed}s]: {err_body}")
            raise RuntimeError(f"Gemini API Error {e.code}: {err_body}") from e
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            logger.error(f"[GEMINI ERROR after {elapsed}s]: {type(e).__name__}: {e}")
            raise e


class GroqProvider(LLMProvider):
    """
    Hosted Free Developer Inference using Groq LPUs.
    Sub-second latency with User-Agent header protection.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GROQ_API_KEY", GROQ_API_KEY)).strip("\"'")
        self.default_model = default_model or os.getenv("GROQ_MODEL", GROQ_MODEL)

    def is_online(self) -> bool:
        key = self.api_key or os.getenv("GROQ_API_KEY", "").strip("\"'")
        if not key:
            return False
        try:
            url = "https://api.groq.com/openai/v1/models"
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            })
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        format_json: bool = False,
        temperature: float = 0.0,
        max_tokens: int = 800,
        model: Optional[str] = None
    ) -> str:
        key = self.api_key or os.getenv("GROQ_API_KEY", "").strip("\"'")
        if not key:
            raise ValueError("GROQ_API_KEY is not configured in environment")

        if not hasattr(self, "_disabled_models") or not isinstance(self._disabled_models, dict):
            self._disabled_models = {}

        now = time.time()
        self._disabled_models = {m: ts for m, ts in self._disabled_models.items() if now - ts < 120}

        selected_model = model or self.default_model or "qwen/qwen3.8-27b"
        if selected_model in self._disabled_models:
            for alt in ["qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b"]:
                if alt not in self._disabled_models:
                    selected_model = alt
                    break

        url = "https://api.groq.com/openai/v1/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        effective_max_tokens = min(max_tokens if max_tokens and max_tokens > 0 else 950, 980)

        body: Dict[str, Any] = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": effective_max_tokens,
        }
        if format_json:
            body["response_format"] = {"type": "json_object"}

        data = json.dumps(body).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        req = urllib.request.Request(url, data=data, headers=headers)

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                elapsed = round(time.time() - t0, 2)
                res = json.loads(resp.read().decode("utf-8"))
                msg = res["choices"][0]["message"]
                content = (msg.get("content") or "").strip()
                import re
                if "</think>" in content:
                    content = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.IGNORECASE).strip()
                elif "<think>" in content:
                    m_sql = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", content, flags=re.IGNORECASE)
                    m_json = re.search(r"```(?:json)?\s*([\s\S]*?)(?:```|$)", content, flags=re.IGNORECASE)
                    if m_sql:
                        content = m_sql.group(1).strip()
                    elif m_json:
                        content = m_json.group(1).strip()
                    else:
                        m_open = content.find("<think>")
                        m_close = content.find("</think>")
                        if m_close != -1:
                            content = content[m_close + 8:].strip()

                if not content and msg.get("reasoning"):
                    m_sql = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", msg["reasoning"], flags=re.IGNORECASE)
                    m_json = re.search(r"(\{[\s\S]*\})", msg["reasoning"])
                    if m_sql:
                        content = m_sql.group(1).strip()
                    elif m_json:
                        content = m_json.group(1).strip()
                    else:
                        content = msg["reasoning"].strip()

                if not content:
                    raise RuntimeError(f"Groq model {selected_model} returned empty content")

                logger.info(f"[GROQ SUCCESS]: {len(content)} chars in {elapsed}s using {selected_model}")
                return content
        except urllib.error.HTTPError as e:
            elapsed = round(time.time() - t0, 2)
            err_body = e.read().decode("utf-8", errors="replace")
            logger.warning(f"[GROQ HTTP ERROR {e.code} after {elapsed}s]: {err_body}")
            if e.code == 400 and "json_validate_failed" in err_body and "response_format" in body:
                logger.info("[GROQ JSON MODE RETRY]: Retrying without explicit response_format constraint...")
                body_no_rf = dict(body)
                body_no_rf.pop("response_format", None)
                data_no_rf = json.dumps(body_no_rf).encode("utf-8")
                req_rf = urllib.request.Request(url, data=data_no_rf, headers=headers)
                try:
                    with urllib.request.urlopen(req_rf, timeout=25) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        msg = res["choices"][0]["message"]
                        content = (msg.get("content") or "").strip()
                        if not content and msg.get("reasoning"):
                            content = msg["reasoning"].strip()
                        logger.info(f"[GROQ JSON RETRY SUCCESS]: {len(content)} chars using {selected_model}")
                        return content
                except Exception as rf_err:
                    logger.warning(f"[GROQ JSON RETRY FAILED]: {rf_err}")

            if e.code == 429:
                import re
                m_ms = re.search(r"try again in ([\d\.]+)\s*ms", err_body)
                m_s = re.search(r"try again in ([\d\.]+)\s*s", err_body)
                wait_sec = 1.0
                if m_ms:
                    wait_sec = max(0.3, (float(m_ms.group(1)) / 1000.0) + 0.2)
                elif m_s:
                    wait_sec = float(m_s.group(1)) + 0.5

                is_tpd = "tokens per day" in err_body or "TPD" in err_body

                # If minute-level rate limit with small wait, sleep and retry on same model
                if not is_tpd and wait_sec <= 5.0:
                    logger.info(f"[GROQ RATE LIMIT 429]: Waiting {wait_sec:.2f}s before retry on {selected_model}...")
                    time.sleep(wait_sec)
                    for attempt in range(1, 4):
                        try:
                            req_retry = urllib.request.Request(url, data=data, headers=headers)
                            with urllib.request.urlopen(req_retry, timeout=25) as resp:
                                res = json.loads(resp.read().decode("utf-8"))
                                msg = res["choices"][0]["message"]
                                content = (msg.get("content") or "").strip()
                                if not content and msg.get("reasoning"):
                                    m_sql = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", msg["reasoning"], flags=re.IGNORECASE)
                                    m_json = re.search(r"(\{[\s\S]*\})", msg["reasoning"])
                                    if m_sql:
                                        content = m_sql.group(1).strip()
                                    elif m_json:
                                        content = m_json.group(1).strip()
                                    else:
                                        content = msg["reasoning"].strip()
                                if content:
                                    logger.info(f"[GROQ RETRY {attempt} SUCCESS]: {len(content)} chars using {selected_model}")
                                    return content
                        except urllib.error.HTTPError as r_err:
                            if r_err.code == 429 and attempt < 3:
                                time.sleep(1.0 * attempt)
                                continue
                            break
                        except Exception as retry_err:
                            logger.warning(f"[GROQ RETRY FAILED]: {retry_err}")
                            break

                # If daily quota reached, long wait time, or retry failed, failover immediately
                self._disabled_models[selected_model] = time.time()
                candidates = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
                if model is None or model == self.default_model or selected_model in self._disabled_models:
                    for alt_model in candidates:
                        if alt_model == selected_model or alt_model in self._disabled_models:
                            continue
                        logger.warning(f"[GROQ 429 RATE LIMIT on {selected_model}]: Automatically attempting alternative Groq model '{alt_model}'...")
                        try:
                            return self.generate(
                                prompt=prompt,
                                system_prompt=system_prompt,
                                format_json=format_json,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                model=alt_model
                            )
                        except Exception as alt_err:
                            logger.warning(f"[GROQ ALTERNATIVE MODEL {alt_model} FAILED]: {alt_err}")

            raise RuntimeError(f"Groq API Error {e.code}: {err_body}") from e
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            logger.warning(f"[GROQ ERROR after {elapsed}s]: {type(e).__name__}: {e}")
            raise e


class OllamaProvider(LLMProvider):
    """
    Local Private Model Provider using Ollama (qwen2.5-coder:7b).
    Completely offline, no external API keys or quota limits.
    """

    def __init__(self, base_url: Optional[str] = None, default_model: Optional[str] = None):
        self.base_url = (base_url or os.getenv("OLLAMA_HOST", OLLAMA_BASE_URL)).rstrip("/")
        self.default_model = default_model or os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)
        self._client = None

    def _get_client(self):
        if self._client is None:
            import ollama
            self._client = ollama.Client(host=self.base_url, timeout=OLLAMA_TIMEOUT)
        return self._client

    def is_online(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/version")
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        format_json: bool = False,
        temperature: float = 0.0,
        max_tokens: int = 800,
        model: Optional[str] = None
    ) -> str:
        client = self._get_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        selected_model = model or self.default_model

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": OLLAMA_NUM_CTX,
            "num_thread": OLLAMA_NUM_THREAD
        }

        t0 = time.time()
        try:
            response = client.chat(
                model=selected_model,
                messages=messages,
                format="json" if format_json else None,
                options=options,
                keep_alive=OLLAMA_KEEP_ALIVE
            )
            elapsed = round(time.time() - t0, 2)
            content = response.get("message", {}).get("content", "").strip()
            logger.info(f"[OLLAMA SUCCESS]: {len(content)} chars in {elapsed}s using {selected_model}")
            return content
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            logger.error(f"[OLLAMA ERROR after {elapsed}s]: {type(e).__name__}: {e}")
            raise e


class MultiModelRouter:
    """
    Stage-Explicit Model Router (Sections 1 & 2):
    Dispatches each stage (intent, sql, verifier, answer) to its explicitly configured
    provider and model without random switching or silent fallback.
    """

    def __init__(self):
        self.gemini_provider = GeminiProvider()
        self.groq_provider = GroqProvider()
        self.ollama_provider = OllamaProvider()
        self.last_provider_used = "unknown"
        self.last_model_used = "unknown"
        self.last_fallback_used = False
        self.last_fallback_reason = None

    def get_provider_instance(self, provider_name: str) -> LLMProvider:
        p = provider_name.strip().lower()
        if p == "gemini":
            return self.gemini_provider
        elif p == "groq":
            return self.groq_provider
        elif p == "ollama":
            return self.ollama_provider
        else:
            # Default fallback based on available keys
            if os.getenv("GEMINI_API_KEY"):
                return self.gemini_provider
            elif os.getenv("GROQ_API_KEY"):
                return self.groq_provider
            return self.ollama_provider

    def resolve_stage_config(self, stage: str) -> tuple[str, str]:
        if stage == "intent":
            p = os.getenv("INTENT_PROVIDER", INTENT_PROVIDER).strip().lower()
            m = os.getenv("INTENT_MODEL", INTENT_MODEL).strip("\"'")
        elif stage == "sql":
            p = os.getenv("SQL_PROVIDER", SQL_PROVIDER).strip().lower()
            m = os.getenv("SQL_MODEL", SQL_MODEL).strip("\"'")
        elif stage == "verifier":
            p = os.getenv("SQL_VERIFIER_PROVIDER", SQL_VERIFIER_PROVIDER).strip().lower()
            m = os.getenv("SQL_VERIFIER_MODEL", SQL_VERIFIER_MODEL).strip("\"'")
        elif stage == "answer":
            p = os.getenv("ANSWER_PROVIDER", ANSWER_PROVIDER).strip().lower()
            m = os.getenv("ANSWER_MODEL", ANSWER_MODEL).strip("\"'")
        else:
            p = "groq" if os.getenv("GROQ_API_KEY") else "ollama"
            m = GROQ_MODEL if p == "groq" else OLLAMA_MODEL
        return p, m

    def get_fallback_chain(self, primary_provider: str, primary_model: str) -> list:
        """
        Builds a 3-tier cascade based on the primary provider.
        Cascade hierarchy:
          - Tier 1: Primary provider (e.g. Gemini 2.5 Flash)
          - Tier 2: Alternative fast cloud provider (e.g. Groq Qwen 3.8 27B)
          - Tier 3: Local offline fallback (Ollama Qwen 2.5 Coder 7B)
        """
        gemini_m = os.getenv("GEMINI_MODEL", GEMINI_MODEL).strip("\"'") or "gemini-2.5-flash"
        groq_m = os.getenv("GROQ_MODEL", GROQ_MODEL).strip("\"'") or "qwen/qwen3.8-27b"
        ollama_m = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL).strip("\"'") or "qwen2.5-coder:7b"

        candidates = {
            "gemini": ("gemini", gemini_m, self.gemini_provider),
            "groq": ("groq", groq_m, self.groq_provider),
            "ollama": ("ollama", ollama_m, self.ollama_provider),
        }

        chain = []
        p_norm = primary_provider.strip().lower()
        if p_norm in candidates:
            chain.append((p_norm, primary_model or candidates[p_norm][1], candidates[p_norm][2]))

        # Define preferred priority order for the remaining providers
        if p_norm == "gemini":
            remaining_order = ["groq", "ollama"]
        elif p_norm == "groq":
            remaining_order = ["gemini", "ollama"]
        else:
            remaining_order = ["gemini", "groq"]

        for p in remaining_order:
            if not any(item[0] == p for item in chain) and p in candidates:
                chain.append(candidates[p])

        return chain

    def execute_stage(
        self,
        stage: str,
        prompt: str,
        system_prompt: str = "",
        format_json: bool = False,
        temperature: float = 0.0,
        max_tokens: int = 800
    ) -> str:
        """
        Executes a pipeline stage using a 3-model automatic fallback chain:
        1. Primary Model (e.g. Gemini 2.5 Flash)
        2. Fast Cloud Fallback (e.g. Groq Qwen 3.8 27B) if primary fails / hits quota
        3. Local Offline Fallback (Ollama Qwen 2.5 Coder 7B) if cloud providers fail / quota reached
        """
        primary_provider, primary_model = self.resolve_stage_config(stage)
        chain = self.get_fallback_chain(primary_provider, primary_model)

        errors = []
        for idx, (p_name, m_name, provider) in enumerate(chain):
            # Check availability before attempting
            if p_name == "gemini":
                key = (provider.api_key or os.getenv("GEMINI_API_KEY", "")).strip("\"'")
                if not key:
                    errors.append("gemini: No API key configured")
                    continue
            elif p_name == "groq":
                key = (provider.api_key or os.getenv("GROQ_API_KEY", "")).strip("\"'")
                if not key:
                    errors.append("groq: No API key configured")
                    continue
            elif p_name == "ollama":
                if not provider.is_online():
                    errors.append("ollama: Local server not reachable")
                    continue

            t0 = time.time()
            try:
                if idx > 0:
                    logger.warning(
                        f"[3-MODEL FALLBACK] Stage '{stage}': Primary model failed or quota reached. "
                        f"Automatically switching to Tier {idx + 1} ({p_name} - {m_name})"
                    )

                res = provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    format_json=format_json,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=m_name
                )
                elapsed_ms = round((time.time() - t0) * 1000, 2)

                self.last_provider_used = p_name
                self.last_model_used = m_name

                if idx > 0:
                    self.last_fallback_used = True
                    prev_name = chain[0][0]
                    self.last_fallback_reason = f"{prev_name} failed/quota reached ({errors[-1] if errors else 'error'}), switched to {p_name}"
                    logger.info(
                        f"[STAGE {stage.upper()} ROUTING (FALLBACK)] provider={p_name} model={m_name} "
                        f"latency={elapsed_ms}ms reason='{self.last_fallback_reason}'"
                    )
                else:
                    self.last_fallback_used = False
                    self.last_fallback_reason = None
                    logger.info(
                        f"[STAGE {stage.upper()} ROUTING] provider={p_name} model={m_name} "
                        f"latency={elapsed_ms}ms fallback_used=False"
                    )
                return res

            except Exception as e:
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                err_summary = f"{type(e).__name__}: {str(e)[:150]}"
                errors.append(f"{p_name} ({m_name}): {err_summary}")
                logger.warning(
                    f"[STAGE {stage.upper()} TIER {idx + 1} ({p_name}) FAILED after {elapsed_ms}ms]: {err_summary}. "
                    f"Initiating automatic switch to next model..."
                )

        combined = " | ".join(errors)
        logger.error(f"[STAGE {stage.upper()} ALL TIERS EXHAUSTED]: {combined}")
        raise RuntimeError(f"All configured multi-model providers failed for stage '{stage}': {combined}")


# Singleton global router
model_router = MultiModelRouter()
