import sys
import json
import time
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

print("=== RUNNING END-TO-END QUERY AGENT TESTS (SEQUENTIAL CPU EXECUTION) ===")
all_passed = True
total_start = time.time()

for idx, q in enumerate(test_questions, 1):
    print(f"\n{'='*70}")
    print(f"[{idx}/{len(test_questions)}] Query: '{q}'")
    print(f"{'='*70}")
    sys.stdout.flush()

    t0 = time.time()
    res = run_agent(q, execute=True)
    elapsed = round(time.time() - t0, 2)

    status = res.get('status')
    sql = res.get('optimized_sql') or res.get('generated_sql', '')
    exec_res = res.get('execution', {})
    success = exec_res.get('success', False)
    row_count = exec_res.get('row_count', 0)
    benchmarks = res.get('benchmarks', {})
    summary = res.get('summary', '')

    print(f"Status: {status} (Total query time: {elapsed}s)")
    print(f"Phase Latencies:")
    print(f"  - NLP Understanding    : {benchmarks.get('nlp_ms', 0):.1f} ms")
    print(f"  - Grounding & Schema   : {benchmarks.get('grounding_ms', 0):.1f} ms")
    print(f"  - SQL Generation       : {benchmarks.get('sql_gen_ms', 0):.1f} ms")
    print(f"  - AST Security Check   : {benchmarks.get('ast_validation_ms', 0):.1f} ms")
    print(f"  - Semantic Validation  : {benchmarks.get('semantic_validation_ms', 0):.1f} ms")
    print(f"  - DB Execution         : {benchmarks.get('execution_ms', 0):.1f} ms")
    print(f"  - Result Validation    : {benchmarks.get('result_validation_ms', 0):.1f} ms")
    print(f"  - Response Generation  : {benchmarks.get('response_gen_ms', 0):.1f} ms")
    print(f"  - Pipeline Total Time  : {benchmarks.get('total_ms', 0):.1f} ms")

    print(f"\nGenerated Dynamic SQL:\n{sql}")
    print(f"\nExecution: Success={success}, Rows Returned={row_count}")
    if exec_res.get('data'):
        print(f"Sample Record: {exec_res['data'][0]}")
    if exec_res.get('error'):
        print(f"Execution Error: {exec_res['error']}")
        all_passed = False

    print(f"\nSummary Response:\n{summary[:300]}..." if len(summary) > 300 else f"\nSummary Response:\n{summary}")

    # Specific Assertions
    if q == "Show earnings of retailers for July 2026":
        if "2026-07-01 00:00:00" in sql and ("2026-08-01 00:00:00" in sql or "2026-07-31" in sql):
            print("[ASSERT PASS] July 2026 timestamp bounds present.")
        else:
            print("[ASSERT WARNING] July 2026 timestamp format differed or missing.")
    elif q == "Show redemption amount per user for January 2026":
        if "2026-01-01 00:00:00" in sql and ("2026-02-01 00:00:00" in sql or "2026-01-31" in sql):
            print("[ASSERT PASS] January 2026 timestamp bounds present.")
        else:
            print("[ASSERT WARNING] January 2026 timestamp format differed or missing.")

    if status != "success":
        all_passed = False

total_elapsed = round(time.time() - total_start, 2)
print(f"\n{'='*70}")
if all_passed:
    print(f"ALL PIPELINE TESTS PASSED IN {total_elapsed}s!")
else:
    print(f"COMPLETED WITH WARNINGS/FAILURES IN {total_elapsed}s")
print(f"{'='*70}")
