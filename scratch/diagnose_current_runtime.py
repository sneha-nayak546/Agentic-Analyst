import sys
import os
import time
import json
import socket
import traceback

sys.path.insert(0, os.path.abspath("."))

from app.agent.nlp_understanding import nlp_agent
from app.knowledge.relationship_resolver import relationship_resolver
from app.prompt.prompt_builder import build_sql_prompt
from app.llm.sql_generator import generate_sql
from app.llm.provider import model_router
from app.validator.sql_ast_validator import validate_sql
from app.validator.semantic_sql_validator import evaluate_semantic_sql, validate_semantic_sql
from app.database.read_executor import execute_read_query, get_execution_plan, get_engine, get_sqlite_engine
from app.database.config import get_db_credentials
from app.validator.result_accuracy_validator import result_accuracy_validator
from app.agent.response_generator import response_generator
from app.validator.response_accuracy_validator import response_accuracy_validator
from app.database.cache_manager import cache_manager

print("=" * 60)
print("DIAGNOSTIC RUNTIME TRACE: 'Show top 3 retailers by earnings for July 2026'")
print("=" * 60)

# Check cache first
cached = cache_manager.get("Show top 3 retailers by earnings for July 2026")
print(f"[CACHE CHECK] Cache hit: {cached is not None}")

# 1. NLP
print("\n--- [1] NLP UNDERSTANDING ---")
t0 = time.time()
try:
    req = nlp_agent.parse_question("Show top 3 retailers by earnings for July 2026")
    nlp_ms = round((time.time() - t0) * 1000, 2)
    print(f"NLP Time: {nlp_ms} ms")
    print(f"Last Provider: {model_router.last_provider_used}, Model: {model_router.last_model_used}")
    print(f"Structured Intent: {json.dumps(req.to_structured_intent(), indent=2)}")
except Exception as e:
    print(f"NLP Error: {e}")
    traceback.print_exc()

# 2. Schema Grounding
print("\n--- [2] SCHEMA GROUNDING ---")
t0 = time.time()
plan = relationship_resolver.resolve(req)
grounding_ms = round((time.time() - t0) * 1000, 2)
print(f"Grounding Time: {grounding_ms} ms")
print(f"Target Tables: {plan.relevant_tables}")
print(f"Target Columns: {plan.relevant_columns}")
print(f"Required Joins: {plan.required_joins}")
print(f"Business Rules: {plan.business_rules}")

# 3. Prompt Builder
print("\n--- [3] PROMPT BUILDER ---")
prompt = build_sql_prompt(plan)
print(f"Prompt length: {len(prompt)} chars")
print(f"Prompt snippet (first 500 chars):\n{prompt[:500]}...")

# 4. SQL Generation
print("\n--- [4] SQL GENERATION ---")
t0 = time.time()
raw_sql = generate_sql(prompt, plan=plan)
sql_gen_ms = round((time.time() - t0) * 1000, 2)
print(f"SQL Generation Time: {sql_gen_ms} ms")
print(f"Last Provider: {model_router.last_provider_used}, Model: {model_router.last_model_used}")
print(f"Raw Generated SQL:\n{raw_sql}")

# 5. AST & Semantic Validation
print("\n--- [5] SQL VALIDATION ---")
t0 = time.time()
validate_sql(raw_sql, plan=plan)
ast_ms = round((time.time() - t0) * 1000, 2)
print(f"AST Validation: PASS ({ast_ms} ms)")

t0 = time.time()
sem_eval = evaluate_semantic_sql(raw_sql, plan)
sem_ms = round((time.time() - t0) * 1000, 2)
print(f"Semantic Validation: {sem_eval} ({sem_ms} ms)")

# 6. Database Latency Breakdown & Execution Plan
print("\n--- [6] DATABASE LATENCY BREAKDOWN ---")
creds = get_db_credentials()
host = creds.get("host", "localhost")
port = int(creds.get("port", 3306))
print(f"Configured DB Host: {host}:{port}, Name: {creds.get('name')}, User: {creds.get('user')}")

# Measure socket probe
t0 = time.time()
socket_ok = False
try:
    with socket.create_connection((host, port), timeout=0.3):
        socket_ok = True
except Exception as e:
    socket_err = str(e)
socket_probe_ms = round((time.time() - t0) * 1000, 2)
print(f"Socket probe to {host}:{port} (timeout=0.3s): socket_ok={socket_ok}, elapsed={socket_probe_ms} ms")

# Measure MySQL engine connect
mysql_eng = get_engine()
t0 = time.time()
mysql_conn = None
try:
    mysql_conn = mysql_eng.connect()
    mysql_connect_ms = round((time.time() - t0) * 1000, 2)
    print(f"MySQL engine connect: SUCCESS in {mysql_connect_ms} ms")
    mysql_conn.close()
except Exception as e:
    mysql_connect_ms = round((time.time() - t0) * 1000, 2)
    print(f"MySQL engine connect: FAILED in {mysql_connect_ms} ms: {type(e).__name__}: {e}")

# Measure EXPLAIN plan
t0 = time.time()
explain_res = get_execution_plan(raw_sql)
explain_ms = round((time.time() - t0) * 1000, 2)
print(f"get_execution_plan time: {explain_ms} ms (Result success: {explain_res.get('success')})")

# Measure execute_read_query
t0 = time.time()
exec_res = execute_read_query(raw_sql)
exec_total_ms = round((time.time() - t0) * 1000, 2)
print(f"execute_read_query total time: {exec_total_ms} ms")
print(f"Execution report execution_time_ms: {exec_res.get('execution_time_ms')} ms")
print(f"Row count: {exec_res.get('row_count')}")
print(f"Columns: {exec_res.get('columns')}")
print(f"Rows data: {exec_res.get('data')}")

# 7. Result Verification
print("\n--- [7] RESULT ACCURACY VALIDATOR ---")
t0 = time.time()
res_val = result_accuracy_validator.validate(
    question="Show top 3 retailers by earnings for July 2026",
    sql=raw_sql,
    context={},
    execution_result=exec_res,
    plan=plan
)
res_val_ms = round((time.time() - t0) * 1000, 2)
print(f"Result Validator Time: {res_val_ms} ms")
print(f"Result Validation output:\n{json.dumps(res_val, indent=2)}")

# 8. Response Generation
print("\n--- [8] RESPONSE GENERATOR ---")
t0 = time.time()
resp_text = response_generator.generate_response(
    plan=plan,
    execution_result=exec_res,
    validation_status=res_val.get("result_confidence", "VERIFIED")
)
resp_gen_ms = round((time.time() - t0) * 1000, 2)
print(f"Response Generator Time: {resp_gen_ms} ms")
print(f"Last Provider: {model_router.last_provider_used}, Model: {model_router.last_model_used}")
print(f"Generated Response:\n{resp_text}")

# 9. Response Accuracy Validator
print("\n--- [9] RESPONSE ACCURACY VALIDATOR ---")
t0 = time.time()
resp_val = response_accuracy_validator.validate(
    question="Show top 3 retailers by earnings for July 2026",
    requirement=req,
    sql=raw_sql,
    execution_result=exec_res,
    final_response=resp_text
)
resp_val_ms = round((time.time() - t0) * 1000, 2)
print(f"Response Accuracy Validator Time: {resp_val_ms} ms")
print(f"Response Accuracy output:\n{json.dumps(resp_val, indent=2)}")
