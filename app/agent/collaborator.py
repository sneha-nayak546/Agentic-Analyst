"""
Full-Spectrum AI Collaborator Orchestrator for JGH Intelligence Engine.
Integrates Intent Router, Specialized Mode Handlers (Tutor QA, ERD Diagram,
Dashboard Spec Builder, Executive Storyteller), Universal Gatekeeper Validation,
Automated Self-Correction Retry Loop, Clarification Fallback Engine, and Unmapped Query Audit Logging.
"""

from typing import Dict, Any
from app.agent.intent_router import route_intent
from app.agent.tutor_agent import tutor_agent
from app.agent.erd_generator import erd_generator
from app.agent.dashboard_builder import dashboard_builder
from app.agent.storyteller import storyteller
from app.agent.response_synthesizer import synthesizer
from app.agent.sql_agent import run_agent
from app.validator.universal_validator import universal_validator
from app.validator.plan_validator import plan_validator
from app.utils.query_logger import query_logger

class AICollaborator:
    def process_request(self, question: str, execute: bool = True) -> Dict[str, Any]:
        from app.agent.query_decomposer import decompose_query
        
        # Split complex queries into sub-queries
        sub_questions = decompose_query(question)
        
        if len(sub_questions) > 1:
            results = []
            combined_response = "### 🔄 Multi-Part Request Detected\nI broke your question down into multiple parts to ensure accuracy.\n\n"
            
            for i, sub_q in enumerate(sub_questions):
                sub_res = self._process_single_request(sub_q, execute)
                results.append(sub_res)
                combined_response += f"#### Part {i+1}: {sub_q}\n" + sub_res.get("response", "") + "\n\n---\n\n"
            
            return {
                "response": combined_response.strip(),
                "status": "success",
                "is_multi_query": True,
                "sub_results": results
            }
        else:
            return self._process_single_request(question, execute)

    def _process_single_request(self, question: str, execute: bool = True) -> Dict[str, Any]:
        # 1. Clarification Fallback Check
        clarification_payload = plan_validator.check_concept_clarification(question)
        if clarification_payload:
            return synthesizer.synthesize("CLARIFICATION", clarification_payload, question)

        # 2. Intent Classification
        intent = route_intent(question)

        # 3. Mode Execution with Self-Correction Retry Loop (1-retry limit)
        max_attempts = 2
        attempt = 0
        error_feedback = ""
        mode_result = {}

        while attempt < max_attempts:
            attempt += 1
            current_prompt = question
            if error_feedback:
                current_prompt += f"\n\n[SELF-CORRECTION NOTICE] Your previous output failed validation with error: {error_feedback}. Please fix the syntax/logic and regenerate."

            mode_result = self._execute_mode(intent, current_prompt, execute)

            # 4. Universal Gatekeeper Validation Check
            val_res = universal_validator.validate(intent, mode_result, question)
            if val_res["status"] == "APPROVED":
                break

            # If validation failed, record error feedback for 1-retry loop
            error_feedback = val_res.get("reason", "Output failed validation.")
            query_logger.log_unmapped_query(question, f"Validation failure (Attempt {attempt}): {error_feedback}", mode=intent)

        return synthesizer.synthesize(intent, mode_result, question)

    def _execute_mode(self, intent: str, prompt: str, execute: bool) -> Dict[str, Any]:
        if intent == "TUTOR_QA":
            return tutor_agent.explain(prompt)
        elif intent == "ERD_GEN":
            return erd_generator.generate_diagram(prompt)
        elif intent == "DASHBOARD_GEN":
            return dashboard_builder.build_dashboard(prompt)
        elif intent == "BUSINESS_STORY":
            return storyteller.tell_story(prompt)
        else:  # SQL_ANALYTICS
            # Directly wrap the tested 20/20 v2.0 SQL pipeline without modifications
            sql_result = run_agent(prompt, "", execute=execute)

            sql_str = sql_result.get("optimized_sql") or sql_result.get("generated_sql", "")
            exec_res = sql_result.get("execution", {})
            rows = exec_res.get("data", [])
            exec_time = exec_res.get("execution_time_ms", 0)
            row_cnt = len(rows)

            narrative = f"### 🔍 SQL Analytics Query Results\n\n"
            if sql_str:
                narrative += f"**Generated SQL Query**:\n```sql\n{sql_str}\n```\n\n"
            narrative += f"Query returned **{row_cnt} rows** in **{exec_time} ms**."

            return {
                "response": narrative,
                "generated_sql": sql_str,
                "data": rows,
                "status": sql_result.get("status", "success"),
                "sql_executed": True,
                "raw_result": sql_result
            }

collaborator = AICollaborator()

def handle_collaborative_query(question: str, execute: bool = True) -> Dict[str, Any]:
    return collaborator.process_request(question, execute=execute)
