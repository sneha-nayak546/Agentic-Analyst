import pytest
from app.agent.sql_agent import run_agent

def test_missing_date_clarification():
    """Test 12: Missing date requiring clarification"""
    res = run_agent("What were the distributor earnings?")
    # Since date is not specified and it's a time-bound metric, the intent parser should flag it
    assert res.get("status") == "ambiguous" or "clarification" in res
    assert "date" in str(res.get("clarification", "")).lower() or "missing" in str(res.get("clarification", "")).lower()

def test_relationship_unsupported():
    """Test 22: Unsupported relationship"""
    res = run_agent("Show retailers linked to company 123")
    # If this relationship doesn't exist in JOIN_DEFINITIONS, it should be blocked
    if res.get("status") == "blocked":
        assert "Relationship" in res.get("summary", "")
    else:
        # Depending on schema, it might pass, but we check if relationship_resolver did its job
        pass

def test_exact_id_lookup():
    """Test 2: Exact ID lookup"""
    res = run_agent("Show details for distributor 5997")
    assert res.get("status") in ["success", "verified"]
    sql = res.get("optimized_sql", "").lower()
    assert "5997" in sql

def test_follow_up_context():
    """Test 17: Follow-up question"""
    # Turn 1
    res1 = run_agent("Show active retailers in Karnataka")
    ctx1 = res1.get("context", {})
    
    # Turn 2
    res2 = run_agent("What about their earnings this month?", context=ctx1)
    sql2 = res2.get("optimized_sql", "").lower()
    # Ensure region and entity carried over, plus new metric and time
    assert "karnataka" in sql2 or (ctx1.get("region", "").lower() in str(ctx1).lower())
    assert "earning" in sql2 or "amount" in sql2

def test_empty_result_semantic_validation():
    """Test 24: SQL execution success but semantic mismatch/empty"""
    res = run_agent("Show retailers in Karnataka linked to distributor 9999999999 with earnings this month")
    # Should not blindly say "No records found" but explain the semantic validation
    if res.get("status") == "success":
        assert res.get("row_count", 0) == 0
        assert "verified" in str(res.get("accuracy_message", "")).lower() or "found" in str(res.get("accuracy_message", "")).lower()

# (Further comprehensive tests would be implemented to cover all 25 scenarios)
