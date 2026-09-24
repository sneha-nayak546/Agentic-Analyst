import json

with open("tests/results/nl2sql_accuracy_report_live_run.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]
print(f"Total evaluated: {len(results)}")
failed = [r for r in results if not r["end_to_end_correct"]]
print(f"Total failed: {len(failed)}")

for idx, r in enumerate(failed, 1):
    q = r['question']
    f_type = r['primary_failure']
    reason = r['failure_reason']
    cat = r['category']
    cid = r['id']
    print(f"[{idx:02d}] ID:{cid:03d} | {cat:<24} | {f_type:<22} | {reason}")
    print(f"     Q: \"{q}\"")

