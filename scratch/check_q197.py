import sqlite3
import pandas as pd

conn = sqlite3.connect("database.db")

ref_sql = """SELECT u.id, u.name, u.wallet_balance, SUM(wt.amount) AS july_earnings 
FROM users u 
JOIN wallet_transaction wt ON u.id = wt.user_id 
WHERE u.user_role = 2 AND u.status = 'approved' AND u.state_id = 11 AND u.wallet_balance > 10000 AND wt.amount > 0 AND wt.created_at >= '2026-07-01 00:00:00' AND wt.created_at < '2026-08-01 00:00:00' 
GROUP BY u.id, u.name, u.wallet_balance;"""

print("Ref rows:")
df_ref = pd.read_sql(ref_sql, conn)
print(df_ref)

# Let's inspect users with role=2 and state_id=11
df_users = pd.read_sql("SELECT u.id, u.name, u.status, u.state_id, s.sname, u.wallet_balance FROM users u LEFT JOIN state s ON u.state_id = s.id WHERE u.user_role = 2", conn)
print("\nAll retailers:")
print(df_users)
