import sys, os
sys.path.insert(0, os.path.abspath("."))
from app.agent.nlp_understanding import parse_nlp_to_requirement
from app.agent.execution_plan import build_execution_plan
from app.prompt.prompt_builder import build_sql_prompt

req = parse_nlp_to_requirement("Show top 3 retailers by earnings for July 2026")
plan = build_execution_plan(req)
prompt = build_sql_prompt(plan)
print(f"Prompt length in chars: {len(prompt)}, approximate tokens: {len(prompt)//4}")
print("\n--- Prompt preview (first 1000 chars) ---")
print(prompt[:1000])
