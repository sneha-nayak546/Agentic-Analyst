import os
import json
from sqlalchemy import text, inspect
from app.database.config import get_db_engine

engine = get_db_engine()
inspector = inspect(engine)

target_tables = [
    "users",
    "role",
    "wallet_transaction",
    "companies",
    "sku_inventories",
    "mechanic_details",
    "withdrawal_request",
    "automatic_transactions"
]

results = {}

with engine.connect() as conn:
    for tbl in target_tables:
        tdata = {}
        try:
            tdata["row_count"] = conn.execute(text(f"SELECT COUNT(*) FROM `{tbl}`")).scalar()
        except Exception as e:
            tdata["row_count_error"] = str(e)

        cols = inspector.get_columns(tbl)
        tdata["columns"] = []
        for c in cols:
            tdata["columns"].append({
                "name": c['name'],
                "type": str(c['type']),
                "nullable": c['nullable'],
                "default": str(c['default'])
            })

        pk = inspector.get_pk_constraint(tbl)
        tdata["primary_keys"] = pk.get('constrained_columns', [])

        fks = inspector.get_foreign_keys(tbl)
        tdata["foreign_keys"] = fks

        idxs = inspector.get_indexes(tbl)
        tdata["indexes"] = [i['name'] for i in idxs]

        # Distinct categorical values
        tdata["categoricals"] = {}
        for c in cols:
            cname = c['name']
            ctype = str(c['type'])
            if 'ENUM' in ctype.upper() or any(k in cname.lower() for k in ['status', 'type', 'role', 'action']):
                try:
                    dist_res = conn.execute(text(f"SELECT `{cname}`, COUNT(*) as cnt FROM `{tbl}` GROUP BY `{cname}` ORDER BY cnt DESC LIMIT 10")).fetchall()
                    tdata["categoricals"][cname] = [(str(r[0]), r[1]) for r in dist_res]
                except Exception as e:
                    pass

        # Sample 2 rows
        try:
            samples = conn.execute(text(f"SELECT * FROM `{tbl}` LIMIT 2")).mappings().fetchall()
            tdata["samples"] = []
            for s in samples:
                clean_s = {}
                for k, v in s.items():
                    if hasattr(v, "isoformat"):
                        clean_s[k] = v.isoformat()
                    elif isinstance(v, (bytes, bytearray)):
                        clean_s[k] = "<binary>"
                    else:
                        clean_s[k] = v
                tdata["samples"].append(clean_s)
        except Exception as e:
            tdata["sample_error"] = str(e)

        results[tbl] = tdata

with open("live_db_profile.json", "w") as f:
    json.dump(results, f, indent=2)

print("Saved live_db_profile.json successfully!")
