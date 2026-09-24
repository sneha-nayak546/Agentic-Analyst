import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables in database.db:", tables)

core_tables = ['users', 'role', 'wallet_transaction', 'sku_inventories', 'sku_qr_points_maps', 'state', 'companies', 'mechanic_details', 'withdrawal_request']
for t in core_tables:
    if t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f"  {t:25s}: {cnt:5d} rows")
    else:
        print(f"  {t:25s}: NOT FOUND")
