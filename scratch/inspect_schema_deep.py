import sqlite3
import json

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("================= SKU_INVENTORIES DEEP DIVE =================")
# Check columns
cols = cursor.execute("PRAGMA table_info(sku_inventories);").fetchall()
for c in cols:
    print(dict(c))

# Check sample values of key columns
print("\n--- DISTINCT order_type ---")
print(cursor.execute("SELECT DISTINCT order_type, count(*) FROM sku_inventories GROUP BY order_type").fetchall())

print("\n--- DISTINCT uom ---")
print(cursor.execute("SELECT DISTINCT uom, count(*) FROM sku_inventories GROUP BY uom").fetchall())

print("\n--- SAMPLE sku_code, sku_description, product_id ---")
for r in cursor.execute("SELECT id, sku_code, sku_description, product_id, uom, lpn_number, distributer_id, status_retailer_id, wholesaler_scanned_at, retailer_scanned_at FROM sku_inventories LIMIT 5;").fetchall():
    print(dict(r))

print("\n--- retailer_scanned_at STATS ---")
print(cursor.execute("SELECT COUNT(*), COUNT(retailer_scanned_at), MIN(retailer_scanned_at), MAX(retailer_scanned_at) FROM sku_inventories;").fetchone())

print("\n--- wholesaler_scanned_at STATS ---")
print(cursor.execute("SELECT COUNT(*), COUNT(wholesaler_scanned_at), MIN(wholesaler_scanned_at), MAX(wholesaler_scanned_at) FROM sku_inventories;").fetchone())

print("\n--- status_retailer_id STATS ---")
print(cursor.execute("SELECT status_retailer_id, COUNT(*) FROM sku_inventories WHERE status_retailer_id IS NOT NULL GROUP BY status_retailer_id;").fetchall())

print("\n--- distributer_id STATS ---")
print(cursor.execute("SELECT distributer_id, COUNT(*) FROM sku_inventories WHERE distributer_id IS NOT NULL GROUP BY distributer_id;").fetchall())

print("\n--- batch_details SAMPLE ---")
for r in cursor.execute("SELECT id, batch_details, customer_info FROM sku_inventories LIMIT 3;").fetchall():
    print(dict(r))

print("\n================= USERS DEEP DIVE =================")
for r in cursor.execute("SELECT id, name, user_role, state_id, city, district FROM users;").fetchall():
    print(dict(r))

print("\n================= RETAILER_DISTRIBUTOR_MAPPINGS =================")
for r in cursor.execute("SELECT * FROM retailer_distributor_mappings;").fetchall():
    print(dict(r))

print("\n================= WALLET_TRANSACTION SAMPLE =================")
for r in cursor.execute("SELECT id, user_id, amount, transaction_type, reference_id, reference_type, status, remark, created_at FROM wallet_transaction LIMIT 5;").fetchall():
    print(dict(r))
