import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
import time
import json
from app.agent.sql_agent import run_agent

print("Executing test for: 'Show top 3 retailers by earnings for July 2026'...")
t0 = time.time()
res = run_agent("Show top 3 retailers by earnings for July 2026")
total_ms = round((time.time() - t0) * 1000, 2)

print("\n" + "="*50)
print("TEST EXECUTION REPORT")
print("="*50)
print("Status:", res.get("status"))
print("Validation Status:", res.get("validation_status"))
print("Result Confidence:", res.get("result_confidence"))
print("\nStructured Intent:")
print(json.dumps(res.get("intent"), indent=2))
print("\nStructured SQL:")
print(json.dumps(res.get("sql"), indent=2))
print("\nStructured Result:")
print(json.dumps(res.get("result"), indent=2))
print("\nStructured Verification:")
print(json.dumps(res.get("verification"), indent=2))
print("\nNatural Language Answer:")
print(res.get("answer", {}).get("text") or res.get("summary"))
print("\nPerformance Profile (ms):")
print(json.dumps(res.get("performance"), indent=2))
print("Total Measured Python Time (ms):", total_ms)
