from app.llm.provider import OllamaProvider

provider = OllamaProvider()
print("Ollama online:", provider.is_online())

prompt = """You are an expert MySQL SQL generator for an enterprise analytics database.
Generate ONLY the SQL query for this question:
"Show top 3 retailers by earnings for July 2026"

Schema:
- users: id, name, mobile_number, user_role (2 = retailer)
- wallet_transaction: user_id, amount, created_at, transaction_type (1 = credit/earnings), reference_type

Requirements:
- Only retailers (user_role = 2)
- Period: July 2026 (created_at >= '2026-07-01 00:00:00' AND created_at < '2026-08-01 00:00:00')
- Sum amount as total_earnings
- Order by total_earnings DESC
- Limit 3
Output ONLY raw SQL. No markdown. No reasoning.
"""

res = provider.generate(prompt=prompt, model="qwen2.5-coder:7b")
print("RESULT:")
print(res)
