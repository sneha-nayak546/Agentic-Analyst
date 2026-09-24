import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
sys.path.insert(0, os.path.abspath("."))
import time
from app.agent.sql_agent import run_agent

print("--- Query 1 (Cold / Pre-warmed) ---")
t0 = time.time()
r1 = run_agent("Show top 3 retailers by earnings for July 2026")
print(f"Total: {round((time.time() - t0)*1000, 2)}ms | Status: {r1.get('status')} | Rows: {len(r1.get('result', {}).get('rows', []))}")

print("\n--- Query 2 (Warm) ---")
t0 = time.time()
r2 = run_agent("Show top 3 retailers by earnings for July 2026")
print(f"Total: {round((time.time() - t0)*1000, 2)}ms | Status: {r2.get('status')} | Rows: {len(r2.get('result', {}).get('rows', []))}")
print("Perf profile 2:", r2.get("performance"))
