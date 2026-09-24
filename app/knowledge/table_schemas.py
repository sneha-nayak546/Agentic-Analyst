import os
import json
from typing import List, Dict, Any, Optional

_schema_cache: Optional[Dict[str, Any]] = None

def get_full_schema_metadata() -> Dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        schema_file = "knowledge/schema/schema_metadata.json"
        if os.path.exists(schema_file):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    _schema_cache = json.load(f)
            except Exception:
                _schema_cache = {}
        else:
            _schema_cache = {}
    return _schema_cache

# Target scope table descriptions and essential column hints
TABLE_SUMMARIES = {
    "users": "Core user accounts (distributors role=4, retailers role=2, mechanics role=3, wholesalers role=5).",
    "wallet_transaction": "Ledger of credits/earnings (cash_point, referral, topup, coupon_redeem) and debits (withdrawal).",
    "withdrawal_request": "Payout / cash withdrawal requests submitted by users with amounts, TDS, and statuses.",
    "sku_inventories": "SKU catalog, invoice tracking, box inventory, and retailer/wholesaler scanning timestamps.",
    "sku_qr_points_map": "Points and box calculation configuration mapped by sku_code.",
    "companies": "Client companies and business units in JGH ecosystem.",
    "mechanic_details": "Workshop/garage profiles and distributor association for mechanics (role=3).",
    "automatic_transactions": "Automated payout/bank transfer transaction logs with reference numbers.",
    "banks": "Bank master directory.",
    "distributor_categories": "Category mapping for distributors."
}

JOIN_DEFINITIONS = [
    ("users", "wallet_transaction", "users.id = wallet_transaction.user_id"),
    ("users", "withdrawal_request", "users.id = withdrawal_request.user_id"),
    ("users", "mechanic_details", "users.id = mechanic_details.mechanic_id"),
    ("users", "sku_inventories", "users.id = sku_inventories.distributer_id (or status_retailer_id / status_wholeseller_id)"),
    ("sku_inventories", "sku_qr_points_map", "sku_inventories.sku_code = sku_qr_points_map.sku_code"),
    ("users", "automatic_transactions", "users.id = automatic_transactions.user_id")
]

IGNORED_COLUMNS = {
    "password", "two_factor_secret", "two_factor_recovery_codes", "remember_token",
    "fcm_token", "device_id", "deleted_at", "email_verified_at"
}

def get_selective_schema_context(tables: List[str]) -> str:
    """
    Returns a compact, targeted schema definition containing ONLY the tables
    and columns necessary for the detected query tables.
    """
    if not tables:
        tables = ["users"]

    full_schema = get_full_schema_metadata()
    lines = []

    for tbl in tables:
        tbl_clean = tbl.strip()
        summary = TABLE_SUMMARIES.get(tbl_clean, "")
        lines.append(f"TABLE `{tbl_clean}`" + (f" ({summary})" if summary else "") + ":")

        if tbl_clean in full_schema:
            cols = full_schema[tbl_clean].get("columns", {})
            col_entries = []
            cols_iterable = cols.values() if isinstance(cols, dict) else (cols if isinstance(cols, list) else [])
            for c in cols_iterable:
                c_name = c.get("name", "")
                if c_name in IGNORED_COLUMNS:
                    continue
                c_type = c.get("type", "")
                if c.get("is_enum") and c.get("enum_values"):
                    enums = ", ".join([f"'{v}'" for v in c["enum_values"][:6]])
                    col_entries.append(f"  - {c_name} ({c_type}) [ENUM: {enums}]")
                else:
                    col_entries.append(f"  - {c_name} ({c_type})")
            lines.extend(col_entries)
        else:
            # Fallback if metadata not loaded for table
            lines.append("  - (Standard table schema applies)")

        lines.append("")

    # Add only relevant joins between requested tables
    relevant_joins = []
    tbl_set = set(tables)
    for t1, t2, join_str in JOIN_DEFINITIONS:
        if t1 in tbl_set and t2 in tbl_set:
            relevant_joins.append(f"- {join_str}")

    if relevant_joins:
        lines.append("RELEVANT JOINS:")
        lines.extend(relevant_joins)

    return "\n".join(lines).strip()
