import json

with open("knowledge/schema/schema_metadata.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

print(f"Top-level type: {type(meta)}")
if isinstance(meta, dict):
    print("Keys:", list(meta.keys())[:20])
    for k in list(meta.keys())[:10]:
        val = meta[k]
        print(f"Key '{k}': type={type(val)}, keys={list(val.keys()) if isinstance(val, dict) else len(val) if isinstance(val, list) else val}")
elif isinstance(meta, list):
    print(f"List length: {len(meta)}")
    if meta:
        print("First item:", meta[0])
