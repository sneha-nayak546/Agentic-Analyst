import json
import sqlite3
import os
import sys
sys.path.insert(0, ".")

# Set test environment
os.environ["USE_LOCAL_TEST_DB"] = "true"
os.environ["DB_ENGINE"] = "sqlite"

from tests.run_e2e_accuracy_evaluator import evaluate_single_question

with open("tests/comprehensive_200_accuracy_benchmark.json", "r", encoding="utf-8") as f:
    bench = json.load(f)

test_ids = [17, 33, 153, 177, 205]
cases = [c for c in bench if c["id"] in test_ids]

db_conn = sqlite3.connect("database.db")
from datetime import datetime
db_conn.create_function("MONTH", 1, lambda val: int(str(val)[5:7]) if val and len(str(val)) >= 7 else None)
db_conn.create_function("YEAR", 1, lambda val: int(str(val)[:4]) if val and len(str(val)) >= 4 else None)
db_conn.create_function("DAY", 1, lambda val: int(str(val)[8:10]) if val and len(str(val)) >= 10 else None)
db_conn.create_function("DAYOFMONTH", 1, lambda val: int(str(val)[8:10]) if val and len(str(val)) >= 10 else None)
db_conn.create_function("NOW", 0, lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
db_conn.create_function("CURDATE", 0, lambda: datetime.now().strftime("%Y-%m-%d"))

passed = 0
for idx, case in enumerate(cases, 1):
    res = evaluate_single_question(case, db_conn)
    status = "✅ PASS" if res["end_to_end_correct"] else f"❌ FAIL ({res['primary_failure']}: {res['failure_reason']})"
    print(f"[{idx}/{len(cases)}] Q#{case['id']} '{case['question']}': {status}")
    if res["end_to_end_correct"]:
        passed += 1

print(f"\nResult: {passed}/{len(cases)} Passed ({passed/len(cases)*100:.1f}%)")
