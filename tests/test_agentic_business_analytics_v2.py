import pytest
from app.agent.sql_agent import run_agent

def test_missing_date_clarification_v2():
    """Test: Missing date requiring clarification - Strict Policy"""
    res = run_agent("What were the distributor earnings?")
    # System should halt and ask for the specific month
    assert res.get("status") == "ambiguous" or "clarification" in res

def test_id_formatting_and_response():
    """Test: Responses must not format IDs with commas"""
    res = run_agent("Show details for distributor 5997")
    response_text = res.get("summary", "")
    assert "5,997" not in response_text
    assert "5997" in response_text

def test_empty_result_semantic_feedback():
    """Test: Handle valid ID but no related records vs invalid ID"""
    res = run_agent("Show retailers linked to distributor 9999999999")
    summary = res.get("summary", "")
    # Should explicitly mention the ID check
    assert "found" in summary.lower() or "no retailers" in summary.lower()

def test_percentage_calculation_explanation():
    """Test: Percentage calculations should be explained"""
    res = run_agent("What percentage of retailers are active?")
    summary = res.get("summary", "")
    assert "%" in summary or "percent" in summary.lower()
