"""
Exact Identifier Search & Nearest Suggestion Engine for JGH Intelligence Engine.
Handles:
  - Exact primary key lookups for entities (distributor, retailer, customer, user, etc.)
  - 4-Digit Distributor Master Code Lookups (companies.id, users.distributer_id, sap_code)
  - True Dynamic Total Earnings calculation: SUM(wt.amount) from wallet_transaction
  - ID format validation (rejects invalid characters like 'ABC@@123')
  - Nearest valid ID suggestions when an ID does not exist
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from app.database.read_executor import execute_read_query

INVALID_ID_CHARS = set("@!#$%^&*~+=/\\?<>{}[]|")

ROLE_MAP = {
    "distributor": 4,
    "distributors": 4,
    "retailer": 2,
    "retailers": 2,
    "wholesaler": 5,
    "wholesalers": 5,
    "mechanic": 3,
    "mechanics": 3,
    "customer": 2,
    "customers": 2,
    "user": None,
    "users": None
}

COMMON_ENGLISH_WORDS = {
    "role", "roles", "user", "users", "distributor", "distributors", "retailer", "retailers",
    "wholesaler", "wholesalers", "mechanic", "mechanics", "customer", "customers",
    "data", "performance", "earnings", "details", "info", "report", "all", "active", "status",
    "for", "in", "the", "a", "an", "and", "or", "to", "of", "with", "table", "tables", "schema",
    "database", "db", "count", "counts", "list", "names", "growth", "transactions", "transaction",
    "wallet", "wallets", "balance", "balances", "system", "analytics", "dashboard", "diagram",
    "profile", "profiles", "overview", "summary", "analysis", "trend", "trends",
    "that", "this", "these", "those", "top", "first", "one", "single", "person", "people",
    "someone", "somebody", "anyone", "anybody", "highest", "lowest", "best", "worst",
    "each", "every", "some", "any", "their", "them", "which", "what", "who", "whom", "whose",
    "me", "my", "give", "show", "find", "get", "fetch", "check"
}

EXPLANATORY_PREFIXES = [
    r"^explain\b", r"^what\s+is\b", r"^what\s+are\b", r"^what\s+do\b", r"^teach\s+me\b",
    r"^how\s+does\b", r"^how\s+do\b", r"^how\s+are\b", r"^tell\s+me\s+about\b", r"^meaning\s+of\b",
    r"^difference\s+between\b", r"^draw\b", r"^build\b", r"^create\b"
]

def extract_id_from_prompt(prompt: str, skip_intent_check: bool = False) -> Optional[Dict[str, Any]]:
    """
    Extracts entity type and identifier string from natural language queries.
    Strictly validates that candidate is an actual ID, not a generic word.
    """
    if not prompt or not isinstance(prompt, str):
        return None

    p_clean = prompt.strip()
    p_lower = p_clean.lower()

    # If it's an educational / tutor question, never treat it as an ID lookup.
    # BUT: If the query also contains an explicit entity+ID+number pattern, it IS an ID lookup
    # regardless of how the sentence starts (e.g. "What are the earnings for user ID 65848").
    HAS_EXPLICIT_ID = bool(re.search(
        r"\b(?:distributor|retailers?|wholesalers?|mechanics?|customers?|users?|account)\s+"
        r"(?:id|#|number|code)\s*[:=\s#]?\s*[0-9]{3,}\b",
        p_clean, re.IGNORECASE
    )) or bool(re.search(
        r"\b(?:id|user_id)\s*[:=\s#]\s*[0-9]{3,}\b",
        p_clean, re.IGNORECASE
    ))
    
    if not skip_intent_check:
        # Check for analytical/comparative intent which should NOT be intercepted as a simple ID lookup
        is_comparative = bool(re.search(
            r"\b(?:compare|vs|versus|difference|growth|change|trend|previous|last\s+month|monthly|how\s+many|count|number\s+of|total\s+number)\b",
            p_lower
        ))
        
        # Check for relational/multi-condition requests (e.g. table, list, linked to, generate)
        is_relational = bool(re.search(
            r"\b(?:table|list|linked|column|generate|multiple|all)\b",
            p_lower
        ))
        
        if is_comparative or is_relational:
            return None

    if any(re.search(pat, p_lower) for pat in EXPLANATORY_PREFIXES) and not HAS_EXPLICIT_ID:
        return None

    # Helper: Check if string is a plausible ID (contains digits, starts with #, or valid code)
    def is_plausible_id(candidate: str) -> bool:
        c_low = candidate.lower().lstrip('#')
        if not c_low or c_low in COMMON_ENGLISH_WORDS:
            return False
        # Must contain at least one digit or be preceded by explicit identifier prefix
        has_digit = any(ch.isdigit() for ch in candidate)
        has_id_char = any(ch in candidate for ch in ["-", "_", "#"])
        return has_digit or has_id_char

    # Pattern 1: Explicit ID keyword: "distributor ID 5842", "distributor ID 10245", "retailer ID RET1025", "user ID: 46965", "ID #12345"
    m1 = re.search(
        r"\b(distributor|retailers?|wholesalers?|mechanics?|customers?|users?|account|company|transactions?)\s+(?:id|#|number|code)\s*[:=\s]?\s*([0-9a-zA-Z@!#$%^&*_\-]+)\b",
        p_clean,
        re.IGNORECASE
    )
    if m1:
        ent = m1.group(1).lower().rstrip('s')
        if ent == 'customer':
            ent = 'retailer'
        raw_id = m1.group(2).strip()
        if is_plausible_id(raw_id):
            return {
                "has_id": True,
                "raw_id": raw_id,
                "entity": ent,
                "role_id": ROLE_MAP.get(ent)
            }

    # Pattern 2: Generic ID keyword: "details of ID 46556", "ID 46556", "details of ID 5842", "find ID 10245", "show ID 47017"
    m2 = re.search(
        r"\b(?:details\s+(?:of|for)\s+id|find\s+id|show\s+id|user\s+id|i\s+want\s+details\s+of\s+id|give\s+details\s+of\s+id|\bid)\s*[:=\s#]\s*([0-9a-zA-Z@!#$%^&*_\-]+)\b",
        p_clean,
        re.IGNORECASE
    )
    if m2:
        raw_id = m2.group(1).strip()
        if is_plausible_id(raw_id):
            ent = "user"
            if "distributor" in p_lower:
                ent = "distributor"
            elif "retailer" in p_lower:
                ent = "retailer"
            elif "wholesaler" in p_lower:
                ent = "wholesaler"
            return {
                "has_id": True,
                "raw_id": raw_id,
                "entity": ent,
                "role_id": ROLE_MAP.get(ent)
            }

    # Pattern 3: Direct Entity + Numeric / Alphanumeric ID (WITHOUT explicit 'id' word):
    # e.g. "distributor 5842", "distributor 46965", "retailer 46556", "show customer 46578", "find user 47017"
    m3 = re.search(
        r"\b(?:find|show|give\s+details\s+for|give\s+me\s+details\s+of|i\s+want\s+details\s+of)?\s*(distributor|retailer|wholesaler|customer|user|mechanic|company)\s+([0-9]+[a-zA-Z0-9_\-]*|[a-zA-Z]+[0-9]+[a-zA-Z0-9_\-]*|#[0-9]+)\b",
        p_clean,
        re.IGNORECASE
    )
    if m3:
        ent = m3.group(1).lower()
        if ent == 'customer':
            ent = 'retailer'
        raw_id = m3.group(2).strip().lstrip('#')
        if is_plausible_id(raw_id):
            return {
                "has_id": True,
                "raw_id": raw_id,
                "entity": ent,
                "role_id": ROLE_MAP.get(ent)
            }

    # Pattern 4: Standalone "details of 46556" or "details of 5842"
    m4 = re.search(
        r"\b(?:details\s+(?:of|for)|i\s+want\s+details\s+of|show\s+details\s+of)\s+([0-9]{3,8})\b",
        p_clean,
        re.IGNORECASE
    )
    if m4:
        raw_id = m4.group(1).strip()
        return {
            "has_id": True,
            "raw_id": raw_id,
            "entity": "user",
            "role_id": None
        }

    return None

def validate_id_format(raw_id: str, entity_name: str = "ID") -> Tuple[bool, Optional[str]]:
    """Validates identifier formatting, rejecting illegal characters."""
    if any(char in raw_id for char in INVALID_ID_CHARS):
        return False, f'"{raw_id}" is not a valid {entity_name.capitalize()} ID format. Please enter a valid identifier (e.g. 46965 or 5842).'
    
    # Must be numeric or alphanumeric without spaces
    if not re.match(r"^[0-9a-zA-Z_\-]+$", raw_id):
        return False, f'"{raw_id}" is not a valid {entity_name.capitalize()} ID format. Please enter a valid identifier.'

    return True, None

def execute_exact_id_search(id_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes an exact ID lookup with TRUE SUM OF EARNINGS and 4-digit distributor code resolution.
    Returns the matching record with dynamic earnings from wallet_transaction.
    """
    raw_id = id_info["raw_id"]
    entity = id_info.get("entity", "user")
    role_id = id_info.get("role_id")

    # 1. Validate Format
    is_valid, err_msg = validate_id_format(raw_id, entity_name=entity)
    if not is_valid:
        return {
            "status": "error",
            "is_id_search": True,
            "id_found": False,
            "message": err_msg,
            "summary": err_msg,
            "raw_id": raw_id,
            "entity": entity,
            "results": [],
            "columns": [],
            "suggested_matches": []
        }

    # 2. Check for 4-Digit Distributor Master Code in `companies` / `users.distributer_id`
    if raw_id.isdigit() and (len(raw_id) <= 4 or entity == "distributor"):
        int_id = int(raw_id)
        # Check if this matches a company distributor code
        comp_sql = f"SELECT c.id AS distributor_code, c.name AS company_name, c.sap_code, c.phone, c.email FROM companies c WHERE c.id = {int_id} LIMIT 1;"
        comp_res = execute_read_query(comp_sql)
        if comp_res.get("data"):
            comp_row = comp_res["data"][0]
            # Find linked user account for this distributor
            user_sql = (
                f"SELECT u.id AS user_id, u.name, u.mobile_number, u.email, u.user_role, u.distributer_id, "
                f"u.city, u.district, u.address, u.wallet_balance, u.status, u.created_at, "
                f"COALESCE((SELECT SUM(wt.amount) FROM wallet_transaction wt WHERE wt.user_id = u.id AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning')), 0) AS total_earnings "
                f"FROM users u WHERE u.distributer_id = {int_id} OR u.id = {int_id} LIMIT 1;"
            )
            u_res = execute_read_query(user_sql)
            u_row = u_res.get("data", [{}])[0] if u_res.get("data") else {}

            tot_earn = u_row.get("total_earnings", 0) or 0
            wal_bal = u_row.get("wallet_balance", 0) or 0
            earn_str = f"₹{tot_earn:,.2f}".replace(".00", "")
            bal_str = f"₹{wal_bal:,.2f}".replace(".00", "")

            loc_str = u_row.get("district") or u_row.get("city") or u_row.get("address") or "N/A"
            contact_str = str(comp_row.get("phone") or u_row.get("mobile_number") or comp_row.get("email") or "N/A")
            sap_str = comp_row.get("sap_code") or "N/A"
            u_id_str = str(u_row.get("user_id")) if u_row.get("user_id") else "N/A"

            summary = (
                f"Found exact match for Distributor ID **{raw_id}**:\n\n"
                f"• **Company / Distributor Name:** {comp_row.get('company_name') or u_row.get('name') or 'N/A'}\n"
                f"• **Distributor Code:** {raw_id} (SAP Code: {sap_str})\n"
                f"• **Linked User Account ID:** {u_id_str} (Role 4 — Distributor)\n"
                f"• **Location / Address:** {loc_str}\n"
                f"• **Status:** {str(u_row.get('status', 'Approved')).capitalize()}\n"
                f"• **Total Earnings (Sum of Amounts):** {earn_str}\n"
                f"• **Current Wallet Balance:** {bal_str}\n"
                f"• **Contact:** {contact_str}"
            )

            merged_result = {
                "distributor_code": raw_id,
                "company_name": comp_row.get("company_name"),
                "sap_code": sap_str,
                "user_id": u_row.get("user_id"),
                "user_name": u_row.get("name"),
                "user_role": 4,
                "status": u_row.get("status", "approved"),
                "total_earnings": tot_earn,
                "wallet_balance": wal_bal,
                "location": loc_str,
                "contact": contact_str
            }

            return {
                "status": "success",
                "is_id_search": True,
                "id_found": True,
                "sql_query": user_sql,
                "results": [merged_result],
                "columns": list(merged_result.keys()),
                "summary": summary,
                "raw_id": raw_id,
                "entity": "distributor",
                "total_earnings": tot_earn,
                "understanding": {
                    "entity": "Distributor",
                    "summary": f"Distributor ID: {raw_id} (Code: {raw_id})"
                }
            }

    # 3. Standard Users / Retailer / Distributor Lookup with TRUE SUM OF EARNINGS
    if raw_id.isdigit():
        int_id = int(raw_id)
        where_clauses = [f"(u.id = {int_id} OR u.distributer_id = {int_id})"]
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        sql = (
            f"SELECT u.id AS user_id, u.name, u.mobile_number, u.email, u.user_role, u.distributer_id, "
            f"u.city, u.district, u.address, u.wallet_balance, u.status, u.created_at, "
            f"COALESCE((SELECT SUM(wt.amount) FROM wallet_transaction wt WHERE wt.user_id = u.id AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning')), 0) AS total_earnings "
            f"FROM users u WHERE {' AND '.join(where_clauses)} LIMIT 1;"
        )
    else:
        where_clauses = [f"(u.id = '{raw_id}' OR u.referral_code = '{raw_id}' OR u.mobile_number = '{raw_id}')"]
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        sql = (
            f"SELECT u.id AS user_id, u.name, u.mobile_number, u.email, u.user_role, u.distributer_id, "
            f"u.city, u.district, u.address, u.wallet_balance, u.status, u.created_at, "
            f"COALESCE((SELECT SUM(wt.amount) FROM wallet_transaction wt WHERE wt.user_id = u.id AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning')), 0) AS total_earnings "
            f"FROM users u WHERE {' AND '.join(where_clauses)} LIMIT 1;"
        )

    exec_res = execute_read_query(sql)
    rows = exec_res.get("data", [])
    columns = exec_res.get("columns", [])

    # 4. Match Found in Users table
    if rows and len(rows) > 0:
        row = rows[0]
        r_num = row.get("user_role")
        role_label = "Distributor" if r_num == 4 else ("Retailer" if r_num == 2 else ("Wholesaler" if r_num == 5 else "User"))
        loc_str = row.get("district") or row.get("city") or row.get("address") or "N/A"
        
        tot_earnings = row.get("total_earnings", 0) or 0
        wal_bal = row.get("wallet_balance", 0) or 0
        earn_str = f"₹{tot_earnings:,.2f}".replace(".00", "")
        bal_str = f"₹{wal_bal:,.2f}".replace(".00", "")

        summary = (
            f"Found exact match for {role_label} ID **{raw_id}**:\n\n"
            f"• **Name:** {row.get('name') or 'N/A'}\n"
            f"• **Role:** {role_label} (Role {r_num})\n"
            f"• **Location:** {loc_str}\n"
            f"• **Status:** {str(row.get('status', 'Active')).capitalize()}\n"
            f"• **Total Earnings (Sum of Amounts):** {earn_str}\n"
            f"• **Current Wallet Balance:** {bal_str}\n"
            f"• **Contact:** {row.get('mobile_number') or row.get('email') or 'N/A'}"
        )

        return {
            "status": "success",
            "is_id_search": True,
            "id_found": True,
            "sql_query": sql,
            "results": rows,
            "columns": columns,
            "summary": summary,
            "raw_id": raw_id,
            "entity": entity,
            "total_earnings": tot_earnings,
            "understanding": {
                "entity": role_label,
                "summary": f"{role_label} ID: {raw_id}"
            }
        }

    # 5. Match Not Found -> Query Nearest Matches in Database
    suggested_ids = []
    if raw_id.isdigit():
        int_id = int(raw_id)
        near_where = f"WHERE user_role = {role_id}" if role_id else ""
        near_sql = f"SELECT id, name FROM users {near_where} ORDER BY ABS(id - {int_id}) ASC LIMIT 3;"
        near_res = execute_read_query(near_sql)
        for r in near_res.get("data", []):
            suggested_ids.append(str(r["id"]))

    ent_label = entity.capitalize()
    not_found_msg = f"{ent_label} ID **{raw_id}** does not exist in the available data."
    if suggested_ids:
        sugg_list = "\n".join([f"• **{sid}**" for sid in suggested_ids])
        summary = (
            f"{not_found_msg}\n\n"
            f"**Did you mean:**\n{sugg_list}\n\n"
            f"*These are suggested matches based on identifier proximity.*"
        )
        options = [f"Show {ent_label} ID {sid}" for sid in suggested_ids]
    else:
        summary = not_found_msg
        options = []

    return {
        "status": "not_found",
        "is_id_search": True,
        "id_found": False,
        "sql_query": sql,
        "results": [],
        "columns": [],
        "summary": summary,
        "raw_id": raw_id,
        "entity": entity,
        "options": options,
        "suggested_matches": suggested_ids,
        "understanding": {
            "entity": ent_label,
            "summary": f"Requested ID: {raw_id} • Exact match: ✗ Not found"
        }
    }
