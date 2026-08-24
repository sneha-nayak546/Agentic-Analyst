from app.database.read_executor import execute_read_query

res = execute_read_query("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();")
print("Tables in live database:")
for r in res.get("data", []):
    print(" -", r)
