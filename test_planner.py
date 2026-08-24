import sys
from app.agent.query_planner import create_plan
from app.llm.sql_generator import _synthesize_sql_from_plan, generate_sql
import json

q = "count how many retailers are available under destributor ID 5997"
plan = create_plan(q)
print("PLAN:")
print(json.dumps(plan, indent=2))
sql = _synthesize_sql_from_plan(plan)
print("\nSYNTH SQL:")
print(sql)
