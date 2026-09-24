import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

print("Query: retailers with positive earnings (transaction_type = 1 / credit / cash_point) in July 2026:")
c.execute("""
SELECT 
    u.id, 
    u.name, 
    u.user_role,
    SUM(w.amount) AS total_earnings
FROM users u
JOIN wallet_transaction w ON u.id = w.user_id
WHERE u.user_role = 2
  AND w.amount > 0
  AND w.created_at >= '2026-07-01' 
  AND w.created_at < '2026-08-01'
GROUP BY u.id, u.name
ORDER BY total_earnings DESC;
""")
rows = c.fetchall()
for r in rows:
    print(" -", r)

print("\nWhat about without user_role = 2 filter (all users with positive earnings in July 2026):")
c.execute("""
SELECT 
    u.id, 
    u.name, 
    u.user_role,
    SUM(w.amount) AS total_earnings
FROM users u
JOIN wallet_transaction w ON u.id = w.user_id
WHERE w.amount > 0
  AND w.created_at >= '2026-07-01' 
  AND w.created_at < '2026-08-01'
GROUP BY u.id, u.name, u.user_role
ORDER BY total_earnings DESC;
""")
for r in c.fetchall():
    print(" -", r)

print("\nWhat about users not in `users` table who have wallet_transactions?")
c.execute("""
SELECT 
    w.user_id, 
    u.name,
    u.user_role,
    SUM(w.amount) AS total_earnings
FROM wallet_transaction w
LEFT JOIN users u ON u.id = w.user_id
WHERE w.amount > 0
  AND w.created_at >= '2026-07-01' 
  AND w.created_at < '2026-08-01'
GROUP BY w.user_id
ORDER BY total_earnings DESC
LIMIT 10;
""")
for r in c.fetchall():
    print(" -", r)

conn.close()
