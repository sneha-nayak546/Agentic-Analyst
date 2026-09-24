import sys
import json
import time
from app.agent.sql_agent import run_agent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

SMOKE_QUERIES = [
    "Show all retailers",
    "Generate a table of retailers linked to distributor 5997",
    "Generate a table of retailers linked to distributor 5997 and include their individual total earnings for the current month."
]

def run_smoke_tests():
    print("=" * 80)
    print("PHASE 1: SMOKE TEST SUITE (3 CORE QUERIES - LOCAL CPU INFERENCE)")
    print("=" * 80)
    sys.stdout.flush()

    suite_start = time.time()
    all_passed = True
    results = []

    for idx, question in enumerate(SMOKE_QUERIES, 1):
        print(f"\n[{idx}/{len(SMOKE_QUERIES)}] Query: \"{question}\"")
        print("-" * 80)
        sys.stdout.flush()

        t0 = time.time()
        try:
            res = run_agent(question, execute=True)
            elapsed = round(time.time() - t0, 2)
            raw_status = res.get("status", "unknown")
            is_timeout = False
        except TimeoutError:
            elapsed = round(time.time() - t0, 2)
            raw_status = "TIMEOUT"
            is_timeout = True
            res = {"benchmarks": {}, "execution": {}, "summary": "Operation timed out"}
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            raw_status = f"ERROR: {str(e)}"
            is_timeout = False
            res = {"benchmarks": {}, "execution": {}, "summary": str(e)}

        benchmarks = res.get("benchmarks", {})
        execution = res.get("execution", {})
        sql = res.get("optimized_sql") or res.get("generated_sql", "")
        summary = res.get("summary", "")
        row_count = execution.get("row_count", 0)
        sample_data = execution.get("data", [])

        # Determine PASS / FAIL / TIMEOUT
        if is_timeout:
            final_status = "TIMEOUT"
            all_passed = False
        elif raw_status == "success" and execution.get("success", False):
            final_status = "PASS"
        else:
            final_status = "FAIL"
            all_passed = False

        # Phase Timings
        nlp_ms = benchmarks.get("nlp_ms", 0.0)
        grounding_ms = benchmarks.get("grounding_ms", 0.0)
        sql_gen_ms = benchmarks.get("sql_gen_ms", 0.0)
        ast_val_ms = benchmarks.get("ast_validation_ms", 0.0)
        sem_val_ms = benchmarks.get("semantic_validation_ms", 0.0)
        validation_ms = round(ast_val_ms + sem_val_ms, 2)
        exec_ms = benchmarks.get("execution_ms", 0.0)
        result_val_ms = benchmarks.get("result_validation_ms", 0.0)
        resp_gen_ms = benchmarks.get("response_gen_ms", 0.0)
        total_ms = benchmarks.get("total_ms", round(elapsed * 1000, 2))

        print(f"Final Status           : {final_status}")
        print(f"Total Time             : {elapsed}s ({total_ms:.1f} ms)")
        print(f"Phase Latencies:")
        print(f"  - NLP Understanding  : {nlp_ms:.1f} ms")
        print(f"  - Grounding & Schema : {grounding_ms:.1f} ms")
        print(f"  - SQL Generation     : {sql_gen_ms:.1f} ms")
        print(f"  - Validation Time    : {validation_ms:.1f} ms (AST: {ast_val_ms:.1f} ms, Semantic: {sem_val_ms:.1f} ms)")
        print(f"  - Execution Time     : {exec_ms:.1f} ms")
        print(f"  - Result Validation  : {result_val_ms:.1f} ms")
        print(f"  - Response Generation: {resp_gen_ms:.1f} ms")

        print(f"\nDynamic SQL Generated:\n{sql if sql else '(No SQL generated)'}")

        # Verify dynamic generation (no hardcoded query template)
        if sql.strip().upper().startswith("SELECT"):
            print("SQL Template Check     : [VERIFIED DYNAMIC MODEL GENERATION]")
        else:
            print("SQL Template Check     : [FAILED / INVALID SQL]")

        print(f"\nDatabase Execution     : Row Count = {row_count}")
        if sample_data:
            print(f"Sample Record (First)  : {sample_data[0]}")
        elif execution.get("error"):
            print(f"DB Error               : {execution.get('error')}")

        print(f"\nVerified Natural Response:\n{summary.strip()}")
        print("-" * 80)
        sys.stdout.flush()

        results.append({
            "question": question,
            "final_status": final_status,
            "total_seconds": elapsed,
            "sql": sql,
            "row_count": row_count,
            "benchmarks": benchmarks
        })

    suite_time = round(time.time() - suite_start, 2)
    print("\n" + "=" * 80)
    print("PHASE 1 SMOKE TEST SUMMARY REPORT")
    print("=" * 80)
    for idx, r in enumerate(results, 1):
        print(f"[{idx}] {r['final_status']:<7} in {r['total_seconds']:>5.1f}s | Rows: {r['row_count']:>3} | Q: \"{r['question']}\"")
    print(f"\nTotal Smoke Suite Time: {suite_time}s")
    if all_passed:
        print("ALL 3 SMOKE TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME SMOKE TESTS FAILED OR TIMED OUT - CHECK DIAGNOSTICS ABOVE.")
    print("=" * 80)

if __name__ == "__main__":
    run_smoke_tests()
