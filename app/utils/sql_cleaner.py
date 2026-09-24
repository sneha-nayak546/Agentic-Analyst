import re


def clean_sql(raw_sql: str) -> str:
    """
    Pure presentation artifact cleaner for JGH Intelligence Engine.
    Only strips markdown fences (```sql ... ```) and trailing semicolons.
    NEVER mutates, rewrites, or truncates the validated SQL query.
    """
    if not raw_sql or not isinstance(raw_sql, str):
        return ""

    # 1. Strip thinking tags safely if present
    sql = re.sub(r"<think>[\s\S]*?</think>", "", raw_sql, flags=re.IGNORECASE).strip()

    # 2. Extract content from markdown code block if wrapped
    match = re.search(r"```(?:sql)?\s*([\s\S]*?)(?:```|$)", sql, re.IGNORECASE)
    if match:
        sql = match.group(1).strip()

    # 3. If leading conversational text exists, isolate from SELECT or WITH
    lines = sql.splitlines()
    start_line_idx = None
    for idx, line in enumerate(lines):
        l_str = line.strip().upper()
        if l_str.startswith("SELECT ") or l_str.startswith("WITH ") or l_str == "SELECT" or l_str == "WITH":
            start_line_idx = idx
            break
    if start_line_idx is not None:
        sql = "\n".join(lines[start_line_idx:]).strip()

    # 4. Strip any stray markdown backticks and surrounding whitespace
    sql = sql.replace("```", "").strip()

    # 5. Remove trailing semicolon for uniform database execution
    sql = sql.rstrip(";").strip()

    return sql


if __name__ == "__main__":
    test1 = "```sql\nWITH cat AS (SELECT 1)\nSELECT * FROM cat;\n```"
    print("Test 1 Result:", repr(clean_sql(test1)))
    test2 = "SELECT u.id, u.name FROM users u;"
    print("Test 2 Result:", repr(clean_sql(test2)))