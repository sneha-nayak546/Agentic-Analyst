import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

url = "http://localhost:8000/query"
payload = {"question": "Show earnings of retailers for July 2026", "live": True}
data = json.dumps(payload).encode("utf-8")

req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))

print("=" * 80)
print("FASTAPI REST API RESPONSE VERIFICATION: 'Show earnings of retailers for July 2026'")
print("=" * 80)
print(f"Status: {resp.get('status')}")
print(f"SQL: {resp.get('sql')}")
print(f"Rows Returned: {resp.get('rows_returned')}")
print(f"Execution Time: {resp.get('execution_time')} ms")
print(f"Summary: {resp.get('summary')}")
print(f"Report URLs: {resp.get('report_urls')}")
if resp.get("results"):
    print(f"First Result Row: {resp['results'][0]}")
print("=" * 80)

# Verification Assertions
assert "2026-07-01 00:00:00" in resp.get("sql", "") and "2026-08-01 00:00:00" in resp.get("sql", ""), "July 2026 timestamp bounds missing from REST API response!"
assert resp.get("status") == "success", "API returned status other than success!"
assert resp.get("rows_returned", 0) > 0, "No rows returned by API!"

print("[SUCCESS] FastAPI REST API endpoint returns verified July 2026 date-bound response!")
