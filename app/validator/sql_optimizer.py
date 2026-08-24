import re
import sqlglot
from sqlglot import exp

DEFAULT_TABLE_COLUMNS = {
    "users": ["id", "name", "email", "mobile_number", "user_role", "wallet_balance", "status", "created_at"],
    "user_role": ["id", "name", "created_at"],
    "role": ["id", "name", "created_at"],
    "wallet_transaction": ["id", "user_id", "amount", "transaction_type", "status", "reference_type", "reference_id", "remark", "created_at", "updated_at"],
    "sku_inventories": [
        "id", "sku_code", "product_id", "lpn_code", "lpn_number", "outer_lpn_number", "carton_no", "batch_details",
        "mrp", "unit_price", "invoiced_quantity", "packed_quantity", "uom", "order_type", "order_reference",
        "invoice_number", "invoice_date", "order_date", "warehouse", "invoiced_by", "customer_info", "distributer_id",
        "status_wholeseller_id", "status_retailer_id", "wholesaler_scanned_at", "retailer_scanned_at", "sources",
        "is_callback", "is_active", "is_offline", "created_at", "updated_at", "sku_description"
    ],
    "sku_qr_points_map": [
        "id", "sku_code", "gride_type", "uom", "box_calculation_uom", "status_wholesaler_id", "status_retailer_id",
        "wholesaler_scanned_at", "retailer_scanned_at", "created_at"
    ],
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

        # Normalize unaliased table prefixes when table aliases (users u, wallet_transaction wt) are used
        if re.search(r"\bFROM\s+users\s+u\b|\bJOIN\s+users\s+u\b", cleaned_sql, flags=re.IGNORECASE):
            cleaned_sql = re.sub(r"\busers\.", "u.", cleaned_sql)
        if re.search(r"\bFROM\s+wallet_transaction\s+wt\b|\bJOIN\s+wallet_transaction\s+wt\b", cleaned_sql, flags=re.IGNORECASE):
            cleaned_sql = re.sub(r"\bwallet_transaction\.", "wt.", cleaned_sql)

        # Remap FROM/JOIN user_role to physical table role in MySQL with alias safety
        def _remap_user_role(m):
            prefix = m.group(1)
            rest = m.group(2)
            first_word = rest.strip().split()[0].upper() if rest.strip() else ""
            if first_word in ("ON", "WHERE", "ORDER", "GROUP", "LIMIT", "INNER", "LEFT", "RIGHT", "JOIN", "CROSS", "UNION", ";", ""):
                return f"{prefix} role AS user_role{rest}"
            return f"{prefix} role{rest}"

        cleaned_sql = re.sub(r"\b(JOIN|FROM)\s+user_role(\s+[^;]*)?$", _remap_user_role, cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r"\b(JOIN|FROM)\s+user_role(\s+(?:ON|WHERE|ORDER|GROUP|LIMIT|INNER|LEFT|RIGHT|JOIN|CROSS|UNION\b|[a-zA-Z0-9_]+))", _remap_user_role, cleaned_sql, flags=re.IGNORECASE)


        # 2. Optimize non-sargable DATE(col) = 'YYYY-MM-DD' into indexed sargable range
        date_eq_pattern = r"(?:DATE|date)\s*\(\s*([a-zA-Z0-9_\.]+)\s*\)\s*=\s*'(\d{4}-\d{2}-\d{2})'"
        match_date = re.search(date_eq_pattern, cleaned_sql)
        if match_date:
            col_expr, date_str = match_date.groups()
            sargable_clause = f"{col_expr} >= '{date_str} 00:00:00' AND {col_expr} <= '{date_str} 23:59:59'"
            cleaned_sql = re.sub(date_eq_pattern, sargable_clause, cleaned_sql)

        # Optimize DATE(col) >= 'YYYY-MM-DD'
        date_gte_pattern = r"(?:DATE|date)\s*\(\s*([a-zA-Z0-9_\.]+)\s*\)\s*>=\s*'(\d{4}-\d{2}-\d{2})'"
        cleaned_sql = re.sub(date_gte_pattern, r"\1 >= '\2 00:00:00'", cleaned_sql)

        # Optimize DATE(col) <= 'YYYY-MM-DD'
        date_lte_pattern = r"(?:DATE|date)\s*\(\s*([a-zA-Z0-9_\.]+)\s*\)\s*<=\s*'(\d{4}-\d{2}-\d{2})'"
        cleaned_sql = re.sub(date_lte_pattern, r"\1 <= '\2 23:59:59'", cleaned_sql)

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
        from sqlglot.optimizer.unnest_subqueries import unnest_subqueries
        parsed = unnest_subqueries(parsed)

        # 5. Table Alias Normalization for ambiguous columns in WHERE, GROUP BY, ORDER BY, HAVING
        table_nodes = list(parsed.find_all(exp.Table))
        alias_to_table = {}
        table_to_alias = {}
        for t in table_nodes:
            tbl_name = t.name.lower() if t.name else ""
            tbl_alias = t.alias.lower() if t.alias else tbl_name
            if tbl_name and tbl_alias:
                alias_to_table[tbl_alias] = tbl_name
                table_to_alias[tbl_name] = tbl_alias

        def _resolve_alias_for_col(col_name: str) -> str:
            col_lower = col_name.lower()
            if col_lower == "created_at":
                if "wallet_transaction" in table_to_alias:
                    return table_to_alias["wallet_transaction"]
                if "sku_inventories" in table_to_alias:
                    return table_to_alias["sku_inventories"]
                if "withdrawal_request" in table_to_alias:
                    return table_to_alias["withdrawal_request"]
                if "automatic_transactions" in table_to_alias:
                    return table_to_alias["automatic_transactions"]
                if "users" in table_to_alias:
                    return table_to_alias["users"]
            if col_lower in ["retailer_scanned_at", "wholesaler_scanned_at", "order_date", "invoice_date"]:
                if "sku_inventories" in table_to_alias:
                    return table_to_alias["sku_inventories"]
                if "sku_qr_points_map" in table_to_alias:
                    return table_to_alias["sku_qr_points_map"]
            if col_lower in ["status", "is_active"]:
                if "wallet_transaction" in table_to_alias:
                    return table_to_alias["wallet_transaction"]
                if "sku_inventories" in table_to_alias:
                    return table_to_alias["sku_inventories"]
                if "withdrawal_request" in table_to_alias:
                    return table_to_alias["withdrawal_request"]
                if "users" in table_to_alias:
                    return table_to_alias["users"]
            if col_lower == "id":
                if "users" in table_to_alias:
                    return table_to_alias["users"]
                if len(alias_to_table) == 1:
                    return list(alias_to_table.keys())[0]

            candidates = []
            for alias, tbl in alias_to_table.items():
                known_cols = DEFAULT_TABLE_COLUMNS.get(tbl, [])
                if col_lower in known_cols:
                    candidates.append(alias)
            if len(candidates) == 1:
                return candidates[0]
            elif len(candidates) > 1:
                for preferred in ["wallet_transaction", "sku_inventories", "users"]:
                    if preferred in table_to_alias and table_to_alias[preferred] in candidates:
                        return table_to_alias[preferred]
                return candidates[0]
            return None

        for clause_key in ["where", "group", "order", "having"]:
            clause_ast = parsed.args.get(clause_key)
            if clause_ast:
                for col in clause_ast.find_all(exp.Column):
                    if not col.table:
                        target_alias = _resolve_alias_for_col(col.name)
                        if target_alias:
                            col.set("table", exp.to_identifier(target_alias))

        # 6. Replace SELECT * with explicit columns where table is unambiguous
        tables_in_query = [t.name.lower() for t in parsed.find_all(exp.Table) if t.name]
        select_expressions = parsed.expressions
        if len(select_expressions) == 1 and isinstance(select_expressions[0], exp.Star):
            if len(tables_in_query) == 1 and tables_in_query[0] in DEFAULT_TABLE_COLUMNS:
                tbl_name = tables_in_query[0]
                cols = DEFAULT_TABLE_COLUMNS[tbl_name]
                parsed = parsed.select(*[exp.to_column(c) for c in cols], append=False)

        # 7. MySQL ONLY_FULL_GROUP_BY AST Sanitizer
        group_clause_ast = parsed.args.get("group")
        has_aggregate = any(isinstance(n, exp.AggFunc) for n in parsed.walk())
        
        if group_clause_ast or has_aggregate:
            existing_group_exprs = [g.sql(dialect="mysql").replace("`", "").strip().lower() for g in group_clause_ast.expressions] if group_clause_ast else []
            new_group_items = list(group_clause_ast.expressions) if group_clause_ast else []

            for expr in parsed.expressions:
                is_agg = any(isinstance(n, exp.AggFunc) for n in expr.walk())
                if not is_agg:
                    unaliased = expr.this if isinstance(expr, exp.Alias) else expr
                    unaliased_sql = unaliased.sql(dialect="mysql").replace("`", "").strip()
                    if unaliased_sql.lower() not in existing_group_exprs:
                        new_group_items.append(unaliased)
                        existing_group_exprs.append(unaliased_sql.lower())

            if new_group_items:
                parsed = parsed.group_by(*new_group_items, append=False)

        # 8. Inject LIMIT 100 for unaggregated queries if no LIMIT clause exists
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


