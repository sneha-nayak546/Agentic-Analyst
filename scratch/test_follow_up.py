import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
import json
from app.agent.memory_manager import memory_manager
from app.agent.sql_agent import run_agent

session_id = "test_session_followup"
memory_manager.clear_session(session_id)

print("\n--- TURN 1: 'Show top 3 retailers by earnings for July 2026' ---")
ctx1 = memory_manager.resolve_session_context(session_id, "Show top 3 retailers by earnings for July 2026")
res1 = run_agent("Show top 3 retailers by earnings for July 2026", context=ctx1)
print("Turn 1 Status:", res1.get("status"))
print("Turn 1 SQL:", res1.get("sql", {}).get("query"))
print("Turn 1 Rows:", len(res1.get("result", {}).get("rows", [])))
print("Turn 1 Answer:", res1.get("answer", {}).get("text"))
memory_manager.add_turn(session_id, "Show top 3 retailers by earnings for July 2026", res1)

print("\n--- TURN 2: 'What about June?' ---")
ctx2 = memory_manager.resolve_session_context(session_id, "What about June?")
print("Resolved context for Turn 2:")
print(json.dumps({k: v for k, v in ctx2.items() if k not in ['last_rows']}, indent=2))

res2 = run_agent("What about June?", context=ctx2)
print("Turn 2 Status:", res2.get("status"))
print("Turn 2 SQL:", res2.get("sql", {}).get("query"))
print("Turn 2 Rows:", len(res2.get("result", {}).get("rows", [])))
print("Turn 2 Answer:", res2.get("answer", {}).get("text"))
