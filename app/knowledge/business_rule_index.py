import os
import json
from typing import List, Dict, Any, Optional

# Targeted business rules per domain table
TABLE_BUSINESS_RULES: Dict[str, List[str]] = {
    "users": [
        "User roles: 1=Business Admin, 2=Retailer ('shop owner'/'dealer'), 3=Super Admin / Mechanic, 4=Distributor, 5=Wholesaler, 6=Executive.",
        "DEALERS: 'Dealer' or 'shop owner' ALWAYS means Retailer (`users.user_role = 2`). NEVER use user_role = 4 for dealers.",
        "Status: 'approved' (active) or 'pending'.",
        "Geographic queries: filter u.district, u.city, u.address, or u.state_id ONLY if explicitly mentioned. For Bengaluru, filter `(u.city = 'Bengaluru' OR u.district = 'Bengaluru Urban')`.",
        "State resolution: Join users.state_id = state.id and select state.sname AS state_name instead of raw state_id. (Karnataka: state_id=12, Maharashtra: state_id=11).",
        "WALLET BALANCE: For questions asking for 'wallet balance' or 'total wallet balance' of users/retailers/distributors, use `users.wallet_balance` directly: `SUM(u.wallet_balance)` or `u.wallet_balance`. Do NOT join `wallet_transaction` for balance queries.",
        "PERCENTAGE CALCULATIONS: In SQLite, ALWAYS multiply by 100.0 first: `ROUND(100.0 * COUNT(...) / COUNT(*), 2)` or `ROUND(100.0 * SUM(...) / COUNT(*), 2)` to prevent integer division truncating to 0.0.",
        "CRITICAL: There is NO separate 'distributors' or 'retailers' table; distributors and retailers are both in `users` (user_role=4 for distributor, user_role=2 for retailer).",
        "CRITICAL: For lookup queries by ID (e.g. 'Show user/retailer/distributor with ID X'), write a clean, direct query on `users` table. Do NOT create multi-CTE queries joining unrelated scan or transaction tables unless explicitly requested."
    ],
    "wallet_transaction": [
        "JGH EARNINGS: SUM(wt.amount) WHERE wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND wt.amount > 0.",
        "Earnings timestamp: Filter date/time using wt.created_at (half-open interval: >= start AND < next_period_start).",
        "Retailer earnings: Join users u ON wt.user_id = u.id WHERE u.user_role = 2 AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND wt.amount > 0.",
        "Distributor earnings: Join users u ON wt.user_id = u.id WHERE u.user_role = 4 AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND wt.amount > 0.",
        "PROHIBITIONS: Do NOT calculate earnings using wallet_balance, COUNT(wt.id), all wallet transactions, or unfiltered SUM(amount)."
    ],
    "withdrawal_request": [
        "Tracks payout requests from users (wr.amount, wr.status, wr.tds_amount, wr.created_at).",
        "Join with users table: `withdrawal_request.user_id = users.id` to retrieve recipient details.",
        "Statuses: 0=pending, 1=approved/paid, 2=rejected."
    ],
    "sku_inventories": [
        "JGH BOX QUANTITY / SCANNING: Authoritative box calculation is SUM(qr_point_map.box_calulation_um) joined on sku_inventories.sku_code = qr_point_map.sku_code.",
        "CRITICAL RULE: NEVER use COUNT(sku_inventories.id) as the box quantity.",
        "Scanning timestamp: Filter date/time using sku_inventories.retailer_scanned_at (half-open interval: >= start AND < next_period_start).",
        "Retailer scanning: si.status_retailer_id = retailer.id WHERE retailer.user_role = 2. Metric is SUM(qr_point_map.box_calulation_um).",
        "Distributor scanning: si.distributer_id = distributor.id WHERE distributor.user_role = 4. Metric is SUM(qr_point_map.box_calulation_um).",
        "Retailer under distributor: Join both users retailer (si.status_retailer_id = retailer.id, role 2) AND users distributor (si.distributer_id = distributor.id, role 4).",
        "State scanning: Join users retailer (si.status_retailer_id = users.id) and state (users.state_id = state.id). Metric is SUM(qr_point_map.box_calulation_um) GROUP BY state.sname."
    ],
    "qr_point_map": [
        "Maps sku_code to box_calulation_um. The authoritative box quantity calculation is SUM(qr_point_map.box_calulation_um) joined on sku_inventories.sku_code = qr_point_map.sku_code."
    ],
    "state": [
        "Contains state definitions (id, sname). Join with users.state_id = state.id and project state.sname AS state_name."
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
        "When computing 'retailer earning under a distributor', join `wallet_transaction` with `retailer_distributor_mappings` ON `wallet_transaction.user_id = retailer_distributor_mappings.retailer_id`, and group by retailer: `GROUP BY u.id, u.name`."
    ]
}

TERM_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "users": {
        "retailers / dealers / shop owners": "users.user_role = 2",
        "distributors": "users.user_role = 4",
        "wholesalers": "users.user_role = 5",
        "active / approved": "users.status = 'approved'",
        "state name": "state.sname AS state_name (via users.state_id = state.id)"
    },
    "wallet_transaction": {
        "earnings / earned / total earnings": "SUM(wt.amount) WHERE wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND wt.amount > 0",
        "balance / current balance": "u.wallet_balance directly from users table (NEVER sum wallet_transaction for current balance)",
        "cashback / qr point": "wt.reference_type = 'cash_point'",
        "referral": "wt.reference_type = 'referral_earning'"
    },
    "withdrawal_request": {
        "withdrawals / payouts": "table `withdrawal_request` wr",
        "total withdrawals count": "COUNT(*) FROM withdrawal_request"
    },
    "sku_inventories": {
        "box scans / boxes scanned / scanning report": "JOIN qr_point_map qpm ON si.sku_code = qpm.sku_code -> SUM(qpm.box_calulation_um)",
        "retailer box scans": "si.retailer_scanned_at IS NOT NULL with retailer.user_role = 2",
        "scanning date filter": "si.retailer_scanned_at >= start AND si.retailer_scanned_at < end"
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


def retrieve_relevant_business_rules(requirement: Any, tables: Optional[List[str]] = None) -> str:
    """
    Dynamically retrieves applicable business rules and term translations based on
    the semantic BusinessRequirement contract and associated table context.
    Eliminates ad-hoc question-specific if/else branches.
    """
    req_entities = []
    req_metrics = []
    if hasattr(requirement, "entities"):
        req_entities = [str(e).lower() for e in requirement.entities]
    elif isinstance(requirement, dict):
        req_entities = [str(e).lower() for e in requirement.get("entities", [])]

    if hasattr(requirement, "metrics"):
        req_metrics = [str(m).lower() for m in requirement.metrics]
    elif isinstance(requirement, dict):
        req_metrics = [str(m).lower() for m in requirement.get("metrics", [])]

    effective_tables = set(tables or [])
    if any("retailer" in e or "distributor" in e or "wholesaler" in e or "mechanic" in e or "user" in e for e in req_entities):
        effective_tables.add("users")
    if any("box" in m or "scan" in m for m in req_metrics):
        effective_tables.add("sku_inventories")
        effective_tables.add("qr_point_map")
    if any("earning" in m or "revenue" in m or "wallet" in m for m in req_metrics):
        effective_tables.add("wallet_transaction")
    if any("state" in e for e in req_entities):
        effective_tables.add("state")
        effective_tables.add("users")
    if any("company" in e for e in req_entities):
        effective_tables.add("companies")

    if not effective_tables:
        effective_tables = {"users", "wallet_transaction", "sku_inventories"}

    return get_selective_business_rules(list(effective_tables))
