import sqlite3
import pandas as pd

conn = sqlite3.connect('database.db')
df = pd.read_sql_query("SELECT * FROM sku_inventories", conn)

print("Shape:", df.shape)
print("\nNon-null counts:")
print(df.notnull().sum())

print("\nSample values of sku_code and sku_description:")
print(df[['sku_code', 'sku_description', 'product_id', 'uom', 'order_type']].drop_duplicates().head(30))
