import requests
import time
import sys

questions = [
    "Show wallet transactions for July 2026",
    "List all companies",
    "What is the total inventory count?",
    "Show active retailers",
    "List pending withdrawals",
    "Show machine statuses",
    "How many users are there?",
    "What are the recent orders?",
    "Show sales data for Q1",
    "List all products in stock"
]

def verify():
    print("Waiting for backend to start...")
    time.sleep(5)
    
    success_count = 0
    
    for q in questions:
        print(f"\nQ: {q}")
        try:
            resp = requests.post("http://localhost:8000/query", json={"question": q, "execute": True}, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    print(f"[SUCCESS] {data.get('execution', {}).get('row_count', 0)} rows returned.")
                    success_count += 1
                else:
                    print(f"[FAILED] {data.get('status')} - {data.get('execution', {}).get('error', 'Unknown Error')}")
            else:
                print(f"[HTTP ERROR] {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[EXCEPTION] {str(e)}")

    print(f"\nFinal Score: {success_count}/{len(questions)}")

if __name__ == "__main__":
    verify()
