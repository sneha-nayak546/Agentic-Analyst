import sqlite3

conn = sqlite3.connect("database.db")
print("Total rows:", conn.execute("SELECT COUNT(*) FROM wallet_transaction").fetchone()[0])
print("July 2026 rows:", conn.execute("SELECT COUNT(*) FROM wallet_transaction WHERE created_at >= '2026-07-01 00:00:00' AND created_at < '2026-08-01 00:00:00'").fetchone()[0])
