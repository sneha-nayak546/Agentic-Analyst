import os
import re
import json
import ollama
from typing import Dict, Any, Optional

DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")

def is_ollama_online() -> bool:
    import urllib.request
    try:
        url = f"{OLLAMA_HOST}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False


def _synthesize_sql_from_plan(plan: Dict[str, Any]) -> Optional[str]:
    """
    Deterministic enterprise SQL synthesizer using STRUCTURED execution plan.
    Only handles standard enterprise queries when the plan has high confidence (>= 85).
    Otherwise returns None to route to LLM (Qwen).
    """
    if not plan or not isinstance(plan, dict):
        return None

    confidence = plan.get("confidence_score", 90)
    intent = plan.get("intent", "").lower()

    # Defer complex multi-conditional queries (thresholds, complex matching) to the LLM
    complex_condition_pattern = r"(?:>|<|=|>=|<=|greater than|less than|more than|at least|at most|under|over|above|below)\s*\d+|starts with|ends with|having|whose"
    if re.search(complex_condition_pattern, intent, re.IGNORECASE):
        return None

    if confidence < 85:
        # Defer ambiguous / low-confidence questions to the LLM
        return None

    primary_entity = plan.get("primary_entity", "users")
    role_id = plan.get("role_id")
    region = plan.get("region")
    region_filter = plan.get("region_filter")
    status_sql = plan.get("status_sql")
    time_filter = plan.get("time_filter", "None")
    is_earnings = plan.get("is_earnings_query", False)
    tables = plan.get("tables", [])
    comparison = plan.get("comparison")
    intent = plan.get("intent", "").lower()
    specific_id = plan.get("specific_id") or plan.get("identifier_value")

    # Determine LIMIT
    limit = plan.get("limit")
    if limit is None:
        limit_m = re.search(r"\b(?:top|first|highest|lowest|limit)\s*(\d+)\b", intent)
        if limit_m:
            limit = int(limit_m.group(1))
        elif any(w in intent for w in ["single person", "the one person", "that one person", "1 person", "single retailer", "single distributor", "single user", "the person", "top 1", "highest 1", "who is the one person", "that single person", "the top one"]):
            limit = 1
        else:
            limit = 500

    # Determine time condition
    injected_time_filter = ""
    if time_filter and time_filter != "None":
        injected_time_filter = time_filter

    # Intent detection
    q_text = intent
    is_user_earnings = is_earnings or any(w in q_text for w in ["earning", "earnings", "earned", "revenue", "sales", "how much"]) or "with earnings" in q_text
    is_total_earnings = any(w in q_text for w in ["total earnings", "sum of earnings", "earnings of all"])
    is_balance = (any(w in q_text for w in ["wallet balance", "total balance", "current balance", "highest balance", "balance", "balances"]) or (limit == 1 and any(w in q_text for w in ["top 1 person", "top person", "highest person", "the top one", "top 1", "that top 1", "top one person", "single person"]))) and not is_user_earnings
    is_withdrawal = any(w in q_text for w in ["withdrawal", "withdraw", "withdrawals", "payout"])
    is_count = ("aggregate" in intent) or any(w in q_text for w in ["count", "total count", "number of", "how many"])
    is_comparison = comparison is not None

    has_withdrawal_request = "withdrawal_request" in tables or primary_entity == "withdrawal_request"
    has_sku = "sku_inventories" in tables or primary_entity == "sku_inventories"
    has_companies = "companies" in tables or primary_entity == "company"
    has_mechanic = "mechanic_details" in tables or primary_entity == "mechanic"
    has_automatic_tx = "automatic_transactions" in tables or primary_entity == "automatic_transactions"

    # Specific ID Query Handling
    if specific_id:
        id_type = plan.get("identifier_type") or plan.get("id_type")
        id_clause = f"u.id = {specific_id}"
        if id_type and id_type != primary_entity and id_type != plan.get("entity", ""):
            if id_type == "distributor":
                id_clause = f"u.distributer_id = {specific_id}"
            else:
                id_clause = f"u.linked_{id_type}_id = {specific_id}"

        if is_user_earnings or is_earnings or "earning" in intent:
            where_parts = [
                "wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning')",
                id_clause
            ]
            if role_id:
                where_parts.append(f"u.user_role = {role_id}")
            if injected_time_filter:
                where_parts.append(injected_time_filter)
            where_clause = " WHERE " + " AND ".join(where_parts)
            return f"SELECT u.id AS user_id, u.name, u.mobile_number, u.city, u.district, u.status, COALESCE(SUM(wt.amount), 0) AS total_earnings FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id{where_clause} GROUP BY u.id, u.name, u.mobile_number, u.city, u.district, u.status;"
        elif is_balance:
            where_clause = f" WHERE {id_clause}"
            return f"SELECT u.id AS user_id, u.name, u.mobile_number, SUM(wt.amount) AS total_balance FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id{where_clause} GROUP BY u.id, u.name, u.mobile_number;"
        else:
            where_parts = [id_clause]
            if role_id:
                where_parts.append(f"u.user_role = {role_id}")
            where_clause = " WHERE " + " AND ".join(where_parts)
            if is_count:
                return f"SELECT COUNT(*) AS total_count FROM users u{where_clause};"
            return f"SELECT u.id AS user_id, u.name, u.mobile_number, u.email, u.user_role, u.city, u.district, u.address, u.wallet_balance, u.status, u.created_at FROM users u{where_clause} LIMIT {limit};"

    # Build region filter from plan's structured field
    region_clause = None
    if region_filter:
        region_clause = region_filter.replace("users.", "u.").replace("LOWER(users.", "LOWER(u.")
    elif region:
        from app.agent.query_planner import STATE_MAP
        reg_lower = region.lower()
        reg_cap = region.title()
        if reg_lower in STATE_MAP:
            state_code = STATE_MAP[reg_lower]
            region_clause = f"(u.district = '{reg_cap}' OR u.city = '{reg_cap}' OR u.address LIKE '%{reg_cap}%' OR u.state_id = {state_code})"
        else:
            region_clause = f"(u.district = '{reg_cap}' OR u.city = '{reg_cap}' OR u.address LIKE '%{reg_cap}%')"

    # === CASE: Percentage Change / Growth Rate Queries ===
    is_percentage_query = any(w in q_text for w in ["percentage change", "percentage growth", "percent change", "% change", "rate of change", "growth percentage", "percent increase", "percent decrease"])
    if is_percentage_query:
        from app.utils.date_parser import MONTH_NAME_TO_NUM, MONTH_NUM_TO_NAME, get_month_bounds
        # Extract two months: e.g. July 2026 and August 2026
        month_matches = list(re.finditer(r"\b(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)\b(?:\s+(20\d{2}))?", q_text))
        if len(month_matches) >= 2:
            m1_num = MONTH_NAME_TO_NUM[month_matches[0].group(1).lower()]
            y1_num = int(month_matches[0].group(2)) if month_matches[0].group(2) else 2026
            m2_num = MONTH_NAME_TO_NUM[month_matches[1].group(1).lower()]
            y2_num = int(month_matches[1].group(2)) if month_matches[1].group(2) else 2026

            s1, e1 = get_month_bounds(m1_num, y1_num)
            s2, e2 = get_month_bounds(m2_num, y2_num)
            lbl1 = f"{MONTH_NUM_TO_NAME[m1_num].lower()}_{y1_num}"
            lbl2 = f"{MONTH_NUM_TO_NAME[m2_num].lower()}_{y2_num}"

            if has_withdrawal_request or is_withdrawal or "payout" in q_text:
                status_clause = "AND wr.status = 1" if ("approved" in q_text or "paid" in q_text) else ""
                return (
                    f"SELECT "
                    f"SUM(CASE WHEN wr.created_at >= '{s1}' AND wr.created_at < '{e1}' {status_clause} THEN wr.amount ELSE 0 END) AS {lbl1}_payouts, "
                    f"SUM(CASE WHEN wr.created_at >= '{s2}' AND wr.created_at < '{e2}' {status_clause} THEN wr.amount ELSE 0 END) AS {lbl2}_payouts, "
                    f"ROUND(((SUM(CASE WHEN wr.created_at >= '{s2}' AND wr.created_at < '{e2}' {status_clause} THEN wr.amount ELSE 0 END) - "
                    f"SUM(CASE WHEN wr.created_at >= '{s1}' AND wr.created_at < '{e1}' {status_clause} THEN wr.amount ELSE 0 END)) / "
                    f"NULLIF(SUM(CASE WHEN wr.created_at >= '{s1}' AND wr.created_at < '{e1}' {status_clause} THEN wr.amount ELSE 0 END), 0)) * 100, 2) AS percentage_change "
                    f"FROM withdrawal_request wr;"
                )
            else:
                return (
                    f"SELECT "
                    f"SUM(CASE WHEN wt.created_at >= '{s1}' AND wt.created_at < '{e1}' AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN wt.amount ELSE 0 END) AS {lbl1}_earnings, "
                    f"SUM(CASE WHEN wt.created_at >= '{s2}' AND wt.created_at < '{e2}' AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN wt.amount ELSE 0 END) AS {lbl2}_earnings, "
                    f"ROUND(((SUM(CASE WHEN wt.created_at >= '{s2}' AND wt.created_at < '{e2}' AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN wt.amount ELSE 0 END) - "
                    f"SUM(CASE WHEN wt.created_at >= '{s1}' AND wt.created_at < '{e1}' AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN wt.amount ELSE 0 END)) / "
                    f"NULLIF(SUM(CASE WHEN wt.created_at >= '{s1}' AND wt.created_at < '{e1}' AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN wt.amount ELSE 0 END), 0)) * 100, 2) AS percentage_change "
                    f"FROM wallet_transaction wt;"
                )

    # === CASE: Multi-Region / Geographic State Comparison ===
    geo_comparison = plan.get("geo_comparison")
    if geo_comparison and len(geo_comparison.get("state_ids", [])) >= 2:
        state_ids_str = ", ".join(str(sid) for sid in geo_comparison["state_ids"])
        time_clause = f"AND {injected_time_filter}" if injected_time_filter else ""
        role_clause = f"AND u.user_role = {role_id}" if role_id else ""
        status_clause = f"AND {status_sql.replace('users.', 'u.')}" if status_sql else ""
        
        if is_user_earnings or is_total_earnings or "earning" in q_text:
            return (
                f"SELECT s.sname AS state_name, COUNT(DISTINCT u.id) AS total_users, "
                f"COALESCE(SUM(wt.amount), 0) AS total_earnings, "
                f"ROUND(COALESCE(SUM(wt.amount), 0) / NULLIF(COUNT(DISTINCT u.id), 0), 2) AS avg_earnings_per_user "
                f"FROM state s "
                f"JOIN users u ON u.state_id = s.id {role_clause} {status_clause} "
                f"LEFT JOIN wallet_transaction wt ON wt.user_id = u.id AND wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') {time_clause} "
                f"WHERE s.id IN ({state_ids_str}) "
                f"GROUP BY s.id, s.sname "
                f"ORDER BY total_earnings DESC;"
            )
        elif is_balance:
            return (
                f"SELECT s.sname AS state_name, COUNT(DISTINCT u.id) AS total_users, "
                f"COALESCE(SUM(u.wallet_balance), 0) AS total_balance "
                f"FROM state s "
                f"JOIN users u ON u.state_id = s.id {role_clause} {status_clause} "
                f"WHERE s.id IN ({state_ids_str}) "
                f"GROUP BY s.id, s.sname "
                f"ORDER BY total_balance DESC;"
            )
        else:
            return (
                f"SELECT s.sname AS state_name, COUNT(DISTINCT u.id) AS total_users "
                f"FROM state s "
                f"JOIN users u ON u.state_id = s.id {role_clause} {status_clause} "
                f"WHERE s.id IN ({state_ids_str}) "
                f"GROUP BY s.id, s.sname "
                f"ORDER BY total_users DESC;"
            )

    # === CASE: Comparison Query ===
    if is_comparison and comparison:
        from app.utils.date_parser import MONTH_NAME_TO_NUM, MONTH_NUM_TO_NAME, get_month_bounds
        comp_m = comparison.get("compare_month", 6)
        comp_y = comparison.get("compare_year", 2026)
        comp_start, comp_end = get_month_bounds(comp_m, comp_y)
        comp_cond = f"wt.created_at >= '{comp_start}' AND wt.created_at < '{comp_end}'"
        comp_label = f"{MONTH_NUM_TO_NAME[comp_m].lower()}_{comp_y}"

        base_cond = injected_time_filter if injected_time_filter else None
        if not base_cond:
            return None  # Route to LLM

        base_label = "primary_period"
        tc = plan.get("time_constraint", {})
        if tc.get("month") and tc.get("year"):
            base_label = f"{MONTH_NUM_TO_NAME.get(tc['month'], 'period').lower()}_{tc['year']}"

        where_clauses = []
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        if region_clause:
            where_clauses.append(region_clause)
        if status_sql:
            where_clauses.append(status_sql.replace("users.", "u."))

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        select_clause = (
            f"u.id AS user_id, u.name, u.mobile_number, u.city, u.district, "
            f"SUM(CASE WHEN {base_cond} THEN wt.amount ELSE 0 END) AS earnings_{base_label}, "
            f"SUM(CASE WHEN {comp_cond} THEN wt.amount ELSE 0 END) AS earnings_{comp_label}, "
            f"(SUM(CASE WHEN {base_cond} THEN wt.amount ELSE 0 END) - SUM(CASE WHEN {comp_cond} THEN wt.amount ELSE 0 END)) AS net_growth"
        )
        return f"SELECT {select_clause} FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id {where_str} GROUP BY u.id, u.name, u.mobile_number, u.city, u.district ORDER BY earnings_{base_label} DESC LIMIT {limit};"

    # === CASE: Reward Points Query (sku_qr_points_maps) ===
    if any(w in q_text for w in ["reward point", "reward points", "qr point", "qr points", "points distributed", "points earned"]):
        where_clauses = []
        if region_clause:
            where_clauses.append(region_clause)
        if injected_time_filter:
            si_time = injected_time_filter.replace("wt.created_at", "si.retailer_scanned_at")
            where_clauses.append(si_time)
        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return (
            f"SELECT SUM(sqm.points) AS total_reward_points, COUNT(si.id) AS total_scanned_boxes "
            f"FROM sku_inventories si "
            f"JOIN sku_qr_points_maps sqm ON si.sku_code = sqm.sku_code "
            f"JOIN users u ON u.id = si.status_retailer_id "
            f"{where_str};"
        )

    # === CASE: Wholesaler Bottleneck Query ===
    if ("wholesaler" in q_text or "wholesalers" in q_text) and any(w in q_text for w in ["dispatched", "dispatch", "boxes", "box"]) and any(w in q_text for w in ["zero", "no scan", "unconfirmed", "zero retailer", "without scan"]):
        return (
            f"SELECT u.id AS wholesaler_id, u.name AS wholesaler_name, u.mobile_number, u.city, u.district, "
            f"COUNT(si.id) AS dispatched_boxes, COUNT(si.retailer_scanned_at) AS retailer_confirmed_scans "
            f"FROM sku_inventories si "
            f"JOIN users u ON u.id = si.status_wholeseller_id "
            f"WHERE si.wholesaler_scanned_at IS NOT NULL "
            f"GROUP BY u.id, u.name, u.mobile_number, u.city, u.district "
            f"HAVING COUNT(si.id) > 100 AND COUNT(si.retailer_scanned_at) = 0 "
            f"ORDER BY dispatched_boxes DESC LIMIT {limit};"
        )

    # === CASE: Withdrawal Request Query ===
    if (has_withdrawal_request or is_withdrawal) and not is_user_earnings:
        where_clauses = []
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        if region_clause:
            where_clauses.append(region_clause)
        status_filter_val = plan.get("status_filter")
        if "pending" in q_text or status_filter_val == "pending" or (status_sql and "pending" in status_sql):
            where_clauses.append("wr.status = 0")
        elif "approved" in q_text or "paid" in q_text or "successful" in q_text or status_filter_val == "approved" or (status_sql and "approved" in status_sql):
            where_clauses.append("wr.status = 1")
        elif "rejected" in q_text or "reject" in q_text or status_filter_val == "rejected":
            where_clauses.append("wr.status = 2")
        elif status_sql:
            where_clauses.append(status_sql.replace("users.", "u."))
        if injected_time_filter:
            wr_time = injected_time_filter.replace("wt.created_at", "wr.created_at")
            where_clauses.append(wr_time)

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        if is_count or ("how many" in q_text and "list" not in q_text) or ("total withdrawals" in q_text and "list" not in q_text):
            return f"SELECT COUNT(*) AS total_withdrawals, SUM(wr.amount) AS total_amount FROM withdrawal_request wr JOIN users u ON wr.user_id = u.id {where_str};"

        # Check if TDS specific query
        if any(w in q_text for w in ["tds", "tax deducted", "tds amount"]):
            return (
                f"SELECT wr.id AS withdrawal_id, u.id AS user_id, u.name, u.mobile_number, "
                f"wr.amount, wr.tds_amount, (wr.amount - wr.tds_amount) AS net_payout, wr.status, wr.created_at "
                f"FROM withdrawal_request wr "
                f"JOIN users u ON wr.user_id = u.id "
                f"{where_str} ORDER BY wr.created_at DESC LIMIT {limit};"
            )

        return (
            f"SELECT wr.id AS withdrawal_id, u.id AS user_id, u.name, u.mobile_number, "
            f"wr.amount, wr.status, wr.tds_amount, wr.created_at "
            f"FROM withdrawal_request wr "
            f"JOIN users u ON wr.user_id = u.id "
            f"{where_str} ORDER BY wr.created_at DESC LIMIT {limit};"
        )

    # === CASE: SKU Inventories Scan Volume Leaderboard ===
    if has_sku or any(w in q_text for w in ["sku", "skus", "scan", "scans", "scanning", "scanned", "box scan", "box scans"]):
        where_clauses = []
        if injected_time_filter:
            if "retailer" in q_text:
                si_time = injected_time_filter.replace("wt.created_at", "si.retailer_scanned_at")
                where_clauses.append("si.retailer_scanned_at IS NOT NULL")
                where_clauses.append(si_time)
            elif "wholesaler" in q_text:
                si_time = injected_time_filter.replace("wt.created_at", "si.wholesaler_scanned_at")
                where_clauses.append("si.wholesaler_scanned_at IS NOT NULL")
                where_clauses.append(si_time)
            elif any(w in q_text for w in ["scan", "scans", "scanning", "scanned", "box scan", "box scans"]):
                si_time_ret = injected_time_filter.replace("wt.created_at", "si.retailer_scanned_at")
                si_time_whole = injected_time_filter.replace("wt.created_at", "si.wholesaler_scanned_at")
                where_clauses.append(f"(({si_time_ret}) OR ({si_time_whole}))")
            else:
                si_time = injected_time_filter.replace("wt.created_at", "si.created_at")
                where_clauses.append(si_time)
        elif any(w in q_text for w in ["scan", "scans", "scanning", "scanned", "box scan", "box scans"]):
            where_clauses.append("(si.retailer_scanned_at IS NOT NULL OR si.wholesaler_scanned_at IS NOT NULL)")

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        if any(w in q_text for w in ["highest scan", "scan volume", "top scan", "most scanned", "scan count", "box scans"]):
            return (
                f"SELECT si.sku_code, MAX(si.sku_description) AS sku_description, COUNT(si.id) AS scan_volume "
                f"FROM sku_inventories si {where_str} "
                f"GROUP BY si.sku_code "
                f"ORDER BY scan_volume DESC LIMIT {limit};"
            )

        if is_count:
            return f"SELECT COUNT(*) AS total_inventory_items FROM sku_inventories si {where_str};"

        return (
            f"SELECT si.id, si.sku_code, si.sku_description, si.uom, si.mrp, "
            f"si.invoice_number, si.distributer_id, si.status_retailer_id, "
            f"si.status_wholeseller_id, si.retailer_scanned_at, si.wholesaler_scanned_at, "
            f"si.created_at "
            f"FROM sku_inventories si {where_str} ORDER BY si.id DESC LIMIT {limit};"
        )

    # === CASE: Companies ===
    if has_companies:
        where_clauses = []
        if injected_time_filter:
            c_time = injected_time_filter.replace("wt.created_at", "c.created_at")
            where_clauses.append(c_time)
        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        if is_count:
            return f"SELECT COUNT(*) AS total_companies FROM companies c {where_str};"

        return (
            f"SELECT c.id, c.name, c.phone, c.email, c.sap_code, c.business_unit, "
            f"c.jgh_company, c.created_at "
            f"FROM companies c {where_str} ORDER BY c.id ASC LIMIT {limit};"
        )

    # === CASE: Mechanic Details ===
    if has_mechanic:
        where_clauses = []
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        elif "mechanic" in q_text:
            where_clauses.append("u.user_role = 3")
        if region_clause:
            where_clauses.append(region_clause)
        if injected_time_filter:
            md_time = injected_time_filter.replace("wt.created_at", "u.created_at")
            where_clauses.append(md_time)

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        return (
            f"SELECT u.id AS user_id, u.name, u.mobile_number, u.city, u.district, "
            f"md.garage_id, md.shop_name, md.owner_name, md.region, md.distributor_code, "
            f"u.status, u.created_at "
            f"FROM users u JOIN mechanic_details md ON u.id = md.mechanic_id "
            f"{where_str} ORDER BY u.id ASC LIMIT {limit};"
        )

    # === CASE: Automatic Transactions ===
    if has_automatic_tx:
        where_clauses = []
        if injected_time_filter:
            at_time = injected_time_filter.replace("wt.created_at", "at.created_at")
            where_clauses.append(at_time)
        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        return (
            f"SELECT at.id, at.user_id, u.name, at.amount, at.transfer_type, "
            f"at.status, at.bank_reference_number, at.created_at "
            f"FROM automatic_transactions at "
            f"JOIN users u ON at.user_id = u.id "
            f"{where_str} ORDER BY at.created_at DESC LIMIT {limit};"
        )

    # === CASE: Earnings Query ===
    id_alias = "user_id"
    if role_id == 2:
        id_alias = "retailer_id"
    elif role_id == 4:
        id_alias = "distributor_id"
    elif role_id == 5:
        id_alias = "wholesaler_id"

    if is_total_earnings and not role_id and not region_clause and not injected_time_filter:
        return "SELECT COUNT(DISTINCT wt.user_id) AS total_earning_users, SUM(wt.amount) AS total_earnings FROM wallet_transaction wt WHERE wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning');"

    if is_user_earnings or is_total_earnings:
        where_clauses = ["wt.reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning')"]
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        if region_clause:
            where_clauses.append(region_clause)
        if status_sql:
            where_clauses.append(status_sql.replace("users.", "u."))
        if injected_time_filter:
            where_clauses.append(injected_time_filter)

        where_str = f"WHERE {' AND '.join(where_clauses)}"
        return f"SELECT u.id AS {id_alias}, u.name, u.mobile_number, u.city, u.district, u.status, SUM(wt.amount) AS total_earnings FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id {where_str} GROUP BY u.id, u.name, u.mobile_number, u.city, u.district, u.status ORDER BY total_earnings DESC LIMIT {limit};"

    # === CASE: Wallet Balance ===
    if is_balance:
        where_clauses = []
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        if region_clause:
            where_clauses.append(region_clause)
        if status_sql:
            where_clauses.append(status_sql.replace("users.", "u."))
        if injected_time_filter:
            where_clauses.append(injected_time_filter)
        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return f"SELECT u.id AS {id_alias}, u.name, u.mobile_number, SUM(wt.amount) AS total_balance FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id {where_str} GROUP BY u.id, u.name, u.mobile_number ORDER BY total_balance DESC LIMIT {limit};"

    # === CASE: Wallet Transactions listing ===
    if "wallet_transaction" in tables and not role_id and not is_user_earnings:
        where_clauses = []
        if injected_time_filter:
            where_clauses.append(injected_time_filter)
        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return (
            f"SELECT wt.id, u.id AS {id_alias}, u.name, wt.amount, wt.reference_type, "
            f"wt.transaction_type, wt.status, wt.remark, wt.created_at "
            f"FROM wallet_transaction wt JOIN users u ON u.id = wt.user_id "
            f"{where_str} ORDER BY wt.created_at DESC LIMIT {limit};"
        )

    # === CASE: Count Query ===
    if is_count:
        where_clauses = []
        if role_id:
            where_clauses.append(f"u.user_role = {role_id}")
        if region_clause:
            where_clauses.append(region_clause)
        if status_sql:
            where_clauses.append(status_sql.replace("users.", "u."))
        if injected_time_filter:
            u_time = injected_time_filter.replace("wt.created_at", "u.created_at")
            where_clauses.append(u_time)
        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return f"SELECT COUNT(*) AS total_count FROM users u {where_str};"

    # === CASE: User Listing (Distributors / Retailers / Wholesalers by Region / Status / Date) ===
    where_clauses = []
    if role_id:
        where_clauses.append(f"u.user_role = {role_id}")
    if region_clause:
        where_clauses.append(region_clause)
    if status_sql:
        where_clauses.append(status_sql.replace("users.", "u."))
    if injected_time_filter:
        u_time = injected_time_filter.replace("wt.created_at", "u.created_at").replace("si.retailer_scanned_at", "u.created_at")
        where_clauses.append(u_time)

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    return f"SELECT u.id AS {id_alias}, u.name, u.mobile_number, u.email, u.user_role, u.city, u.district, u.address, u.wallet_balance, u.status, u.created_at FROM users u {where_str} ORDER BY u.id ASC LIMIT {limit};"


def generate_sql(prompt: str, model_name: str = None, temperature: float = 0.0, plan: Dict[str, Any] = None) -> str:
    """
    Generate SQL using structured execution plan (preferred) or selective LLM (Qwen).
    Priority:
      1. If structured plan is provided and confidence is high, use _synthesize_sql_from_plan()
      2. If plan is complex/ambiguous (confidence < 85) or unhandled, call Qwen with selective prompt
      3. If Qwen unavailable, fall back safely
    """
    # Auto-create structured plan from prompt if not explicitly passed
    if plan is None and prompt and not prompt.startswith("You are an expert") and not prompt.startswith("User asked:"):
        try:
            from app.agent.query_planner import create_plan
            plan = create_plan(prompt)
        except Exception:
            plan = None

    # 1. Structured plan-based generation (for high confidence standard patterns)
    if plan:
        plan_sql = _synthesize_sql_from_plan(plan)
        if plan_sql and plan_sql.strip().upper().startswith("SELECT"):
            return plan_sql

    # 2. Try LLM (Qwen) if available
    if is_ollama_online():
        model = model_name or DEFAULT_MODEL
        options = {
            "temperature": 0.0,
            "top_p": 0.9,
            "num_predict": 300,
            "stop": ["```", "Explanation:"]
        }
        try:
            client = ollama.Client(host=OLLAMA_HOST)
            response = client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert MySQL Data Analyst. Write only valid MySQL SELECT queries. Output the SQL query inside ```sql code blocks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options=options,
                keep_alive="60m"
            )
            content = response.get("message", {}).get("content", "").strip()
            content = re.sub(r"^```(?:sql)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content).strip()
            if content and ";" in content:
                return content.split(";")[0].strip() + ";"
            if content:
                return content
        except Exception as e:
            print(f"[LLM WARNING] Ollama call failed: {e}")

    # 3. Fallback to plan synthesis if LLM unavailable
    if plan:
        # Temporarily bypass confidence threshold as fallback
        relaxed_plan = plan.copy()
        relaxed_plan["confidence_score"] = 100
        fallback_sql = _synthesize_sql_from_plan(relaxed_plan)
        if fallback_sql and fallback_sql.strip().upper().startswith("SELECT"):
            return fallback_sql

    return ""