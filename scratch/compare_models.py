import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
from app.llm.provider import GroqProvider

p = GroqProvider()
prompt = """
Write an optimized MySQL SELECT query for: Show top 3 retailers by earnings for July 2026.
Tables: users (id, name, user_role), wallet_transaction (user_id, amount, created_at, reference_type)
Rules: user_role = 2, created_at >= '2026-07-01' and created_at < '2026-08-01', amount > 0.
Return ```sql ... ```
"""
res = p.generate(prompt, model="openai/gpt-oss-20b", max_tokens=600)
print("GPT-20b Result:\n", res)
print("="*40)
res2 = p.generate(prompt, model="groq/compound-mini", max_tokens=600)
print("Compound-mini Result:\n", res2)
