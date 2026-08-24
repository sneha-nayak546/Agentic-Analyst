import time
from app.agent.sql_agent import run_agent

test_queries = [
    "Show first 10 users with their roles",
    "What are top 5 wallet transactions with user details?",
    "Total earnings of all retailers in wallet transaction table",
    "List all users who have wallet transactions",
    "Show wallet transaction total amount per transaction type for retailers",
    "What is the sum of wallet balance for all active retailers?",
    "Show top 5 users with highest sum of transaction amount",
    "Show total cash point earnings per retailer",
    "Show wallet transaction sum for user with mobile number 9651819580",
    "Show total withdrawal transactions amount for retailers"
]

print("=" * 80)
print("DEEP VERIFICATION SUITE: USER & WALLET TRANSACTION PIPELINE")
print("=" * 80)

passed_count = 0
failed_queries = []

for idx, q in enumerate(test_queries, 1):
    print(f"\n[{idx}/{len(test_queries)}] Question: {q}")
    t0 = time.time()
    res = run_agent(q)
    elapsed = round(time.time() - t0, 2)
    
    status = res.get("status")
    sql = res.get("optimized_sql") or res.get("generated_sql")
    exec_success = res.get("execution", {}).get("success", False)
    row_count = res.get("execution", {}).get("row_count", 0)
    error = res.get("execution", {}).get("error") or res.get("validation", {}).get("reason")
    
    print(f"Status: {status} | DB Exec Success: {exec_success} | Rows Returned: {row_count} | Time: {elapsed}s")
    print(f"Generated SQL:\n{sql}")
    
    if status == "success" and exec_success:
        passed_count += 1
        print("RESULT: PASSED [OK]")
    else:
        failed_queries.append((q, error, sql))
        print(f"RESULT: FAILED [ERROR]: {error}")

print("\n" + "=" * 80)
print(f"VERIFICATION SUMMARY: {passed_count}/{len(test_queries)} QUERIES PASSED")
print("=" * 80)

if failed_queries:
    print("\nFAILED QUERIES DETAILS:")
    for f_q, f_err, f_sql in failed_queries:
        print(f"- Question: {f_q}\n  Error: {f_err}\n  SQL: {f_sql}\n")
    exit(1)
else:
    print("ALL USER & WALLET TRANSACTION QUERIES PASSED WITH 100% SUCCESS AND ZERO ERRORS!")
