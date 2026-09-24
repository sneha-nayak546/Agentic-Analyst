import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
from app.llm.provider import GroqProvider

p = GroqProvider()
q_clean = "Show top 3 retailers by earnings for July 2026"
ctx_str = "None"

prompt = f"""You are the NLP Understanding module of the JGH Intelligence Engine.
Extract the structured business requirements from the question into pure JSON.

Question: "{q_clean}"
Active Context: {ctx_str}

JSON schema to return:
{{
  "original_question": "{q_clean}",
  "intent": "ranking | aggregate_analytics | lookup | comparison | list_entities",
  "entities": ["retailer", "distributor", "wallet_transaction", "sku_inventories"],
  "metrics": ["earnings", "count", "balance"],
  "aggregation": ["SUM", "COUNT", "AVG"],
  "filters": [{{"field": "...", "operator": "=", "value": "..."}}],
  "periods": ["July 2026", "June 2026"],
  "comparison": null,
  "ranking": "top 3",
  "limit": 3,
  "sorting": ["DESC"],
  "grouping": [],
  "clarification_required": false
}}
RULES:
1. For retailers, entities = ["retailer"]. For distributors, entities = ["distributor"].
2. If Active Context has entity/metric and the question is a follow-up (e.g. 'What about June?'), inherit entities, metrics, ranking, and limit, and set periods to the new timeframe.
3. Earnings = metric ["earnings"], aggregation ["SUM"].
4. Do NOT invent unrequested entities, rankings, or group-by dimensions.
"""
system_prompt = "You are a precise NLP parser enforcing the strict Business Requirement Contract. Always respond with pure valid JSON."

try:
    res = p.generate(prompt, system_prompt=system_prompt, model="openai/gpt-oss-20b", format_json=True, max_tokens=1200)
    print("SUCCESS:\n", res)
except Exception as e:
    print("ERROR:", e)
