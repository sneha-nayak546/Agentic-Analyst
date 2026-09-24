import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
import time
from app.llm.provider import GroqProvider

p = GroqProvider()
prompt = """
Extract intent from: "Show top 3 retailers by earnings for July 2026"
Return JSON with: intent, entities, metrics, periods, limit.
"""
t0 = time.time()
res = p.generate(prompt, model="openai/gpt-oss-20b", format_json=True, max_tokens=600)
print("Response time:", round((time.time() - t0)*1000, 2), "ms")
print("Result:\n", res)
