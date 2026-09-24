import json
from app.agent.sql_agent import run_agent
from app.agent.memory_manager import memory_manager

queries = [
    "Show top 3 retailers by earnings for July 2026",
    "Show top 10 retailers by earnings for July 2026",
    "What is the total earnings for July 2026?",
    "What is the average earnings for July 2026?",
    "Show earnings by retailer for July 2026",
    "Compare earnings between June and July 2026",
    "Which retailer has the highest earnings?",
    "Show earnings"
]

session_id = "trace_session"
results = []

for idx, q in enumerate(queries, 1):
    print(f"\n{'='*70}\nTEST {idx}: {q}\n{'='*70}")
    ctx = memory_manager.resolve_session_context(session_id, q)
    hist = memory_manager.get_history_summary(session_id)
    res = run_agent(q, history_context=hist, context=ctx)
    results.append({
        "test": idx,
        "query": q,
        "status": res.get("status"),
        "sql": res.get("sql", {}).get("query") if isinstance(res.get("sql"), dict) else res.get("sql"),
        "row_count": res.get("row_count"),
        "data": res.get("data", [])[:3],
        "summary": res.get("summary", "")[:200]
    })
    if not res.get("is_ambiguous"):
        memory_manager.add_turn(session_id, q, res)

# Now test follow-ups 9 & 10 continuing from test 1:
print(f"\n{'='*70}\nRESETTING SESSION FOR FOLLOW-UP TEST 9 & 10\n{'='*70}")
s2 = "followup_session"
q_base = "Show top 3 retailers by earnings for July 2026"
c_base = memory_manager.resolve_session_context(s2, q_base)
r_base = run_agent(q_base, context=c_base)
memory_manager.add_turn(s2, q_base, r_base)

q9 = "What about June?"
print(f"\nTEST 9: {q9}")
c9 = memory_manager.resolve_session_context(s2, q9)
h9 = memory_manager.get_history_summary(s2)
r9 = run_agent(q9, history_context=h9, context=c9)
results.append({
    "test": 9,
    "query": q9,
    "status": r9.get("status"),
    "sql": r9.get("sql", {}).get("query") if isinstance(r9.get("sql"), dict) else r9.get("sql"),
    "row_count": r9.get("row_count"),
    "data": r9.get("data", []),
    "summary": r9.get("summary")
})
memory_manager.add_turn(s2, q9, r9)

q10 = "Which one earned the most?"
print(f"\nTEST 10: {q10}")
c10 = memory_manager.resolve_session_context(s2, q10)
h10 = memory_manager.get_history_summary(s2)
r10 = run_agent(q10, history_context=h10, context=c10)
results.append({
    "test": 10,
    "query": q10,
    "status": r10.get("status"),
    "sql": r10.get("sql", {}).get("query") if isinstance(r10.get("sql"), dict) else r10.get("sql"),
    "row_count": r10.get("row_count"),
    "data": r10.get("data", []),
    "summary": r10.get("summary")
})

print("\n\n" + "="*80)
print("TRACE SUMMARY TABLE")
print("="*80)
for r in results:
    print(f"[{r['test']}] {r['query']}")
    print(f"    Status: {r['status']} | Rows: {r['row_count']}")
    print(f"    SQL: {r['sql']}")
    print(f"    Data: {r['data']}")
    print(f"    Summary: {r['summary']}")
    print("-" * 60)
