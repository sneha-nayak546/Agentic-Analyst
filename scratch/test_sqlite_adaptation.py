import re

def adapt_sql_for_sqlite_test(sql: str) -> str:
    s = sql
    # 1. Compound DATE_FORMAT(DATE_ADD/SUB(CURRENT_DATE...))
    s = re.sub(
        r"(?i)DATE_FORMAT\s*\(\s*DATE_ADD\s*\(\s*CURRENT_DATE(?:\(\))?\s*,\s*INTERVAL\s*['\"]?(\d+)['\"]?\s*MONTH\s*\)\s*,\s*['\"][^'\"]*['\"]\s*\)",
        r"date('now', 'start of month', '+\1 month')",
        s
    )
    s = re.sub(
        r"(?i)DATE_FORMAT\s*\(\s*DATE_SUB\s*\(\s*CURRENT_DATE(?:\(\))?\s*,\s*INTERVAL\s*['\"]?(\d+)['\"]?\s*MONTH\s*\)\s*,\s*['\"][^'\"]*['\"]\s*\)",
        r"date('now', 'start of month', '-\1 month')",
        s
    )
    s = re.sub(
        r"(?i)DATE_ADD\s*\(\s*DATE_FORMAT\s*\(\s*CURRENT_DATE(?:\(\))?\s*,\s*['\"][^'\"]*['\"]\s*\)\s*,\s*INTERVAL\s*['\"]?(\d+)['\"]?\s*MONTH\s*\)",
        r"date('now', 'start of month', '+\1 month')",
        s
    )
    s = re.sub(
        r"(?i)DATE_FORMAT\s*\(\s*CURRENT_DATE(?:\(\))?\s*,\s*['\"][^'\"]*['\"]\s*\)",
        "date('now', 'start of month')",
        s
    )
    s = re.sub(r"(?i)CURRENT_DATE\(\)", "date('now')", s)
    s = re.sub(r"(?i)\bCURRENT_DATE\b", "date('now')", s)
    s = re.sub(r"(?i)NOW\(\)", "datetime('now')", s)
    s = re.sub(r"(?i)DATE_ADD\(\s*date\([^)]+\)\s*,\s*INTERVAL\s*['\"]?(\d+)['\"]?\s*MONTH\s*\)", r"date('now', '+\1 month')", s)
    s = re.sub(r"(?i)DATE_ADD\(([^,]+),\s*INTERVAL\s*['\"]?(\d+)['\"]?\s*MONTH\)", r"date(\1, '+\2 month')", s)
    s = re.sub(r"(?i)DATE_FORMAT\(([^,]+),\s*['\"]%Y-%m['\"]\)", r"strftime('%Y-%m', \1)", s)
    s = re.sub(r"(?i)DATE_FORMAT\(([^,]+),\s*['\"]%Y-%m-%d['\"]\)", r"strftime('%Y-%m-%d', \1)", s)
    s = re.sub(r"(?i)DATE_FORMAT\(([^,]+),\s*['\"]%Y['\"]\)", r"strftime('%Y', \1)", s)
    s = re.sub(r"(?i)DATE_FORMAT\(([^,]+),\s*['\"]%m['\"]\)", r"strftime('%m', \1)", s)
    s = re.sub(r"(?i)MONTH\(([^)]+)\)", r"CAST(strftime('%m', \1) AS INTEGER)", s)
    s = re.sub(r"(?i)YEAR\(([^)]+)\)", r"CAST(strftime('%Y', \1) AS INTEGER)", s)
    return s

test_sql = "SELECT u.id AS user_id, u.name, COUNT(si.id) AS box_scan_count FROM sku_inventories AS si JOIN users AS u ON si.distributer_id = u.id WHERE u.user_role = 4 AND si.retailer_scanned_at >= DATE_FORMAT(CURRENT_DATE, '%Y-%m-01 00:00:00') AND si.retailer_scanned_at < DATE_FORMAT(DATE_ADD(CURRENT_DATE, INTERVAL '1' MONTH), '%Y-%m-01 00:00:00') GROUP BY u.id, u.name ORDER BY box_scan_count DESC LIMIT 1"
res = adapt_sql_for_sqlite_test(test_sql)
print("RESULT:\n", res)
