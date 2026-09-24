import sqlite3
import os
import pandas as pd

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall()]
print('=== Tables in database.db ===')
for t in tables:
    cursor.execute(f'SELECT count(*) FROM "{t}"')
    cnt = cursor.fetchone()[0]
    print(f'  {t}: {cnt} rows')

print('\n=== CSV Dump Files ===')
if os.path.exists('Sku_Inventeries_Dump_data.csv'):
    df_sku = pd.read_csv('Sku_Inventeries_Dump_data.csv', nrows=3)
    total_sku = sum(1 for _ in open('Sku_Inventeries_Dump_data.csv', encoding='utf-8', errors='ignore')) - 1
    print(f'Sku_Inventeries_Dump_data.csv: {total_sku} rows')
    print('  Columns:', list(df_sku.columns))

if os.path.exists('Wallet_Transaction_Dump_Data.csv'):
    df_w = pd.read_csv('Wallet_Transaction_Dump_Data.csv', nrows=3)
    total_w = sum(1 for _ in open('Wallet_Transaction_Dump_Data.csv', encoding='utf-8', errors='ignore')) - 1
    print(f'Wallet_Transaction_Dump_Data.csv: {total_w} rows')
    print('  Columns:', list(df_w.columns))
