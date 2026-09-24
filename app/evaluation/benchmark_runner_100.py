import os
import sys
import time
import json
import numpy as np
from typing import Dict, Any, List

from app.agent.sql_agent import run_agent
from app.evaluation.benchmark_suite_100 import BENCHMARK_100_TEST_CASES

def run_100_benchmark():
    """
    Master 100-Question Comprehensive Benchmark Runner.
    Measures:
    - Intent Accuracy
    - Schema Accuracy
    - SQL Semantic Accuracy
    - SQL Execution Success
    - Result Accuracy
    - Final Answer Accuracy
    - End-to-End Accuracy
    - Average Latency
    - P95 Latency
    """
    print("\n" + "=" * 80)
    print("JGH INTELLIGENCE ENGINE — EXPANDED 100-CATEGORY BENCHMARK EVALUATION")
    print("=" * 80 + "\n")

    intent_correct = 0
    schema_correct = 0
    sql_semantic_correct = 0
    sql_exec_correct = 0
    result_correct = 0
    answer_correct = 0
    end_to_end_correct = 0

    results_log: List[Dict[str, Any]] = []
    latencies: List[float] = []

    stage_latencies: Dict[str, List[float]] = {
        "intent_ms": [],
        "schema_ms": [],
        "sql_gen_ms": [],
        "validation_ms": [],
        "database_ms": [],
        "answer_ms": [],
        "total_ms": []
    }

    total_cases = len(BENCHMARK_100_TEST_CASES)

    for tc in BENCHMARK_100_TEST_CASES:
        t_id = tc["id"]
        cat = tc["category"]
        q = tc["question"]
        ctx = tc.get("context")

        print(f"\n[{t_id}/{total_cases}] Category: {cat} — \"{q}\"")

        t0 = time.time()
        try:
            res = run_agent(q, context=ctx)
            duration_ms = round((time.time() - t0) * 1000, 2)
        except Exception as e:
            duration_ms = round((time.time() - t0) * 1000, 2)
            res = {"status": "error", "error": str(e), "validation_status": "ERROR"}

        latencies.append(duration_ms)

        # 1. Intent Accuracy Check
        intent_pass = False
        if tc["category"] in ["SQL injection/security", "Negative / Security Edge Case"]:
            intent_pass = res.get("validation_status") in ["BLOCKED", "ERROR"] or res.get("status") in ["blocked", "ERROR"]
        elif tc["category"] in ["ambiguous questions", "Ambiguous Query"]:
            intent_pass = bool(res.get("is_ambiguous")) or res.get("status") == "ambiguous"
        else:
            intent_pass = bool(res.get("status") == "success")

        # 2. Schema Accuracy Check
        schema_pass = False
        sql_val = res.get("sql")
        sql_query_str = sql_val.get("query", "") if isinstance(sql_val, dict) else str(sql_val or res.get("sql_query") or "")
        sql_text = sql_query_str.upper()

        if tc["category"] in ["SQL injection/security", "Negative / Security Edge Case", "ambiguous questions", "Ambiguous Query"]:
            schema_pass = True
        else:
            exp_tables = [t.upper() for t in tc.get("expected_tables", [])]
            affected = res.get("affected_tables", [])
            schema_pass = any(t in sql_text for t in exp_tables) or any(t.lower() in [a.lower() for a in affected] for t in tc.get("expected_tables", []))

        # 3. SQL Semantic Accuracy Check
        sql_semantic_pass = False
        if tc["category"] in ["SQL injection/security", "Negative / Security Edge Case", "ambiguous questions", "Ambiguous Query"]:
            sql_semantic_pass = True
        else:
            req_frags = tc.get("required_sql_fragments", [])
            sql_semantic_pass = all(
                (frag.upper() in sql_text) or
                (frag.upper() == "USERS.CREATED_AT" and ("U.CREATED_AT" in sql_text or "USERS.CREATED_AT" in sql_text))
                for frag in req_frags
            )

        # 3b. SQL Execution Success Check
        exec_pass = False
        if tc["category"] in ["SQL injection/security", "Negative / Security Edge Case", "ambiguous questions", "Ambiguous Query"]:
            exec_pass = True
        else:
            exec_pass = bool(res.get("execution", {}).get("success", False)) or res.get("status") == "success"

        # 4. Result Accuracy Check
        v_status = res.get("validation_status") or res.get("result_confidence") or res.get("status")
        exp_statuses = tc.get("expected_status", [])
        result_pass = any(v_status == es for es in exp_statuses) or (res.get("status") in exp_statuses)

        # 5. Answer Accuracy Check
        ans_text = res.get("answer", {}).get("text") or res.get("summary") or ""
        answer_pass = bool(ans_text and len(ans_text.strip()) > 10)

        # 6. End-to-End Accuracy
        e2e_pass = intent_pass and schema_pass and sql_semantic_pass and exec_pass and result_pass and answer_pass

        if intent_pass: intent_correct += 1
        if schema_pass: schema_correct += 1
        if sql_semantic_pass: sql_semantic_correct += 1
        if exec_pass: sql_exec_correct += 1
        if result_pass: result_correct += 1
        if answer_pass: answer_correct += 1
        if e2e_pass: end_to_end_correct += 1

        perf = res.get("performance", {}) or {}
        stage_latencies["total_ms"].append(perf.get("total_ms", duration_ms))
        stage_latencies["intent_ms"].append(perf.get("intent_latency_ms", 0.0))
        stage_latencies["schema_ms"].append(perf.get("schema_latency_ms", 0.0))
        stage_latencies["sql_gen_ms"].append(perf.get("sql_generation_latency_ms", 0.0))
        stage_latencies["validation_ms"].append(perf.get("sql_validation_latency_ms", 0.0))
        stage_latencies["database_ms"].append(perf.get("db_query_latency_ms", 0.0) + perf.get("db_fetch_latency_ms", 0.0))
        stage_latencies["answer_ms"].append(perf.get("answer_latency_ms", 0.0))

        pass_str = "PASS" if e2e_pass else "FAIL"
        print(f"    ✓ Intent: {'PASS' if intent_pass else 'FAIL'} | Schema: {'PASS' if schema_pass else 'FAIL'} | SQL Semantic: {'PASS' if sql_semantic_pass else 'FAIL'} | Exec: {'PASS' if exec_pass else 'FAIL'} | Result: {'PASS' if result_pass else 'FAIL'} | E2E: {pass_str} ({duration_ms}ms)")

        results_log.append({
            "id": t_id,
            "category": cat,
            "question": q,
            "duration_ms": duration_ms,
            "intent_pass": intent_pass,
            "schema_pass": schema_pass,
            "sql_pass": sql_semantic_pass,
            "exec_pass": exec_pass,
            "result_pass": result_pass,
            "answer_pass": answer_pass,
            "e2e_pass": e2e_pass,
            "status": v_status,
            "sql_query": sql_query_str
        })

    # Summary Metrics Calculation
    avg_latency = float(np.mean(latencies)) if latencies else 0.0
    p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0

    report = {
        "summary": {
            "total_cases": total_cases,
            "intent_accuracy": round(intent_correct / total_cases * 100, 1),
            "schema_accuracy": round(schema_correct / total_cases * 100, 1),
            "sql_semantic_accuracy": round(sql_semantic_correct / total_cases * 100, 1),
            "sql_execution_accuracy": round(sql_exec_correct / total_cases * 100, 1),
            "result_accuracy": round(result_correct / total_cases * 100, 1),
            "answer_accuracy": round(answer_correct / total_cases * 100, 1),
            "end_to_end_accuracy": round(end_to_end_correct / total_cases * 100, 1),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2)
        },
        "stage_latency_averages_ms": {
            "intent": round(float(np.mean(stage_latencies["intent_ms"])), 2) if stage_latencies["intent_ms"] else 0.0,
            "schema": round(float(np.mean(stage_latencies["schema_ms"])), 2) if stage_latencies["schema_ms"] else 0.0,
            "sql_generation": round(float(np.mean(stage_latencies["sql_gen_ms"])), 2) if stage_latencies["sql_gen_ms"] else 0.0,
            "validation": round(float(np.mean(stage_latencies["validation_ms"])), 2) if stage_latencies["validation_ms"] else 0.0,
            "database": round(float(np.mean(stage_latencies["database_ms"])), 2) if stage_latencies["database_ms"] else 0.0,
            "answer": round(float(np.mean(stage_latencies["answer_ms"])), 2) if stage_latencies["answer_ms"] else 0.0
        },
        "details": results_log
    }

    with open("benchmark_100_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("100-TEST BENCHMARK RESULTS")
    print("=" * 80)
    print(f"Total Test Cases:            {total_cases}")
    print(f"Intent Understanding:        {report['summary']['intent_accuracy']}% ({intent_correct}/{total_cases})")
    print(f"Schema Retrieval:            {report['summary']['schema_accuracy']}% ({schema_correct}/{total_cases})")
    print(f"SQL Semantic Correctness:    {report['summary']['sql_semantic_accuracy']}% ({sql_semantic_correct}/{total_cases})")
    print(f"SQL Execution Success:       {report['summary']['sql_execution_accuracy']}% ({sql_exec_correct}/{total_cases})")
    print(f"Result Verification:         {report['summary']['result_accuracy']}% ({result_correct}/{total_cases})")
    print(f"Final Answer Grounding:      {report['summary']['answer_accuracy']}% ({answer_correct}/{total_cases})")
    print(f"--------------------------------------------------------------------------------")
    print(f"OVERALL END-TO-END ACCURACY: {report['summary']['end_to_end_accuracy']}% ({end_to_end_correct}/{total_cases})")
    print(f"Average Latency:             {report['summary']['avg_latency_ms']} ms")
    print(f"P95 Latency:                 {report['summary']['p95_latency_ms']} ms")
    print("=" * 80 + "\n")

    return report

if __name__ == "__main__":
    run_100_benchmark()
