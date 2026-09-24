import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
from app.prompt.prompt_builder import build_sql_prompt
from app.agent.nlp_understanding import nlp_agent
from app.knowledge.relationship_resolver import relationship_resolver
from app.llm.sql_generator import generate_sql, extract_sql_queries
from app.llm.provider import model_router

req = nlp_agent.parse_question("Show top 3 retailers by earnings for July 2026")
plan = relationship_resolver.resolve(req)
prompt = build_sql_prompt(plan)

print("Generated Prompt:\n", prompt)
print("\n--- Model raw response ---")
raw = model_router.execute_stage("sql", prompt, max_tokens=600)
print("RAW:\n", raw)
print("\nExtracted SQL:")
queries = extract_sql_queries(raw)
print(queries)
