from dotenv import load_dotenv
import os, time
from groq import Groq
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

sql_prompt = """You are an expert MySQL Data Analyst for JGH Enterprise.
Write ONLY a valid MySQL SELECT query inside ```sql code block.
Query: Show top 3 retailers by earnings for July 2026.
Schema: users(id, name, user_role, status), wallet_transaction(user_id, amount, created_at, reference_type).
Rules:
- Retailers have user_role = 2.
- Earnings are amount > 0 in wallet_transaction.
- Filter created_at in July 2026.
- Order by earnings DESC LIMIT 3.
"""

t0 = time.time()
r = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {"role": "system", "content": "You are an expert MySQL Data Analyst. Write valid MySQL SELECT queries. Output only ```sql ... ```."},
        {"role": "user", "content": sql_prompt}
    ],
    temperature=0.0
)
print("SQL Time:", round(time.time() - t0, 2), "s")
print("SQL Output:\n", r.choices[0].message.content)
