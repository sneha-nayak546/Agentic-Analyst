import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from app.retriever.retriever import retrieve_sql_history, retrieve_schema
from app.knowledge.table_schemas import get_selective_schema_context
from app.knowledge.business_rule_index import get_selective_business_rules

def resolve_runtime_dates(question: str) -> Dict[str, Any]:
    """
    Computes runtime timestamp boundaries for temporal expressions in business questions.
    Defaults to 2026 enterprise reference timeline.
    Supports single months, relative periods (today, this month, last month),
    and multi-period comparison queries (e.g. June and July, previous month and current month).
    """
    q_lower = question.lower()
    now = datetime.now()
    year_match = re.search(r"\b(202[0-9])\b", q_lower)
    if year_match:
        year = int(year_match.group(1))
    else:
        year = now.year if now.year >= 2026 else 2026

    # 1. Multi-Period Comparisons: "previous month and current month" / "last month and this month"
    if ("previous month" in q_lower or "last month" in q_lower) and ("current month" in q_lower or "this month" in q_lower):
        month = now.month
        prev_m = month - 1 if month > 1 else 12
        prev_y = year if month > 1 else year - 1
        st = f"{prev_y:04d}-{prev_m:02d}-01 00:00:00"
        next_m = month + 1 if month < 12 else 1
        next_y = year if month < 12 else year + 1
        en = f"{next_y:04d}-{next_m:02d}-01 00:00:00"
        return {
            "start": st,
            "end": en,
            "period": "Previous Month and Current Month",
            "is_comparison": True,
            "period1": (st, f"{year:04d}-{month:02d}-01 00:00:00", "Previous Month"),
            "period2": (f"{year:04d}-{month:02d}-01 00:00:00", en, "Current Month"),
            "explicit": True
        }

    # 2. Multi-Period Comparisons: "june and july", "july and august", etc.
    month_indices = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }
    found_months = [m for m in month_indices if m in q_lower]
    if len(found_months) >= 2 and any(w in q_lower for w in ["compare", "between", "and", "vs"]):
        m1, m2 = found_months[0], found_months[1]
        i1, i2 = month_indices[m1], month_indices[m2]
        if i1 > i2:
            m1, m2 = m2, m1
            i1, i2 = i2, i1
        st = f"{year:04d}-{i1:02d}-01 00:00:00"
        next_i2 = i2 + 1 if i2 < 12 else 1
        next_y2 = year if i2 < 12 else year + 1
        en = f"{next_y2:04d}-{next_i2:02d}-01 00:00:00"
        return {
            "start": st,
            "end": en,
            "period": f"{m1.capitalize()} and {m2.capitalize()} {year}",
            "is_comparison": True,
            "period1": (f"{year:04d}-{i1:02d}-01 00:00:00", f"{year:04d}-{i1+1:02d}-01 00:00:00" if i1 < 12 else f"{year+1:04d}-01-01 00:00:00", f"{m1.capitalize()} {year}"),
            "period2": (f"{year:04d}-{i2:02d}-01 00:00:00", en, f"{m2.capitalize()} {year}"),
            "explicit": True
        }

    # 3. Specific Individual Month
    for m_name, m_idx in month_indices.items():
        if m_name in q_lower:
            st = f"{year:04d}-{m_idx:02d}-01 00:00:00"
            next_m = m_idx + 1 if m_idx < 12 else 1
            next_y = year if m_idx < 12 else year + 1
            en = f"{next_y:04d}-{next_m:02d}-01 00:00:00"
            return {"start": st, "end": en, "period": f"{m_name.capitalize()} {year}", "explicit": True}

    # 4. Relative "this month" / "current month"
    if "this month" in q_lower or "current month" in q_lower:
        month = now.month
        st = f"{year:04d}-{month:02d}-01 00:00:00"
        next_m = month + 1 if month < 12 else 1
        next_y = year if month < 12 else year + 1
        en = f"{next_y:04d}-{next_m:02d}-01 00:00:00"
        return {"start": st, "end": en, "period": "this month", "explicit": True}

    # 5. Relative "last month" / "previous month"
    if "last month" in q_lower or "previous month" in q_lower:
        month = now.month
        prev_m = month - 1 if month > 1 else 12
        prev_y = year if month > 1 else year - 1
        st = f"{prev_y:04d}-{prev_m:02d}-01 00:00:00"
        en = f"{year:04d}-{month:02d}-01 00:00:00"
        return {"start": st, "end": en, "period": "last month", "explicit": True}

    # 6. Relative "today"
    if "today" in q_lower:
        today_str = now.strftime("%Y-%m-%d")
        import datetime as dt_module
        tomorrow = now + dt_module.timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        return {"start": f"{today_str} 00:00:00", "end": f"{tomorrow_str} 00:00:00", "period": "today", "explicit": True}

    return {"start": None, "end": None, "period": None, "explicit": False}



def build_sql_prompt(
    target: Union[str, Any],
    context: Optional[Dict[str, Any]] = None,
    schema_context: Optional[str] = None,
    examples: Optional[str] = None
) -> str:
    """
    SQLAI.ai-Style Database-Aware Prompt Builder.
    Supplies:
      1. Original User Question
      2. MySQL Dialect Instructions
      3. Relevant Physical Schema & Foreign Keys (Dynamically Retrieved via RAG)
      4. Core Business Semantics & Rules
      5. Runtime Date References
      6. Relevant Query Examples
    """
    ctx = context or {}
    
    # Handle backward compatibility: target could be ExecutionPlan or raw question string
    if hasattr(target, "business_requirement"):
        original_question = target.business_requirement.original_question
        tables = getattr(target, "relevant_tables", [])
    elif isinstance(target, str):
        original_question = target
        tables = []
    else:
        original_question = str(target)
        tables = []

    # 1. Physical Schema Context via Database Knowledge / Schema RAG
    if not schema_context:
        if tables:
            schema_context = get_selective_schema_context(tables)
        else:
            schema_context = retrieve_schema(original_question)

    # 2. Date Boundaries
    date_info = resolve_runtime_dates(original_question)
    date_section = ""
    if date_info["explicit"] and date_info["start"] and date_info["end"]:
        if date_info.get("is_comparison"):
            p1 = date_info["period1"]
            p2 = date_info["period2"]
            date_section = (
                f"TEMPORAL RUNTIME BOUNDARIES for '{date_info['period']}':\n"
                f"- Period 1 ({p1[2]}): timestamp >= '{p1[0]}' AND timestamp < '{p1[1]}'\n"
                f"- Period 2 ({p2[2]}): timestamp >= '{p2[0]}' AND timestamp < '{p2[1]}'\n"
                f"- Combined Filter: timestamp >= '{date_info['start']}' AND timestamp < '{date_info['end']}'\n"
                f"- MULTI-PERIOD COMPARISON GUIDANCE:\n"
                f"    Use CASE to label periods: CASE WHEN timestamp >= '{p1[0]}' AND timestamp < '{p1[1]}' THEN '{p1[2]}' ELSE '{p2[2]}' END AS period_name\n"
                f"    Use 'GROUP BY period_name' (or 'GROUP BY 1') to group by the labeled period cleanly.\n"

            )
        else:
            date_section = (
                f"TEMPORAL RUNTIME BOUNDARIES for '{date_info['period']}':\n"
                f"- Start Timestamp: '{date_info['start']}'\n"
                f"- End Timestamp: '{date_info['end']}'\n"
                f"- MANDATORY SQL FILTER: timestamp_col >= '{date_info['start']}' AND timestamp_col < '{date_info['end']}'\n"
            )

    # 3. Relevant Few-Shot Exemplars (Strictly from verified training split)
    if not examples:
        try:
            from app.training.dynamic_exemplar_retriever import get_dynamic_few_shot_examples
            examples = get_dynamic_few_shot_examples(original_question, k=2)
        except Exception:
            examples = retrieve_sql_history(original_question, k=2)

    # 4. Core Authoritative Business Rules
    business_rules = (
        "CORE JGH BUSINESS SEMANTICS & AUTHORITATIVE RULES:\n"
        "1. JGH BOX QUANTITY / SCANNING:\n"
        "   - The authoritative box quantity calculation is: SUM(qpm.box_calculation_uom) joined on `sku_inventories.sku_code = qpm.sku_code` (table `sku_qr_points_maps` qpm, also known as `qr_point_map`).\n"
        "   - CRITICAL RULE: NEVER use `COUNT(sku_inventories.id)` or `COUNT(si.id)` as the box quantity! COUNT(si.id) counts database records, NOT actual boxes.\n"
        "   - Temporal filtering: ALWAYS filter scanning date/time using `si.retailer_scanned_at` (half-open interval: >= start AND < next_period_start). NEVER use `users.created_at`.\n"
        "2. RETAILER SCANNING:\n"
        "   - Retailer scan owner: `si.status_retailer_id = users.id` (where `users.user_role = 2`).\n"
        "   - Join: `FROM sku_inventories si JOIN sku_qr_points_maps qpm ON si.sku_code = qpm.sku_code JOIN users u ON si.status_retailer_id = u.id WHERE u.user_role = 2`.\n"
        "   - Metric: `SUM(qpm.box_calculation_uom) AS box_scan_count` (or `total_boxes_scanned`).\n"
        "3. DISTRIBUTOR SCANNING:\n"
        "   - Distributor relationship: `si.distributer_id = u.id` (where `users.user_role = 4`).\n"
        "   - Join: `FROM sku_inventories si JOIN sku_qr_points_maps qpm ON si.sku_code = qpm.sku_code JOIN users u ON si.distributer_id = u.id WHERE u.user_role = 4`.\n"
        "   - Metric: `SUM(qpm.box_calculation_uom) AS box_scan_count`.\n"
        "4. RETAILER UNDER DISTRIBUTOR SCANNING:\n"
        "   - Join both: `users retailer ON si.status_retailer_id = retailer.id` (role 2) AND `users distributor ON si.distributer_id = distributor.id` (role 4).\n"
        "   - Select `retailer.id AS retailer_id, retailer.name AS retailer_name, distributor.id AS distributor_id, distributor.name AS distributor_name, SUM(qpm.box_calculation_uom) AS box_scan_count`.\n"
        "   - Group by retailer and distributor.\n"
        "5. STATE SCANNING & HUMAN-READABLE LOCATION NAMES:\n"
        "   - Join `u.state_id = s.id` with `state s` (or `states s`).\n"
        "   - Select `s.sname AS state_name` (or `s.name AS state_name`) and `SUM(qpm.box_calculation_uom) AS box_scan_count`.\n"
        "   - NEVER expose raw `state_id` alone in reports; always resolve and project `state_name`.\n"
        "6. JGH EARNINGS & WALLET TRANSACTIONS:\n"
        "   - Always query `wallet_transaction wt`.\n"
        "   - Valid earning types: `wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')`.\n"
        "   - Positive amount condition: `wt.amount > 0`.\n"
        "   - Metric: `SUM(wt.amount) AS total_earnings`.\n"
        "   - Timestamp: `wt.created_at` (half-open interval: >= start AND < next_period_start).\n"
        "   - Retailer earnings: `users u JOIN wallet_transaction wt ON u.id = wt.user_id WHERE u.user_role = 2 AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND wt.amount > 0`.\n"
        "   - Distributor earnings: `users u JOIN wallet_transaction wt ON u.id = wt.user_id WHERE u.user_role = 4 AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND wt.amount > 0`.\n"
        "   - PROHIBITION: Do NOT use `wallet_balance` or unfiltered `wt.amount` as earnings.\n"
        "7. USER ROLES: `user_role = 2` (Retailer), `user_role = 4` (Distributor), `user_role = 5` (Wholesaler), `user_role = 6` (Mechanic).\n"
        "8. RANKINGS & LIMITS:\n"
        "   - 'Highest' / 'top' / 'most' -> ORDER BY metric DESC.\n"
        "   - 'Lowest' / 'bottom' / 'least' -> ORDER BY metric ASC.\n"
        "   - 'Top N' -> LIMIT N; 'Highest single' / 'Which retailer' / 'Which distributor' / 'Which state' -> LIMIT 1.\n"
        "9. MULTI-PERIOD COMPARISONS:\n"
        "   - Labeled CASE expression: `CASE WHEN ... THEN 'Period 1' ELSE 'Period 2' END AS period_name` and `GROUP BY period_name`.\n"
        "10. EXACT GROUNDING: Generate ONE authoritative query. No synthetic values or unjoined columns.\n"
        "11. MULTI-METRIC QUERIES (BOX SCANS + EARNINGS):\n"
        "   - When a question asks for BOTH scanning quantity (e.g. total boxes scanned) AND financial earnings (e.g. total earnings) for retailers:\n"
        "     Use CTEs to pre-aggregate scanning records and wallet earnings separately before joining to prevent Cartesian row multiplication:\n"
        "     WITH retailer_scans AS (\n"
        "         SELECT r.id AS retailer_id, r.name AS retailer_name, d.name AS distributor_name, s.sname AS state_name, SUM(qpm.box_calculation_uom) AS total_boxes_scanned\n"
        "         FROM sku_inventories si JOIN sku_qr_points_maps qpm ON si.sku_code = qpm.sku_code JOIN users r ON si.status_retailer_id = r.id JOIN users d ON si.distributer_id = d.id JOIN state s ON r.state_id = s.id\n"
        "         WHERE r.user_role = 2 AND d.user_role = 4 AND si.retailer_scanned_at >= '2026-07-01 00:00:00' AND si.retailer_scanned_at < '2026-08-01 00:00:00'\n"
        "         GROUP BY r.id, r.name, d.name, s.sname\n"
        "     ),\n"
        "     retailer_earnings AS (\n"
        "         SELECT u.id AS retailer_id, SUM(wt.amount) AS total_earnings\n"
        "         FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id\n"
        "         WHERE u.user_role = 2 AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND wt.amount > 0 AND wt.created_at >= '2026-07-01 00:00:00' AND wt.created_at < '2026-08-01 00:00:00'\n"
        "         GROUP BY u.id\n"
        "     )\n"
        "     SELECT rs.retailer_name, rs.distributor_name, rs.state_name, rs.total_boxes_scanned, COALESCE(re.total_earnings, 0) AS total_earnings\n"
        "     FROM retailer_scans rs LEFT JOIN retailer_earnings re ON rs.retailer_id = re.retailer_id\n"
        "     ORDER BY rs.total_boxes_scanned DESC LIMIT 5;\n"
        "12. SIMPLE LOOKUP QUERIES BY ID OR NAME:\n"
        "   - If the user asks for details of a user, retailer, or distributor by ID or name (e.g. 'Give details for retailer ID 50225' or 'Lookup distributor 6016'):\n"
        "     DO NOT use CTEs. DO NOT join sku_inventories or wallet_transaction. Simply query the `users` table directly (optionally joined with `state` for state_name):\n"
        "     Example: SELECT u.*, s.sname AS state_name FROM users u LEFT JOIN state s ON u.state_id = s.id WHERE u.id = 50225 AND u.user_role = 2;\n"
        "13. CRITICAL TABLE GROUNDING:\n"
        "   - There is NO separate 'distributors' or 'retailers' table! Both retailers and distributors are in the `users` table (user_role = 2 for retailer, user_role = 4 for distributor).\n"
        "14. TEMPORAL FILTERING STRICTNESS:\n"
        "   - ONLY filter date or time columns if the user question explicitly specifies a timeframe, month, or year (e.g. 'July 2026', 'last month').\n"
        "   - If the question contains NO date or timeframe (e.g. 'What is the average transaction amount for distributor 6016?'), DO NOT ADD ANY DATE FILTERS. Query across all time.\n"
        "15. TRANSACTION AMOUNT VS EARNINGS:\n"
        "   - If a question asks for 'transaction amount', 'average transaction amount', or 'all transactions' (not 'earnings'): query `amount` from `wallet_transaction` directly (e.g. `SELECT AVG(amount) FROM wallet_transaction WHERE user_id = ...`) without restricting `reference_type`.\n"
    )

    prompt = (
        "You are an expert MySQL Data Analyst for JGH Enterprise. Write a single, highly accurate MySQL SELECT query based on the user's business question.\n\n"
        "============================================================\n"
        "DATABASE SCHEMA & RELATIONSHIPS:\n"
        "============================================================\n"
        f"{schema_context}\n\n"
        "============================================================\n"
        f"{business_rules}\n\n"
    )

    if date_section:
        prompt += (
            "============================================================\n"
            f"{date_section}\n"
        )

    if examples:
        prompt += (
            "============================================================\n"
            "RELEVANT QUERY EXAMPLES (REFERENCE):\n"
            "============================================================\n"
            f"{examples}\n\n"
        )

    prompt += (
        "============================================================\n"
        "USER QUESTION:\n"
        "============================================================\n"
        f"\"{original_question}\"\n\n"
        "INSTRUCTIONS:\n"
        "- RETURN SQL ONLY. Do not output explanations, reasoning, analysis, comments, or markdown code fences (no ```sql).\n"
        "- The output must be a single executable MySQL SELECT or WITH query starting immediately with SELECT or WITH.\n"
        "- Strictly use real tables and real columns from the schema provided.\n"
        "- Qualify all columns (e.g. `u.id`, `si.id`, `wt.amount`).\n"
        "- Ensure ALL requested fields (e.g. retailer name, distributor name, state name, total boxes scanned, total earnings) are explicitly projected in the outer SELECT. Never silently omit any requested field.\n"
        "- When combining multiple aggregates (e.g. box scans + earnings), use CTEs to avoid Cartesian row multiplication.\n"
    )

    return prompt