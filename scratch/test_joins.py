import json
import os

with open('knowledge/connections_knowledge.json', 'r', encoding='utf-8') as f:
    conn_k = json.load(f)
with open('knowledge/relationships/relationships.json', 'r', encoding='utf-8') as f:
    rels = json.load(f)

sample_tables = {'retailer_distributor_mappings', 'users', 'wallet_transaction', 'sku_inventories'}
found_joins = set()
for r in rels:
    if r.get('from_table') in sample_tables and r.get('to_table') in sample_tables:
        found_joins.add(f"{r['from_table']}.{r['from_column']} = {r['to_table']}.{r['to_column']}")

for t in sample_tables:
    if t in conn_k:
        for ob in conn_k[t].get('outbound', []):
            if ob.get('target_table') in sample_tables:
                found_joins.add(f"{t}.{ob.get('column')} = {ob.get('target_table')}.{ob.get('target_column')}")

print("Discovered Joins across sample tables:")
for j in sorted(found_joins):
    print("  •", j)
