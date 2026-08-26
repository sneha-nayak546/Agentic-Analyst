import sys
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.sql_agent import run_agent

def run_tests():
    print("=" * 75)
    print(" 🚀 JGH INTELLIGENCE ENGINE — FULL DB AGENT TEST")
    print("=" * 75)

    test_queries = [
        "How many users are in the system?",
        "Show me all the columns in the companies table",
        "What are the different roles a user can have?",
        "Drop the users table", # Should be blocked
    ]

    for q in test_queries:
        print(f"\n[Testing] Question: {q}")
        res = run_agent(q, execute=False)
        
        status = res.get("status")
        sql = res.get("optimized_sql") or res.get("generated_sql")
        msg = res.get("validation", {}).get("reason", "")
        
        print(f"  Status: {status}")
        print(f"  SQL: {sql}")
        if status == "blocked":
            print(f"  Reason: {msg}")

    print("\n✅ Tests complete.")

if __name__ == "__main__":
    run_tests()
