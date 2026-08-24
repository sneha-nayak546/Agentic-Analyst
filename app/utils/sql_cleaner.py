import re


def clean_sql(raw_sql: str) -> str:
    if not raw_sql or not isinstance(raw_sql, str):
        return ""

    # 1. Strip markdown fences and whitespace
    match = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", raw_sql, re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
    else:
        select_index = raw_sql.upper().find("SELECT")
        if select_index != -1:
            sql = raw_sql[select_index:].strip()
        else:
            sql = raw_sql.strip()

    sql = re.sub(r"```.*$", "", sql).strip()
    sql = sql.replace("```", "").strip()

    # 2. Remove leading semicolons or orphaned punctuation at start
    sql = re.sub(r"^[;\s]+", "", sql)

    # 3. Fix trailing commas right before SQL clauses (WHERE, GROUP BY, ORDER BY, HAVING, LIMIT)
    sql = re.sub(r",\s*(GROUP BY|ORDER BY|WHERE|HAVING|LIMIT)", r" \1", sql, flags=re.IGNORECASE)

    # 4. Remove illegal trailing commas before semicolons or statement ends
    sql = re.sub(r",\s*;", ";", sql)
    sql = re.sub(r",\s*$", "", sql)

    # 5. Deduplicate identical WHERE conditions
    where_match = re.search(r"(\bWHERE\b\s+)(.+?)(\bGROUP BY\b|\bORDER BY\b|\bHAVING\b|\bLIMIT\b|;|$)", sql, flags=re.IGNORECASE | re.DOTALL)
    if where_match:
        prefix, cond_str, suffix = where_match.groups()
        conds = [c.strip() for c in re.split(r"\bAND\b", cond_str, flags=re.IGNORECASE) if c.strip()]
        unique_conds = []
        for c in conds:
            if c not in unique_conds:
                unique_conds.append(c)
        clean_where = prefix + " AND ".join(unique_conds) + " " + suffix
        sql = sql[:where_match.start()] + clean_where.strip() + sql[where_match.end():]

    # 6. Extract first non-empty query if multiple exist
    if ";" in sql:
        parts = [p.strip() for p in sql.split(";") if p.strip()]
        if parts:
            sql = parts[0] + ";"
        else:
            return ""
    elif sql and not sql.endswith(";"):
        sql += ";"

    sql = re.sub(r",\s*;", ";", sql)
    sql = re.sub(r"^[;\s]+", "", sql)

    # Apply AST optimizer and table alias normalizer
    try:
        from app.validator.sql_optimizer import optimize_sql
        sql = optimize_sql(sql)
    except Exception:
        pass

    return sql.strip()


if __name__ == "__main__":
    test1 = ";;; ```sql ; SELECT u.id, u.name, FROM users u GROUP BY u.id,; ```"
    print("Test 1 Result:", clean_sql(test1))
    test2 = "; ; ;"
    print("Test 2 Result:", repr(clean_sql(test2)))