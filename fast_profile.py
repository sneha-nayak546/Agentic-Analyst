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
        cols = inspector.get_columns(tbl)
        tdata["columns"] = [{
            "name": c['name'],
            "type": str(c['type']),
            "nullable": c['nullable'],
            "default": str(c['default'])
        } for c in cols]

        pk = inspector.get_pk_constraint(tbl)
        tdata["primary_keys"] = pk.get('constrained_columns', [])

        fks = inspector.get_foreign_keys(tbl)
        tdata["foreign_keys"] = fks

        idxs = inspector.get_indexes(tbl)
        tdata["indexes"] = [i['name'] for i in idxs]

        # Fast sample rows (LIMIT 2 without ORDER BY)
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

# Fetch all role rows (14 rows total)
with engine.connect() as conn:
    role_rows = conn.execute(text("SELECT * FROM `role`")).mappings().fetchall()
    results["role"]["all_rows"] = [dict(r) for r in role_rows]

with open("live_db_profile.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("SUCCESS_WRITTEN_PROFILE")
