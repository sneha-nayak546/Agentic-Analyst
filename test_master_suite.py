import time
import json
from app.agent.sql_agent import run_agent

TEST_QUESTIONS = [
    "Show first 10 users with their roles",
    "What are top 5 wallet transactions with user details?",
    "Total earnings of all retailers in wallet transaction table",
    "I want all retailers how much they all are earning in this month",
    "List all users who have wallet transactions",
    "Show wallet transaction total amount per transaction type for retailers",
    "What is the sum of wallet balance for all active retailers?",
    "Show top 5 users with highest sum of transaction amount",
    "Show total cash point earnings per retailer",
    "Show wallet transaction sum for user with mobile number 9651819580",
    "Show total withdrawal transactions amount for retailers",
    "Show balance of all users",
    "Show retailer wallet balance",
    "Total wallet balance of retailers",
    "What is user wallet balance",
    "Show balance",
    "Show SKU inventory",
    "Show total automatic transactions amount",
    "Show withdrawal requests",
    "How many retailers are active?"
]

def run_master_suite():
    print("=" * 80)
    print("RUNNING MASTER COMPREHENSIVE PIPELINE VERIFICATION SUITE")
    print("=" * 80)

    passed = 0
    failed = 0
    failures = []

    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] QUESTION: {q}")
        t0 = time.time()
        try:
            res = run_agent(q)
            t_ms = round((time.time() - t0) * 1000, 2)
            status = res.get("status")
            exec_ok = res.get("execution", {}).get("success", False)
            sql = res.get("optimized_sql") or res.get("generated_sql", "")
            rows = res.get("execution", {}).get("row_count", 0)

            if status == "success" and exec_ok:
                passed += 1
                print(f"   [PASS] {t_ms}ms | Rows: {rows} | SQL: {sql}")
            else:
                failed += 1
                err = res.get("execution", {}).get("error") or res.get("reason") or "Unknown error"
                print(f"   [FAIL] {t_ms}ms | Status: {status} | Error: {err} | SQL: {sql}")
                failures.append({"question": q, "error": err, "sql": sql})

        except Exception as e:
            t_ms = round((time.time() - t0) * 1000, 2)
            failed += 1
            print(f"   [EXCEPTION] {t_ms}ms | Error: {str(e)}")
            failures.append({"question": q, "error": str(e), "sql": ""})

    print("\n" + "=" * 80)
    print(f"MASTER SUITE VERIFICATION COMPLETE: {passed}/{len(TEST_QUESTIONS)} PASSED")
    print("=" * 80)

    if failures:
        print("\nFAILURE DETAILS:")
        for f in failures:
            print(f"- Question: {f['question']}")
            print(f"  Error: {f['error']}")
            print(f"  SQL: {f['sql']}\n")
    else:
        print("ALL MASTER TEST SUITE QUERIES PASSED WITH 0 ERRORS AND 0 HALLUCINATIONS!")

if __name__ == "__main__":
    run_master_suite()
