import os
import sys
import json
import time

# Ensure Windows encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.sql_agent import run_agent

QUESTIONS = [
    "Show all retailers",
    "Generate a table of retailers linked to distributor 5997.",
    "Generate a table of retailers linked to distributor 5997, and include a column for their individual total earnings for the current month.",
    "Show the top 5 retailers by wallet balance.",
    "Show retailer earnings for July 2026.",
    "Show the total wallet amount for July 2026.",
    "Show distributors with their retailer count.",
    "Show retailers from Karnataka.",
    "Show retailers linked to distributor 99999999.",  # Invalid / non-existent distributor ID
    "Show data for 2026"  # Ambiguous question that should require clarification
]

def format_trace(idx: int, question: str, result: dict):
    print("\n" + "=" * 80)
    print(f"TEST {idx + 1}/10: {question}")
    print("=" * 80)

    print("\nOriginal Question:")
    print(f"  {result.get('question')}")

    print("\n↓ BusinessRequirement:")
    req = result.get("business_requirement") or {}
    print(f"  Intent:        {req.get('intent')}")
    print(f"  Entities:      {req.get('entities')}")
    print(f"  Specific IDs:  {req.get('specific_ids')}")
    print(f"  Metrics:       {req.get('metrics')}")
    print(f"  Filters:       {req.get('filters')}")
    print(f"  Output Format: {req.get('output_format')}")
    if req.get("clarification_required") or result.get("is_ambiguous"):
        print(f"  Clarification: {result.get('clarification')}")

    print("\n↓ Retrieved Schema:")
    exec_plan = result.get("execution_plan") or {}
    print(f"  Relevant Tables:  {result.get('affected_tables') or exec_plan.get('relevant_tables')}")
    print(f"  Relevant Columns: {exec_plan.get('relevant_columns')}")

    print("\n↓ ExecutionPlan:")
    print(f"  Required Joins: {exec_plan.get('required_joins')}")
    print(f"  Grouping:       {exec_plan.get('grouping')}")
    print(f"  Sorting:        {exec_plan.get('sorting')}")
    print(f"  Limit:          {exec_plan.get('limit')}")

    print("\n↓ Generated SQL:")
    print(f"  {result.get('generated_sql') or result.get('optimized_sql')}")

    print("\n↓ AST Validation:")
    val = result.get("validation") or {}
    print(f"  Status: {val.get('status')} {('- ' + val.get('reason')) if val.get('reason') else ''}")

    print("\n↓ Semantic Validation:")
    res_acc = result.get("result_accuracy") or {}
    print(f"  Result Confidence: {result.get('result_confidence') or res_acc.get('result_confidence')}")
    print(f"  Accuracy Message:  {result.get('accuracy_message') or res_acc.get('accuracy_message')}")

    print("\n↓ Correction Attempts:")
    thinking = result.get("thinking_steps") or []
    attempts = [step for step in thinking if "Attempt" in step]
    print(f"  Total Attempt Steps: {len(attempts) if attempts else 1}")
    for a in attempts:
        print(f"    • {a}")

    print("\n↓ Database Result:")
    execution = result.get("execution") or {}
    data = execution.get("data") or []
    print(f"  Success:   {execution.get('success')}")
    print(f"  Row Count: {len(data)}")
    print(f"  Columns:   {execution.get('columns')}")
    if data:
        print(f"  Sample Record: {data[0]}")

    print("\n↓ Result Validation:")
    print(f"  Status: {result.get('status')}")

    print("\n↓ Final Response:")
    print(result.get("summary") or "No response generated.")
    print("-" * 80)

def main():
    print("=" * 80)
    print("STARTING STEP 11: 10 MANUAL VERIFICATION PIPELINE TESTS")
    print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results_summary = []

    for i, q in enumerate(QUESTIONS):
        t0 = time.time()
        try:
            res = run_agent(q, execute=True)
            elapsed = round(time.time() - t0, 2)
            res["test_elapsed_seconds"] = elapsed
            format_trace(i, q, res)
            results_summary.append({
                "id": i + 1,
                "question": q,
                "status": res.get("status"),
                "elapsed_s": elapsed,
                "sql": res.get("optimized_sql") or res.get("generated_sql"),
                "row_count": len(res.get("execution", {}).get("data", [])),
                "summary": res.get("summary")
            })
        except Exception as e:
            elapsed = round(time.time() - t0, 2)
            print(f"\n[ERROR ON TEST {i+1}]: {e}")
            results_summary.append({
                "id": i + 1,
                "question": q,
                "status": "error",
                "elapsed_s": elapsed,
                "error": str(e)
            })

    with open("step11_results.json", "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, default=str)

    print("\n" + "=" * 80)
    print("STEP 11 TESTING COMPLETE. Results saved to step11_results.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
