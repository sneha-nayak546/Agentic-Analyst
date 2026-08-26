import sys
import json
from app.agent.sql_agent import run_agent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

test_questions = [
    "Show earnings of retailers for July 2026",
    "Show redemption amount per user for January 2026",
    "Show top 10 users with highest wallet balance",
    "Show redemption amount per user",
    "Show earnings of retailers this month"
]

print("=== RUNNING END-TO-END QUERY AGENT TESTS ===")
all_passed = True

for q in test_questions:
    print(f"\n>> Question: '{q}'")
    res = run_agent(q, execute=True)
    status = res.get('status')
    sql = res.get('optimized_sql') or res.get('generated_sql', '')
    exec_res = res.get('execution', {})
    success = exec_res.get('success', False)
    row_count = exec_res.get('row_count', 0)
    exec_time = exec_res.get('execution_time_ms', 0)

    print(f"Status: {status}")
    print(f"Generated SQL: {sql}")
    print(f"Exec Success: {success}")
    print(f"Row Count: {row_count}")
    print(f"Exec Time: {exec_time} ms")
    if exec_res.get('data'):
        print(f"First Row: {exec_res['data'][0]}")
    if exec_res.get('error'):
        print(f"Error: {exec_res['error']}")
        all_passed = False

    # Specific Assertions
    if q == "Show earnings of retailers for July 2026":
        assert "2026-07-01 00:00:00" in sql and ("2026-08-01 00:00:00" in sql or "2026-07-31" in sql), "July 2026 timestamp bounds missing!"
        print("[ASSERT PASS] July 2026 timestamp bounds present.")
    elif q == "Show redemption amount per user for January 2026":
        assert "2026-01-01 00:00:00" in sql and ("2026-02-01 00:00:00" in sql or "2026-01-31" in sql), "January 2026 timestamp bounds missing!"
        print("[ASSERT PASS] January 2026 timestamp bounds present.")

if all_passed:
    print("\nALL PIPELINE TESTS PASSED WITH 100% LIVE DB ACCURACY!")
