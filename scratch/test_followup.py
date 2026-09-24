import json
from app.agent.sql_agent import run_agent
from app.agent.memory_manager import memory_manager

session_id = "test_conv_1"

# Turn 1
q1 = "Show top 3 retailers by earnings for July 2026"
print(f"\n{'='*50}\nTURN 1: {q1}\n{'='*50}")
ctx1 = memory_manager.resolve_session_context(session_id, q1)
hist1 = memory_manager.get_history_summary(session_id)
res1 = run_agent(q1, history_context=hist1, context=ctx1)
print("Turn 1 SQL:", res1.get("sql"))
print("Turn 1 Data:", res1.get("data"))
print("Turn 1 Summary:\n", res1.get("summary"))
memory_manager.add_turn(session_id, q1, res1)

# Turn 2
q2 = "What about June?"
print(f"\n{'='*50}\nTURN 2: {q2}\n{'='*50}")
ctx2 = memory_manager.resolve_session_context(session_id, q2)
hist2 = memory_manager.get_history_summary(session_id)
print("Resolved Context for Turn 2:", ctx2)
print("History summary for Turn 2:", hist2)
res2 = run_agent(q2, history_context=hist2, context=ctx2)
print("Turn 2 SQL:", res2.get("sql"))
print("Turn 2 Data:", res2.get("data"))
print("Turn 2 Summary:\n", res2.get("summary"))
print("Turn 2 Verification:\n", res2.get("verification"))
memory_manager.add_turn(session_id, q2, res2)

# Turn 3
q3 = "Which one earned the most?"
print(f"\n{'='*50}\nTURN 3: {q3}\n{'='*50}")
ctx3 = memory_manager.resolve_session_context(session_id, q3)
hist3 = memory_manager.get_history_summary(session_id)
print("Resolved Context for Turn 3:", ctx3)
res3 = run_agent(q3, history_context=hist3, context=ctx3)
print("Turn 3 SQL:", res3.get("sql"))
print("Turn 3 Data:", res3.get("data"))
print("Turn 3 Summary:\n", res3.get("summary"))
