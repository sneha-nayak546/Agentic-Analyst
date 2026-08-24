import pytest
from app.agent.sql_agent import run_agent
from app.agent.context_resolver import context_resolver

# Helper to verify response correctness
def assert_valid_response(result: dict, required_sql_terms: list, required_summary_terms: list):
    assert result["status"] == "success", f"Expected success, got {result['status']}: {result.get('error', '')}"
    
    sql = result.get("optimized_sql") or result.get("generated_sql", "")
    for term in required_sql_terms:
        assert term.lower() in sql.lower(), f"Missing required SQL term: {term} in query: {sql}"
        
    summary = result.get("summary", "")
    for term in required_summary_terms:
        assert term.lower() in summary.lower(), f"Missing required summary term: {term} in summary: {summary}"


def test_01_distributor_retailers_individual_earnings():
    q = "Generate a table of retailers linked to distributor 5997, and include a column for their individual total earnings for the current month."
    res = run_agent(q, execute=False)
    assert_valid_response(
        res,
        required_sql_terms=["group by", "distributer_id", "5997", "sum(", "amount"],
        required_summary_terms=["retailer", "earnings", "distributor", "5997"]
    )

def test_02_distributor_retailers_earnings_tds():
    q = "Show distributor 5997's retailers, their individual earnings, and TDS deducted this month."
    res = run_agent(q, execute=False)
    assert_valid_response(
        res,
        required_sql_terms=["group by", "tds", "5997"],
        required_summary_terms=["tds", "earnings", "retailer"]
    )

def test_03_distributor_top_5_retailers():
    q = "Give the top 5 retailers under distributor 5997 by earnings this month."
    res = run_agent(q, execute=False)
    assert_valid_response(
        res,
        required_sql_terms=["limit 5", "order by", "desc", "5997"],
        required_summary_terms=["top 5", "retailer", "earnings"]
    )

def test_04_distributor_current_month_earnings():
    q = "What are the earnings for distributor 5997 this month?"
    res = run_agent(q, execute=False)
    assert_valid_response(
        res,
        required_sql_terms=["5997", "sum(", "amount"],
        required_summary_terms=["earnings", "distributor"]
    )
    assert "group by" not in (res.get("optimized_sql") or res.get("generated_sql")).lower()

def test_05_july_vs_august_comparison():
    q = "Compare July and August approved payouts and give percentage change."
    res = run_agent(q, execute=False)
    assert_valid_response(
        res,
        required_sql_terms=["withdrawal_request", "1", "2026-07-01", "2026-08-01"],
        required_summary_terms=["compare", "percentage", "payout"]
    )

def test_06_percentage_change():
    q = "What is the percentage change in retailer earnings from last month?"
    res = run_agent(q, execute=False)
    assert_valid_response(
        res,
        required_sql_terms=["wallet_transaction", "amount"],
        required_summary_terms=["percentage", "earnings"]
    )

def test_07_exact_retailer_id():
    # In full pipeline, this might route through exact ID lookup, but we test the agent capability
    q = "Show retailer 47973"
    from app.agent.id_search import extract_id_from_prompt
    id_info = extract_id_from_prompt(q)
    assert id_info and id_info.get("raw_id") == "47973"

def test_08_wrong_id_suggestion():
    q = "Show distributor 9999999"
    # Agent should handle missing ID gracefully without hallucinating
    res = run_agent(q, execute=True)
    assert "no matching records found" in res.get("summary", "").lower() or "not found" in res.get("summary", "").lower()

def test_09_missing_date_clarification():
    q = "What were the earnings for Karnataka?"
    # It might ask for clarification if period is required but missing.
    res = run_agent(q, execute=False)
    assert res.get("status") in ["ambiguous", "success"]
    if res.get("status") == "ambiguous":
        assert "period" in res.get("clarification", "").lower() or "time" in res.get("clarification", "").lower()

def test_10_multi_condition_query():
    q = "Show approved retailers in Karnataka with TDS deducted in August."
    res = run_agent(q, execute=False)
    assert_valid_response(
        res,
        required_sql_terms=["11", "1", "tds", "2026-08-01"],
        required_summary_terms=["karnataka", "approved", "tds"]
    )

def test_11_and_12_follow_up_and_standalone():
    session_id = "test_session_1"
    ctx1 = context_resolver.resolve("Show Karnataka distributors")
    assert ctx1.get("region") == "Karnataka"
    
    ctx2 = context_resolver.resolve("What about their earnings?", previous_context=ctx1)
    assert ctx2.get("region") == "Karnataka"
    assert ctx2.get("metric") == "earnings"
    
    ctx3 = context_resolver.resolve("Show total withdrawals.", previous_context=ctx2)
    assert ctx3.get("region") is None
    assert ctx3.get("entity") == "withdrawal_request"

def test_13_zero_result_validation():
    q = "Show approved retailers in Goa with 0 earnings this month."
    res = run_agent(q, execute=True)
    # The system shouldn't just say 'No records found'. It should validate why.
    assert "no records found" in res.get("summary", "").lower() or "0" in res.get("summary", "")

def test_18_earnings_transaction_type():
    q = "What are the total earnings for July?"
    res = run_agent(q, execute=False)
    sql = (res.get("optimized_sql") or res.get("generated_sql", "")).lower()
    assert "reference_type !=" not in sql, "Should not use exclusion logic for earnings"
    assert "reference_type in" in sql or "reference_type =" in sql, "Should use inclusion logic for valid earnings types"

if __name__ == "__main__":
    pytest.main(["-v", "test_intent_pipeline.py"])
