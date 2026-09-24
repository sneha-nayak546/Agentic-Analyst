import os
import sys
import time
import json
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.agent.sql_agent import run_agent

BENCHMARK_QUERIES = [
    {"q": "Show all users", "expected_tables": ["users"]},
    {"q": "Show top 10 retailers by wallet transaction amount", "expected_tables": ["users", "wallet_transaction", "user_role", "role"]},
    {"q": "List active companies", "expected_tables": ["companies"]},
    {"q": "Show machine details for company X", "expected_tables": ["companies", "machine_details"]},
    {"q": "Total withdrawals this month", "expected_tables": ["withdrawal_request"]},
    {"q": "Show SKU inventories for distributor Y", "expected_tables": ["sku_inventories", "users", "user_role", "role"]}
]

def evaluate_query(query_info):
    q = query_info["q"]
    expected_tables = set(query_info["expected_tables"])
    
    print(f"Running Eval: '{q}'")
    try:
        t0 = time.time()
        res = run_agent(q, execute=False)
        latency = round((time.time() - t0) * 1000, 2)
        
        status = res.get("status")
        validation = res.get("validation", {})
        affected_tables = set(res.get("affected_tables", []))
        confidence = res.get("confidence_score", 0)
        
        hallucination = False
        if status == "blocked" and "Hallucinated" in validation.get("reason", ""):
            hallucination = True
            
        join_correct = True
        # If it's a multi table expected query, check if joins were at least generated
        if len(expected_tables) > 1 and len(affected_tables) <= 1:
            join_correct = False
            
        accuracy = 1 if (status == "success" and not hallucination) else 0

        return {
            "query": q,
            "status": status,
            "latency_ms": latency,
            "hallucination": hallucination,
            "join_correct": join_correct,
            "confidence": confidence,
            "accuracy": accuracy,
            "sql": res.get("optimized_sql", "")
        }
    except Exception as e:
        return {
            "query": q,
            "status": "error",
            "error": str(e)
        }

def run_test_suite():
    print("=" * 50)
    print("STARTING AUTOMATED EVALUATION SUITE")
    print("=" * 50)
    
    results = []
    
    # Run strictly sequentially on CPU to prevent resource starvation and thread contention
    with ThreadPoolExecutor(max_workers=1) as executor:
        results = list(executor.map(evaluate_query, BENCHMARK_QUERIES))
        
    total_latency = 0
    total_accuracy = 0
    total_hallucinations = 0
    
    successful_runs = [r for r in results if r.get("status") != "error"]
    n = len(successful_runs)
    
    for r in successful_runs:
        total_latency += r.get("latency_ms", 0)
        total_accuracy += r.get("accuracy", 0)
        if r.get("hallucination"):
            total_hallucinations += 1
            
    avg_latency = total_latency / n if n > 0 else 0
    accuracy_rate = (total_accuracy / n * 100) if n > 0 else 0
    hallucination_rate = (total_hallucinations / n * 100) if n > 0 else 0
    
    print("\n" + "=" * 50)
    print("EVALUATION REPORT")
    print("=" * 50)
    print(f"Total Queries Evaluated : {len(BENCHMARK_QUERIES)}")
    print(f"Average Latency         : {avg_latency:.2f} ms")
    print(f"Accuracy Rate           : {accuracy_rate:.2f}%")
    print(f"Hallucination Rate      : {hallucination_rate:.2f}%")
    print("=" * 50)
    
    report_path = "tests/eval_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    run_test_suite()
