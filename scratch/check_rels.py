import json

rels = json.load(open("knowledge/relationships/relationships.json", encoding="utf-8"))
core = {
    "users", "role", "roles", "wallet_transaction", "sku_inventories",
    "sku_qr_points_maps", "sku_qr_points_map", "qr_point_map",
    "state", "states", "companies", "withdrawal_request",
    "automatic_transactions", "mechanic_details"
}

matched_core = []
matched_any = []

for r in rels:
    ft = r.get("from_table", "").lower()
    tt = r.get("to_table", "").lower()
    if ft in core and tt in core:
        matched_core.append(r)
    elif ft in core or tt in core:
        matched_any.append(r)

print(f"Matched {len(matched_core)} relationships strictly between core tables:")
for m in matched_core:
    print(f"  {m['from_table']}.{m['from_column']} -> {m['to_table']}.{m['to_column']} | Type: {m['type']} | Origin: {m['origin']}")

print(f"\nTotal relationships where at least one table is core: {len(matched_core) + len(matched_any)}")
