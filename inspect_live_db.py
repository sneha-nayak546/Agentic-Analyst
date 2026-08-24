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

print("=== TABLE PROFILES ===")
with engine.connect() as conn:
    for tbl in target_tables:
        print(f"\n==========================================")
        print(f"TABLE: {tbl}")
        print(f"==========================================")
        try:
            count_res = conn.execute(text(f"SELECT COUNT(*) FROM `{tbl}`")).scalar()
            print(f"Row count: {count_res}")
        except Exception as e:
            print(f"Row count error: {e}")

        cols = inspector.get_columns(tbl)
        print(f"\nColumns ({len(cols)}):")
        for c in cols:
            print(f"  - {c['name']} : {c['type']} (nullable={c['nullable']}, default={c['default']})")

        pk = inspector.get_pk_constraint(tbl)
        print(f"\nPrimary Key: {pk.get('constrained_columns')}")

        fks = inspector.get_foreign_keys(tbl)
        print(f"\nForeign Keys: {fks}")

        idxs = inspector.get_indexes(tbl)
        print(f"\nIndexes: {[i['name'] for i in idxs]}")

        # Top distinct values for enum/status/type cols
        for c in cols:
            cname = c['name']
            ctype = str(c['type'])
            if 'ENUM' in ctype.upper() or any(k in cname.lower() for k in ['status', 'type', 'role', 'action']):
                try:
                    dist_res = conn.execute(text(f"SELECT `{cname}`, COUNT(*) as cnt FROM `{tbl}` GROUP BY `{cname}` ORDER BY cnt DESC LIMIT 10")).fetchall()
                    print(f"\n  [Distinct values for {cname}]: {dist_res}")
                except Exception as e:
                    pass

        # Sample rows
        try:
            sample = conn.execute(text(f"SELECT * FROM `{tbl}` LIMIT 2")).mappings().fetchall()
            print(f"\nSample Row 1:\n{dict(sample[0]) if sample else 'None'}")
        except Exception as e:
            print(f"Sample error: {e}")
