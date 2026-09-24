import json
from app.agent.nlp_understanding import nlp_agent
from app.knowledge.relationship_resolver import relationship_resolver

test_questions = [
    "Show all retailers",
    "Generate a table of retailers linked to distributor 5997",
    "Show total wallet amount for July 2026",
    "Compare total wallet transactions between July and June 2026",
    "Show top 10 retailers by earnings for July 2026",
    "Which distributor has the highest number of box scans this month?",
    "Which retailer under which distributor has scanned the highest number of boxes this month?",
    "Which state has the highest number of box scans this month?",
    "Which category has the highest number of box scans this month?",
    "Which category has the lowest number of box scans this month, and which state has the lowest number of box scans?",
    "Which distributor has the lowest number of box scans this month?",
    "Which retailer has scanned the highest number of boxes this month?",
    "Which category has the highest box scan count in July 2026?"
]

for i, q in enumerate(test_questions, 1):
    print(f"=== TEST {i}: {q} ===")
    req = nlp_agent.parse_question(q)
    plan = relationship_resolver.resolve(req)
    print(f"  Req Entities: {req.entities} | Metric: {req.metric} | Metric Source: {req.metric_source} | Time Col: {req.time_column} | Time Range: {req.time_range}")
    print(f"  Plan Tables: {plan.relevant_tables} | Joins: {plan.required_joins} | Grouping: {plan.grouping} | Sorting: {plan.sorting} | Limit: {plan.limit}")
    print()
