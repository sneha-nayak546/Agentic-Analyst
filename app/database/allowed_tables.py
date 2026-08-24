TARGET_SCOPE_TABLES = [
    "users",
    "companies",
    "wallet_transaction",
    "role",
    "user_role",
    "sku_inventories",
    "mechanic_details",
    "withdrawal_request",
    "automatic_transactions",
    "sku_qr_points_map",
    "state"
]

def is_allowed_table(table_name: str) -> bool:
    if not table_name:
        return False
    return table_name.lower() in TARGET_SCOPE_TABLES

def get_canonical_table_name(table_name: str) -> str:
    if not table_name:
        return ""
    return table_name.lower()

