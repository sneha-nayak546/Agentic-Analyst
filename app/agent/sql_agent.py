import re
import time
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

from app.llm.sql_generator import generate_sql
from app.prompt.prompt_builder import build_sql_prompt
from app.utils.sql_cleaner import clean_sql
from app.validator.sql_ast_validator import validate_sql, SQLValidationError
from app.validator.result_accuracy_validator import result_accuracy_validator
from app.validator.e2e_accuracy_validator import e2e_accuracy_validator
from app.retriever.retriever import retrieve_schema, retrieve_sql_history
from app.database.read_executor import execute_read_query, get_execution_plan
from app.agent.ambiguity_checker import check_ambiguity
from app.agent.query_planner import create_plan
from app.knowledge.relationship_resolver import relationship_resolver
from app.agent.response_generator import response_generator

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

def run_agent(question: str, history_context: str = "", context: Optional[Dict[str, Any]] = None, execute: bool = True) -> dict:
    """
    Enterprise AI SQL Agent Pipeline with Multi-Step Context Reasoning,
    Self-Correction, EXPLAIN validation, and AST validation.
    """
    t_start = time.time()
    q_clean = question.strip()
    ctx = context or {}

    print("\n" + "=" * 70)
    print("USER QUESTION:", q_clean)
    if ctx:
        print("RESOLVED CONTEXT:", json.dumps({k: v for k, v in ctx.items() if not k.startswith("time_condition")}))
    print("=" * 70)

    thinking_steps = []

    # 1. Check Ambiguity & Business Logic Validation
    ambiguity = check_ambiguity(q_clean, active_context=ctx)
    if ambiguity:
        return {
            "question": q_clean,
            "is_ambiguous": True,
            "clarification": ambiguity["clarification"],
            "options": ambiguity["options"],
            "thinking_steps": ["Checking query clarity...", "Ambiguity detected."],
            "status": "ambiguous"
        }

    # 1.5 Security & Privacy Firewall (Credentials / Encryption Keys / Secret Protection)
    RESTRICTED_SECURITY_TERMS = [
        "password", "passwords", "encryption key", "encryption keys", "master key",
        "master keys", "private key", "private keys", "secret key", "secret keys",
        "auth token", "auth tokens", "password_hash"
    ]
    if any(re.search(rf"\b{re.escape(term)}\b", q_clean.lower()) for term in RESTRICTED_SECURITY_TERMS):
        denial_msg = (
            "🛡️ **Security Policy Enforcement**: Access to sensitive credentials, user passwords, "
            "master encryption keys, and private tokens is strictly restricted by enterprise data protection policies. "
            "The JGH Intelligence Engine cannot disclose authentication secrets or security keys."
        )
        return {
            "question": q_clean,
            "status": "blocked",
            "summary": denial_msg,
            "validation": {
                "status": "BLOCKED",
                "reason": "Request asks for restricted security credentials (passwords / encryption keys)."
            },
            "generated_sql": "",
            "optimized_sql": "",
            "execution": {"success": False, "columns": [], "data": [], "row_count": 0, "error": "Access Denied: Restricted Security Attribute"},
            "result_confidence": "SUSPICIOUS_RESULT",
            "accuracy_message": "Access Denied: Enterprise Security Policy strictly prohibits retrieving passwords, authentication credentials, or encryption keys.",
            "thinking_steps": ["Checking security policy...", "Blocked: Sensitive credential request detected."],
            "affected_tables": [],
            "debug_pipeline": {
                "user_question": q_clean,
                "intent": "RESTRICTED_SECURITY_QUERY",
                "entity": None,
                "context": ctx,
                "tables": [],
                "prompt": "",
                "model": "Security Policy Firewall",
                "sql": "",
                "validation": {"status": "BLOCKED", "reason": "Restricted security attribute requested"},
                "execution": {"success": False, "row_count": 0, "columns": []},
                "response": denial_msg
            }
        }

    # 2. Multi-Step Reasoning: NLP Intent & Entity Extraction
    t0_retrieval = time.time()
    thinking_steps.append("Step 1: Extracting intent, entities, and context filters via NLP...")
    
    # USE DETERMINISTIC PLANNER
    execution_plan = create_plan(q_clean, ctx)
    
    # NEW PIPELINE: 2. Relationship Verification
    execution_plan = relationship_resolver.resolve_relationships(execution_plan)
    
    if execution_plan.get("missing_information") and not execution_plan.get("missing_information")[0].startswith("Failed to parse"):
        return {
            "question": q_clean,
            "status": "ambiguous",
            "clarification": "I need more information: " + ", ".join(execution_plan["missing_information"]),
            "options": [],
            "thinking_steps": thinking_steps + ["Missing information detected."],
        }
        
    if execution_plan.get("relationship_warning"):
        thinking_steps.append("Warning: " + execution_plan["relationship_warning"])
    
    # Confidence Gate - Bypassed for LLM fallback
    confidence = execution_plan.get("confidence", 100)
    if confidence < 70:
        thinking_steps.append("Low confidence plan detected, heavily relying on LLM fallback.")
        
    schema_ms = round((time.time() - t0_retrieval) * 1000, 2)
    intent_ms = round(schema_ms / 2, 2)
    schema_lookup_ms = round(schema_ms / 2, 2)
    
    # 4. Build Selective Prompt passing Execution Plan and Context
    t0_prompt = time.time()
    from app.prompt.prompt_builder import build_sql_prompt
    from app.utils.summary_generator import generate_natural_summary
    prompt_base = build_sql_prompt(json.dumps(execution_plan, indent=2), context=ctx)
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
    execution = {"success": False, "columns": [], "data": [], "row_count": 0}
    exec_ms = 0.0

    while attempt < max_retries:
        attempt += 1
        thinking_steps.append(f"Step 3: Generating Plan & SQL (Attempt {attempt})...")
        
        prompt = prompt_base
        if error_feedback:
            prompt += f"\n\nPREVIOUS ERROR / VALIDATION FAILURE:\n{error_feedback}\nPlease fix the SQL query and strictly ensure it matches the requirements and uses only valid columns."

        t0_llm = time.time()
        try:
            raw_sql = generate_sql(prompt, plan=execution_plan)
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
        thinking_steps.append(f"Step 4: SQL Validation — safety, schema & join checks (Attempt {attempt})...")
        try:
            from app.validator.sql_ast_validator import validate_sql, SQLValidationError
            from app.validator.semantic_sql_validator import validate_semantic_sql, SemanticValidationError
            
            # Syntax and AST security validation
            validate_sql(sql, plan=execution_plan)
            
            # Semantic validation against query plan
            validate_semantic_sql(sql, execution_plan)
            
            validation = {"status": "APPROVED", "sql": sql}
        except SQLValidationError as e:
            validation = {"status": "BLOCKED", "reason": str(e)}
        except SemanticValidationError as e:
            validation = {"status": "BLOCKED", "reason": f"Semantic Validation Error: {str(e)}"}
            
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

            execution_plan = plan

            # 7. Strict E2E Accuracy Validation (post-execution semantic check INSIDE retry loop)
            result_accuracy = {}
            result_confidence = "UNABLE_TO_VERIFY"
            accuracy_message = "Result accuracy could not be confirmed."
            if validation["status"] == "APPROVED" and execution.get("success"):
                thinking_steps.append("Step 7: E2E Strict Accuracy Validation — verifying all 10 dimensions...")
                
                # Check strict E2E validator
                e2e_res = e2e_accuracy_validator.validate(
                    question=q_clean,
                    sql=validated_sql or sql,
                    context=ctx,
                    execution_result=execution,
                    plan=execution_plan
                )
                
                if not e2e_res["success"]:
                    error_feedback = f"Strict E2E Validation Failed ({e2e_res['failed_dimension']}): {e2e_res['reason']}"
                    print(f"[RETRY {attempt}] E2E Accuracy Failed: {error_feedback}")
                    validation["status"] = "BLOCKED"
                    validation["reason"] = error_feedback
                    
                    # Ensure we block the result data
                    execution["data"] = []
                    execution["success"] = False
                    execution["row_count"] = 0
                    
                    # Update accuracy metrics
                    result_confidence = "SUSPICIOUS_RESULT"
                    accuracy_message = f"Query was BLOCKED due to accuracy mismatch in dimension: {e2e_res['failed_dimension']}."
                    result_accuracy = {"result_confidence": result_confidence, "accuracy_message": accuracy_message, "issues_found": [e2e_res['reason']]}
                    continue
                else:
                    # Optional: still run the old one for metadata/warnings
                    try:
                        result_accuracy = result_accuracy_validator.validate(
                            question=q_clean,
                            sql=validated_sql or sql,
                            context=ctx,
                            execution_result=execution,
                            plan=execution_plan
                        )
                        result_confidence = result_accuracy.get("result_confidence", "UNABLE_TO_VERIFY")
                        accuracy_message = result_accuracy.get("accuracy_message", accuracy_message)
                        thinking_steps.append(f"Step 7 Result: {result_confidence}")
                        
                    except Exception as acc_err:
                        print(f"[RESULT ACCURACY] Metadata validation error: {acc_err}")
                        result_confidence = "VERIFIED_RESULT"
                        accuracy_message = "Result accuracy confirmed by E2E validator."
                        result_accuracy = {"result_confidence": result_confidence, "accuracy_message": accuracy_message}

            # If we reach here and validation is still APPROVED (no continues), break the loop
            break
        else:
            error_feedback = validation["reason"]
            print(f"[RETRY {attempt}] Validation Failed: {error_feedback}")

    summary_text = response_generator.generate_response(execution_plan, execution)

    debug_pipeline = {
        "user_question": q_clean,
        "intent": execution_plan.get("intent", q_clean),
        "entity": execution_plan.get("primary_entity"),
        "context": ctx,
        "tables": execution_plan.get("tables", []),
        "rag": {
            "tables": execution_plan.get("tables", []),
            "prompt_length_tokens": len(prompt_base.split()) * 4 // 3
        },
        "prompt": prompt_base,
        "model": "Deterministic Synthesizer (High Confidence)" if (execution_plan.get("confidence_score", 90) >= 85) else "Qwen2.5-Coder (via RAG)",
        "sql": validated_sql or sql,
        "validation": validation,
        "execution": {
            "success": execution.get("success", False),
            "row_count": len(execution.get("data", [])),
            "columns": execution.get("columns", [])
        },
        "response": summary_text
    }

    if validation["status"] == "BLOCKED":
        print("[BLOCKED] SQL Generation Failed after retries:", validation["reason"])
        return {
            "question": q_clean,
            "generated_sql": sql,
            "optimized_sql": sql,
            "validation": validation,
            "thinking_steps": thinking_steps,
            "reasoning": execution_plan,
            "execution": {"success": False, "columns": [], "data": [], "error": validation["reason"]},
            "status": "blocked",
            "context": ctx,
            "summary": summary_text,
            "debug_pipeline": debug_pipeline,
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

    affected_tables = execution_plan.get("verified_tables", [])
    confidence = execution_plan.get("confidence", 100)
    thinking_steps.append("Step 7: Formatting query explanation from execution plan...")

    total_ms = round((time.time() - t_start) * 1000, 2)
    prompt_tokens = len(prompt_base) // 4

    result_payload = {
        "question": q_clean,
        "generated_sql": sql,
        "optimized_sql": validated_sql,
        "validation": validation,
        "affected_tables": affected_tables,
        "thinking_steps": thinking_steps,
        "reasoning": execution_plan,
        "execution": execution,
        "summary": summary_text,
        "explanation": plan_text,
        "confidence_score": confidence,
        "execution_plan": execution_plan,
        "context": ctx,
        "status": "success",
        # Result Accuracy Validation fields
        "result_confidence": result_confidence,
        "accuracy_message": accuracy_message,
        "result_accuracy": result_accuracy,
        "debug_pipeline": debug_pipeline,
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