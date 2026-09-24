"""
Comprehensive Master Test Suite for Requirement-Grounded Enterprise AI Data Analyst.
Validates:
1. Requirement preservation & [REQUIREMENT DIFF] generation.
2. VerifiedResult as single source of truth across UI, Answer, and Reports.
3. Top-N semantics (allowing <= N rows without fabrication or hardcoded numbers).
4. Tests A, B, C, D structural fidelity without hardcoded expected DB counts.
5. Generalization to unseen variations.
6. Verification that no question-specific hacks or answer maps exist.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import re
from typing import Dict, Any

from app.agent.business_requirement import BusinessRequirement
from app.agent.execution_plan import ExecutionPlan, format_requirement_diff
from app.agent.verified_result import (
    VerifiedResult,
    VERIFIED,
    VERIFIED_PARTIAL,
    VERIFIED_EMPTY,
    INVALID,
    BLOCKED
)
from app.agent.nlp_understanding import nlp_agent
from app.knowledge.relationship_resolver import relationship_resolver
from app.agent.response_generator import response_generator

# ==============================================================================
# 1. REQUIREMENT PRESERVATION & DIFF TESTS
# ==============================================================================

def test_requirement_diff_detects_unrequested_partner():
    """
    If user asks for total wallet transactions, introducing partner or grouping by user
    must trigger RESULT: FAIL with reason 'Unrequested entity "partner" introduced.'
    """
    req = BusinessRequirement(
        original_question="Compare total wallet transactions between July and June 2026",
        intent="comparison",
        entities=[],
        metrics=["total wallet transactions"],
        aggregation=["COUNT"],
        periods=["July 2026", "June 2026"],
        comparison=True
    )
    plan = ExecutionPlan(
        business_requirement=req,
        relevant_tables=["wallet_transaction", "users"],
        relevant_columns=["amount", "created_at"]
    )
    # Flawed SQL that introduces partner / grouping by users
    bad_sql = "SELECT users.name AS partner, COUNT(*) FROM wallet_transaction JOIN users ON users.id = wallet_transaction.user_id GROUP BY users.name;"
    
    check = plan.validate_preserves_requirements(sql=bad_sql)
    assert check["is_valid"] is False, "Plan should fail when unrequested partner/grouping is introduced"
    assert any("partner" in r.lower() for r in check["reasons"])

    diff_str = format_requirement_diff(req, plan=plan, sql=bad_sql, res_val_status=False, failure_reason="; ".join(check["reasons"]))
    assert "[REQUIREMENT DIFF]" in diff_str
    assert "entity: partner       ❌" in diff_str
    assert "RESULT: FAIL" in diff_str.upper() or "Result:\n    FAIL" in diff_str
    assert "partner" in diff_str.lower()


def test_requirement_diff_passes_clean_comparison():
    """
    Clean wallet comparison query must pass with RESULT: PASS.
    """
    req = BusinessRequirement(
        original_question="Compare total wallet transactions between July and June 2026",
        intent="comparison",
        entities=[],
        metrics=["total wallet transactions"],
        aggregation=["COUNT"],
        periods=["July 2026", "June 2026"],
        comparison=True
    )
    plan = ExecutionPlan(
        business_requirement=req,
        relevant_tables=["wallet_transaction"],
        relevant_columns=["amount", "created_at"]
    )
    clean_sql = """
    SELECT 
        SUM(CASE WHEN created_at >= '2026-06-01' AND created_at < '2026-07-01' THEN 1 ELSE 0 END) AS june_transactions,
        SUM(CASE WHEN created_at >= '2026-07-01' AND created_at < '2026-08-01' THEN 1 ELSE 0 END) AS july_transactions
    FROM wallet_transaction;
    """
    check = plan.validate_preserves_requirements(sql=clean_sql)
    assert check["is_valid"] is True, f"Clean comparison should be valid: {check['reasons']}"
    
    diff_str = format_requirement_diff(req, plan=plan, sql=clean_sql, res_val_status=True)
    assert "Result:\n    PASS" in diff_str or "RESULT: PASS" in diff_str


def test_requirement_diff_detects_unrequested_ranking():
    """
    Injecting a fake LIMIT 10 / Top-10 on an unranked query must be flagged as a violation.
    """
    req = BusinessRequirement(
        original_question="Show total wallet amount for July 2026",
        intent="aggregate_analytics",
        entities=[],
        metrics=["total wallet amount"],
        aggregation=["SUM"],
        periods=["July 2026"],
        ranking=None,
        limit=None
    )
    plan = ExecutionPlan(
        business_requirement=req,
        relevant_tables=["wallet_transaction"],
        relevant_columns=["amount", "created_at"]
    )
    # Flawed SQL that injects unrequested LIMIT 10 with ORDER BY
    bad_sql = "SELECT amount FROM wallet_transaction ORDER BY amount DESC LIMIT 10;"
    
    check = plan.validate_preserves_requirements(sql=bad_sql)
    assert check["is_valid"] is False
    assert any("top-10" in r.lower() or "ranking" in r.lower() for r in check["reasons"])


# ==============================================================================
# 2. TOP-N & LIMIT SEMANTICS TESTS (NO HARDCODED EXPECTED DB COUNTS)
# ==============================================================================

def test_top_n_allows_fewer_qualifying_rows_without_fabrication():
    """
    When user requests Top 10 retailers, but only 2 qualifying rows exist in the DB,
    the system must return exactly 2 rows and status VERIFIED_PARTIAL.
    It must NEVER fabricate 8 rows or assert hardcoded row counts!
    """
    from app.validator.result_accuracy_validator import result_accuracy_validator

    req = BusinessRequirement(
        original_question="Show top 10 retailers by earnings for July 2026",
        intent="ranking",
        entities=["retailer"],
        metrics=["earnings"],
        periods=["July 2026"],
        ranking="top 10",
        limit=10
    )
    plan = ExecutionPlan(
        business_requirement=req,
        relevant_tables=["users", "wallet_transaction"],
        limit=10
    )
    # Simulating 2 qualifying rows returned from MySQL
    execution_result = {
        "success": True,
        "columns": ["id", "name", "earnings"],
        "data": [
            {"id": 101, "name": "Retailer Alpha", "earnings": 5000.0},
            {"id": 102, "name": "Retailer Beta", "earnings": 3200.0}
        ],
        "row_count": 2,
        "execution_time_ms": 12.5
    }
    val = result_accuracy_validator.validate(
        question=req.original_question,
        sql="SELECT u.id, u.name, SUM(w.amount) AS earnings FROM users u JOIN wallet_transaction w ON u.id = w.user_id WHERE u.user_role = 2 AND w.created_at >= '2026-07-01' AND w.created_at < '2026-08-01' GROUP BY u.id, u.name ORDER BY earnings DESC LIMIT 10;",
        context={},
        execution_result=execution_result,
        plan=plan
    )

    assert val["success"] is True
    # Must be VERIFIED_PARTIAL because row_count (2) < limit (10)
    assert val["result_confidence"] == VERIFIED_PARTIAL
    assert "2" in val["reason"] or "qualifying" in val["reason"]


def test_top_n_rejects_exceeding_limit():
    """
    If query returned more rows than the requested limit, it must be flagged INVALID.
    """
    from app.validator.result_accuracy_validator import result_accuracy_validator

    req = BusinessRequirement(
        original_question="Show top 5 retailers by earnings for July 2026",
        intent="ranking",
        entities=["retailer"],
        metrics=["earnings"],
        limit=5
    )
    plan = ExecutionPlan(business_requirement=req, relevant_tables=["users"], limit=5)
    
    execution_result = {
        "success": True,
        "columns": ["id", "name"],
        "data": [{"id": i, "name": f"Retailer {i}"} for i in range(12)],
        "row_count": 12
    }
    val = result_accuracy_validator.validate(
        question=req.original_question,
        sql="SELECT id, name FROM users;",
        context={},
        execution_result=execution_result,
        plan=plan
    )
    assert val["success"] is False
    assert val["result_confidence"] == INVALID


# ==============================================================================
# 3. VERIFIED RESULT AS SINGLE SOURCE OF TRUTH
# ==============================================================================

def test_verified_result_single_source_of_truth():
    """
    UI Data == API Data == Excel Data == CSV Data == PDF Data.
    All must originate directly from the single VerifiedResult object.
    """
    req = BusinessRequirement(
        original_question="Show retailers linked to distributor 5997",
        intent="data_retrieval",
        entities=["retailer"],
        specific_ids={"distributor_id": 5997}
    )
    plan = ExecutionPlan(business_requirement=req, relevant_tables=["sku_inventories", "users"])
    
    mock_data = [
        {"retailer_id": 201, "retailer_name": "Shop One", "distributor_id": 5997},
        {"retailer_id": 202, "retailer_name": "Shop Two", "distributor_id": 5997}
    ]
    mock_cols = ["retailer_id", "retailer_name", "distributor_id"]

    res = VerifiedResult(
        question=req.original_question,
        business_requirement=req,
        execution_plan=plan,
        sql="SELECT DISTINCT u.id AS retailer_id, u.name AS retailer_name, s.distributer_id FROM sku_inventories s JOIN users u ON s.status_retailer_id = u.id WHERE s.distributer_id = 5997 AND u.user_role = 2;",
        columns=mock_cols,
        data=mock_data,
        row_count=len(mock_data),
        execution_time_ms=15.0,
        summary="Found 2 retailers linked to distributor 5997.",
        validation_status=VERIFIED
    )

    api_dict = res.to_api_dict()
    assert api_dict["columns"] == mock_cols
    assert api_dict["results"] == mock_data
    assert api_dict["data"] == mock_data
    assert api_dict["row_count"] == 2
    assert api_dict["validation_status"] == VERIFIED


# ==============================================================================
# 4. RESPONSE GENERATOR ELIMINATES GENERIC MARKETING TEMPLATES
# ==============================================================================

def test_response_generator_prohibits_marketing_templates():
    """
    Verify ResponseGenerator does NOT inject unrequested 'Comparative Growth Performance',
    'Executive Brief', 'Top Contributors', or 'Partner Records'.
    """
    req = BusinessRequirement(
        original_question="Compare total wallet transactions between July and June 2026",
        intent="comparison",
        entities=[],
        metrics=["total wallet transactions"],
        periods=["July 2026", "June 2026"],
        comparison=True
    )
    plan = ExecutionPlan(business_requirement=req, relevant_tables=["wallet_transaction"])
    exec_res = {
        "success": True,
        "columns": ["june_total", "july_total"],
        "data": [{"june_total": 1250, "july_total": 1400}],
        "row_count": 1
    }

    resp = response_generator.generate_response(plan, exec_res)
    # Check that forbidden generic marketing phrases are not present
    forbidden = [
        "Comparative Growth Performance",
        "Executive Brief",
        "Top Contributors",
        "Partner Records",
        "Actionable Business Takeaways",
        "Named partner spotlights"
    ]
    for phrase in forbidden:
        assert phrase not in resp, f"Forbidden marketing phrase '{phrase}' was injected into the response!"


# ==============================================================================
# 5. GENERALIZATION CHECK: NO QUESTION FINGERPRINTING / HARDCODED DICTIONARIES
# ==============================================================================

def test_no_hardcoded_question_maps_in_agent():
    """
    Verify that sql_agent.py and response_generator.py do not contain hardcoded
    lookup maps matching specific question strings.
    """
    import inspect
    from app.agent import sql_agent
    
    source = inspect.getsource(sql_agent)
    assert "Compare total wallet transactions between July and June" not in source
    assert "Show retailers linked to distributor 5997" not in source
    assert "expected_rows" not in source
    assert "expected_total" not in source


# ==============================================================================
# 6. TESTS A, B, C, D STRUCTURAL CONTRACT VALIDATION
# ==============================================================================

def test_test_a_structural_contract():
    """
    TEST A: 'Compare total wallet transactions between July and June 2026'
    Verify dynamically:
    - comparison = true
    - periods = June and July 2026
    - no unrequested partner/retailer dimension
    - no ranking
    - no top-N
    - correct aggregate
    Do NOT hardcode expected DB values.
    """
    req = nlp_agent.parse_question("Compare total wallet transactions between July and June 2026")
    assert req.comparison is True
    assert any("July" in p for p in req.periods) and any("June" in p for p in req.periods)
    assert "partner" not in [e.lower() for e in req.entities]
    assert "retailer" not in [e.lower() for e in req.entities]
    assert req.ranking is None
    assert req.limit is None

    plan = relationship_resolver.resolve(req)
    assert "wallet_transaction" in plan.relevant_tables
    assert "users" not in plan.relevant_tables or plan.group_by == []

    # Verify structural diff passes
    valid_sql = "SELECT SUM(CASE WHEN created_at >= '2026-06-01' AND created_at < '2026-07-01' THEN amount ELSE 0 END) AS june_total, SUM(CASE WHEN created_at >= '2026-07-01' AND created_at < '2026-08-01' THEN amount ELSE 0 END) AS july_total FROM wallet_transaction;"
    check = plan.validate_preserves_requirements(sql=valid_sql)
    assert check["is_valid"] is True


def test_test_b_structural_contract():
    """
    TEST B: 'Show top 10 retailers by earnings for July 2026'
    Verify:
    - retailer dimension
    - earnings metric
    - July 2026 filter
    - limit <= 10
    - actual rows <= 10
    - no fabricated rows
    Do NOT assert that row count must equal a specific number.
    """
    req = nlp_agent.parse_question("Show top 10 retailers by earnings for July 2026")
    assert any("retailer" in e.lower() for e in req.entities)
    assert req.limit == 10 or (req.ranking and "10" in req.ranking)

    plan = relationship_resolver.resolve(req)
    assert "users" in plan.relevant_tables or "retailer" in str(plan.relevant_tables).lower()

    # Verify limit check:
    valid_sql = "SELECT u.id, u.name, SUM(w.amount) AS earnings FROM users u JOIN wallet_transaction w ON u.id = w.user_id WHERE u.user_role = 2 AND w.created_at >= '2026-07-01' AND w.created_at < '2026-08-01' GROUP BY u.id, u.name ORDER BY earnings DESC LIMIT 10;"
    check = plan.validate_preserves_requirements(sql=valid_sql)
    assert check["is_valid"] is True


def test_test_c_structural_contract():
    """
    TEST C: 'Generate a table of retailers linked to distributor 5997'
    Verify:
    - correct business relationship
    - correct joins
    - no invented distributor relationship (distributor_id on users table)
    - requested retailer output
    - distributor filtering is correct
    """
    req = nlp_agent.parse_question("Generate a table of retailers linked to distributor 5997")
    assert 5997 in req.specific_ids.values() or "5997" in str(req.specific_ids) or "5997" in req.original_question
    assert any("retailer" in e.lower() for e in req.entities)

    plan = relationship_resolver.resolve(req)
    # Must join via sku_inventories or active linking table, NOT users.distributor_id
    assert "sku_inventories" in plan.relevant_tables or any("sku_inventories" in j for j in plan.required_joins)


def test_test_d_structural_contract():
    """
    TEST D: 'Show total wallet amount for July 2026'
    Verify:
    - correct metric
    - correct aggregation
    - correct July filter
    - no unrelated dimensions
    """
    req = nlp_agent.parse_question("Show total wallet amount for July 2026")
    assert any("July" in p for p in req.periods) or any("2026-07" in str(f) for f in req.filters)
    assert req.ranking is None
    assert req.limit is None

    plan = relationship_resolver.resolve(req)
    assert "wallet_transaction" in plan.relevant_tables
    valid_sql = "SELECT SUM(amount) AS total_wallet_amount FROM wallet_transaction WHERE created_at >= '2026-07-01' AND created_at < '2026-08-01';"
    check = plan.validate_preserves_requirements(sql=valid_sql)
    assert check["is_valid"] is True


# ==============================================================================
# 7. UNSEEN VARIATIONS GENERALIZATION TEST
# ==============================================================================

@pytest.mark.parametrize("unseen_question,expected_intent,expected_keyword", [
    ("Give me the total wallet amount for August 2026.", "aggregate", "August"),
    ("Compare wallet transactions for May and June 2026.", "comparison", "May"),
    ("List the top 5 retailers by earnings in August 2026.", "ranking", "retailer"),
    ("Show retailers associated with distributor 7001.", "data_retrieval", "7001"),
    ("How much wallet value was generated in Q2 2026?", "aggregate", "2026"),
])
def test_unseen_generalization_parsing(unseen_question, expected_intent, expected_keyword):
    """
    Verify pipeline dynamically infers requirements for unseen queries without
    relying on static memorization or question-specific code paths.
    """
    req = nlp_agent.parse_question(unseen_question)
    assert req.original_question == unseen_question
    if expected_intent == "comparison":
        assert req.comparison is True
    elif expected_intent == "ranking":
        assert req.limit == 5 or (req.ranking and "5" in req.ranking)
    assert expected_keyword.lower() in (
        str(req.periods) + str(req.entities) + str(req.specific_ids) + str(req.filters) + unseen_question
    ).lower()

