from app.agent.sql_agent import run_agent

res = run_agent("Compare total wallet transactions between July and June 2026", execute=True)
print("=== RESULT ===")
print("SQL:", res.get("sql_query"))
print("Data:", res.get("data"))
print("Summary:", res.get("summary"))
