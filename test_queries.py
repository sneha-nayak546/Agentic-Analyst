import requests
import json
import time

queries = [
    "Show first 10 users",
    "Show first 10 wallet transactions",
    "Show companies",
    "Show withdrawal requests",
    "Show machine details",
    "Show retailer scan count in January 2026",
    "Show wallet transactions for July 2026",
    "Show SKU inventory"
]

url = "http://localhost:8000/query"

for q in queries:
    print(f"Testing: {q}")
    payload = {"question": q, "execute": True}
    try:
        res = requests.post(url, json=payload)
        data = res.json()
        if "error" in data.get("execution", {}):
            print(f"FAILED (SQL Error): {data['execution']['error']}")
            print(f"Generated SQL: {data.get('generated_sql')}")
        elif res.status_code != 200:
            print(f"FAILED (HTTP {res.status_code}): {res.text}")
        else:
            print("SUCCESS")
    except Exception as e:
        print(f"FAILED (Exception): {e}")
    time.sleep(1)
