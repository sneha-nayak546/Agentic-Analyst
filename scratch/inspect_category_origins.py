import sqlite3
import pandas as pd
import json

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Check non-empty batch_details
batch_samples = cursor.execute("SELECT batch_details FROM sku_inventories WHERE batch_details != '[]' AND batch_details IS NOT NULL LIMIT 5;").fetchall()
print("Non-empty batch_details count:", cursor.execute("SELECT count(*) FROM sku_inventories WHERE batch_details != '[]' AND batch_details IS NOT NULL;").fetchone()[0])
for b in batch_samples:
    print(b[0])

# Check what category could mean:
# Look at the question:
# "Which category has the highest number of box scans this month?"
# "Which category has the lowest number of box scans this month, and which state has the lowest number of box scans?"
# Where could category be?
# Could category be:
# 1) In sku_inventories? E.g., order_type, uom, or prefix of sku_code / sku_description?
# 2) Or does category refer to order_categories / master_categories / categories in MySQL schema or a missing table or something?
# Let's inspect all tables and columns in schema_metadata.json for "category" and what joins to sku_inventories!

with open("knowledge/schema/schema_metadata.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

for tname, tinfo in meta.items():
    cols = tinfo.get("columns", {})
    for cname, cinfo in cols.items():
        if "category" in cname.lower():
            print(f"Table: {tname}, Col: {cname}, Type: {cinfo.get('datatype')}")

