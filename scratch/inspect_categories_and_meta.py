import sqlite3
import json

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Let's inspect sku_code, sku_description
sample_skus = cursor.execute("SELECT DISTINCT sku_code, sku_description FROM sku_inventories LIMIT 20;").fetchall()
print("Sample sku_codes & sku_descriptions:")
for s in sample_skus:
    print(s)

# Let's check knowledge/business_dictionary.json
try:
    with open("knowledge/business_dictionary.json", "r", encoding="utf-8") as f:
        bdict = json.load(f)
    print("\nBusiness Dictionary keys / sample:")
    print(list(bdict.keys())[:15] if isinstance(bdict, dict) else len(bdict))
    print(json.dumps(bdict, indent=2)[:500])
except Exception as e:
    print("Error reading business dictionary:", e)

# Let's check knowledge/business_metadata.json
try:
    with open("knowledge/business_metadata.json", "r", encoding="utf-8") as f:
        bmeta = json.load(f)
    print("\nBusiness Metadata keys / sample:")
    if isinstance(bmeta, dict):
        print(list(bmeta.keys())[:15])
        # search for 'category', 'box', 'scan'
        for k, v in bmeta.items():
            kstr = json.dumps(v).lower()
            if 'box' in kstr or 'scan' in kstr or 'category' in kstr:
                print(f"Matched key: {k} -> {str(v)[:200]}")
except Exception as e:
    print("Error reading business metadata:", e)
