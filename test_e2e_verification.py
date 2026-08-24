import sys
import json
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

BASE_URL = "http://localhost:8000"

queries = [
    {
        "id": 1,
        "name": "Box Scan Routing & Ambiguous Column Test",
        "question": "How many box he have scanned in this month",
        "checks": [
            ("Routes to sku_inventories", lambda res, sql: "sku_inventories" in sql.lower()),
            ("Uses si.retailer_scanned_at", lambda res, sql: "retailer_scanned_at" in sql.lower()),
            ("0 MySQL 1052 / table errors", lambda res, sql: res.get("status") == "success"),
            ("Returns live rows", lambda res, sql: res.get("rows_returned", 0) > 0)
        ]
    },
    {
        "id": 2,
        "name": "Temporal Earnings Test",
        "question": "Show earnings of retailers for July 2026",
        "checks": [
            ("Date range July 2026 starting", lambda res, sql: "2026-07-01" in sql),
            ("Date range July 2026 ending", lambda res, sql: "2026-08-01" in sql),
            ("Successful execution", lambda res, sql: res.get("status") == "success"),
            ("Returns live rows", lambda res, sql: res.get("rows_returned", 0) > 0)
        ]
    },
    {
        "id": 3,
        "name": "Dynamic Ledger Balance Test",
        "question": "Show top 10 users with highest wallet balance",
        "checks": [
            ("Uses SUM(wt.amount)", lambda res, sql: "sum(" in sql.lower() and "amount" in sql.lower()),
            ("Joined on wallet_transaction", lambda res, sql: "wallet_transaction" in sql.lower()),
            ("Successful execution", lambda res, sql: res.get("status") == "success"),
            ("Returns 10 rows", lambda res, sql: res.get("rows_returned", 0) == 10)
        ]
    },
    {
        "id": 4,
        "name": "Redemption Filter Test",
        "question": "Show redemption amount per user",
        "checks": [
            ("Filters wt.reference_type = 'withdrawal'", lambda res, sql: "withdrawal" in sql.lower()),
            ("Successful execution", lambda res, sql: res.get("status") == "success"),
            ("Returns live rows", lambda res, sql: res.get("rows_returned", 0) > 0)
        ]
    }
]

print("=== STARTING BACKEND API BENCHMARK VERIFICATION ===")
all_passed = True

for item in queries:
    print(f"\n--- Test #{item['id']}: {item['name']} ---")
    print(f"Prompt: \"{item['question']}\"")
    
    req_data = json.dumps({"question": item["question"], "execute": True, "bypass_cache": True}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/query", data=req_data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            sql = res.get("sql_query") or res.get("sql") or ""
            print(f"Status: {res.get('status')}")
            print(f"SQL Generated: {sql}")
            print(f"Rows Returned: {res.get('rows_returned')}")
            print(f"Summary: {res.get('summary')}")
            
            test_passed = True
            for check_name, check_fn in item["checks"]:
                passed = check_fn(res, sql)
                icon = "[PASS]" if passed else "[FAIL]"
                print(f"  {icon} Check '{check_name}'")
                if not passed:
                    test_passed = False
                    all_passed = False
            if test_passed:
                print(f"RESULT: PASS")
            else:
                print(f"RESULT: FAIL")
    except Exception as e:
        print(f"ERROR: {e}")
        all_passed = False

print("\n==========================================")
if all_passed:
    print("ALL 4 BENCHMARK TESTS PASSED SUCCESSFULLY!")
else:
    print("SOME TESTS FAILED - REVIEW OUTPUT ABOVE.")
