import sqlite3
import json

con = sqlite3.connect("database.db")
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Matching tables in database.db:")
for t in tables:
    if any(k in t.lower() for k in ["sku", "qr", "point", "map", "box"]):
        print(f"\nTABLE: {t}")
        cols = cur.execute(f"PRAGMA table_info({t})").fetchall()
        for c in cols:
            print("  ", c)
        rows = cur.execute(f"SELECT * FROM {t} LIMIT 3").fetchall()
        print("   Sample:", rows)

with open("knowledge/schema/schema_metadata.json", "r") as f:
    meta = json.load(f)

print("\n\nMatching in schema_metadata.json:")
for t, info in meta.items():
    if any(k in t.lower() for k in ["sku", "qr", "point", "map", "box"]):
        print(f"Metadata Table: {t}")
        print("  Columns:", list(info.get("columns", {}).keys()))
