import sqlite3
import pandas as pd

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print("retailer_scanned_at distribution:")
dates = cursor.execute("""
    SELECT substr(retailer_scanned_at, 1, 7) as ym, count(*) 
    FROM sku_inventories 
    WHERE retailer_scanned_at IS NOT NULL 
    GROUP BY ym 
    ORDER BY ym;
""").fetchall()
for d in dates:
    print(d)

print("\nSample retailer_scanned_at rows:")
for r in cursor.execute("SELECT id, status_retailer_id, distributer_id, retailer_scanned_at, sku_code, sku_description FROM sku_inventories LIMIT 5;").fetchall():
    print(r)

print("\nDistributor count in sku_inventories:")
print(cursor.execute("""
    SELECT distributer_id, count(*) 
    FROM sku_inventories 
    GROUP BY distributer_id 
    ORDER BY count(*) DESC;
""").fetchall())

print("\nRetailer count in sku_inventories:")
print(cursor.execute("""
    SELECT status_retailer_id, count(*) 
    FROM sku_inventories 
    GROUP BY status_retailer_id 
    ORDER BY count(*) DESC;
""").fetchall())
