import json
import urllib.request

payload = {
    "question": "Top 3 retailers by earnings in July 2026",
    "execute": True
}

req = urllib.request.Request(
    "http://localhost:8000/query",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode("utf-8"))
        print("STATUS:", res.get("status"))
        print("QUESTION:", res.get("question"))
        print("INTENT:", json.dumps(res.get("intent"), indent=2))
        print("EXECUTION PLAN:", json.dumps(res.get("execution_plan"), indent=2))
        print("SQL:", json.dumps(res.get("sql"), indent=2))
        print("RESULT:", json.dumps(res.get("result"), indent=2))
        print("VERIFICATION:", json.dumps(res.get("verification"), indent=2))
        print("ANALYSIS:", json.dumps(res.get("analysis"), indent=2))
        print("ANSWER:", json.dumps(res.get("answer"), indent=2))
        print("PERFORMANCE:", json.dumps(res.get("performance"), indent=2))
except Exception as e:
    print("ERROR:", e)
