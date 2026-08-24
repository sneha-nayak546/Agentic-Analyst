from app.agent.sql_agent import run_agent

queries = [
    "Show wallet transactions of January 2026",
    "List top 5 companies"
]

for q in queries:
    print(f"\n==========================================")
    print(f"QUERY: {q}")
    print(f"==========================================")
    res = run_agent(q, execute=True)
    print("STATUS:", res.get("status"))
    print("SQL:", res.get("optimized_sql"))
    print("ROWS:", res.get("execution", {}).get("row_count"))
    if res.get("execution", {}).get("data"):
        print("SAMPLE ROW:", res["execution"]["data"][0])
    if res.get("execution", {}).get("error"):
        print("ERROR:", res["execution"]["error"])
