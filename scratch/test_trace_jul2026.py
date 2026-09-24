import sys, os
sys.path.insert(0, os.path.abspath("."))
import time
import json
from app.agent.sql_agent import run_agent

print("Running trace for: 'Show top 3 retailers by earnings for July 2026'...")
t0 = time.time()
result = run_agent("Show top 3 retailers by earnings for July 2026")
total_time = round((time.time() - t0), 2)

print("\n=== RUN RESULT ===")
print("Status:", result.get("status"))
print("Validation Status:", result.get("validation_status"))
print("Generated SQL:", result.get("generated_sql"))
print("Optimized SQL:", result.get("optimized_sql"))
print("SQL Query:", result.get("sql_query"))
print("Execution Success:", result.get("execution", {}).get("success"))
print("Row Count:", result.get("row_count"))
print("Columns:", result.get("columns"))
print("Data Rows:", result.get("results") or result.get("data"))
print("Summary Text:", result.get("summary"))
print("Total Time (s):", total_time)
print("Benchmarks:", json.dumps(result.get("benchmarks", {}), indent=2))
