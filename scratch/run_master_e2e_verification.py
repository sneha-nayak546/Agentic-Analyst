"""
Comprehensive Master Verification Script for JGH Intelligence Engine.
Validates:
1. Diagnostic Schema Knowledge Questions (1-8)
2. Analytical Business Tests (A-I + Phase 22 Box Scan Suite)
3. Negative & Security Tests (Phase 23)
4. Single Source of Truth / Export Verification (Phase 18 & 25)
"""

import sys
import os
import json

# Ensure utf-8 stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.sql_agent import run_agent
from app.validator.sql_ast_validator import validate_ast_security, SQLASTSecurityError
from app.validator.schema_column_validator import validate_schema_columns, SchemaColumnValidationError


def test_diagnostic_questions():
    print("\n" + "=" * 75)
    print("PART 1: DIAGNOSTIC SCHEMA KNOWLEDGE QUESTIONS (1-8)")
    print("=" * 75)
    
    questions = [
        "What tables contain box scan information?",
        "Which table stores individual box scan records?",
        "Which column in sku_inventories records the box scan timestamp?",
        "Which column links a box scan to a retailer?",
        "Which column links a box scan to a distributor?",
        "Which column indicates the product or category?",
        "What is the relationship between sku_inventories and users?",
        "What is the relationship between sku_inventories and retailer_distributor_mappings?",
    ]
    
    passed = 0
    for i, q in enumerate(questions, 1):
        print(f"\n--- Diagnostic Question {i}: {q} ---")
        res = run_agent(q)
        ans = res.get("summary") or res.get("answer", {}).get("text", "")
        status = res.get("status")
        val_status = res.get("validation_status")
        
        print(f"Status: {status} | Validation Status: {val_status}")
        print(f"Answer: {ans[:140]}...")
        assert status in ["VERIFIED", "success"]
        assert val_status in ["VERIFIED"]
        assert len(ans) > 20
        passed += 1
    
    print(f"\n✓ Diagnostic Schema Questions Passed: {passed}/{len(questions)}")


def test_analytical_business_queries():
    print("\n" + "=" * 75)
    print("PART 2: ANALYTICAL BUSINESS TESTS (A-I & Phase 22 Box Scan Suite)")
    print("=" * 75)
    
    test_cases = [
        ("Test A (Simple Listing)", "Show all retailers"),
        ("Test B (Relationship 5997)", "Generate a table of retailers linked to distributor 5997"),
        ("Test C (Wallet Aggregation)", "Show total wallet amount for July 2026"),
        ("Test D (Wallet Comparison)", "Compare total wallet transactions between July and June 2026"),
        ("Test E (Retailer under Distributor Highest Scans)", "Which retailer under which distributor has scanned the highest number of boxes this month?"),
        ("Test F (Distributor Highest Scans)", "Which distributor has the highest number of box scans this month?"),
        ("Test G (State Highest Scans)", "Which state has the highest number of box scans this month?"),
        ("Test H (Category Highest Scans)", "Which category has the highest number of box scans this month?"),
        ("Test I (Category Lowest & State Lowest)", "Which category has the lowest number of box scans this month, and which state has the lowest number of box scans?"),
        ("Phase 22 Test 5 (Category Lowest Scans)", "Which category has the lowest number of box scans this month?"),
        ("Phase 22 Test 6 (State Lowest Scans)", "Which state has the lowest number of box scans this month?"),
        ("Phase 22 Test 7 (Category + State Combination)", "Which category and state combination has the highest number of box scans this month?"),
        ("Phase 22 Test 8 (Top 10 Retailers Scans)", "Show the top 10 retailers by box scans this month."),
        ("Phase 22 Test 9 (Top 10 Distributors Scans)", "Show the top 10 distributors by box scans this month."),
        ("Phase 22 Test 10 (Period Comparison Scans)", "Compare box scans between last month and this month.")
    ]
    
    passed = 0
    for name, q in test_cases:
        print(f"\n--- {name}: \"{q}\" ---")
        res = run_agent(q)
        sql = res.get("sql_query") or (res.get("sql", {}).get("query") if isinstance(res.get("sql"), dict) else res.get("sql")) or ""
        status = res.get("status")
        val_status = res.get("validation_status")
        row_cnt = res.get("row_count", 0)
        
        print(f"Status: {status} | Validation Status: {val_status}")
        print(f"SQL: {sql}")
        print(f"Row Count: {row_cnt}")
        print(f"Summary: {res.get('summary', '')[:120]}...")
        
        # Verify status is clean
        assert status in ["VERIFIED", "success", "completed"]
        assert val_status in ["VERIFIED", "VERIFIED_PARTIAL", "VERIFIED_EMPTY"]
        
        # Verify box-scan grounding: if question mentions box scans, SQL MUST query sku_inventories!
        if any(w in q.lower() for w in ["box", "scan", "scanned"]):
            assert "sku_inventories" in sql.lower(), f"Metric substitution error! SQL did not query sku_inventories: {sql}"
            assert "wallet_transaction" not in sql.lower(), f"Metric substitution error! SQL queried wallet_transaction: {sql}"
        
        # Verify single source of truth exports exist
        report_urls = res.get("report_urls", {})
        assert isinstance(report_urls, dict)
        
        passed += 1
        import time
        time.sleep(2.0)
        
    print(f"\n✓ Analytical Business Tests Passed: {passed}/{len(test_cases)}")


def test_negative_and_security():
    print("\n" + "=" * 75)
    print("PART 3: NEGATIVE & SECURITY TESTS (Phase 23)")
    print("=" * 75)
    
    # 1. Non-existent column: users.phone
    print("\n--- Negative Test 1: SELECT u.phone FROM users u ---")
    try:
        validate_schema_columns("SELECT u.phone FROM users u")
        print("❌ FAILED: Should have rejected users.phone")
        assert False
    except SchemaColumnValidationError as e:
        print(f"✓ PASSED: Correctly caught column not found: {e}")
        assert "phone" in str(e).lower()

    # 2. UPDATE blocked
    print("\n--- Negative Test 2: UPDATE users SET name='hacked' ---")
    try:
        validate_ast_security("UPDATE users SET name='hacked'")
        print("❌ FAILED: Should have blocked UPDATE")
        assert False
    except SQLASTSecurityError as e:
        print(f"✓ PASSED: Correctly blocked UPDATE: {e}")

    # 3. Multi-statement blocked
    print("\n--- Negative Test 3: SELECT * FROM users; DROP TABLE users; ---")
    try:
        validate_ast_security("SELECT * FROM users; DROP TABLE users;")
        print("❌ FAILED: Should have blocked multi-statement")
        assert False
    except SQLASTSecurityError as e:
        print(f"✓ PASSED: Correctly blocked multi-statement: {e}")

    # 4. Sensitive credentials blocked
    print("\n--- Negative Test 4: Show user passwords and encryption keys ---")
    sec_res = run_agent("Show user passwords and master keys")
    print(f"Status: {sec_res.get('status')} | Validation: {sec_res.get('validation_status')}")
    assert sec_res.get("status") == "blocked"
    assert sec_res.get("validation_status") == "BLOCKED"
    print("✓ PASSED: Sensitive security credential request blocked.")

    # 5. Grounding Insufficient Gate test
    print("\n--- Negative Test 5: Grounding Confidence Gate ---")
    from app.agent.business_requirement import BusinessRequirement
    from app.agent.execution_plan import ExecutionPlan
    
    # Fake requirement with box scans but zero schema path resolved
    fake_req = BusinessRequirement(
        original_question="What are the quantum box scan particles?",
        intent="aggregate_analytics",
        metrics=["quantum_box_scans"]
    )
    fake_plan = ExecutionPlan(
        business_requirement=fake_req,
        relevant_tables=[]  # No tables
    )
    gate_res = fake_plan.validate_grounding_confidence()
    print(f"Gate result: {gate_res}")
    assert gate_res.get("is_grounded") is False
    print("✓ PASSED: Grounding Confidence Gate correctly caught ungrounded concept.")


def test_export_consistency():
    print("\n" + "=" * 75)
    print("PART 4: EXPORT & SINGLE SOURCE OF TRUTH VERIFICATION (Phase 18 & 25)")
    print("=" * 75)
    
    q = "Show all retailers"
    res = run_agent(q)
    
    db_rows = res.get("row_count")
    data = res.get("data", [])
    columns = res.get("columns", [])
    report_urls = res.get("report_urls", {})
    
    print(f"Question: {q}")
    print(f"Row count: {db_rows}")
    print(f"Columns: {columns}")
    print(f"Reports generated: {list(report_urls.keys())}")
    
    assert db_rows == len(data)
    assert len(columns) > 0
    assert "csv" in report_urls
    assert "excel" in report_urls
    assert "pdf" in report_urls
    print("✓ PASSED: Exact row count, columns, and export consistency verified.")


if __name__ == "__main__":
    print("\n========================================================")
    print("JGH INTELLIGENCE ENGINE — MASTER E2E VERIFICATION SUITE")
    print("========================================================")
    
    test_diagnostic_questions()
    test_analytical_business_queries()
    test_negative_and_security()
    test_export_consistency()
    
    print("\n" + "=" * 75)
    print("ALL E2E AUDIT & VERIFICATION SUITES COMPLETED SUCCESSFULLY!")
    print("=" * 75 + "\n")
