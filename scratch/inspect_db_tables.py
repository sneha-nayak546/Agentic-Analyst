import sqlite3
import json
import os

conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = sorted([r[0] for r in cur.fetchall()])
print(f"Total SQLite tables: {len(tables)}")
print("Sample tables (first 30):", tables[:30])

schema_file = "knowledge/schema/schema_metadata.json"
if os.path.exists(schema_file):
    with open(schema_file, "r") as f:
        schema = json.load(f)
    print(f"Tables in schema_metadata.json: {len(schema)}")
    print("Schema keys count:", len(schema.keys()))
else:
    print("schema_metadata.json does not exist")
