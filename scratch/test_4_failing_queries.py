import sys
sys.path.insert(0, ".")

from app.agent.sql_agent import run_agent

for q in [
    "Which distributor has the highest number of box scans this month?",
    "Which state has the highest number of box scans this month?",
    "Which category has the highest number of box scans this month?",
    "Which category has the lowest number of box scans this month, and which state has the lowest number of box scans?"
]:
    print(f"\n{'='*70}\nRUNNING: {q}\n{'='*70}")
    res = run_agent(q)
    print("Status:", res.get("status"))
    print("Validation Status:", res.get("validation_status"))
    print("SQL:", res.get("sql", {}).get("query") if isinstance(res.get("sql"), dict) else res.get("sql"))
    print("Summary:", res.get("summary"))
    print("Data:", res.get("data", [])[:2])
