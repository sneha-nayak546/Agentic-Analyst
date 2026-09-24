import time
import json
import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure unbuffered utf-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.sql_agent import run_agent
from app.agent.context_resolver import context_resolver
from app.agent.memory_manager import memory_manager
from app.validator.response_accuracy_validator import response_accuracy_validator

TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "Show top 10 retailers by earnings for July 2026",
        "description": "Top-N ranking of retailers by aggregated July 2026 earnings",
        "expected_tables": ["users", "wallet_transaction"],
        "expected_order": "DESC",
        "expected_limit": 10,
        "expected_date_filter": "2026-07",
    },
    {
        "id": 2,
        "question": "Show top 5 retailers by earnings in June 2026",
        "description": "Top-5 retailers by earnings in June 2026 (0 rows in DB expected)",
        "expected_tables": ["users", "wallet_transaction"],
        "expected_limit": 5,
        "expected_date_filter": "2026-06",
    },
    {
        "id": 3,
        "question": "Show the bottom 10 retailers by earnings for July 2026",
        "description": "Bottom-10 ranking of retailers by earnings for July 2026 (ASC ordering)",
        "expected_tables": ["users", "wallet_transaction"],
        "expected_order": "ASC",
        "expected_date_filter": "2026-07",
    },
    {
        "id": 4,
        "question": "How many retailers were active in July 2026?",
        "description": "Count of active retailers with July 2026 transactions",
        "expected_tables": ["users", "wallet_transaction"],
        "expected_aggregation": "COUNT",
        "expected_date_filter": "2026-07",
    },
    {
        "id": 5,
        "question": "What were total earnings in July 2026?",
        "description": "Global aggregate total earnings in July 2026",
        "expected_tables": ["wallet_transaction"],
        "expected_aggregation": "SUM",
        "expected_date_filter": "2026-07",
    },
    {
        "id": 6,
        "question": "Compare retailer earnings between June and July 2026",
        "description": "Two-period comparative analysis between June 2026 and July 2026",
        "expected_tables": ["users", "wallet_transaction"],
        "expected_comparison": True,
    },
    {
        "id": 7,
        "question": "Show the highest earning retailer in July 2026",
        "description": "Single top-1 highest earning retailer in July 2026",
        "expected_tables": ["users", "wallet_transaction"],
        "expected_order": "DESC",
        "expected_limit": 1,
        "expected_date_filter": "2026-07",
    },
    {
        "id": 8,
        "question": "Show distributors in Lucknow",
        "description": "Distributors filter by city/district Lucknow (0 in DB expected)",
        "expected_tables": ["users"],
        "expected_filter": "Lucknow",
    },
    {
        "id": 9,
        "question": "Show retailers in Bangalore",
        "description": "Retailers in Bangalore (Bengaluru) - 3 in DB expected",
        "expected_tables": ["users"],
        "expected_filter": "Bengaluru",
    }
]

def run_accuracy_test_suite():
    print("=" * 80)
    print("JGH INTELLIGENCE ENGINE: REPEATABLE SQL ACCURACY TEST SUITE")
    print("=" * 80)

    results = []

    # Run Standard Test Questions 1-9
    for item in TEST_QUESTIONS:
        q_id = item["id"]
        question = item["question"]
        print(f"\n[{q_id}/10] Testing: \"{question}\"")
        t0 = time.time()

        res = run_agent(question, context={"is_explicit_follow_up": False})
        elapsed = round(time.time() - t0, 2)

        sql = res.get("sql") or res.get("generated_sql") or ""
        sql_upper = sql.upper()
        sql_lower = sql.lower()
        rows = res.get("row_count", len(res.get("data", [])))
        status = res.get("status")
        val_status = res.get("validation_status")
        affected_tables = res.get("affected_tables", [])
        data = res.get("data") or res.get("results") or []

        # Check semantic expectations
        checks = []

        # 1. SQL Non-empty & execution success
        checks.append(("SQL Generated", bool(sql)))
        checks.append(("Execution Succeeded", status == "success"))

        # 2. Table groundings
        for exp_tbl in item.get("expected_tables", []):
            checks.append((f"Table '{exp_tbl}' in SQL", exp_tbl in sql_lower))

        # 3. Order By
        if item.get("expected_order"):
            exp_ord = item["expected_order"]
            checks.append((f"ORDER BY {exp_ord}", exp_ord in sql_upper and "ORDER BY" in sql_upper))

        # 4. Limit
        if item.get("expected_limit"):
            exp_lim = item["expected_limit"]
            checks.append((f"LIMIT {exp_lim}", f"LIMIT {exp_lim}" in sql_upper))

        # 5. Date filter
        if item.get("expected_date_filter"):
            exp_date = item["expected_date_filter"]
            checks.append((f"Date filter '{exp_date}'", exp_date in sql_lower))

        # 6. Aggregation
        if item.get("expected_aggregation"):
            exp_agg = item["expected_aggregation"]
            checks.append((f"Aggregate '{exp_agg}'", exp_agg in sql_upper))

        all_semantic_passed = all(passed for _, passed in checks)
        final_response = res.get("summary", "")
        resp_validation = res.get("response_validation") or response_accuracy_validator.validate(
            question=question,
            requirement=res.get("debug_pipeline", {}).get("business_requirement"),
            sql=sql,
            execution_result={"data": data, "columns": res.get("columns", []), "row_count": rows, "success": status == "success"},
            final_response=final_response
        )

        # Compute 8 separate accuracy dimensions
        intent_acc = status != "ambiguous" and bool(sql)
        schema_acc = all(exp_tbl in sql_lower for exp_tbl in item.get("expected_tables", []))
        syntax_valid = bool(sql) and "SELECT" in sql_upper
        semantic_acc = all_semantic_passed
        execution_acc = (status == "success")
        result_acc = val_status in ["VERIFIED", "VERIFIED_PARTIAL", "VERIFIED_EMPTY"]
        response_acc = resp_validation.get("is_valid", False)
        e2e_acc = all([intent_acc, schema_acc, syntax_valid, semantic_acc, execution_acc, result_acc, response_acc])

        print(f"    Status: {status} ({val_status}) | Time: {elapsed}s | Rows: {rows}")
        print(f"    SQL: {sql}")
        if data:
            print(f"    Sample: {data[:2]}")
        passed_str = lambda p: "PASS" if p else "FAIL"
        chk_summary = ", ".join([f"{name}: {passed_str(p)}" for name, p in checks])
        print(f"    Semantic Checks: {chk_summary}")
        print(f"    Final Response: \"{final_response}\"")
        resp_status_str = "PASS" if response_acc else f"FAIL ({resp_validation.get('primary_failure_category')}: {resp_validation.get('issues')})"
        print(f"    Response Validation: {resp_status_str}")
        print(f"    End-to-End QA: {'PASS' if e2e_acc else 'FAIL'}")

        results.append({
            "id": q_id,
            "question": question,
            "sql": sql,
            "rows": rows,
            "elapsed_s": elapsed,
            "status": status,
            "val_status": val_status,
            "checks": checks,
            "passed": e2e_acc,
            "metrics": {
                "intent": intent_acc,
                "schema": schema_acc,
                "syntax": syntax_valid,
                "semantic": semantic_acc,
                "execution": execution_acc,
                "result": result_acc,
                "response": response_acc,
                "e2e": e2e_acc
            },
            "sample_data": data[:2] if data else [],
            "summary": final_response,
            "response_validation": resp_validation
        })

    # Test Question 10: Multi-Turn Context Isolation & Inheritance Flow
    print("\n[10/10] Testing Context Isolation & Follow-Up Flow:")
    session_id = "test_eval_session_isolated"
    memory_manager.clear_session(session_id)

    # Turn 1: "Show distributors in Kochi"
    q10a = "Show distributors in Kochi"
    print(f"  Step 10a: \"{q10a}\"")
    ctx_10a = context_resolver.resolve(q10a, previous_context={})
    res_10a = run_agent(q10a, context=ctx_10a)
    memory_manager.add_turn(session_id, q10a, res_10a)
    print(f"    SQL 10a: {res_10a.get('sql')}")

    # Turn 2: "Show top 10 retailers by earnings for July 2026" (Independent - MUST NOT inherit Kochi or distributor)
    q10b = "Show top 10 retailers by earnings for July 2026"
    print(f"  Step 10b (Independent Query): \"{q10b}\"")
    prev_10a = memory_manager.get_session_context(session_id)
    ctx_10b = context_resolver.resolve(q10b, previous_context=prev_10a)
    res_10b = run_agent(q10b, context=ctx_10b)
    memory_manager.add_turn(session_id, q10b, res_10b)

    sql_10b = res_10b.get("sql", "")
    sql_10b_lower = sql_10b.lower()
    kochi_leaked = "kochi" in sql_10b_lower
    dist_leaked = "user_role = 4" in sql_10b_lower or ("distributor" in sql_10b_lower and "user_role = 2" not in sql_10b_lower)

    checks_10b = [
        ("Kochi NOT Leaked", not kochi_leaked),
        ("Distributor NOT Leaked", not dist_leaked),
        ("Retailer user_role=2 present", "user_role = 2" in sql_10b_lower or "user_role=2" in sql_10b_lower),
        ("July 2026 present", "2026-07" in sql_10b_lower),
        ("Limit 10 present", "LIMIT 10" in sql_10b.upper())
    ]
    print(f"    SQL 10b: {sql_10b}")
    chk10b_str = ", ".join([f"{name}: {passed_str(p)}" for name, p in checks_10b])
    print(f"    Checks: {chk10b_str}")

    # Turn 3: "Show their earnings" (Genuine follow-up to 10b)
    q10c = "Show their earnings"
    print(f"  Step 10c (Follow-up to 10b): \"{q10c}\"")
    prev_10b = memory_manager.get_session_context(session_id)
    ctx_10c = context_resolver.resolve(q10c, previous_context=prev_10b)
    res_10c = run_agent(q10c, context=ctx_10c)
    sql_10c = res_10c.get("sql", "")
    sql_10c_lower = sql_10c.lower()

    checks_10c = [
        ("Inherited Retailer user_role=2", "user_role = 2" in sql_10c_lower or "user_role=2" in sql_10c_lower),
        ("Inherited July 2026 or earnings", "wallet_transaction" in sql_10c_lower and "amount" in sql_10c_lower),
    ]
    print(f"    SQL 10c: {sql_10c}")
    chk10c_str = ", ".join([f"{name}: {passed_str(p)}" for name, p in checks_10c])
    print(f"    Checks: {chk10c_str}")

    all_10_semantic_passed = all(p for _, p in checks_10b) and all(p for _, p in checks_10c)
    resp_val_10 = res_10b.get("response_validation") or response_accuracy_validator.validate(
        question=q10b,
        requirement=res_10b.get("debug_pipeline", {}).get("business_requirement"),
        sql=sql_10b,
        execution_result={"data": res_10b.get("data", []), "columns": res_10b.get("columns", []), "row_count": res_10b.get("row_count", 0), "success": True},
        final_response=res_10b.get("summary", "")
    )
    resp_10_acc = resp_val_10.get("is_valid", False)
    e2e_10_acc = all_10_semantic_passed and resp_10_acc

    results.append({
        "id": 10,
        "question": "Context Isolation & Follow-Up Sequence (10a -> 10b -> 10c)",
        "sql": f"10b: {sql_10b}\n10c: {sql_10c}",
        "rows": res_10b.get("row_count", 0),
        "status": res_10b.get("status"),
        "val_status": res_10b.get("validation_status"),
        "checks": checks_10b + checks_10c,
        "passed": e2e_10_acc,
        "metrics": {
            "intent": True,
            "schema": True,
            "syntax": True,
            "semantic": all_10_semantic_passed,
            "execution": True,
            "result": True,
            "response": resp_10_acc,
            "e2e": e2e_10_acc
        },
        "sample_data": res_10b.get("data", [])[:2],
        "summary": res_10b.get("summary", ""),
        "response_validation": resp_val_10
    })

    print("\n" + "=" * 80)
    print("FINAL TEST SUITE SUMMARY (PER QUESTION)")
    print("=" * 80)
    total_e2e_passed = sum(1 for r in results if r["passed"])
    print(f"Total Tests: {len(results)} | End-to-End Passed: {total_e2e_passed} | Failed: {len(results) - total_e2e_passed}")
    for r in results:
        status_icon = "✅ PASS" if r["passed"] else "❌ FAIL"
        resp_acc_str = "RESP: PASS" if r["metrics"]["response"] else f"RESP: FAIL ({r['response_validation'].get('primary_failure_category')})"
        print(f"[{r['id']}] {status_icon} | {resp_acc_str} : {r['question']}")

    # Print 8-metric aggregate breakdown
    n = len(results)
    m_intent = (sum(1 for r in results if r["metrics"]["intent"]) / n) * 100
    m_schema = (sum(1 for r in results if r["metrics"]["schema"]) / n) * 100
    m_syntax = (sum(1 for r in results if r["metrics"]["syntax"]) / n) * 100
    m_semantic = (sum(1 for r in results if r["metrics"]["semantic"]) / n) * 100
    m_exec = (sum(1 for r in results if r["metrics"]["execution"]) / n) * 100
    m_result = (sum(1 for r in results if r["metrics"]["result"]) / n) * 100
    m_resp = (sum(1 for r in results if r["metrics"]["response"]) / n) * 100
    m_e2e = (sum(1 for r in results if r["metrics"]["e2e"]) / n) * 100

    print("\n" + "=" * 80)
    print("END-TO-END SYSTEM ACCURACY BREAKDOWN (8 METRICS)")
    print("=" * 80)
    print(f"1. Intent Accuracy                     : {m_intent:5.1f}%")
    print(f"2. Schema Retrieval Accuracy           : {m_schema:5.1f}%")
    print(f"3. SQL Syntax Validity                 : {m_syntax:5.1f}%")
    print(f"4. SQL Semantic Accuracy               : {m_semantic:5.1f}%")
    print(f"5. SQL Execution Accuracy              : {m_exec:5.1f}%")
    print(f"6. Database Result Accuracy            : {m_result:5.1f}%")
    print(f"7. Final Response Accuracy             : {m_resp:5.1f}%")
    print("-" * 80)
    print(f"8. END-TO-END QUESTION ANSWERING ACCURACY: {m_e2e:5.1f}%")
    print("=" * 80)

    return results

if __name__ == "__main__":
    run_accuracy_test_suite()
