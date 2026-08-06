TARGET_SCOPE_TABLES = [
    "users",
    "user_role",
    "wallet_transaction",
    "sku_inventory",
    "companies",
    "machine_details",
    "withdrawal",
    "automatic_transaction_bank",
    "automate"
]

def is_allowed_table(table_name: str) -> bool:
    if not table_name:
        return False
    return table_name.lower() in TARGET_SCOPE_TABLES
