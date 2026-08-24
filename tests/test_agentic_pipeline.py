import pytest
import json
from app.agent.sql_agent import run_agent

TEST_QUERIES = [
    "Show distributor 5997",
    "Show retailers linked to distributor 5997",
    "Show earnings of retailers linked to distributor 5997 this month",
    "Show retailer count for distributor 5997",
    "Compare earnings of retailers linked to distributor 5997 between July and August",
    "Show TDS deducted for retailers linked to distributor 5997",
    "Show distributor 5997's own earnings",
    "Show retailer ID 47973",
    "What about their earnings?",
    "Show distributor 5997's retailers for July",
    "Show the highest earning retailer linked to distributor 5997",
    "Show the same for August",
    "Show total earnings of all retailers linked to distributor 5997"
]

@pytest.mark.parametrize("query", TEST_QUERIES)
def test_agentic_pipeline(query):
    context = {}
    
    if query == "What about their earnings?":
        context = {"entity": "retailer", "specific_id": "47973", "is_explicit_follow_up": True}
    elif query == "Show the same for August":
        context = {"entity": "retailer", "specific_id": "5997", "is_explicit_follow_up": True, "limit": 1, "metric": "earnings"}

    res = run_agent(query, context=context, execute=True)
    
    assert res["status"] == "success", f"Failed query: {query}\nReason: {res.get('validation', {}).get('reason', 'Unknown error')}"
    
    confidence = res.get("result_confidence", "UNABLE_TO_VERIFY")
    assert confidence in ["VERIFIED_RESULT", "VERIFIED_EMPTY", "UNABLE_TO_VERIFY"], f"Query returned suspicious result: {confidence} for query '{query}'"
    
    plan = res.get("execution_plan", {})
    if "distributor 5997" in query.lower():
        assert any("5997" in str(f.get("value", "")) for f in plan.get("filters", [])), "Query Plan did not extract distributor ID 5997"

