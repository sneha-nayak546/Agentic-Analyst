import urllib.request
import json

queries = [
    "Show wallet transactions of January 2026",
    "List 5 approved retailers in Lucknow",
    "List top 5 companies",
    "Show total withdrawal requests by status",
    "List 5 automatic transactions with IMPS transfer type"
]

results = []
for q in queries:
    try:
        data = json.dumps({"question": q}).encode()
        req = urllib.request.Request("http://localhost:8000/query", data=data, headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req).read().decode())
        results.append({
            "question": q,
            "status": resp.get("status"),
            "sql": resp.get("sql_query"),
            "rows": resp.get("rows_returned"),
            "summary": resp.get("summary"),
            "reports": resp.get("report_urls")
        })
    except Exception as e:
        results.append({"question": q, "error": str(e)})

with open("api_verified_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("API VERIFICATION COMPLETE")
