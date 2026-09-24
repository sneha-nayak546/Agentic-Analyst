import sys
sys.path.insert(0, ".")

from app.agent.nlp_understanding import NLPUnderstanding
from app.knowledge.relationship_resolver import RelationshipResolver

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

nlp = NLPUnderstanding()
resolver = RelationshipResolver()

queries = [
    "Which distributor recorded the most box scans during the current month?",
    "Which retailer recorded the fewest box scans during the current month?",
    "Which state contributed the most retailer box scans this month?",
    "Which product category had the highest number of retailer scans this month?",
    "Which category had the lowest number of scans this month?",
    "Show the top 5 retailers by box scans this month.",
    "Show the bottom 5 retailers by box scans this month.",
    "Compare box scans between the previous month and the current month.",
    "Show the top 3 distributors by retailer box scans this month.",
    "For each distributor, show the number of retailer box scans this month.",
    "For each state, show the number of box scans this month.",
    "For each category, show the number of box scans this month.",
    "Which retailer and distributor combination has the highest number of box scans this month?",
    "Show all retailers who scanned at least one box this month.",
    "How many boxes were scanned by retailers this month?"
]

print("=" * 80)
print("TESTING NLP + RELATIONSHIP RESOLUTION ON 15 UNSEEN QUERIES")
print("=" * 80)

all_ok = True
for i, q in enumerate(queries, 1):
    req = nlp.parse_question(q)
    plan = resolver.resolve(req)
    has_sku = "sku_inventories" in plan.relevant_tables
    print(f"Q{i:02d}: tables={plan.relevant_tables} metric={req.metric} agg={req.aggregation} sort={getattr(req, 'ranking_direction', None)} limit={getattr(req, 'limit', None)} group={plan.grouping}")
    if not has_sku:
        print(f"  ❌ ERROR: sku_inventories missing for Q{i}: {q}")
        all_ok = False

if all_ok:
    print("\n✅ ALL 15 QUERIES SUCCESSFULLY GROUNDED TO SKU_INVENTORIES!")
else:
    print("\n❌ SOME QUERIES FAILED GROUNDING!")
