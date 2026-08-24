"""
Executive Natural Language Summary & Business Insight Generator for JGH Intelligence Engine.

Transforms raw SQL result rows into human-friendly, executive-ready explanations:
  - Plain English dataset summary (no technical jargon)
  - Key business highlights (totals, averages, top contributors)
  - Named partner spotlights (who earned the most or has highest pending request)
  - Actionable business takeaways for non-technical users
"""

import re
from typing import List, Dict, Any, Optional

def _fmt_curr(val: float) -> str:
    """Formats float into Indian rupee currency string."""
    try:
        return f"₹{val:,.2f}".replace(".00", "")
    except Exception:
        return f"₹{val}"

def generate_natural_summary(
    question: str,
    sql_query: str,
    columns: List[str],
    data: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a clear natural language summary and structured business insights
    so non-technical users immediately understand what the data represents.
    """
    ctx = context or {}
    und = ctx.get("understanding_summary")
    period = ctx.get("period")
    region = ctx.get("region")
    entity = ctx.get("entity")

    if not data:
        if und:
            return f"No records found for **{und}**."
        return f"No matching records found for query: *\"{question}\"*."

    row_count = len(data)

    # ── 1. Single-Row Aggregate Queries (e.g. COUNT, SUM, total_withdrawals) ──
    if row_count == 1:
        first_row = data[0]
        keys = list(first_row.keys())

        # Percentage Change / Growth Rate
        if "percentage_change" in keys:
            pct_val = first_row.get("percentage_change")
            p1_key = next((k for k in keys if k != "percentage_change" and ("_payouts" in k or "_earnings" in k or "july" in k or "june" in k)), None)
            p2_key = next((k for k in keys if k != "percentage_change" and k != p1_key and ("_payouts" in k or "_earnings" in k or "august" in k or "july" in k)), None)

            p1_val = float(first_row.get(p1_key) or 0) if p1_key else None
            p2_val = float(first_row.get(p2_key) or 0) if p2_key else None
            p1_name = p1_key.replace('_', ' ').title() if p1_key else "Baseline Period"
            p2_name = p2_key.replace('_', ' ').title() if p2_key else "Comparison Period"

            sign = "+" if (pct_val is not None and float(pct_val) > 0) else ""
            pct_str = f"{sign}{pct_val}%" if pct_val is not None else "0.0%"
            growth_desc = "an increase" if (pct_val is not None and float(pct_val) > 0) else "a decrease" if (pct_val is not None and float(pct_val) < 0) else "no change"

            details = [
                f"• **Percentage Change**: **{pct_str}** ({growth_desc}).",
            ]
            if p1_val is not None:
                details.append(f"• **{p1_name}**: **{_fmt_curr(p1_val)}**")
            if p2_val is not None:
                details.append(f"• **{p2_name}**: **{_fmt_curr(p2_val)}**")
            if p1_val is not None and p2_val is not None:
                details.append(f"• **Net Difference**: **{_fmt_curr(p2_val - p1_val)}**")

            return (
                f"### 📈 Percentage Growth Analysis\n\n"
                + "\n".join(details) + "\n\n"
                f"📌 *Calculated as `(({p2_name} - {p1_name}) / {p1_name}) * 100` based on verified database records.*"
            )

        # Reward Points Aggregation
        if "total_reward_points" in keys:
            pts = float(first_row.get("total_reward_points") or 0)
            scans = first_row.get("total_scanned_boxes", 0)
            avg_pts = (pts / scans) if scans else 0
            return (
                f"### 🎁 Reward Points Summary\n\n"
                f"• **Total Reward Points Distributed**: **{pts:,.0f} points**.\n"
                f"• **Total Verified QR Box Scans**: **{scans:,} boxes**.\n"
                f"• **Average Points per Box**: **{avg_pts:,.1f} points/box**.\n\n"
                f"📌 *Aggregated across dual-scan telemetry records and master SKU point maps for **{und or question}**.*"
            )

        # Withdrawal Aggregation
        if any("withdrawal" in k.lower() for k in keys) and any("amount" in k.lower() for k in keys):
            cnt_key = next((k for k in keys if "count" in k.lower() or "withdrawal" in k.lower()), keys[0])
            amt_key = next((k for k in keys if "amount" in k.lower()), keys[1] if len(keys) > 1 else keys[0])
            cnt = first_row.get(cnt_key, 0)
            amt = float(first_row.get(amt_key) or 0)
            return (
                f"### 📊 Executive Summary\n\n"
                f"• **Total Volume**: **{cnt:,} withdrawal requests** recorded.\n"
                f"• **Total Financial Outflow**: **{_fmt_curr(amt)}**.\n"
                f"• **Average per Request**: **{_fmt_curr(amt / cnt if cnt else 0)}**.\n\n"
                f"📌 *This represents the aggregated withdrawal liability matching your search criteria.*"
            )

        # Earnings Aggregation
        if any(k in keys for k in ["total_earnings", "earnings", "total_revenue"]):
            amt = float(first_row.get("total_earnings") or first_row.get("earnings") or 0)
            users_cnt = first_row.get("total_earning_users") or first_row.get("user_count")
            users_str = f" across **{users_cnt:,} active partners**" if users_cnt else ""
            time_str = f" for **{period}**" if period else ""
            reg_str = f" in **{region}**" if region else ""
            return (
                f"### 📊 Executive Earnings Summary\n\n"
                f"• **Total Combined Earnings**: **{_fmt_curr(amt)}**{users_str}{reg_str}{time_str}.\n\n"
                f"📌 *Calculated from verified wallet transaction ledger credits (excluding redemptions/withdrawals).*"
            )

        # Single Partner Record Lookup
        if any(k in keys for k in ["user_id", "id", "distributor_code"]):
            name = first_row.get("name") or first_row.get("company_name") or f"Partner #{first_row.get('id') or first_row.get('user_id')}"
            role = str(first_row.get("user_role") or "Partner")
            city = first_row.get("city") or first_row.get("district") or "Not Specified"
            status = first_row.get("status", "Active")
            bal = first_row.get("wallet_balance")
            earnings = first_row.get("total_earnings")

            details = [
                f"• **Partner Name**: **{name}**",
                f"• **Location**: {city}",
                f"• **Status**: {status.capitalize() if isinstance(status, str) else status}"
            ]
            if bal is not None:
                details.append(f"• **Wallet Balance**: **{_fmt_curr(float(bal or 0))}**")
            if earnings is not None:
                details.append(f"• **Total Earnings**: **{_fmt_curr(float(earnings or 0))}**")

            return (
                f"### 👤 Partner Profile Overview\n\n"
                + "\n".join(details) + "\n\n"
                f"📌 *Direct record retrieved for **{und or question}**.*"
            )

    # ── 2. Comparison / Aggregation Responses ─────────────
    # If the AI explicitly determined it's a comparison or aggregation
    is_comp = any(kw in question.lower() for kw in ["compare", "vs", "versus", "difference", "growth", "percentage", "change"])
    
    if is_comp and len(data) == 2:
        amt_col = next((c for c in columns if any(kw in c.lower() for kw in ["total_earnings", "earnings", "amount", "payout", "wallet_balance"])), None)
        name_col = next((c for c in columns if c.lower() in ["name", "state_name", "region", "city", "month", "period"]), columns[0] if columns else None)
        
        if amt_col and name_col:
            v1 = float(data[0].get(amt_col) or 0)
            v2 = float(data[1].get(amt_col) or 0)
            n1 = str(data[0].get(name_col, 'Entity 1'))
            n2 = str(data[1].get(name_col, 'Entity 2'))
            
            if v1 >= v2:
                win, lose, w_val, l_val = n1, n2, v1, v2
            else:
                win, lose, w_val, l_val = n2, n1, v2, v1
                
            diff = w_val - l_val
            pct = (diff / l_val * 100) if l_val > 0 else 0
            metric_name = amt_col.replace('_', ' ').title()
            
            return (
                f"### 📊 Comparative Analysis: {win} vs {lose}\n\n"
                f"**{win}** has a higher {metric_name} compared to **{lose}**.\n\n"
                f"• **{win}**: **{_fmt_curr(w_val)}**\n"
                f"• **{lose}**: **{_fmt_curr(l_val)}**\n\n"
                f"💡 **Key Insight**: {win} generated **{_fmt_curr(diff)}** more than {lose}" + (f", which is a **{pct:.1f}%** difference." if pct > 0 else ".")
            )

    if len(data) <= 5 and is_comp:
        return (
            f"### 📊 Comparative Growth Performance\n\n"
            f"Found **{row_count} partner records** comparing performance periods for **{und or 'Period Comparison'}**.\n\n"
            f"• **Scope**: Side-by-side metric comparison across primary and reference periods.\n"
            f"• **Data Grid**: Displays individual partner totals, baseline comparison figures, and net growth deltas.\n"
            f"• **Visualization**: See chart below for visual growth trends across top contributors."
        )

    # ── 3. Multi-Row Table Datasets (Leaderboards, Lists, Queues) ─────────────
    # Detect relevant columns
    name_col = next((c for c in columns if c.lower() in ["name", "company_name", "user_name", "state_name", "region", "city"]), None)
    if not name_col and columns:
        # Fallback to the first column if it's a string/identifier type
        name_col = columns[0]

    amt_col = next((c for c in columns if any(kw in c.lower() for kw in ["total_earnings", "earnings", "amount", "wallet_balance", "balance", "price", "mrp"])), None)
    status_col = next((c for c in columns if c.lower() in ["status", "order_status", "request_status"]), None)
    city_col = next((c for c in columns if c.lower() in ["city", "district", "state", "region", "state_name"]), None)

    # Calculate Totals & Top Contributors
    total_val = 0.0
    has_numeric = False
    top_contributors = []

    if amt_col:
        try:
            valid_rows = [r for r in data if r.get(amt_col) is not None]
            vals = [float(r[amt_col]) for r in valid_rows]
            if vals:
                total_val = sum(vals)
                has_numeric = True
                # Get top 3
                sorted_rows = sorted(valid_rows, key=lambda x: float(x[amt_col]), reverse=True)
                for r in sorted_rows[:3]:
                    fallback_id = r.get('id') or r.get('user_id') or r.get('withdrawal_id')
                    p_name = r.get(name_col) if name_col and r.get(name_col) else (f"Record #{fallback_id}" if fallback_id else "Unknown")
                    p_val = float(r[amt_col])
                    top_contributors.append(f"**{p_name}** ({_fmt_curr(p_val)})")
        except Exception:
            has_numeric = False

    # Build Contextual Narrative
    lines = []
    scope_title = und or question

    # Header
    lines.append(f"### 📋 Business Insights & Data Breakdown")
    lines.append(f"Retrieved **{row_count} matching records** for **{scope_title}**.\n")

    # Financial & Quantitative Summary
    if has_numeric and total_val > 0:
        label = amt_col.replace('_', ' ').title()
        avg_val = total_val / row_count if row_count else 0
        lines.append(f"• **Combined Total {label}**: **{_fmt_curr(total_val)}** (Average: **{_fmt_curr(avg_val)}** per record).")

    # Top Contributors Spotlight
    if top_contributors:
        lines.append(f"• **Top Highlights**: {', '.join(top_contributors)}.")

    # Location / Status Context
    if status_col:
        statuses = set(str(r[status_col]) for r in data if r.get(status_col) is not None)
        if len(statuses) == 1:
            st = list(statuses)[0]
            st_label = "Pending Review" if st == "0" else "Approved" if st == "1" else "Rejected" if st == "2" else st
            lines.append(f"• **Status Filter**: All records are in **{st_label}** status.")

    if city_col:
        cities = list(filter(None, [r.get(city_col) for r in data]))
        if cities:
            unique_cities = list(dict.fromkeys(cities))[:3]
            lines.append(f"• **Key Regions Represented**: {', '.join(unique_cities)}{' and more' if len(unique_cities) < len(set(cities)) else ''}.")

    # Practical Takeaway for non-technical users
    if "withdrawal" in question.lower() or "payout" in question.lower():
        lines.append("\n💡 **Business Context**: *Review individual bank withdrawal requests in the table below before executing treasury batch payments.*")
    elif "distributor" in question.lower() or "retailer" in question.lower():
        lines.append("\n💡 **Business Context**: *Leaderboard sorted by primary performance metric. You can download the complete report as Excel, CSV, or PDF using the export buttons.*")

    return "\n".join(lines)
