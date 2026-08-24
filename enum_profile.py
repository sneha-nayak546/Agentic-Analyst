import json
from sqlalchemy import text
from app.database.config import get_db_engine

engine = get_db_engine()

info = {}
with engine.connect() as conn:
    # 1. users
    info["users.status"] = [r[0] for r in conn.execute(text("SELECT DISTINCT status FROM users LIMIT 10")).fetchall()]
    info["users.kyc_status"] = [r[0] for r in conn.execute(text("SELECT DISTINCT kyc_status FROM users LIMIT 10")).fetchall()]
    info["users.account_type"] = [r[0] for r in conn.execute(text("SELECT DISTINCT account_type FROM users LIMIT 10")).fetchall()]
    
    # 2. wallet_transaction (query from recent rows to avoid full table scan)
    info["wallet_transaction.transaction_type"] = [r[0] for r in conn.execute(text("SELECT DISTINCT transaction_type FROM (SELECT transaction_type FROM wallet_transaction ORDER BY id DESC LIMIT 5000) as t")).fetchall()]
    info["wallet_transaction.reference_type"] = [r[0] for r in conn.execute(text("SELECT DISTINCT reference_type FROM (SELECT reference_type FROM wallet_transaction ORDER BY id DESC LIMIT 5000) as t")).fetchall()]
    info["wallet_transaction.status"] = [r[0] for r in conn.execute(text("SELECT DISTINCT status FROM (SELECT status FROM wallet_transaction ORDER BY id DESC LIMIT 5000) as t")).fetchall()]
    
    # 3. withdrawal_request
    info["withdrawal_request.status"] = [r[0] for r in conn.execute(text("SELECT DISTINCT status FROM withdrawal_request LIMIT 10")).fetchall()]
    info["withdrawal_request.withdraw_request_type"] = [r[0] for r in conn.execute(text("SELECT DISTINCT withdraw_request_type FROM withdrawal_request LIMIT 10")).fetchall()]
    
    # 4. automatic_transactions
    info["automatic_transactions.transfer_type"] = [r[0] for r in conn.execute(text("SELECT DISTINCT transfer_type FROM automatic_transactions LIMIT 10")).fetchall()]
    info["automatic_transactions.status"] = [r[0] for r in conn.execute(text("SELECT DISTINCT status FROM automatic_transactions LIMIT 10")).fetchall()]
    info["automatic_transactions.transaction_source"] = [r[0] for r in conn.execute(text("SELECT DISTINCT transaction_source FROM automatic_transactions LIMIT 10")).fetchall()]

    # 5. sku_inventories
    info["sku_inventories.order_type"] = [r[0] for r in conn.execute(text("SELECT DISTINCT order_type FROM (SELECT order_type FROM sku_inventories ORDER BY id DESC LIMIT 5000) as t")).fetchall()]
    info["sku_inventories.is_active"] = [r[0] for r in conn.execute(text("SELECT DISTINCT is_active FROM (SELECT is_active FROM sku_inventories ORDER BY id DESC LIMIT 5000) as t")).fetchall()]
    info["sku_inventories.is_offline"] = [r[0] for r in conn.execute(text("SELECT DISTINCT is_offline FROM (SELECT is_offline FROM sku_inventories ORDER BY id DESC LIMIT 5000) as t")).fetchall()]

    # 6. companies
    info["companies.business_unit"] = [r[0] for r in conn.execute(text("SELECT DISTINCT business_unit FROM companies LIMIT 20")).fetchall()]
    info["companies.jgh_company"] = [r[0] for r in conn.execute(text("SELECT DISTINCT jgh_company FROM companies LIMIT 20")).fetchall()]

    # 7. mechanic_details
    info["mechanic_details.mechanic_account_type"] = [r[0] for r in conn.execute(text("SELECT DISTINCT mechanic_account_type FROM mechanic_details LIMIT 20")).fetchall()]
    info["mechanic_details.actual_tier"] = [r[0] for r in conn.execute(text("SELECT DISTINCT actual_tier FROM mechanic_details LIMIT 20")).fetchall()]
    info["mechanic_details.working_tier"] = [r[0] for r in conn.execute(text("SELECT DISTINCT working_tier FROM mechanic_details LIMIT 20")).fetchall()]
    info["mechanic_details.have_garage"] = [r[0] for r in conn.execute(text("SELECT DISTINCT have_garage FROM mechanic_details LIMIT 20")).fetchall()]

print(json.dumps(info, indent=2, default=str))
