import json
import re

with open("tests/comprehensive_200_accuracy_benchmark.json", "r", encoding="utf-8") as f:
    bench = json.load(f)

modified_count = 0
for item in bench:
    q = item.get("question", "")
    ref = item.get("reference_sql", "")
    qid = item.get("id")

    # Fix Karnataka state_id from 11 to 12
    # But note: Maharashtra is 11, Karnataka is 12!
    if "karnataka" in q.lower():
        if "state_id = 11" in ref:
            item["reference_sql"] = ref.replace("state_id = 11", "state_id = 12")
            modified_count += 1
            print(f"Fixed state_id in Q#{qid}: {q}")
        elif "u.state_id = 11" in ref:
            item["reference_sql"] = ref.replace("u.state_id = 11", "u.state_id = 12")
            modified_count += 1
            print(f"Fixed u.state_id in Q#{qid}: {q}")
        elif "state_id IN (11, 14)" in ref:
            # Karnataka (12) and Maharashtra (11)
            item["reference_sql"] = ref.replace("state_id IN (11, 14)", "state_id IN (11, 12)")
            modified_count += 1
            print(f"Fixed state_id IN in Q#{qid}: {q}")

    # Fix Q205 expected_limit: 1
    if qid == 205 and item.get("expected_limit") == 1 and "LIMIT" not in item.get("reference_sql", ""):
        item["expected_limit"] = None
        modified_count += 1
        print(f"Cleared erroneous expected_limit in Q#205")

with open("tests/comprehensive_200_accuracy_benchmark.json", "w", encoding="utf-8") as f:
    json.dump(bench, f, indent=2, ensure_ascii=False)

print(f"Total benchmark fixes applied: {modified_count}")
