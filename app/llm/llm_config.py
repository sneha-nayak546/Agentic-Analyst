import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ==============================================================================
# Centralized Multi-Model Provider Configuration for JGH Intelligence Engine
# ==============================================================================

# 1. API Keys & Hosts (Sanitized, Never Exposed or Logged)
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip("\"'")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip("\"'")

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip("\"'")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip("\"'")

OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
OLLAMA_BASE_URL: str = OLLAMA_HOST
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", os.getenv("QWEN_MODEL", "qwen2.5-coder:7b")).strip("\"'")

# Configurable Ollama runtime parameters
try:
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "300"))
except ValueError:
    OLLAMA_TIMEOUT = 300.0

OLLAMA_KEEP_ALIVE: str = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

try:
    OLLAMA_NUM_CTX: int = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
except ValueError:
    OLLAMA_NUM_CTX = 2048

try:
    default_threads = min(8, max(1, (os.cpu_count() or 4) - 2))
    OLLAMA_NUM_THREAD: int = int(os.getenv("OLLAMA_NUM_THREAD", str(default_threads)))
except Exception:
    OLLAMA_NUM_THREAD = 4

# ==============================================================================
# Per-Stage Provider and Model Routing (Sections 1 & 2)
# Supported Providers: "gemini", "groq", "ollama"
# ==============================================================================

def _resolve_default_cloud_provider() -> str:
    if GEMINI_API_KEY:
        return "gemini"
    if GROQ_API_KEY:
        return "groq"
    return "ollama"

def _resolve_default_cloud_model(provider: str) -> str:
    if provider == "gemini":
        return GEMINI_MODEL
    if provider == "groq":
        return GROQ_MODEL
    return OLLAMA_MODEL

# Intent / NLP Stage
INTENT_PROVIDER: str = (
    os.getenv("INTENT_PROVIDER") or os.getenv("LLM_INTENT_PROVIDER") or _resolve_default_cloud_provider()
).strip().lower()
INTENT_MODEL: str = (
    os.getenv("INTENT_MODEL") or os.getenv("LLM_INTENT_MODEL") or _resolve_default_cloud_model(INTENT_PROVIDER)
).strip("\"'")

# SQL Generation Stage (Defaults to local Ollama qwen2.5-coder:7b per Section 2, or configured provider)
SQL_PROVIDER: str = (
    os.getenv("SQL_PROVIDER") or os.getenv("LLM_SQL_PROVIDER") or "ollama"
).strip().lower()
SQL_MODEL: str = (
    os.getenv("SQL_MODEL") or os.getenv("LLM_SQL_MODEL") or OLLAMA_MODEL
).strip("\"'")

# SQL Semantic Verifier Stage
SQL_VERIFIER_PROVIDER: str = (
    os.getenv("SQL_VERIFIER_PROVIDER") or os.getenv("LLM_SQL_VERIFIER_PROVIDER") or _resolve_default_cloud_provider()
).strip().lower()
SQL_VERIFIER_MODEL: str = (
    os.getenv("SQL_VERIFIER_MODEL") or os.getenv("LLM_SQL_VERIFIER_MODEL") or _resolve_default_cloud_model(SQL_VERIFIER_PROVIDER)
).strip("\"'")

# Final Answer Generation Stage
ANSWER_PROVIDER: str = (
    os.getenv("ANSWER_PROVIDER") or os.getenv("LLM_ANSWER_PROVIDER") or _resolve_default_cloud_provider()
).strip().lower()
ANSWER_MODEL: str = (
    os.getenv("ANSWER_MODEL") or os.getenv("LLM_ANSWER_MODEL") or _resolve_default_cloud_model(ANSWER_PROVIDER)
).strip("\"'")

# Legacy aliases
LLM_INTENT_PROVIDER = INTENT_PROVIDER
LLM_INTENT_MODEL = INTENT_MODEL
LLM_SQL_PROVIDER = SQL_PROVIDER
LLM_SQL_MODEL = SQL_MODEL
LLM_SQL_VERIFIER_PROVIDER = SQL_VERIFIER_PROVIDER
LLM_SQL_VERIFIER_MODEL = SQL_VERIFIER_MODEL
LLM_ANSWER_PROVIDER = ANSWER_PROVIDER
LLM_ANSWER_MODEL = ANSWER_MODEL
LLM_PROVIDER = SQL_PROVIDER
