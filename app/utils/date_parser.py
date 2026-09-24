"""
Natural Language Date & Temporal Expression Parser for JGH Intelligence Engine.
Extracts:
  - Exact Month Variations: Jan/January, Feb/February, Mar/March, Apr/April, May, Jun/June,
    Jul/July, Aug/August, Sep/Sept/September, Oct/October, Nov/November, Dec/December.
  - Year Specifications: '2026', '2025', 'FY 2026', 'FY26', or inferred from context.
  - Quarters: 'Q1', 'Q2', 'Q3', 'Q4', 'Q1 2026', 'last quarter', 'this quarter'.
  - Relative Periods: 'last month', 'this month', 'previous month', 'next month', 'year to date', 'today', 'yesterday'.
  - Comparison Periods: 'compare with June', 'vs July', 'compared to last month'.
  - Date Ranges: 'between Jan 2026 and March 2026', 'from July to August'.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

MONTH_NAME_TO_NUM = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

MONTH_NUM_TO_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

DEFAULT_YEAR = 2026

def get_month_bounds(month: int, year: int) -> Tuple[str, str]:
    """Returns SQL timestamp bounds ('YYYY-MM-01 00:00:00', 'YYYY-MM-01 00:00:00') for a month."""
    start_date = f"{year:04d}-{month:02d}-01 00:00:00"
    if month == 12:
        end_date = f"{year + 1:04d}-01-01 00:00:00"
    else:
        end_date = f"{year:04d}-{month + 1:02d}-01 00:00:00"
    return start_date, end_date

def get_quarter_bounds(quarter: int, year: int) -> Tuple[str, str]:
    """Returns SQL timestamp bounds for a quarter."""
    q_starts = {1: (1, 4), 2: (4, 7), 3: (7, 10), 4: (10, 1)}
    start_m, end_m = q_starts[quarter]
    start_date = f"{year:04d}-{start_m:02d}-01 00:00:00"
    end_year = year + 1 if quarter == 4 else year
    end_date = f"{end_year:04d}-{end_m:02d}-01 00:00:00"
    return start_date, end_date

def parse_temporal_expressions(
    text: str,
    table_prefix: str = "wt",
    date_column: Optional[str] = None,
    inherited_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Parses any natural language date/time expression from text into structured metadata.
    """
    p_lower = text.lower().strip()
    if date_column:
        col = date_column
    elif table_prefix == "si":
        col = "si.retailer_scanned_at"
    elif table_prefix == "u":
        col = "u.created_at"
    else:
        col = f"{table_prefix}.created_at" if table_prefix else "created_at"

    effective_year = inherited_year or DEFAULT_YEAR

    # 1. Check for Year in text (e.g. 2024, 2025, 2026, FY 2026, FY26)
    year_match = re.search(r"\b(?:20|fy\s*|fy)?(20\d{2})\b", p_lower)
    if year_match:
        effective_year = int(year_match.group(1))
    else:
        fy_short = re.search(r"\bfy\s*(\d{2})\b", p_lower)
        if fy_short:
            effective_year = 2000 + int(fy_short.group(1))

    # 2. Check for Comparison Period: "compare with June", "vs July", "compared to June 2026"
    comparison_info = None
    comp_match = re.search(
        r"\b(?:compare(?:\s+with|\s+to)?|vs\.?|versus)\s+(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)(?:\s+(20\d{2}))?\b",
        p_lower
    )
    if comp_match:
        comp_m_str, comp_y_str = comp_match.groups()
        comp_m = MONTH_NAME_TO_NUM.get(comp_m_str.lower(), 1)
        comp_y = int(comp_y_str) if comp_y_str else effective_year
        comp_start, comp_end = get_month_bounds(comp_m, comp_y)
        comparison_info = {
            "has_comparison": True,
            "compare_month_name": MONTH_NUM_TO_NAME[comp_m],
            "compare_month": comp_m,
            "compare_year": comp_y,
            "compare_label": f"{MONTH_NUM_TO_NAME[comp_m]} {comp_y}",
            "compare_condition": f"{col} >= '{comp_start}' AND {col} < '{comp_end}'",
            "compare_start": comp_start,
            "compare_end": comp_end
        }

    # 3. Explicit Month Range: "between Jan and March", "from July 2026 to August 2026"
    range_match = re.search(
        r"\b(?:between|from)\s+(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)(?:\s+(20\d{2}))?\s+(?:and|to)\s+(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)(?:\s+(20\d{2}))?\b",
        p_lower
    )
    if range_match:
        m1_str, y1_str, m2_str, y2_str = range_match.groups()
        m1 = MONTH_NAME_TO_NUM.get(m1_str.lower(), 1)
        m2 = MONTH_NAME_TO_NUM.get(m2_str.lower(), 12)
        y2 = int(y2_str) if y2_str else effective_year
        y1 = int(y1_str) if y1_str else y2

        start_date, _ = get_month_bounds(m1, y1)
        _, end_date = get_month_bounds(m2, y2)
        condition = f"{col} >= '{start_date}' AND {col} < '{end_date}'"
        return {
            "has_time_filter": True,
            "period_type": "month_range",
            "label": f"{MONTH_NUM_TO_NAME[m1]} {y1} to {MONTH_NUM_TO_NAME[m2]} {y2}",
            "month": m1,
            "end_month": m2,
            "year": y1,
            "condition": condition,
            "start_date": start_date,
            "end_date": end_date,
            "comparison": comparison_info
        }

    # 4. Quarter match: "Q1 2026", "Q2", "last quarter", "this quarter"
    quarter_match = re.search(r"\bq([1-4])(?:\s+(20\d{2}))?\b", p_lower)
    if quarter_match:
        q_num = int(quarter_match.group(1))
        q_year = int(quarter_match.group(2)) if quarter_match.group(2) else effective_year
        start_date, end_date = get_quarter_bounds(q_num, q_year)
        condition = f"{col} >= '{start_date}' AND {col} < '{end_date}'"
        return {
            "has_time_filter": True,
            "period_type": "quarter",
            "quarter": q_num,
            "year": q_year,
            "label": f"Q{q_num} {q_year}",
            "condition": condition,
            "start_date": start_date,
            "end_date": end_date,
            "comparison": comparison_info
        }

    # 5. Standalone or Year-bound Month: "August", "Aug", "July 2026", "distributor data for Aug"
    month_regex = r"\b(january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|sept|october|oct|november|nov|december|dec)\b(?:\s+(20\d{2}))?"
    # Find all matches, skipping comparison target
    matches = list(re.finditer(month_regex, p_lower))
    if matches:
        target_match = matches[0]
        # If the first match was part of 'compare with X', take the second if available
        if comp_match and target_match.start() == comp_match.start(1):
            target_match = matches[1] if len(matches) > 1 else None

        if target_match:
            m_str = target_match.group(1)
            y_str = target_match.group(2)
            m = MONTH_NAME_TO_NUM.get(m_str.lower(), 1)
            y = int(y_str) if y_str else effective_year

            start_date, end_date = get_month_bounds(m, y)
            condition = f"{col} >= '{start_date}' AND {col} < '{end_date}'"
            return {
                "has_time_filter": True,
                "period_type": "month",
                "month_name": MONTH_NUM_TO_NAME[m],
                "month": m,
                "year": y,
                "label": f"{MONTH_NUM_TO_NAME[m]} {y}",
                "condition": condition,
                "start_date": start_date,
                "end_date": end_date,
                "comparison": comparison_info
            }

    # 6. Relative time filters
    if "today" in p_lower:
        condition = f"{col} >= CURDATE() AND {col} < CURDATE() + INTERVAL 1 DAY"
        return {"has_time_filter": True, "period_type": "relative", "label": "Today", "condition": condition, "start_date": "CURDATE()", "end_date": "CURDATE() + 1 DAY", "comparison": comparison_info}

    if "yesterday" in p_lower:
        condition = f"{col} >= CURDATE() - INTERVAL 1 DAY AND {col} < CURDATE()"
        return {"has_time_filter": True, "period_type": "relative", "label": "Yesterday", "condition": condition, "start_date": "CURDATE() - 1 DAY", "end_date": "CURDATE()", "comparison": comparison_info}

    if "last 7 days" in p_lower or "past 7 days" in p_lower:
        condition = f"{col} >= NOW() - INTERVAL 7 DAY"
        return {"has_time_filter": True, "period_type": "relative", "label": "Last 7 Days", "condition": condition, "start_date": "NOW() - 7 DAY", "end_date": "NOW()", "comparison": comparison_info}

    if "last 30 days" in p_lower or "past 30 days" in p_lower:
        condition = f"{col} >= NOW() - INTERVAL 30 DAY"
        return {"has_time_filter": True, "period_type": "relative", "label": "Last 30 Days", "condition": condition, "start_date": "NOW() - 30 DAY", "end_date": "NOW()", "comparison": comparison_info}

    if "this month" in p_lower or "current month" in p_lower:
        now = datetime.now()
        cur_m = now.month
        cur_y = now.year
        start_date, end_date = get_month_bounds(cur_m, cur_y)
        condition = f"{col} >= '{start_date}' AND {col} < '{end_date}'"
        return {"has_time_filter": True, "period_type": "month", "month_name": MONTH_NUM_TO_NAME[cur_m], "month": cur_m, "year": cur_y, "label": f"{MONTH_NUM_TO_NAME[cur_m]} {cur_y}", "condition": condition, "start_date": start_date, "end_date": end_date, "comparison": comparison_info}

    if "last month" in p_lower or "previous month" in p_lower:
        now = datetime.now()
        if now.month == 1:
            prev_m = 12
            prev_y = now.year - 1
        else:
            prev_m = now.month - 1
            prev_y = now.year
        start_date, end_date = get_month_bounds(prev_m, prev_y)
        condition = f"{col} >= '{start_date}' AND {col} < '{end_date}'"
        return {"has_time_filter": True, "period_type": "month", "month_name": MONTH_NUM_TO_NAME[prev_m], "month": prev_m, "year": prev_y, "label": f"{MONTH_NUM_TO_NAME[prev_m]} {prev_y}", "condition": condition, "start_date": start_date, "end_date": end_date, "comparison": comparison_info}

    if "year to date" in p_lower or "ytd" in p_lower:
        condition = f"{col} >= '{effective_year}-01-01 00:00:00' AND {col} < '{effective_year + 1}-01-01 00:00:00'"
        return {"has_time_filter": True, "period_type": "year_to_date", "year": effective_year, "label": f"YTD {effective_year}", "condition": condition, "start_date": f"{effective_year}-01-01 00:00:00", "end_date": f"{effective_year + 1}-01-01 00:00:00", "comparison": comparison_info}

    return {
        "has_time_filter": False,
        "period_type": None,
        "label": None,
        "month": None,
        "year": effective_year if year_match else None,
        "condition": None,
        "start_date": None,
        "end_date": None,
        "comparison": comparison_info
    }
