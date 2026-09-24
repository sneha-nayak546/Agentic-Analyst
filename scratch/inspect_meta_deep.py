import json

with open("knowledge/schema/schema_metadata.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

print(f"Total tables in schema_metadata.json: {len(meta)}")

# Find tables matching scan, box, category, retailer, distributor, state, product, inventory, sku
keywords = ["scan", "box", "category", "retailer", "distributor", "state", "product", "inventory", "sku"]
for kw in keywords:
    matched = [t for t in meta.keys() if kw in t.lower()]
    print(f"\nKeyword '{kw}' in table name ({len(matched)}):")
    print(", ".join(matched))

print("\n--- Inspect sku_inventories in schema_metadata.json ---")
if "sku_inventories" in meta:
    print(json.dumps(meta["sku_inventories"], indent=2)[:1500])

print("\n--- Inspect categories / category tables in schema_metadata.json ---")
cat_tables = [t for t in meta.keys() if "category" in t.lower() or "cat" in t.lower()]
for ct in cat_tables:
    print(f"\nTable: {ct}")
    cols = meta[ct].get("columns", {})
    print("Columns:", list(cols.keys()))
