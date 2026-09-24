import sys
import json
import time

import os
sys.path.insert(0, os.path.abspath("."))

from app.agent.sql_agent import run_agent

t0 = time.time()
print("Calling run_agent...")
res = run_agent("Top 3 retailers by earnings in July 2026", execute=True)
print(f"Elapsed: {time.time() - t0:.2f}s")
print("STATUS:", res.get("status"))
print("QUESTION:", res.get("question"))
print("INTENT:", json.dumps(res.get("intent"), indent=2))
print("EXECUTION PLAN:", json.dumps(res.get("execution_plan"), indent=2))
print("SQL:", json.dumps(res.get("sql"), indent=2))
print("RESULT:", json.dumps(res.get("result"), indent=2))
print("VERIFICATION:", json.dumps(res.get("verification"), indent=2))
print("ANALYSIS:", json.dumps(res.get("analysis"), indent=2))
print("ANSWER:", json.dumps(res.get("answer"), indent=2))
print("PERFORMANCE:", json.dumps(res.get("performance"), indent=2))
