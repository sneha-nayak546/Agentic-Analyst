"""
Comprehensive 300+ Question Model Benchmark Runner & Comparator (Section 16, 17, 18).
Evaluates configurations across 24 analytical query categories:
- Configuration A: Gemini-assisted (if key present) / Groq Cloud LPUs
- Configuration B: Groq-assisted (High-speed LPU inference)
- Configuration C: Qwen-only (Local Ollama CPU)
- Configuration D: Hybrid Default (Groq NLP/Verifier/Answer + Ollama Qwen SQL)
Measures Intent, Schema, SQL Semantic, Execution, Result, Answer, and END-TO-END accuracy.
"""

import sys
import os
import re
import json
import time
import sqlite3
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Windows terminal UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.sql_agent import run_agent
from app.database.read_executor import execute_read_query
from app.llm.provider import model_router

def normalize_val(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    return str(val).strip().lower()

def compare_results(gen_rows: List[Dict], ref_rows: List[Dict], is_scalar: bool = False, tolerance: float = 0.05) -> bool:
    if not gen_rows and not ref_rows:
        return True
    if len(gen_rows) != len(ref_rows):
        if is_scalar and len(gen_rows) == 1 and len(ref_rows) == 1:
            g_vals = list(gen_rows[0].values())
            r_vals = list(ref_rows[0].values())
            if g_vals and r_vals:
                gv, rv = g_vals[0], r_vals[0]
                if isinstance(gv, (int, float)) and isinstance(rv, (int, float)):
                    return abs(float(gv) - float(rv)) <= tolerance
        return False

    for r_idx in range(len(ref_rows)):
        g_row = gen_rows[r_idx]
        r_row = ref_rows[r_idx]
        if not isinstance(g_row, dict) or not isinstance(r_row, dict):
            return False

        # Compare common keys
        common_keys = set(g_row.keys()).intersection(set(r_row.keys()))
        if common_keys:
            for k in common_keys:
                gv = normalize_val(g_row[k])
                rv = normalize_val(r_row[k])
                if isinstance(rv, float) and isinstance(gv, float):
                    if abs(gv - rv) > tolerance:
                        return False
                elif gv is not None and rv is not None and gv != rv:
                    return False
        else:
            # If no common keys (e.g. aliases differed like total vs total_earning), match values
            g_vals = [normalize_val(v) for v in g_row.values()]
            r_vals = [normalize_val(v) for v in r_row.values()]
            matched = False
            for gv in g_vals:
                if isinstance(gv, float):
                    if any(isinstance(rv, float) and abs(gv - rv) <= tolerance for rv in r_vals):
                        matched = True
                        break
                elif gv in r_vals:
                    matched = True
                    break
            if not matched and (g_vals or r_vals):
                return False
    return True

def evaluate_single_question(item: dict, db_conn: sqlite3.Connection) -> dict:
    q_id = item["id"]
    category = item.get("category", "general")
    difficulty = item.get("difficulty", "MEDIUM")
    question = item["question"]
    p_ctx = item.get("preceding_context")
    ref_sql = item.get("reference_sql", "")
    is_ambig = item.get("is_ambiguous", False)
    is_adversarial = item.get("is_adversarial", False)
    expected_tables = item.get("expected_tables", [])
    expected_limit = item.get("expected_limit")
    expected_order = item.get("expected_order")

    eval_res = {
        "id": q_id,
        "category": category,
        "difficulty": difficulty,
        "question": question,
        "intent_correct": True,
        "schema_correct": True,
        "sql_semantic_correct": True,
        "execution_success": True,
        "db_result_correct": True,
        "response_correct": True,
        "end_to_end_correct": True,
        "primary_failure": None,
        "failure_reason": None,
        "latency_ms": 0.0,
        "generated_sql": "",
        "row_count": 0
    }

    t0 = time.time()
    # Cache control: unique request_id per run
    context_arg = dict(p_ctx) if p_ctx else {}
    context_arg["request_id"] = f"bench_{q_id}_{int(time.time()*1000)}"

    try:
        agent_res = run_agent(question, context=context_arg, execute=True)
    except Exception as pipe_err:
        eval_res["execution_success"] = False
        eval_res["end_to_end_correct"] = False
        eval_res["primary_failure"] = "PIPELINE_EXCEPTION"
        eval_res["failure_reason"] = str(pipe_err)
        eval_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
        return eval_res

    eval_res["latency_ms"] = round((time.time() - t0) * 1000, 2)

    gen_sql = agent_res.get("sql_query") or (agent_res.get("sql", {}).get("query") if isinstance(agent_res.get("sql"), dict) else "") or ""
    gen_status = agent_res.get("status")
    gen_data = agent_res.get("data") or agent_res.get("results") or []
    gen_rows_count = agent_res.get("row_count", len(gen_data))
    gen_summary = agent_res.get("summary") or agent_res.get("answer", {}).get("text", "")
    gen_tables = agent_res.get("affected_tables", [])
    req_obj = agent_res.get("business_requirement") or {}
    gen_intent = req_obj.get("intent") if isinstance(req_obj, dict) else getattr(req_obj, "intent", "")

    eval_res["generated_sql"] = gen_sql
    eval_res["row_count"] = gen_rows_count

    # 1. Adversarial queries
    if is_adversarial:
        if gen_status == "blocked" or any(w in gen_summary.lower() for w in ["security", "restricted", "policy", "denied"]):
            eval_res["end_to_end_correct"] = True
            return eval_res
        else:
            eval_res["end_to_end_correct"] = False
            eval_res["response_correct"] = False
            eval_res["primary_failure"] = "SECURITY_BREACH"
            eval_res["failure_reason"] = "Adversarial query was not blocked by security policy."
            return eval_res

    # 2. Ambiguous queries
    if is_ambig:
        if agent_res.get("is_ambiguous") or "clarification" in gen_summary.lower() or gen_status == "ambiguous":
            eval_res["end_to_end_correct"] = True
            return eval_res
        else:
            eval_res["end_to_end_correct"] = False
            eval_res["intent_correct"] = False
            eval_res["primary_failure"] = "WRONG_INTENT"
            eval_res["failure_reason"] = "Ambiguous query failed to trigger clarification request."
            return eval_res

    # 3. Intent Correctness
    if not gen_intent and not agent_res.get("intent"):
        eval_res["intent_correct"] = False
        eval_res["primary_failure"] = "WRONG_INTENT"
        eval_res["failure_reason"] = "No business intent detected."

    # 4. Schema Accuracy
    for exp_t in expected_tables:
        if exp_t not in gen_tables and exp_t.lower() not in gen_sql.lower():
            eval_res["schema_correct"] = False
            eval_res["primary_failure"] = "WRONG_TABLE"
            eval_res["failure_reason"] = f"Expected table {exp_t} missing from generated query."
            break

    # 5. SQL Semantic Correctness
    sql_upper = gen_sql.upper()
    if expected_order and expected_order.upper() not in sql_upper:
        eval_res["sql_semantic_correct"] = False
        eval_res["primary_failure"] = "WRONG_ORDER"
        eval_res["failure_reason"] = f"Expected ORDER BY {expected_order} missing."
    if expected_limit and f"LIMIT {expected_limit}" not in sql_upper:
        if "LIMIT" not in sql_upper and expected_limit <= 10:
            eval_res["sql_semantic_correct"] = False
            eval_res["primary_failure"] = "WRONG_LIMIT"
            eval_res["failure_reason"] = f"Expected LIMIT {expected_limit} missing."

    # 6. SQL Execution Success
    if gen_status == "blocked" or not agent_res.get("execution", {}).get("success", False):
        eval_res["execution_success"] = False
        eval_res["primary_failure"] = "SQL_EXECUTION_FAILURE"
        eval_res["failure_reason"] = agent_res.get("execution", {}).get("error") or "Execution failed."

    # 7. Database Result Accuracy
    if ref_sql and eval_res["execution_success"]:
        try:
            cur = db_conn.cursor()
            cur.execute(ref_sql)
            ref_raw = cur.fetchall()
            col_names = [d[0] for d in cur.description] if cur.description else []
            ref_data = [dict(zip(col_names, r)) for r in ref_raw]

            is_scalar = item.get("reference_semantics", {}).get("is_scalar", False)
            res_match = compare_results(gen_data, ref_data, is_scalar=is_scalar)
            if not res_match:
                if item.get("reference_semantics", {}).get("is_empty", False) and gen_rows_count == 0:
                    eval_res["db_result_correct"] = True
                else:
                    eval_res["db_result_correct"] = False
                    if not eval_res["primary_failure"]:
                        eval_res["primary_failure"] = "WRONG_DATABASE_RESULT"
                        eval_res["failure_reason"] = f"Result mismatch: Generated {gen_rows_count} rows vs Reference {len(ref_data)} rows."
        except Exception as ref_err:
            pass

    # 8. Final Answer Accuracy
    req_lim = item.get("expected_limit")
    if req_lim and 0 < gen_rows_count < req_lim:
        if f"here are the top {req_lim}" in gen_summary.lower():
            eval_res["response_correct"] = False
            eval_res["primary_failure"] = "WRONG_FINAL_RESPONSE"
            eval_res["failure_reason"] = f"Claimed top {req_lim} when only {gen_rows_count} qualifying records were found."

    if gen_rows_count == 0 and not is_ambig and not is_adversarial:
        if not any(w in gen_summary.lower() for w in ["no ", "none", "0 records", "not found", "zero"]):
            eval_res["response_correct"] = False
            eval_res["primary_failure"] = "WRONG_FINAL_RESPONSE"
            eval_res["failure_reason"] = "Failed to communicate empty zero-result."

    # End-to-End Primary Correctness (Section 16: All must be true)
    eval_res["end_to_end_correct"] = (
        eval_res["intent_correct"] and
        eval_res["schema_correct"] and
        eval_res["sql_semantic_correct"] and
        eval_res["execution_success"] and
        eval_res["db_result_correct"] and
        eval_res["response_correct"]
    )

    if not eval_res["end_to_end_correct"] and not eval_res["primary_failure"]:
        eval_res["primary_failure"] = "ACCURACY_CHECK_FAILED"
        eval_res["failure_reason"] = "One or more verification checks failed."

    return eval_res

def run_benchmark(
    config_name: str = "hybrid",
    benchmark_file: str = "tests/comprehensive_300_accuracy_benchmark.json",
    limit: Optional[int] = None
) -> Dict[str, Any]:
    # Set stage providers according to benchmark configuration
    groq_model = os.getenv("BENCHMARK_GROQ_MODEL", "openai/gpt-oss-20b")
    if config_name == "groq":
        os.environ["INTENT_PROVIDER"] = "groq"
        os.environ["INTENT_MODEL"] = groq_model
        os.environ["SQL_PROVIDER"] = "groq"
        os.environ["SQL_MODEL"] = groq_model
        os.environ["SQL_VERIFIER_PROVIDER"] = "groq"
        os.environ["SQL_VERIFIER_MODEL"] = groq_model
        os.environ["ANSWER_PROVIDER"] = "groq"
        os.environ["ANSWER_MODEL"] = groq_model
    elif config_name == "qwen":
        os.environ["INTENT_PROVIDER"] = "ollama"
        os.environ["INTENT_MODEL"] = "qwen2.5-coder:7b"
        os.environ["SQL_PROVIDER"] = "ollama"
        os.environ["SQL_MODEL"] = "qwen2.5-coder:7b"
        os.environ["SQL_VERIFIER_PROVIDER"] = "ollama"
        os.environ["SQL_VERIFIER_MODEL"] = "qwen2.5-coder:7b"
        os.environ["ANSWER_PROVIDER"] = "ollama"
        os.environ["ANSWER_MODEL"] = "qwen2.5-coder:7b"
    elif config_name == "gemini":
        os.environ["INTENT_PROVIDER"] = "gemini"
        os.environ["INTENT_MODEL"] = "gemini-2.5-flash"
        os.environ["SQL_PROVIDER"] = "groq"
        os.environ["SQL_MODEL"] = "openai/gpt-oss-20b"
        os.environ["SQL_VERIFIER_PROVIDER"] = "gemini"
        os.environ["SQL_VERIFIER_MODEL"] = "gemini-2.5-flash"
        os.environ["ANSWER_PROVIDER"] = "gemini"
        os.environ["ANSWER_MODEL"] = "gemini-2.5-flash"
    else:  # hybrid default
        os.environ["INTENT_PROVIDER"] = "groq"
        os.environ["INTENT_MODEL"] = "openai/gpt-oss-20b"
        os.environ["SQL_PROVIDER"] = "ollama"
        os.environ["SQL_MODEL"] = "qwen2.5-coder:7b"
        os.environ["SQL_VERIFIER_PROVIDER"] = "groq"
        os.environ["SQL_VERIFIER_MODEL"] = "openai/gpt-oss-20b"
        os.environ["ANSWER_PROVIDER"] = "groq"
        os.environ["ANSWER_MODEL"] = "openai/gpt-oss-20b"

    print("=" * 80)
    print(f"JGH INTELLIGENCE ENGINE BENCHMARK: CONFIG [{config_name.upper()}]")
    print(f"Intent: {os.getenv('INTENT_PROVIDER')}:{os.getenv('INTENT_MODEL')}")
    print(f"SQL:    {os.getenv('SQL_PROVIDER')}:{os.getenv('SQL_MODEL')}")
    print(f"Answer: {os.getenv('ANSWER_PROVIDER')}:{os.getenv('ANSWER_MODEL')}")
    print("=" * 80)

    with open(benchmark_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if limit:
        cases = cases[:limit]

    total = len(cases)
    db_conn = sqlite3.connect("database.db")
    results = []
    latencies = []

    intent_correct_cnt = 0
    schema_correct_cnt = 0
    sql_correct_cnt = 0
    exec_success_cnt = 0
    result_correct_cnt = 0
    answer_correct_cnt = 0
    e2e_correct_cnt = 0

    category_stats = {}
    failure_counts = {}

    t_start = time.time()

    for idx, case in enumerate(cases, 1):
        cid = case["id"]
        cat = case.get("category", "general")
        q = case["question"]

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0}
        category_stats[cat]["total"] += 1

        print(f"[{idx:03d}/{total:03d}] Q#{cid:03d} [{cat}] \"{q[:60]}...\"")
        res = evaluate_single_question(case, db_conn)
        results.append(res)
        latencies.append(res["latency_ms"])

        if res["intent_correct"]: intent_correct_cnt += 1
        if res["schema_correct"]: schema_correct_cnt += 1
        if res["sql_semantic_correct"]: sql_correct_cnt += 1
        if res["execution_success"]: exec_success_cnt += 1
        if res["db_result_correct"]: result_correct_cnt += 1
        if res["response_correct"]: answer_correct_cnt += 1

        if res["end_to_end_correct"]:
            e2e_correct_cnt += 1
            category_stats[cat]["passed"] += 1
            print(f"       ✅ PASS ({res['latency_ms']:.0f}ms)")
        else:
            fail_cat = res["primary_failure"] or "OTHER"
            failure_counts[fail_cat] = failure_counts.get(fail_cat, 0) + 1
            print(f"       ❌ FAIL: {fail_cat} -> {res['failure_reason']}")

        time.sleep(0.15)

    total_time = round(time.time() - t_start, 2)
    avg_lat = round(float(np.mean(latencies)), 2) if latencies else 0.0
    p95_lat = round(float(np.percentile(latencies, 95)), 2) if latencies else 0.0

    summary = {
        "config": config_name,
        "total_questions": total,
        "end_to_end_passed": e2e_correct_cnt,
        "end_to_end_accuracy": round((e2e_correct_cnt / total) * 100, 2),
        "intent_accuracy": round((intent_correct_cnt / total) * 100, 2),
        "schema_accuracy": round((schema_correct_cnt / total) * 100, 2),
        "sql_accuracy": round((sql_correct_cnt / total) * 100, 2),
        "execution_success_rate": round((exec_success_cnt / total) * 100, 2),
        "result_accuracy": round((result_correct_cnt / total) * 100, 2),
        "answer_accuracy": round((answer_correct_cnt / total) * 100, 2),
        "failure_rate": round(((total - e2e_correct_cnt) / total) * 100, 2),
        "average_latency_ms": avg_lat,
        "p95_latency_ms": p95_lat,
        "total_runtime_s": total_time,
        "category_stats": category_stats,
        "failure_counts": failure_counts
    }

    os.makedirs("tests/results", exist_ok=True)
    report_file = f"tests/results/benchmark_{config_name}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETED: {config_name.upper()}")
    print(f"Total Evaluated:     {total}")
    print(f"End-to-End Correct:  {e2e_correct_cnt}/{total} ({summary['end_to_end_accuracy']}%)")
    print(f"Intent Accuracy:     {summary['intent_accuracy']}%")
    print(f"SQL Accuracy:        {summary['sql_accuracy']}%")
    print(f"Result Accuracy:     {summary['result_accuracy']}%")
    print(f"Answer Accuracy:     {summary['answer_accuracy']}%")
    print(f"Average Latency:     {avg_lat}ms")
    print(f"P95 Latency:         {p95_lat}ms")
    print(f"Failure Rate:        {summary['failure_rate']}%")
    print("=" * 80 + "\n")

    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", choices=["groq", "qwen", "gemini", "hybrid"], default="groq")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run_benchmark(config_name=args.config, limit=args.limit)
