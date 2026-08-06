"""
Local Ollama Qwen2.5-Coder Model Wrapper.
"""
from app.llm.sql_generator import generate_sql

def query_qwen_coder(prompt: str) -> str:
    """Wrapper function calling local Ollama qwen2.5-coder:7b."""
    return generate_sql(prompt)
