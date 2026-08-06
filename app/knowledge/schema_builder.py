import json
import os
from app.database.allowed_tables import TARGET_SCOPE_TABLES, get_canonical_table_name

schema_path = "knowledge/schema/schema_metadata.json"
rel_path = "knowledge/relationships/relationships.json"
biz_meta_path = "knowledge/business_metadata.json"

schema = {}
if os.path.exists(schema_path):
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

relationships = []
if os.path.exists(rel_path):
    with open(rel_path, "r", encoding="utf-8") as f:
        relationships = json.load(f)

business_meta = {}
if os.path.exists(biz_meta_path):
    with open(biz_meta_path, "r", encoding="utf-8") as f:
        business_meta = json.load(f)

knowledge_chunks = []

# 1. Schema Chunks
for table_name, table_data in schema.items():
    canonical_name = get_canonical_table_name(table_name)
    if TARGET_SCOPE_TABLES and canonical_name not in TARGET_SCOPE_TABLES and table_data.get("category") != "lookup_master_table":
        continue

    primary_keys = table_data.get("primary_keys", [])
    pk = primary_keys[0] if primary_keys else "id"

    # Gather relationships dynamically instead of hardcoded
    common_joins = []
    if table_data.get("foreign_keys"):
        for fk in table_data["foreign_keys"]:
            common_joins.append(f"{canonical_name}.{fk['column']} = {fk['referenced_table']}.{fk['referenced_column']}")
    
    # Check incoming joins from relationships list
    for rel in relationships:
        if rel.get("to_table") == canonical_name:
            common_joins.append(f"{rel['from_table']}.{rel['from_column']} = {canonical_name}.{rel['to_column']}")

    columns = table_data.get("columns", [])
    col_lines = []
    for c in columns:
        c_name = c.get("name", "")
        c_type = c.get("datatype") or c.get("type") or "varchar"
        c_null = c.get("nullable", "YES")
        is_pk = " (PRIMARY KEY)" if c_name == pk else ""
        col_lines.append(f"  - {c_name} ({c_type}){is_pk} Nullable: {c_null}")

    chunk_text = f"""
Table Name: {canonical_name}
Primary Key: {pk}
Category: {table_data.get('category', 'unknown')}
Common Join Conditions:
  {chr(10).join(['- ' + j for j in common_joins]) if common_joins else 'None'}

Columns Schema:
{chr(10).join(col_lines)}
""".strip()

    knowledge_chunks.append({
        "id": f"table_{canonical_name}",
        "type": "table_card",
        "table_name": canonical_name,
        "text": chunk_text
    })

# 2. Enum Chunks
enum_values = business_meta.get("enum_values", {})
for col_key, values in enum_values.items():
    if not values: continue
    tbl = col_key.split(".")[0]
    chunk_text = f"Valid ENUM values for column {col_key}:\n" + "\n".join([f"- '{v}'" for v in values])
    knowledge_chunks.append({
        "id": f"enum_{col_key}",
        "type": "enum_card",
        "table_name": tbl,
        "text": chunk_text
    })

# 3. Lookup Chunks
business_terms = business_meta.get("business_terminology", {})
for term, info in business_terms.items():
    tbl = info.get("table")
    chunk_text = f"Business Term: {term}\nMaps to Lookup Table: {tbl}\nCondition: {info.get('condition')}\nDescription: {info.get('description')}"
    knowledge_chunks.append({
        "id": f"lookup_{term.replace(' ', '_')}",
        "type": "lookup_card",
        "table_name": tbl,
        "text": chunk_text
    })

os.makedirs("knowledge/generated", exist_ok=True)
output_file = "knowledge/generated/knowledge_chunks.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(knowledge_chunks, f, indent=2, ensure_ascii=False)

print(f"Generated {len(knowledge_chunks)} dynamic knowledge chunks -> {output_file}")