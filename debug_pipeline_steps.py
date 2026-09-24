import time
import json
import sys

# Ensure unbuffered output
sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
import functools
_builtin_print = print
print = functools.partial(_builtin_print, flush=True)

from app.agent.sql_agent import run_agent

q = sys.argv[1] if len(sys.argv) > 1 else "Compare total wallet transactions between July and June 2026"
print(f"DEBUG PIPELINE: '{q}'\n")

t0 = time.time()
res = run_agent(q)
elapsed = time.time() - t0

print("\n" + "="*60)
print("FINAL PIPELINE RESULT:")
print("="*60)
print(f"Status            : {res.get('status')} / {res.get('validation_status')}")
print(f"SQL Query         : {res.get('sql')}")
print(f"Rows Returned     : {res.get('row_count')}")
print(f"Columns           : {res.get('columns')}")
print(f"Summary Answer    :\n{res.get('summary')}")

req_diff = res.get("requirement_diff")
if req_diff:
    print("\n" + req_diff)

print(f"\nCompleted in {elapsed:.2f}s")
