import os
import json
from typing import List, Dict, Any

# Targeted business rules per domain table
TABLE_BUSINESS_RULES: Dict[str, List[str]] = {
    "users": [
        "User roles: 1=Business Admin, 2=Retailer ('shop owner'/'dealer'), 3=Super Admin / Mechanic, 4=Distributor, 5=Wholesaler, 6=Executive.",
        "Status: 'approved' (active) or 'pending'.",
        "Geographic queries: filter u.district, u.city, u.address, or u.state_id ONLY if explicitly mentioned."
    ],
    "wallet_transaction": [
        "Earnings / Money made / Revenue: SUM(wt.amount) WHERE wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning').",
        "Wallet balance / Net balance: SUM(wt.amount) across all transactions.",
        "Reference types: 'cash_point'=QR scan earning, 'referral_earning'=Referral bonus, 'topup'=Recharge, 'coupon_redeem'=Coupon, 'withdrawal'=Cash out.",
        "Positive amount = credit (earning); negative amount = debit (withdrawal)."
    ],
    "withdrawal_request": [
        "Tracks payout requests from users (wr.amount, wr.status, wr.tds_amount, wr.created_at).",
        "Join with users table: `withdrawal_request.user_id = users.id` to retrieve recipient details.",
        "Statuses: 0=pending, 1=approved/paid, 2=rejected."
    ],
    "sku_inventories": [
        "Scanned boxes / Box scans: filter `sku_inventories.retailer_scanned_at IS NOT NULL` for retailers, or `sku_inventories.wholesaler_scanned_at IS NOT NULL` for wholesalers.",
        "Do NOT route physical box scan questions to wallet_transaction.",
        "Join with `sku_qr_points_map` ON `sku_inventories.sku_code = sku_qr_points_map.sku_code`."
    ],
    "sku_qr_points_map": [
        "Contains QR point rules, uom, and box calculation multiplier."
    ],
    "companies": [
        "Contains company profiles, SAP codes, and business units (id, name, phone, email, sap_code, business_unit, jgh_company)."
    ],
    "mechanic_details": [
        "Workshop details associated with mechanic users (user_role=3): garage_id, shop_name, owner_name, region, distributor_code."
    ],
    "automatic_transactions": [
        "Bank automated transfer logs with bank_reference_number and transfer_type."
    ],
    "retailer_distributor_mappings": [
        "Tracks relationships between retailers and distributors.",
        "Join with `users` ON `users.id = retailer_distributor_mappings.retailer_id` for retailers.",
        "Join with `users` ON `users.id = retailer_distributor_mappings.distributor_id` for distributors.",
        "When computing 'retailer earning under a distributor', join `wallet_transaction` with `retailer_distributor_mappings` ON `wallet_transaction.user_id = retailer_distributor_mappings.retailer_id`."
    ]
}

TERM_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "users": {
        "retailers / dealers / shop owners": "users.user_role = 2",
        "distributors": "users.user_role = 4",
        "wholesalers": "users.user_role = 5",
        "active / approved": "users.status = 'approved'"
    },
    "wallet_transaction": {
        "earnings / earned / revenue": "SUM(wt.amount) with reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning')",
        "balance / current balance": "SUM(wt.amount)",
        "cashback / qr point": "wt.reference_type = 'cash_point'",
        "referral": "wt.reference_type = 'referral_earning'"
    },
    "withdrawal_request": {
        "withdrawals / payouts": "table `withdrawal_request` wr",
        "total withdrawals count": "COUNT(*) FROM withdrawal_request"
    },
    "sku_inventories": {
        "retailer box scans": "si.retailer_scanned_at IS NOT NULL",
        "wholesaler box scans": "si.wholesaler_scanned_at IS NOT NULL",
        "box inventory / skus": "table `sku_inventories` si"
    }
}

def get_selective_business_rules(tables: List[str], intent: str = "") -> str:
    """
    Returns only the business rules and term translations applicable to the
    tables and intent of the current query.
    """
    if not tables:
        tables = ["users"]

    rules_lines = []
    terms_lines = []

    for tbl in tables:
        if tbl in TABLE_BUSINESS_RULES:
            for rule in TABLE_BUSINESS_RULES[tbl]:
                rules_lines.append(f"- [{tbl}] {rule}")
        if tbl in TERM_TRANSLATIONS:
            for term, mapping in TERM_TRANSLATIONS[tbl].items():
                terms_lines.append(f"- \"{term}\" → `{mapping}`")

    output = []
    if rules_lines:
        output.append("APPLICABLE BUSINESS RULES:\n" + "\n".join(rules_lines))
    if terms_lines:
        output.append("APPLICABLE TERM TRANSLATIONS:\n" + "\n".join(terms_lines))

    return "\n\n".join(output).strip()
