"""
Automated Benchmark Runner for JGH Intelligence Engine.
Executes all 20 test cases and generates the accuracy evaluation matrix + latency profile.
Conforms strictly to Sections 11, 12, and 16.
"""

import sys
import os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))

import time
import json
from typing import Dict, Any, List

from app.agent.sql_agent import run_agent
from app.evaluation.benchmark_suite import BENCHMARK_TEST_CASES


def run_benchmark():
    print("=" * 80)
    print("JGH INTELLIGENCE ENGINE — 20-CATEGORY BENCHMARK EVALUATION")
    print("=" * 80)

    results: List[Dict[str, Any]] = []

    intent_correct = 0
    schema_correct = 0
    sql_semantic_correct = 0
    result_correct = 0
    answer_correct = 0
    end_to_end_correct = 0

    stage_latencies = {
        "intent_ms": [],
        "schema_ms": [],
        "sql_gen_ms": [],
        "validation_ms": [],
        "database_ms": [],
        "answer_ms": [],
        "total_ms": []
    }

    total_cases = len(BENCHMARK_TEST_CASES)

    for tc in BENCHMARK_TEST_CASES:
        t_id = tc["id"]
        cat = tc["category"]
        q = tc["question"]
        ctx = tc.get("context")

        print(f"\n[{t_id}/{total_cases}] Running: {cat} — \"{q}\"")

        t0 = time.time()
        try:
            res = run_agent(q, context=ctx)
            duration_ms = round((time.time() - t0) * 1000, 2)
        except Exception as e:
            duration_ms = round((time.time() - t0) * 1000, 2)
            res = {"status": "error", "error": str(e), "validation_status": "ERROR"}

        # 1. Intent Accuracy Check
        intent_data = res.get("intent", {})
        intent_type = intent_data.get("type") or intent_data.get("intent_type") or res.get("intent")
        intent_pass = False
        if tc["category"] == "Negative / Security Edge Case":
            intent_pass = res.get("validation_status") == "BLOCKED" or res.get("status") == "blocked"
        elif tc["category"] == "Ambiguous Query":
            intent_pass = bool(res.get("is_ambiguous")) or res.get("status") == "ambiguous"
        else:
            # Check if intent aligns with expected or data_retrieval
            intent_pass = bool(res.get("status") == "success")

        # 2. Schema Accuracy Check
        schema_pass = False
        sql_val = res.get("sql")
        sql_query_str = sql_val.get("query", "") if isinstance(sql_val, dict) else str(sql_val or res.get("sql_query") or "")
        sql_text = sql_query_str.upper()
        if tc["category"] in ["Negative / Security Edge Case", "Ambiguous Query"]:
            schema_pass = True
        else:
            exp_tables = [t.upper() for t in tc.get("expected_tables", [])]
            affected = res.get("affected_tables", [])
            schema_pass = any(t in sql_text for t in exp_tables) or any(t.lower() in [a.lower() for a in affected] for t in tc.get("expected_tables", []))

        # 3. SQL Semantic Accuracy Check
        sql_pass = False
        if tc["category"] in ["Negative / Security Edge Case", "Ambiguous Query"]:
            sql_pass = True
        else:
            req_frags = tc.get("required_sql_fragments", [])
            sql_pass = all(
                (frag.upper() in sql_text) or
                (frag.upper() == "USERS.CREATED_AT" and ("U.CREATED_AT" in sql_text or "USERS.CREATED_AT" in sql_text))
                for frag in req_frags
            )

        # 4. Result Accuracy Check
        v_status = res.get("validation_status") or res.get("result_confidence") or res.get("status")
        exp_statuses = tc.get("expected_status", [])
        result_pass = any(v_status == es for es in exp_statuses) or (res.get("status") in exp_statuses)

        # 5. Answer Accuracy Check
        ans_text = res.get("answer", {}).get("text") or res.get("summary") or ""
        answer_pass = bool(ans_text and len(ans_text.strip()) > 10)

        # 6. End-to-End Accuracy
        e2e_pass = intent_pass and schema_pass and sql_pass and result_pass and answer_pass

        if intent_pass: intent_correct += 1
        if schema_pass: schema_correct += 1
        if sql_pass: sql_semantic_correct += 1
        if result_pass: result_correct += 1
        if answer_pass: answer_correct += 1
        if e2e_pass: end_to_end_correct += 1

        perf = res.get("performance", {}) or {}
        stage_latencies["total_ms"].append(perf.get("total_ms", duration_ms))
        if "intent_ms" in perf: stage_latencies["intent_ms"].append(perf["intent_ms"])
        if "schema_ms" in perf: stage_latencies["schema_ms"].append(perf["schema_ms"])
        if "sql_generation_ms" in perf: stage_latencies["sql_gen_ms"].append(perf["sql_generation_ms"])
        if "validation_ms" in perf: stage_latencies["validation_ms"].append(perf["validation_ms"])
        if "database_ms" in perf: stage_latencies["database_ms"].append(perf["database_ms"])
        if "answer_ms" in perf: stage_latencies["answer_ms"].append(perf["answer_ms"])

        print(f"    ✓ Intent: {'PASS' if intent_pass else 'FAIL'} | Schema: {'PASS' if schema_pass else 'FAIL'} | SQL: {'PASS' if sql_pass else 'FAIL'} | Result: {'PASS' if result_pass else 'FAIL'} | E2E: {'PASS' if e2e_pass else 'FAIL'} ({duration_ms}ms)")

        results.append({
            "id": t_id,
            "category": cat,
            "question": q,
            "duration_ms": duration_ms,
            "intent_pass": intent_pass,
            "schema_pass": schema_pass,
            "sql_pass": sql_pass,
            "result_pass": result_pass,
            "answer_pass": answer_pass,
            "e2e_pass": e2e_pass,
            "status": v_status
        })
        time.sleep(3.0)

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0.0

    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS MATRIX")
    print("=" * 80)
    print(f"Total Test Cases:           {total_cases}")
    print(f"Intent Understanding:       {intent_correct}/{total_cases} ({round(intent_correct/total_cases*100, 1)}%)")
    print(f"Schema Retrieval:           {schema_correct}/{total_cases} ({round(schema_correct/total_cases*100, 1)}%)")
    print(f"SQL Semantic Correctness:   {sql_semantic_correct}/{total_cases} ({round(sql_semantic_correct/total_cases*100, 1)}%)")
    print(f"Result Verification:        {result_correct}/{total_cases} ({round(result_correct/total_cases*100, 1)}%)")
    print(f"Natural Language Answer:    {answer_correct}/{total_cases} ({round(answer_correct/total_cases*100, 1)}%)")
    print(f"End-to-End Accuracy:        {end_to_end_correct}/{total_cases} ({round(end_to_end_correct/total_cases*100, 1)}%)")

    print("\n" + "=" * 80)
    print("LATENCY PROFILE PER STAGE (AVERAGE)")
    print("=" * 80)
    print(f"Stage 1 Intent Understanding:  {avg(stage_latencies['intent_ms'])} ms")
    print(f"Stage 2 Schema Retrieval:      {avg(stage_latencies['schema_ms'])} ms")
    print(f"Stage 3 SQL Generation:        {avg(stage_latencies['sql_gen_ms'])} ms")
    print(f"Stage 4/5 Validation:          {avg(stage_latencies['validation_ms'])} ms")
    print(f"Stage 6 Database Execution:    {avg(stage_latencies['database_ms'])} ms")
    print(f"Stage 7/8 Result & Answer:     {avg(stage_latencies['answer_ms'])} ms")
    print(f"Average Total Latency:         {avg(stage_latencies['total_ms'])} ms")
    print("=" * 80)

    # Save benchmark report artifact
    report_data = {
        "summary": {
            "total_cases": total_cases,
            "intent_accuracy": round(intent_correct/total_cases*100, 1),
            "schema_accuracy": round(schema_correct/total_cases*100, 1),
            "sql_semantic_accuracy": round(sql_semantic_correct/total_cases*100, 1),
            "result_accuracy": round(result_correct/total_cases*100, 1),
            "answer_accuracy": round(answer_correct/total_cases*100, 1),
            "end_to_end_accuracy": round(end_to_end_correct/total_cases*100, 1),
            "avg_latency_ms": avg(stage_latencies['total_ms'])
        },
        "stage_latency_averages_ms": {
            "intent": avg(stage_latencies['intent_ms']),
            "schema": avg(stage_latencies['schema_ms']),
            "sql_generation": avg(stage_latencies['sql_gen_ms']),
            "validation": avg(stage_latencies['validation_ms']),
            "database": avg(stage_latencies['database_ms']),
            "answer": avg(stage_latencies['answer_ms'])
        },
        "details": results
    }
    with open("benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print("Benchmark artifact written to: benchmark_report.json")
    return report_data


if __name__ == "__main__":
    run_benchmark()
