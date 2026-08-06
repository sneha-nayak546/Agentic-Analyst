import re
import time
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from app.llm.sql_generator import generate_sql
from app.prompt.prompt_builder import build_sql_prompt
from app.utils.sql_cleaner import clean_sql
from app.validator.sql_ast_validator import validate_sql, SQLValidationError
from app.retriever.retriever import retrieve_schema, retrieve_sql_history
from app.database.read_executor import execute_read_query, get_execution_plan
from app.agent.ambiguity_checker import check_ambiguity
from app.knowledge.knowledge_graph import get_knowledge_graph




def compute_confidence(validation: dict, resolution: dict, execution_plan: dict) -> int:
    score = 100
    if execution_plan.get("cost", 0.0) > 1000:
        score -= 10
    if resolution.get("is_multi_table") and not resolution.get("detected_joins"):
        score -= 15
    return max(0, min(100, int(score)))


def explain_sql(question: str, sql: str) -> str:
    prompt = f"User asked: '{question}'. \n\nGenerated SQL: {sql}\n\nExplain this SQL query step-by-step in natural language briefly. Do not include the SQL query itself in your response."
    try:
        explanation = generate_sql(prompt, temperature=0.3)
        return explanation
    except Exception:
        return "Explanation not available."


def run_agent(question: str, history_context: str = "", execute: bool = True) -> dict:
    """
    Enterprise AI SQL Agent Pipeline with Multi-Step Reasoning,
    Self-Correction, EXPLAIN validation, and AST validation.
    """
    t_start = time.time()
    q_clean = question.strip()
    q_key = q_clean.lower()

    print("\n" + "=" * 70)
    print("USER QUESTION:", q_clean)
    print("=" * 70)

    thinking_steps = []



    # 2. Check Ambiguity & Business Logic Validation
    ambiguity = check_ambiguity(q_clean)
    if ambiguity:
        return {
            "question": q_clean,
            "is_ambiguous": True,
            "clarification": ambiguity["clarification"],
            "options": ambiguity["options"],
            "thinking_steps": ["Checking query clarity...", "Ambiguity detected."],
            "status": "ambiguous"
        }

    # 3. Multi-Step Reasoning: Intent & Entities
    t0_retrieval = time.time()
    thinking_steps.append("Step 1: Extracting intent and entities...")
    kg = get_knowledge_graph()
    resolution = kg.resolve_business_query(q_clean)

    if resolution.get("detected_tables"):
        thinking_steps.append(f"Entities Discovered: {', '.join(resolution['detected_tables'])}")

    # 3. Create Structured Execution Plan (Fast, Deterministic)
    from app.agent.query_planner import create_plan
    execution_plan = create_plan(q_clean)
    
    thinking_steps.append(f"Step 2: Execution Plan created for {len(execution_plan.get('tables', []))} tables.")
    if execution_plan.get("relationships_required"):
        thinking_steps.append(f"Joins Discovered: {', '.join(execution_plan['relationships_required'])}")
        
    schema_ms = round((time.time() - t0_retrieval) * 1000, 2)
    intent_ms = round(schema_ms / 2, 2)
    schema_lookup_ms = round(schema_ms / 2, 2)
    
    # 4. Compressed Prompt Build (Only passing the Execution Plan)
    t0_prompt = time.time()
    prompt_base = build_sql_prompt(json.dumps(execution_plan, indent=2))
    prompt_ms = round((time.time() - t0_prompt) * 1000, 2)

    # 5. Generation & Self-Correction Loop
    max_retries = 3
    attempt = 0
    validation = {"status": "BLOCKED", "reason": "Not started"}
    sql = ""
    validated_sql = ""
    error_feedback = ""
    plan_text = ""
    llm_ms = 0.0
    val_ms = 0.0

    while attempt < max_retries:
        attempt += 1
        thinking_steps.append(f"Step 3: Generating Plan & SQL (Attempt {attempt})...")
        
        prompt = prompt_base
        if error_feedback:
            prompt += f"\n\nPREVIOUS ERROR:\n{error_feedback}\nPlease fix the SQL query."

        t0_llm = time.time()
        try:
            raw_sql = generate_sql(prompt)
        except Exception as e:
            error_feedback = f"LLM Generation Error: {str(e)}"
            validation["status"] = "BLOCKED"
            validation["reason"] = error_feedback
            break
        llm_ms += round((time.time() - t0_llm) * 1000, 2)

        if "SQL:" in raw_sql:
            parts = raw_sql.split("SQL:")
            plan_text = parts[0].replace("PLAN:", "").strip()
            sql_str = parts[1].strip()
        else:
            plan_text = "No structured plan generated."
            sql_str = re.sub(r"(?i)^SQL:\s*", "", raw_sql.strip())
            
        sql = clean_sql(sql_str)

        t0_val = time.time()
        thinking_steps.append(f"Step 4: AST Validating SQL (Attempt {attempt})...")
        try:
            # AST Validation (strict SELECT only)
            validate_sql(sql)
            validation = {"status": "APPROVED", "sql": sql}
        except SQLValidationError as e:
            validation = {"status": "BLOCKED", "reason": str(e)}
            
        val_ms += round((time.time() - t0_val) * 1000, 2)

        if validation["status"] == "APPROVED":
            validated_sql = validation["sql"]
            # 6. Verify Execution Plan (EXPLAIN)
            thinking_steps.append(f"Step 5: Evaluating Execution Plan (Attempt {attempt})...")
            plan = get_execution_plan(validated_sql)
            if not plan["success"]:
                error_feedback = plan.get("error", "Invalid query execution plan")
                validation["status"] = "BLOCKED"
                validation["reason"] = f"Execution Plan Error: {error_feedback}"
                continue
            
            # 7. Execute Query and Self-Correct on DB Error
            if execute:
                thinking_steps.append(f"Step 6: Executing query against database (Attempt {attempt})...")
                t0_exec = time.time()
                execution_temp = execute_read_query(validated_sql)
                if not execution_temp["success"]:
                    error_feedback = execution_temp.get("error", "Database Execution Error")
                    print(f"[RETRY {attempt}] Execution Failed: {error_feedback}")
                    validation["status"] = "BLOCKED"
                    validation["reason"] = f"Execution Error: {error_feedback}"
                    continue
                
                execution = execution_temp
                exec_ms = round((time.time() - t0_exec) * 1000, 2)
            else:
                execution = {"success": True, "columns": [], "data": [], "row_count": 0}
                exec_ms = 0.0

            # Successful validation & plan & execution
            execution_plan = plan
            break
        else:
            error_feedback = validation["reason"]
            print(f"[RETRY {attempt}] Validation Failed: {error_feedback}")

    if validation["status"] == "BLOCKED":
        print("[BLOCKED] SQL Generation Failed after retries:", validation["reason"])
        return {
            "question": q_clean,
            "generated_sql": sql,
            "optimized_sql": sql,
            "validation": validation,
            "thinking_steps": thinking_steps,
            "reasoning": resolution,
            "execution": {"success": False, "columns": [], "data": [], "error": validation["reason"]},
            "status": "blocked",
            "benchmarks": {
                "intent_detection_ms": intent_ms,
                "schema_lookup_ms": schema_lookup_ms,
                "prompt_build_ms": prompt_ms,
                "llm_generation_ms": llm_ms,
                "validation_ms": val_ms,
                "execution_ms": 0.0,
                "total_ms": round((time.time() - t_start) * 1000, 2)
            }
        }

    affected_tables = resolution.get("detected_tables", [])
    confidence = compute_confidence(validation, resolution, execution_plan)

    thinking_steps.append("Step 7: Formatting query explanation from execution plan...")
    explanation = plan_text

    total_ms = round((time.time() - t_start) * 1000, 2)
    prompt_tokens = len(prompt_base) // 4  # Approximate token count

    result_payload = {
        "question": q_clean,
        "generated_sql": sql,
        "optimized_sql": validated_sql,
        "validation": validation,
        "affected_tables": affected_tables,
        "thinking_steps": thinking_steps,
        "reasoning": resolution,
        "execution": execution,
        "explanation": explanation,
        "confidence_score": confidence,
        "execution_plan": execution_plan,
        "status": "success",
        "benchmarks": {
            "intent_detection_ms": intent_ms,
            "schema_lookup_ms": schema_lookup_ms,
            "prompt_build_ms": prompt_ms,
            "llm_generation_ms": llm_ms,
            "validation_ms": val_ms,
            "execution_ms": exec_ms,
            "total_ms": total_ms,
            "prompt_tokens": prompt_tokens
        }
    }



    return result_payload

if __name__ == "__main__":
    res = run_agent("Show wallet transactions for July 2026")
    print(res)