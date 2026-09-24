import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
for t in tables:
    cols = [col[1] for col in c.execute(f"PRAGMA table_info({t});").fetchall()]
    print(f"{t}: {cols}")
conn.close()
