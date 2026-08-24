from app.agent.sql_agent import run_agent
from app.retriever.retriever import retrieve_sql_history
from app.agent.query_planner import create_plan
from app.prompt.prompt_builder import build_sql_prompt
import json

def test_few_shot_rag():
    print("=" * 80)
    print("TESTING FEW-SHOT RAG RETRIEVAL & PROMPT BUILDER")
    print("=" * 80)

    q = "who all are retailers available in the users table, for those retailers how much they all are earning in this month: cash_point, referral earning, topup, coupon_redeem"
    
    print(f"\n1. Question: {q}\n")
    
    # Test Exemplar Retrieval
    exemplars = retrieve_sql_history(q, k=2)
    print("RETRIEVED EXEMPLARS:\n", exemplars)
    print("-" * 50)
    
    # Test Execution Plan
    plan = create_plan(q)
    print("STRUCTURED PLAN:\n", json.dumps(plan, indent=2))
    print("-" * 50)
    
    # Test Prompt Builder
    prompt = build_sql_prompt(json.dumps(plan))
    print("GENERATED PROMPT:\n", prompt)
    print("=" * 80)
    
    # Test Full Agent Execution
    print("\nRUNNING AGENT EXECUTION:\n")
    res = run_agent(q)
    print("STATUS:", res.get("status"))
    print("OPTIMIZED SQL:\n", res.get("optimized_sql"))
    print("EXECUTION SUCCESS:", res.get("execution", {}).get("success"))
    print("ROW COUNT:", res.get("execution", {}).get("row_count"))
    
    if res.get("status") == "success" and res.get("execution", {}).get("success"):
        print("\nPASSED ALL FEW-SHOT RAG & DISAMBIGUATION TESTS!")
    else:
        print("\nTEST FAILED:", res.get("execution", {}).get("error") or res.get("validation", {}).get("reason"))

if __name__ == "__main__":
    test_few_shot_rag()
