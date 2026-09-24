import os
import sys
import time
import json
import ollama
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
model_name = os.getenv("OLLAMA_MODEL", os.getenv("QWEN_MODEL", "qwen2.5-coder:7b")).strip("\"'")

print("=" * 60)
print("TESTING NATIVE OLLAMA CLIENT")
print(f"Host:  {host}")
print(f"Model: {model_name}")
print("=" * 60)

client = ollama.Client(host=host)

test_question = "Show all retailers"

prompt = f"""You are the NLP Understanding module of the JGH Intelligence Engine.
Analyze the user's question and extract the complete business requirements.

User Question: "{test_question}"

Respond ONLY with a JSON object in this exact schema, with no markdown or formatting outside JSON:
{{
  "original_question": "{test_question}",
  "intent": "list_entities",
  "entities": ["retailer"],
  "entity_roles": {{"retailer": "retailer"}},
  "relationships": [],
  "specific_ids": {{}},
  "metrics": [],
  "aggregation": [],
  "filters": [],
  "date_period": null,
  "relative_dates": null,
  "comparisons": [],
  "grouping": [],
  "sorting": [],
  "ranking": null,
  "limit": null,
  "requested_columns": ["id", "name", "phone", "state_id", "status"],
  "output_format": "table",
  "conditions": [],
  "clarification_required": false,
  "clarification_reason": null
}}
"""

t0 = time.time()
try:
    response = client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a precise JSON-only extraction engine. Always output pure valid JSON."},
            {"role": "user", "content": prompt}
        ],
        format="json",
        options={"temperature": 0.0}
    )
    t1 = time.time()
    elapsed = t1 - t0

    content = response["message"]["content"].strip()
    print("\n[HTTP/API SUCCESS]: True")
    print(f"[RESPONSE TIME]:   {elapsed:.2f} seconds")
    
    parsed = json.loads(content)
    print("[VALID JSON]:      True")
    print("\n[GENERATED BUSINESS REQUIREMENT]:")
    print(json.dumps(parsed, indent=2))

except Exception as e:
    t1 = time.time()
    print(f"\n[HTTP/API SUCCESS]: False (Failed in {t1-t0:.2f}s)")
    print(f"[ERROR]: {e}")
    sys.exit(1)
