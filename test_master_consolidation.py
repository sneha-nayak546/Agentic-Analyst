from app.agent.sql_agent import run_agent
from app.utils.sql_cleaner import clean_sql

def test_master_consolidation():
    # 1. Test clean_sql unit edge-cases
    raw_bad_sql = "SELECT u.id, u.name, FROM users u WHERE u.user_role = 2, GROUP BY u.id, u.name,;"
    cleaned = clean_sql(raw_bad_sql)
    print("Sanitizer Unit Test:")
    print("RAW BAD SQL :", raw_bad_sql)
    print("CLEANED SQL :", cleaned)
    assert not cleaned.endswith(",;"), "Trailing comma before semicolon was not stripped!"
    assert ", GROUP BY" not in cleaned, "Trailing comma before GROUP BY clause was not stripped!"
    print("Sanitizer Unit Test PASSED!\n" + "=" * 70)

    # 2. Test full agent pipeline
    question = "who all are retailers are available in the users table, for those retailers how much they all are earning in this month :- cash_point, referral earning , topup , coupon _reedom"
    print(f"Testing Agent Pipeline with Question:\n'{question}'\n")
    
    res = run_agent(question)
    
    status = res.get("status")
    gen_sql = res.get("generated_sql", "")
    opt_sql = res.get("optimized_sql", "")
    exec_success = res.get("execution", {}).get("success")
    row_count = res.get("execution", {}).get("row_count", 0)
    error = res.get("execution", {}).get("error") or res.get("validation", {}).get("reason")

    print("=" * 70)
    print("STATUS          :", status)
    print("OPTIMIZED SQL   :\n", opt_sql)
    print("EXECUTION SUCCESS:", exec_success)
    print("ROW COUNT       :", row_count)
    if res.get("execution", {}).get("data"):
        print("SAMPLE ROW      :", res["execution"]["data"][0])
    print("=" * 70)

    # Assertions
    assert not opt_sql.endswith(",;"), "Optimized SQL has trailing comma before semicolon!"
    assert ", GROUP BY" not in opt_sql, "Optimized SQL has trailing comma before GROUP BY!"
    assert "user_role = 2" in opt_sql or "user_role=2" in opt_sql, "Retailer role filter missing!"
    assert "reference_type" in opt_sql, "reference_type missing from optimized SQL!"
    assert exec_success is True, f"Execution failed: {error}"

    print("\nMASTER CONSOLIDATION TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_master_consolidation()
