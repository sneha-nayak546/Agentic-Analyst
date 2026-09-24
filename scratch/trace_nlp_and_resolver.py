import sys
sys.path.insert(0, ".")

from app.agent.nlp_understanding import nlp_agent
from app.knowledge.relationship_resolver import relationship_resolver

questions = [
    "Which retailer under which distributor has scanned the highest number of boxes this month?",
    "Which distributor has the highest number of box scans this month?",
    "Which state has the highest number of box scans this month?",
    "Which category has the highest number of box scans this month?",
    "Which category has the lowest number of box scans this month, and which state has the lowest number of box scans?"
]

for idx, q in enumerate(questions, 1):
    print(f"\n=======================================================")
    print(f"QUESTION {idx}: {q}")
    print(f"=======================================================")
    req = nlp_agent.parse_question(q)
    print("--- NLP BusinessRequirement ---")
    print(f"  intent: {req.intent}")
    print(f"  query_type: {req.query_type}")
    print(f"  entities: {req.entities}")
    print(f"  metrics: {req.metrics}")
    print(f"  aggregation: {req.aggregation}")
    print(f"  periods: {req.periods}")
    print(f"  date_period: {req.date_period}")
    print(f"  ranking: {req.ranking}")
    print(f"  limit: {req.limit}")
    print(f"  sorting: {req.sorting}")
    print(f"  confidence: {getattr(req, 'confidence', None)}")

    plan = relationship_resolver.resolve(req)
    print("--- ExecutionPlan ---")
    print(f"  relevant_tables: {plan.relevant_tables}")
    print(f"  required_joins: {plan.required_joins}")
    print(f"  resolved_entities: {plan.resolved_entities}")
    print(f"  date_boundaries: {plan.date_boundaries}")
    print(f"  business_rules: {plan.business_rules}")
