import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

print("--- USER ROLES ---")
c.execute("SELECT user_role, count(*) FROM users GROUP BY user_role;")
print(c.fetchall())

print("--- SAMPLE USERS (roles) ---")
c.execute("SELECT id, name, user_role, status FROM users LIMIT 10;")
for r in c.fetchall():
    print(r)

print("--- WALLET TRANSACTIONS SUMMARY ---")
c.execute("SELECT count(*), min(created_at), max(created_at) FROM wallet_transaction;")
print(c.fetchone())

print("--- WALLET TRANSACTION TYPES / STATUSES ---")
c.execute("SELECT transaction_type, status, count(*) FROM wallet_transaction GROUP BY transaction_type, status;")
print(c.fetchall())

print("--- JULY 2026 TRANSACTIONS ---")
c.execute("SELECT * FROM wallet_transaction WHERE created_at >= '2026-07-01' AND created_at < '2026-08-01' LIMIT 20;")
rows = c.fetchall()
print(f"Total found in sample: {len(rows)}")
for r in rows:
    print(r)

print("--- RETAILERS IN USERS TABLE ---")
# Check which role is retailer vs distributor
# Let's search knowledge base or user_role mapping
conn.close()
