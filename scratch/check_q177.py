import sqlite3
import pandas as pd

conn = sqlite3.connect("database.db")

# For ID 177: Follow up question in Bengaluru context
ref_sql = """SELECT u.id, u.name, SUM(wt.amount) AS earnings 
FROM users u 
JOIN wallet_transaction wt ON u.id = wt.user_id 
WHERE u.user_role = 2 AND (u.city = 'Bengaluru' OR u.district = 'Bengaluru Urban') AND wt.amount > 0 AND wt.created_at >= '2026-07-01 00:00:00' AND wt.created_at < '2026-08-01 00:00:00' 
GROUP BY u.id, u.name;"""

gen_sql = """SELECT u.id AS retailer_id, u.name AS retailer_name, SUM(wt.amount) AS total_earnings 
FROM users u 
JOIN wallet_transaction wt ON u.id = wt.user_id 
WHERE u.user_role = 2 AND wt.reference_type IN ('topup','cash_point','referral_earning','coupon_redeem') AND wt.amount > 0 
GROUP BY u.id, u.name ORDER BY total_earnings DESC;"""

print("Ref:")
print(pd.read_sql(ref_sql, conn))

print("\nGen:")
print(pd.read_sql(gen_sql, conn))
