from app.agent.sql_agent import run_agent

questions = [
    ("TEST 6", "Which distributor has the highest number of box scans this month?"),
    ("TEST 7", "Which retailer under which distributor has scanned the highest number of boxes this month?"),
    ("TEST 8", "Which state has the highest number of box scans this month?"),
    ("TEST 9", "Which category has the highest number of box scans this month?"),
    ("TEST 11", "Which distributor has the lowest number of box scans this month?"),
    ("TEST 12", "Which retailer has scanned the highest number of boxes this month?"),
    ("TEST 13", "Which category has the highest box scan count in July 2026?")
]

for tid, q in questions:
    print(f"\n==================== {tid}: {q} ====================")
    res = run_agent(q, execute=True)
    print("STATUS:", res.get("status"))
    print("SQL:", res.get("sql_query"))
    print("DATA:", res.get("data"))
    print("SUMMARY:", res.get("summary"))
