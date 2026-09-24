import json
from app.agent.sql_agent import run_agent

question = "Show top 3 retailers by earnings for July 2026"
print(f"=== TESTING PIPELINE FOR: {question} ===")
result = run_agent(question)
print("\n=== PIPELINE RETURN DICT KEYS ===")
print(list(result.keys()))

print("\n=== STATUS ===")
print("status:", result.get("status"))
print("validation_status:", result.get("validation_status"))

print("\n=== INTENT ===")
print(json.dumps(result.get("intent"), indent=2))

print("\n=== SQL ===")
print("sql:", result.get("sql"))
print("sql_query:", result.get("sql_query"))

print("\n=== DATA / ROWS ===")
print("row_count:", result.get("row_count"))
print("data:", result.get("data"))

print("\n=== VERIFICATION ===")
print(json.dumps(result.get("verification"), indent=2))

print("\n=== ANSWER ===")
print(json.dumps(result.get("answer"), indent=2))
print("summary:", result.get("summary"))

print("\n=== PERFORMANCE ===")
print(json.dumps(result.get("performance"), indent=2))
