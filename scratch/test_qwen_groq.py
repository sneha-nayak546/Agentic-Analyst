import sys, os
sys.path.insert(0, os.path.abspath("."))
import time
from app.llm.provider import GroqProvider

p = GroqProvider()
prompt = "Generate SQL for: Show top 3 retailers by earnings for July 2026. Target tables: users, wallet_transaction. u.user_role = 2. Format: ```sql ... ```"
t0 = time.time()
res = p.generate(prompt, model="qwen/qwen3.6-27b")
print("Response time:", round((time.time() - t0)*1000, 2), "ms")
print("Result:\n", res)
