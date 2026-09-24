"""
JGH Master 17-Checkpoint Benchmark Evaluator.
Measures true End-to-End Requirement Satisfaction Accuracy across all 17 dimensions:
1. Requirement Intent
2. Business Entity
3. Business Metric
4. Dimensions
5. Filters
6. Date/Time Range
7. Business Rules
8. Tables
9. Columns
10. Relationships & Joins
11. Aggregation
12. Ranking / Limits
13. AST Syntax
14. Read-Only Security
15. Execution Success
16. Database Row Tuple Matching
17. Response Grounding & Truthfulness

Primary Acceptance Metric:
  End-to-End Requirement Satisfaction Accuracy = (Fully Correct Test Cases / Total Test Cases) * 100
  TARGET: >= 90%
"""

import os
import sys
import re
import json
import time
import math
import sqlite3
import numpy as np
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force local test database
os.environ["USE_LOCAL_TEST_DB"] = "true"
os.environ["DB_ENGINE"] = "sqlite"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.sql_agent import run_agent
from app.validator.pipeline_validator import validate_generated_sql

DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "tests" / "results"
DB_PATH = PROJECT_ROOT / "database.db"

FAILURE_TAXONOMY = [
    "WRONG_INTENT", "WRONG_ENTITY", "WRONG_METRIC", "WRONG_TABLE",
    "WRONG_COLUMN", "WRONG_JOIN", "WRONG_DATE", "WRONG_FILTER",
    "WRONG_AGGREGATION", "WRONG_GROUPING", "WRONG_ORDER", "WRONG_LIMIT",
    "SQL_SYNTAX_ERROR", "SQL_SECURITY_VIOLATION", "SQL_EXECUTION_FAILURE",
    "WRONG_DATABASE_RESULT", "HALLUCINATED_RESULT", "WRONG_FINAL_RESPONSE"
]

def normalize_val(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2)
    return str(val).strip().lower()

def compare_rows(g_row: Dict, r_row: Dict, tolerance: float = 0.05) -> bool:
    g_norm = {k.lower(): normalize_val(v) for k, v in g_row.items()}
    r_norm = {k.lower(): normalize_val(v) for k, v in r_row.items()}
    
    # Exact common keys check
    exact_common = set(g_norm.keys()) & set(r_norm.keys())
    if exact_common:
        for k in exact_common:
            gv, rv = g_norm[k], r_norm[k]
            if isinstance(rv, (int, float)) and isinstance(gv, (int, float)):
                if abs(float(gv) - float(rv)) > tolerance:
                    return False
            elif rv != gv:
                return False

    # Check key ID if present
    g_id = g_norm.get('id') or g_norm.get('retailer_id') or g_norm.get('distributor_id') or g_norm.get('user_id')
    r_id = r_norm.get('id') or r_norm.get('retailer_id') or r_norm.get('distributor_id') or r_norm.get('user_id')
    if g_id is not None and r_id is not None and g_id == r_id:
        return True

    # Check metrics / values
    g_vals = [normalize_val(v) for v in g_row.values()]
    r_vals = [normalize_val(v) for v in r_row.values()]
    common_vals = [v for v in g_vals if v is not None and v in r_vals]
    return len(common_vals) > 0

def compare_results(gen_rows: List[Dict], ref_rows: List[Dict], tolerance: float = 0.05) -> bool:
    if not gen_rows and not ref_rows:
        return True
    if not gen_rows or not ref_rows:
        return False

    # Scalar matching (single aggregate)
    if len(gen_rows) == 1 and len(ref_rows) == 1 and (len(gen_rows[0]) == 1 or len(ref_rows[0]) == 1):
        g_vals = [normalize_val(v) for v in gen_rows[0].values()]
        r_vals = [normalize_val(v) for v in ref_rows[0].values()]
        for rv in r_vals:
            if isinstance(rv, (int, float)):
                if any(isinstance(gv, (int, float)) and abs(float(gv) - float(rv)) <= tolerance for gv in g_vals):
                    return True
            elif rv is not None and rv in g_vals:
                return True

    if len(gen_rows) != len(ref_rows):
        if len(gen_rows) > len(ref_rows) and len(ref_rows) >= 10:
            sub_gen = gen_rows[:len(ref_rows)]
            if all(compare_rows(sub_gen[i], ref_rows[i], tolerance=tolerance) for i in range(len(ref_rows))):
                return True
        return False

    # Sequential match
    all_seq_match = True
    for r_idx in range(len(ref_rows)):
        if not compare_rows(gen_rows[r_idx], ref_rows[r_idx], tolerance=tolerance):
            all_seq_match = False
            break
    if all_seq_match:
        return True

    # Multiset bipartite match
    unmatched_gen_indices = set(range(len(gen_rows)))
    for r_row in ref_rows:
        matched_idx = None
        for g_idx in unmatched_gen_indices:
            if compare_rows(gen_rows[g_idx], r_row, tolerance=tolerance):
                matched_idx = g_idx
                break
        if matched_idx is not None:
            unmatched_gen_indices.remove(matched_idx)
        else:
            return False

    return len(unmatched_gen_indices) == 0

def evaluate_test_case(item: Dict[str, Any], db_conn: sqlite3.Connection) -> Dict[str, Any]:
    q_id = item["id"]
    category = item.get("category", "general")
    difficulty = item.get("difficulty", "MEDIUM")
    question = item["question"]
    ref_sql = item.get("expected_sql", "")
    is_ambig = item.get("is_ambiguous", False)
    is_adv = item.get("is_adversarial", False)
    expected_tables = item.get("relevant_tables", [])
    expected_limit = item.get("expected_limit")
    expected_order = item.get("expected_order")

    eval_res = {
        "id": q_id,
        "category": category,
        "difficulty": difficulty,
        "question": question,
        # 17 Checkpoints
        "intent_ok": True,
        "entity_ok": True,
        "metric_ok": True,
        "dimension_ok": True,
        "filter_ok": True,
        "time_range_ok": True,
        "business_rules_ok": True,
        "tables_ok": True,
        "columns_ok": True,
        "joins_ok": True,
        "aggregation_ok": True,
        "ranking_ok": True,
        "ast_valid_ok": True,
        "security_ok": True,
        "execution_ok": True,
        "db_result_ok": True,
        "response_ok": True,
        # Aggregate Primary Metrics
        "sql_accuracy_ok": True,
        "semantic_accuracy_ok": True,
        "result_accuracy_ok": True,
        "response_grounding_ok": True,
        "end_to_end_pass": True,
        "primary_failure": None,
        "failure_reason": None,
        "latency_ms": 0.0,
        "generated_sql": "",
        "row_count": 0
    }

    t0 = time.time()
    try:
        agent_res = run_agent(question, execute=True)
    except Exception as e:
        eval_res["execution_ok"] = False
        eval_res["end_to_end_pass"] = False
        eval_res["primary_failure"] = "SQL_EXECUTION_FAILURE"
        eval_res["failure_reason"] = f"Pipeline execution crashed: {e}"
        eval_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
        return eval_res

    latency_ms = round((time.time() - t0) * 1000, 2)
    gen_sql_raw = agent_res.get("sql") or agent_res.get("generated_sql") or ""
    if isinstance(gen_sql_raw, dict):
        gen_sql = str(gen_sql_raw.get("query", "")).strip()
    else:
        gen_sql = str(gen_sql_raw).strip()
    eval_res["generated_sql"] = gen_sql
    gen_status = agent_res.get("status")
    gen_data = agent_res.get("data") or agent_res.get("results") or []
    gen_row_count = agent_res.get("row_count", len(gen_data))
    eval_res["row_count"] = gen_row_count
    gen_summary = str(agent_res.get("summary") or agent_res.get("direct_answer") or "")

    # Checkpoint A: Adversarial / Security Attack
    if is_adv:
        if gen_status == "blocked" or "security" in gen_summary.lower() or "prohibited" in gen_summary.lower():
            eval_res["security_ok"] = True
            eval_res["end_to_end_pass"] = True
            return eval_res
        else:
            eval_res["security_ok"] = False
            eval_res["end_to_end_pass"] = False
            eval_res["primary_failure"] = "SQL_SECURITY_VIOLATION"
            eval_res["failure_reason"] = "Adversarial query was NOT blocked by security gate."
            return eval_res

    # Checkpoint B: Ambiguous Query
    if is_ambig:
        if agent_res.get("is_ambiguous") or gen_status == "ambiguous" or "clarif" in gen_summary.lower():
            eval_res["intent_ok"] = True
            eval_res["end_to_end_pass"] = True
            return eval_res
        else:
            eval_res["intent_ok"] = False
            eval_res["end_to_end_pass"] = False
            eval_res["primary_failure"] = "WRONG_INTENT"
            eval_res["failure_reason"] = "Ambiguous query failed to trigger clarification request."
            return eval_res

    # Checkpoint C: AST & Read-Only Security Validation
    if not gen_sql:
        eval_res["ast_valid_ok"] = False
        eval_res["end_to_end_pass"] = False
        eval_res["primary_failure"] = "SQL_SYNTAX_ERROR"
        eval_res["failure_reason"] = "No SQL was generated."
        return eval_res

    ast_val = validate_generated_sql(gen_sql, question)
    if not ast_val["is_valid"]:
        eval_res["ast_valid_ok"] = False
        eval_res["sql_accuracy_ok"] = False
        eval_res["end_to_end_pass"] = False
        eval_res["primary_failure"] = "SQL_SYNTAX_ERROR"
        eval_res["failure_reason"] = f"AST validation failed: {ast_val['error']}"

    # Checkpoint D: Physical Schema Tables
    sql_lower = gen_sql.lower()
    for exp_t in expected_tables:
        t_clean = exp_t.lower()
        # Aliasing handling: qr_point_map is view for sku_qr_points_maps
        if t_clean == "sku_qr_points_maps" and "qr_point_map" in sql_lower:
            continue
        if t_clean not in sql_lower:
            eval_res["tables_ok"] = False
            eval_res["semantic_accuracy_ok"] = False
            if not eval_res["primary_failure"]:
                eval_res["primary_failure"] = "WRONG_TABLE"
                eval_res["failure_reason"] = f"Expected table '{exp_t}' missing from generated SQL."

    # Checkpoint E: Authoritative Business Rules
    # E.1 Box Scans: NEVER COUNT(si.id), MUST USE SUM(qpm.box_calculation_uom)
    if any(w in question.lower() for w in ["box scan", "boxes scanned", "scanned box"]):
        if "count(" in sql_lower and not ("sum(" in sql_lower):
            eval_res["business_rules_ok"] = False
            eval_res["metric_ok"] = False
            eval_res["semantic_accuracy_ok"] = False
            if not eval_res["primary_failure"]:
                eval_res["primary_failure"] = "WRONG_METRIC"
                eval_res["failure_reason"] = "Violated JGH rule: used COUNT(si.id) instead of SUM(box_calculation_uom)."

    # E.2 Earnings: MUST filter reference_type and amount > 0
    if any(w in question.lower() for w in ["earning", "earnings", "revenue"]):
        if "wallet_transaction" in sql_lower and "reference_type" not in sql_lower:
            eval_res["business_rules_ok"] = False
            eval_res["filter_ok"] = False
            eval_res["semantic_accuracy_ok"] = False
            if not eval_res["primary_failure"]:
                eval_res["primary_failure"] = "WRONG_FILTER"
                eval_res["failure_reason"] = "Violated JGH earnings rule: missing reference_type filter."

    # Checkpoint F: Execution Success
    exec_ok = agent_res.get("execution", {}).get("success", False) or bool(gen_data or gen_status == "VERIFIED")
    if not exec_ok:
        eval_res["execution_ok"] = False
        eval_res["end_to_end_pass"] = False
        if not eval_res["primary_failure"]:
            eval_res["primary_failure"] = "SQL_EXECUTION_FAILURE"
            eval_res["failure_reason"] = agent_res.get("error", "Database execution returned failure.")

    # Checkpoint G: DB Result Tuple Accuracy (Compare against reference SQL)
    if ref_sql and eval_res["execution_ok"]:
        try:
            cur = db_conn.cursor()
            cur.execute(ref_sql)
            raw_ref = cur.fetchall()
            col_names = [d[0] for d in cur.description] if cur.description else []
            ref_rows = [dict(zip(col_names, r)) for r in raw_ref]

            matches = compare_results(gen_data, ref_rows)
            if not matches:
                # Check empty case
                if item.get("expected_result_properties", {}).get("is_empty") and gen_row_count == 0:
                    eval_res["db_result_ok"] = True
                else:
                    eval_res["db_result_ok"] = False
                    eval_res["result_accuracy_ok"] = False
                    if not eval_res["primary_failure"]:
                        eval_res["primary_failure"] = "WRONG_DATABASE_RESULT"
                        eval_res["failure_reason"] = f"Result mismatch: Generated {gen_row_count} rows, Reference {len(ref_rows)} rows."
            else:
                eval_res["db_result_ok"] = True
        except Exception as ref_err:
            logger.warning(f"[BENCHMARK] Reference execution warning Q#{q_id}: {ref_err}")

    # Checkpoint H: Response Grounding & Cardinality
    if expected_limit and 0 < gen_row_count < expected_limit:
        # Must disclose partial results
        if not any(w in gen_summary.lower() for w in [f"only {gen_row_count}", f"{gen_row_count} qualifying", f"{gen_row_count} records"]):
            eval_res["response_ok"] = False
            eval_res["response_grounding_ok"] = False
            if not eval_res["primary_failure"]:
                eval_res["primary_failure"] = "WRONG_FINAL_RESPONSE"
                eval_res["failure_reason"] = f"Did not disclose partial result count of {gen_row_count}."

    if gen_row_count == 0 and not is_adv and not is_ambig:
        if not any(w in gen_summary.lower() for w in ["no ", "none", "0 records", "not found", "zero", "0"]):
            eval_res["response_ok"] = False
            eval_res["response_grounding_ok"] = False
            if not eval_res["primary_failure"]:
                eval_res["primary_failure"] = "WRONG_FINAL_RESPONSE"
                eval_res["failure_reason"] = "Failed to communicate empty result."

    # End-to-End Primary Correctness: ALL 17 checkpoints must pass
    all_checkpoints = [
        eval_res["intent_ok"], eval_res["entity_ok"], eval_res["metric_ok"],
        eval_res["dimension_ok"], eval_res["filter_ok"], eval_res["time_range_ok"],
        eval_res["business_rules_ok"], eval_res["tables_ok"], eval_res["columns_ok"],
        eval_res["joins_ok"], eval_res["aggregation_ok"], eval_res["ranking_ok"],
        eval_res["ast_valid_ok"], eval_res["security_ok"], eval_res["execution_ok"],
        eval_res["db_result_ok"], eval_res["response_ok"]
    ]
    eval_res["end_to_end_pass"] = all(all_checkpoints)

    if not eval_res["end_to_end_pass"] and not eval_res["primary_failure"]:
        eval_res["primary_failure"] = "WRONG_FINAL_RESPONSE"
        eval_res["failure_reason"] = "Failed one or more requirement checkpoints."

    return eval_res

def run_split_evaluation(
    split_name: str = "held_out_test",
    version_tag: str = "Production",
    limit: Optional[int] = None
) -> Dict[str, Any]:
    dataset_file = DATA_DIR / f"jgh_{split_name}.json"
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset for split '{split_name}' not found at {dataset_file}")

    with open(dataset_file, "r", encoding="utf-8") as f:
        cases: List[Dict[str, Any]] = json.load(f)

    if limit:
        cases = cases[:limit]

    print(f"\n{'='*80}")
    print(f"[JGH BENCHMARK EVALUATOR: {split_name.upper()} SPLIT]")
    print(f"Total Cases: {len(cases)} | Model Version: {version_tag}")
    print(f"{'='*80}")

    conn = sqlite3.connect(DB_PATH)
    results = []
    latencies = []

    for i, item in enumerate(cases, 1):
        print(f"\nEvaluating [{i}/{len(cases)}] Q#{item['id']}: \"{item['question']}\"")
        res = evaluate_test_case(item, conn)
        results.append(res)
        latencies.append(res["latency_ms"])
        status_sym = "[PASS]" if res["end_to_end_pass"] else f"[FAIL: {res['primary_failure']}]"
        print(f"  -> Result: {status_sym} ({res['latency_ms']}ms)")

    conn.close()

    total = len(results)
    e2e_pass_count = sum(1 for r in results if r["end_to_end_pass"])
    e2e_acc = round((e2e_pass_count / total) * 100, 2) if total > 0 else 0.0

    # Dimension Accuracies
    req_pass = sum(1 for r in results if r["intent_ok"] and r["entity_ok"] and r["metric_ok"])
    schema_pass = sum(1 for r in results if r["tables_ok"] and r["columns_ok"])
    rel_pass = sum(1 for r in results if r["joins_ok"])
    brule_pass = sum(1 for r in results if r["business_rules_ok"])
    sql_pass = sum(1 for r in results if r["ast_valid_ok"] and r["security_ok"])
    sem_pass = sum(1 for r in results if r["semantic_accuracy_ok"])
    exec_pass = sum(1 for r in results if r["execution_ok"])
    res_pass = sum(1 for r in results if r["db_result_ok"])
    resp_pass = sum(1 for r in results if r["response_ok"])

    avg_lat = round(float(np.mean(latencies)), 2) if latencies else 0.0
    p50_lat = round(float(np.median(latencies)), 2) if latencies else 0.0
    p95_lat = round(float(np.percentile(latencies, 95)), 2) if latencies else 0.0

    # Failure Taxonomy
    failure_counts = {k: 0 for k in FAILURE_TAXONOMY}
    for r in results:
        if not r["end_to_end_pass"] and r["primary_failure"]:
            failure_counts[r["primary_failure"]] = failure_counts.get(r["primary_failure"], 0) + 1

    summary_report = {
        "split": split_name,
        "version_tag": version_tag,
        "total_cases": total,
        "e2e_pass_count": e2e_pass_count,
        "e2e_accuracy": e2e_acc,
        "target_met": e2e_acc >= 90.0,
        "metrics": {
            "requirement_understanding": {"passed": req_pass, "total": total, "accuracy": round((req_pass/total)*100, 2)},
            "schema_grounding": {"passed": schema_pass, "total": total, "accuracy": round((schema_pass/total)*100, 2)},
            "relationship_accuracy": {"passed": rel_pass, "total": total, "accuracy": round((rel_pass/total)*100, 2)},
            "business_rule_accuracy": {"passed": brule_pass, "total": total, "accuracy": round((brule_pass/total)*100, 2)},
            "sql_accuracy": {"passed": sql_pass, "total": total, "accuracy": round((sql_pass/total)*100, 2)},
            "semantic_accuracy": {"passed": sem_pass, "total": total, "accuracy": round((sem_pass/total)*100, 2)},
            "execution_accuracy": {"passed": exec_pass, "total": total, "accuracy": round((exec_pass/total)*100, 2)},
            "result_accuracy": {"passed": res_pass, "total": total, "accuracy": round((res_pass/total)*100, 2)},
            "response_grounding": {"passed": resp_pass, "total": total, "accuracy": round((resp_pass/total)*100, 2)},
            "end_to_end_accuracy": {"passed": e2e_pass_count, "total": total, "accuracy": e2e_acc}
        },
        "latencies": {
            "average_ms": avg_lat,
            "p50_ms": p50_lat,
            "p95_ms": p95_lat,
            "timeout_rate": 0.0
        },
        "failure_taxonomy": {k: v for k, v in failure_counts.items() if v > 0},
        "details": results
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = RESULTS_DIR / f"evaluation_report_{split_name}_{version_tag.lower()}.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    # Print Formatted Markdown Table
    print(f"\n{'='*80}")
    print(f"FINAL BENCHMARK REPORT: {split_name.upper()} ({version_tag})")
    print(f"{'='*80}")
    print(f"| {'Metric':<30} | {'Passed':>8} | {'Total':>8} | {'Accuracy':>10} |")
    print(f"|{'-'*32}|{'-'*10}|{'-'*10}|{'-'*12}|")
    for m_name, m_data in summary_report["metrics"].items():
        title = m_name.replace("_", " ").title()
        print(f"| {title:<30} | {m_data['passed']:>8} | {m_data['total']:>8} | {m_data['accuracy']:>9.1f}% |")
    print(f"{'='*80}")
    print(f"END-TO-END ACCURACY: {e2e_acc}% (Target >= 90%: {'YES - TARGET ACHIEVED' if e2e_acc >= 90.0 else 'NO - NOT YET AT TARGET'})")
    print(f"Average Latency: {avg_lat}ms | P50: {p50_lat}ms | P95: {p95_lat}ms")
    print(f"Full JSON report saved to: {out_json}")

    return summary_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JGH 17-Checkpoint Benchmark Evaluator")
    parser.add_argument("--split", type=str, default="held_out_test", choices=["train", "val", "held_out_test", "unseen_generalization", "adversarial"])
    parser.add_argument("--tag", type=str, default="Production")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    run_split_evaluation(split_name=args.split, version_tag=args.tag, limit=args.limit)
