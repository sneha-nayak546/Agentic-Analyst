import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
import time
from app.llm.provider import GroqProvider

p = GroqProvider()
prompt = """
Target Tables: users, wallet_transaction
Relationships: users.id = wallet_transaction.user_id
Business Rules:
- Retailer has users.user_role = 2
- Earnings means SUM(wallet_transaction.amount) WHERE wallet_transaction.amount > 0
- Filter for July 2026 on wallet_transaction.created_at

Generate a MySQL query for: Show top 3 retailers by earnings for July 2026.
Output in ```sql ``` block.
"""

t0 = time.time()
res = p.generate(prompt, model="openai/gpt-oss-20b")
print("Response time:", round((time.time() - t0)*1000, 2), "ms")
print("Result:\n", res)
