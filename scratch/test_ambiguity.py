import sys, os
sys.path.insert(0, os.path.abspath("."))
from app.agent.sql_agent import run_agent

res = run_agent("Show earnings")
print("Status:", res.get("status"))
print("Is Ambiguous:", res.get("is_ambiguous"))
print("Clarification:", res.get("clarification"))
print("Options:", res.get("options"))
