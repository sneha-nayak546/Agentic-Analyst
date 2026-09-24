import sqlite3
import json

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

tables = cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';").fetchall()
print(f"Total tables in database.db: {len(tables)}")
for name, sql in tables:
    print(f"\n==========================================")
    print(f"TABLE: {name}")
    print(f"CREATE SQL: {sql}")
    # Sample rows
    try:
        count = cursor.execute(f"SELECT COUNT(*) FROM `{name}`;").fetchone()[0]
        print(f"ROW COUNT: {count}")
        sample = cursor.execute(f"SELECT * FROM `{name}` LIMIT 3;").fetchall()
        cols = [d[0] for d in cursor.description]
        print(f"COLUMNS: {cols}")
        for r in sample:
            print(f"  SAMPLE ROW: {r}")
    except Exception as e:
        print(f"Error reading {name}: {e}")
