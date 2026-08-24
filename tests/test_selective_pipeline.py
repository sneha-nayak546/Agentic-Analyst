import sys
import json

# Fix Windows encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

sys.path.insert(0, ".")

from app.agent.context_resolver import context_resolver
from app.agent.query_planner import create_plan
from app.prompt.prompt_builder import build_sql_prompt
from app.llm.sql_generator import generate_sql, _synthesize_sql_from_plan
from app.agent.memory_manager import MemoryManager

def run_pipeline(session_id: str, question: str, mm: MemoryManager):
    print(f"\n=======================================================")
    print(f"QUESTION: \"{question}\" (Session: {session_id})")
    print(f"=======================================================")
    
    ctx = mm.resolve_session_context(session_id, question)
    print("RESOLVED CONTEXT:")
    print(json.dumps(ctx, indent=2))
    
    plan = create_plan(question, context=ctx)
    print("\nEXECUTION PLAN:")
    print(json.dumps({k: v for k, v in plan.items() if k not in ['time_constraint', 'business_terms']}, indent=2))
    
    prompt = build_sql_prompt(json.dumps(plan), context=ctx)
    tokens_approx = len(prompt.split()) * 4 // 3
    print(f"\nPROMPT STATS:")
    print(f"- Prompt length: {len(prompt)} chars, {len(prompt.split())} words, ~{tokens_approx} tokens")
    
    sql = generate_sql(prompt, plan=plan)
    print(f"\nGENERATED SQL:")
    print(sql)
    return ctx, plan, prompt, sql

mm = MemoryManager()

print("\n### SCENARIO 1: Standalone after region/entity")
mm.clear_session("s1")
run_pipeline("s1", "Show Karnataka distributors.", mm)
c1, p1, pr1, sql1 = run_pipeline("s1", "Show total withdrawals.", mm)

print("\n### SCENARIO 2: Genuine follow-up")
mm.clear_session("s2")
run_pipeline("s2", "Show Karnataka distributors.", mm)
c2, p2, pr2, sql2 = run_pipeline("s2", "What about their earnings?", mm)

print("\n### SCENARIO 3: ID follow-up vs standalone new ID")
mm.clear_session("s3")
run_pipeline("s3", "Show distributor ID 12345.", mm)
c3, p3, pr3, sql3 = run_pipeline("s3", "Show ID 67890.", mm)

print("\n" + "="*80)
print("EXACT COMPACT PROMPT SENT TO QWEN FOR 'Show total withdrawals':")
print("="*80)
print(pr1)
