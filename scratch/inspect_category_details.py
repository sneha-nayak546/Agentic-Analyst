import sqlite3
import pandas as pd

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Check distinct uom, order_type, warehouse in sku_inventories
print("sku_inventories UOM:", cursor.execute("SELECT DISTINCT uom FROM sku_inventories").fetchall())
print("sku_inventories order_type:", cursor.execute("SELECT DISTINCT order_type FROM sku_inventories").fetchall())
print("sku_inventories warehouse:", cursor.execute("SELECT DISTINCT warehouse FROM sku_inventories").fetchall())

# Check if there are other columns or text patterns in sku_description
sample_descs = cursor.execute("SELECT DISTINCT sku_description FROM sku_inventories LIMIT 25;").fetchall()
print("Sample sku_description:", sample_descs)

# Check Sku_Inventeries_Dump_data.csv header
df = pd.read_csv("Sku_Inventeries_Dump_data.csv", nrows=5)
print("CSV columns:", list(df.columns))

# Check Wallet_Transaction_Dump_Data.csv
df_w = pd.read_csv("Wallet_Transaction_Dump_Data.csv", nrows=5)
print("Wallet CSV columns:", list(df_w.columns))
print(df_w.head(2))
