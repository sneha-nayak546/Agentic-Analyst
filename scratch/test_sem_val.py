import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, '.')
from app.agent.business_requirement import BusinessRequirement
from app.agent.execution_plan import ExecutionPlan
from app.validator.semantic_sql_validator import evaluate_semantic_sql

req = BusinessRequirement(
    original_question='Show top 3 retailers by earnings for July 2026',
    intent='ranking',
    entities=['retailer'],
    metrics=['earnings'],
    periods=['July 2026'],
    limit=3
)
plan = ExecutionPlan(business_requirement=req, relevant_tables=['users', 'wallet_transaction'])

complete_sql = """
SELECT u.name AS retailer, SUM(wt.amount) AS earnings 
FROM users AS u 
JOIN wallet_transaction AS wt ON u.id = wt.user_id 
WHERE u.user_role = 2 
  AND wt.created_at >= '2026-07-01 00:00:00' 
  AND wt.created_at < '2026-08-01 00:00:00' 
  AND wt.amount > 0 
GROUP BY u.id, u.name 
ORDER BY earnings DESC 
LIMIT 3;
"""

res = evaluate_semantic_sql(complete_sql, plan)
print('Complete SQL validation:')
print(res)
