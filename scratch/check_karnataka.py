import json

with open("tests/comprehensive_200_accuracy_benchmark.json", "r", encoding="utf-8") as f:
    bench = json.load(f)

for item in bench:
    q = item.get("question", "")
    ref = item.get("reference_sql", "")
    if "karnataka" in q.lower() or "state_id = 11" in ref:
        print(f"ID {item['id']}: Q: '{q}'")
        print(f"    Ref: {ref}")
