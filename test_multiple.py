import json
from app.agent.sql_agent import run_agent

queries = [
    "Show wallet transactions of January 2026",
    "List 5 approved retailers",
    "Show total withdrawal requests by status",
    "List 5 automatic transactions with IMPS transfer type"
]

results = []
for q in queries:
    res = run_agent(q, execute=True)
    results.append({
        "question": q,
        "status": res.get("status"),
        "sql": res.get("optimized_sql"),
        "row_count": res.get("execution", {}).get("row_count"),
        "sample": res.get("execution", {}).get("data", [])[:2],
        "error": res.get("execution", {}).get("error")
    })

with open("test_queries_summary.json", "w") as f:
    json.dump(results, f, indent=2)

print("ALL TEST QUERIES COMPLETED")
