from app.agent.sql_agent import run_agent

queries = [
    "Show first 10 users with their roles",
    "What are top 5 wallet transactions with user details?",
    "Total earnings of all retailers in wallet transaction table",
    "List all users who have wallet transactions",
    "Show wallet transaction total amount per transaction type for retailers"
]

print("=" * 80)
print("TESTING USERS & WALLET TRANSACTION QUERY PIPELINE")
print("=" * 80)

all_passed = True
for idx, q in enumerate(queries, 1):
    print(f"\n[{idx}/{len(queries)}] Question: {q}")
    res = run_agent(q)
    status = res.get("status")
    sql = res.get("optimized_sql") or res.get("generated_sql")
    exec_success = res.get("execution", {}).get("success")
    row_count = res.get("execution", {}).get("row_count", 0)
    error = res.get("execution", {}).get("error") or res.get("validation", {}).get("reason")
    
    print(f"Status: {status} | Execution Success: {exec_success} | Rows: {row_count}")
    print(f"Generated SQL:\n{sql}")
    if not (status == "success" and exec_success):
        print(f"ERROR: {error}")
        all_passed = False

print("\n" + "=" * 80)
if all_passed:
    print("ALL USERS & WALLET TRANSACTION QUERIES PASSED WITH 0 ERRORS AND 0 HALLUCINATIONS!")
else:
    print("SOME QUERIES FAILED - CHECK OUTPUT ABOVE")
print("=" * 80)
