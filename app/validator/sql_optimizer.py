import re
import sqlglot
from sqlglot import exp

DEFAULT_TABLE_COLUMNS = {
    "users": ["id", "name", "email", "mobile_number", "user_role", "wallet_balance", "status", "created_at"],
    "user_role": ["id", "name", "created_at"],
    "role": ["id", "name", "created_at"],
    "wallet_transaction": ["id", "user_id", "amount", "transaction_type", "status", "created_at"],
    "sku_inventories": ["id", "sku_code", "mrp", "unit_price", "invoiced_quantity", "distributer_id", "created_at"],
    "companies": ["id", "name", "phone", "email", "sap_code", "business_unit", "created_at"],
    "machine_details": ["id", "created_at"],
    "withdrawal_request": ["id", "user_id", "amount", "bank_transaction_id", "status", "tds_amount", "created_at"],
    "automatic_transactions": ["id", "user_id", "transaction_id", "transfer_type", "amount", "bank_reference_number", "created_at"],
    "automate": ["id", "created_at"]
}


def optimize_sql(sql: str) -> str:
    """
    AST & pattern optimization pass for MySQL 8.0 SELECT queries using sqlglot.
    - Expands SELECT * to explicit table columns.
    - Converts DATE(col) = 'YYYY-MM-DD' and YEAR()/MONTH() to sargable indexed date ranges.
    - Converts IN subqueries to EXISTS where applicable.
    - Translates JOIN/FROM user_role to physical table role in MySQL.
    - Enforces LIMIT 100 default on unaggregated queries.
    - Removes unnecessary wildcards and hallucinated column names.
    """
    if not sql or not sql.strip():
        return sql

    cleaned_sql = sql.strip().rstrip(";")

    try:
        # 1. Remap common hallucinated column names and table aliases
        cleaned_sql = re.sub(r"\b([a-zA-Z0-9_]+\.)?username\b", r"\1name", cleaned_sql, flags=re.IGNORECASE)
        # Remap FROM/JOIN user_role to physical table role in MySQL if user_role table doesn't exist directly
        cleaned_sql = re.sub(r"\b(JOIN|FROM)\s+user_role\b", r"\1 role", cleaned_sql, flags=re.IGNORECASE)

        # 2. Optimize non-sargable DATE(col) = 'YYYY-MM-DD' into indexed range
        date_eq_pattern = r"(?:DATE|date)\s*\(\s*([a-zA-Z0-9_\.]+)\s*\)\s*=\s*'(\d{4}-\d{2}-\d{2})'"
        match_date = re.search(date_eq_pattern, cleaned_sql)
        if match_date:
            col_expr, date_str = match_date.groups()
            sargable_clause = f"{col_expr} >= '{date_str} 00:00:00' AND {col_expr} <= '{date_str} 23:59:59'"
            cleaned_sql = re.sub(date_eq_pattern, sargable_clause, cleaned_sql)

        # 3. Optimize YEAR(col) = YYYY AND MONTH(col) = MM into indexed date range
        ym_pattern = r"(?:YEAR|year)\s*\(\s*([a-zA-Z0-9_\.]+)\s*\)\s*=\s*(\d{4})\s+AND\s+(?:MONTH|month)\s*\(\s*\1\s*\)\s*=\s*(\d{1,2})"
        match_ym = re.search(ym_pattern, cleaned_sql, re.IGNORECASE)
        if match_ym:
            col_expr, year_str, month_str = match_ym.groups()
            year = int(year_str)
            month = int(month_str)
            start_date = f"{year:04d}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1:04d}-01-01"
            else:
                end_date = f"{year:04d}-{month+1:02d}-01"
            
            sargable_clause = f"{col_expr} >= '{start_date}' AND {col_expr} < '{end_date}'"
            cleaned_sql = re.sub(ym_pattern, sargable_clause, cleaned_sql, flags=re.IGNORECASE)

        parsed = sqlglot.parse_one(cleaned_sql, read="mysql")
        if not parsed or not isinstance(parsed, exp.Select):
            return cleaned_sql

        # 4. Convert IN subqueries to EXISTS for performance
        # For simplicity in this AST manipulation, we'll let the DB optimizer handle IN vs EXISTS in MySQL 8.0 natively.
        # But we can explicitly optimize with sqlglot if needed.
        from sqlglot.optimizer.unnest_subqueries import unnest_subqueries
        parsed = unnest_subqueries(parsed)

        # 5. Replace SELECT * with explicit columns where table is unambiguous
        tables_in_query = [t.name.lower() for t in parsed.find_all(exp.Table) if t.name]
        select_expressions = parsed.expressions
        if len(select_expressions) == 1 and isinstance(select_expressions[0], exp.Star):
            if len(tables_in_query) == 1 and tables_in_query[0] in DEFAULT_TABLE_COLUMNS:
                tbl_name = tables_in_query[0]
                cols = DEFAULT_TABLE_COLUMNS[tbl_name]
                parsed = parsed.select(*[exp.to_column(c) for c in cols], append=False)

        # 6. Inject LIMIT 100 for unaggregated queries if no LIMIT clause exists
        has_group_by = parsed.args.get("group") is not None
        has_limit = parsed.args.get("limit") is not None
        has_aggregate = any(isinstance(n, exp.AggFunc) for n in parsed.walk())

        if not has_limit and not has_group_by and not has_aggregate:
            parsed = parsed.limit(100)

        optimized = parsed.sql(dialect="mysql")
        return optimized

    except Exception:
        # Fallback to cleaned SQL if sqlglot parse encounters dialect nuance
        return cleaned_sql


