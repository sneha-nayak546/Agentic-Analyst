import os
import time
import pandas as pd
from sqlalchemy import text
from app.database.config import get_db_engine, get_db_credentials
from app.utils.sql_cleaner import clean_sql

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        creds = get_db_credentials()
        if not all([creds.get("host"), creds.get("user"), creds.get("name")]):
            return None
        _engine = get_db_engine()
    return _engine


def execute_read_query(sql: str, limit: int = 500) -> dict:
    """
    Executes a read-only SQL query against the MySQL database using persistent connection pool.
    Returns a dictionary with columns, rows, execution time, and error status.
    """
    sql = clean_sql(sql)
    start_time = time.time()
    engine = get_engine()

    if engine is None:
        return {
            "success": False,
            "columns": [],
            "data": [],
            "row_count": 0,
            "execution_time_ms": 0,
            "error": "Database environment variables missing (.env)"
        }

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            if result.returns_rows:
                raw_rows = result.fetchmany(limit)
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in raw_rows]
            else:
                columns = []
                rows = []

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        if not rows:
            return {
                "success": True,
                "columns": columns,
                "data": [],
                "row_count": 0,
                "execution_time_ms": execution_time_ms,
                "error": None
            }

        import math

        df = pd.DataFrame(rows)
        for col in df.columns:
            df[col] = df[col].apply(lambda x: float(x) if hasattr(x, 'quantize') else (x.isoformat() if hasattr(x, 'isoformat') else x))

        columns = list(df.columns)
        raw_data = df.to_dict(orient="records")

        # Sanitize data to replace NaN/Inf floats and un-serializable objects with None for strict JSON compliance
        data = []
        for row in raw_data:
            clean_row = {}
            for k, v in row.items():
                if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                    clean_row[k] = None
                else:
                    clean_row[k] = v
            data.append(clean_row)

        return {
            "success": True,
            "columns": columns,
            "data": data,
            "row_count": len(data),
            "execution_time_ms": execution_time_ms,
            "error": None
        }

    except Exception as e:
        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "success": False,
            "columns": [],
            "data": [],
            "row_count": 0,
            "execution_time_ms": execution_time_ms,
            "error": str(e)
        }


def execute_query(sql: str) -> pd.DataFrame:
    """Legacy helper for backward compatibility returning Pandas DataFrame."""
    res = execute_read_query(sql)
    if res["success"] and res["data"]:
        return pd.DataFrame(res["data"])
    return pd.DataFrame()


def get_execution_plan(sql: str) -> dict:
    """
    Runs EXPLAIN FORMAT=JSON on the provided SQL query to estimate execution cost
    and enforce the EXPLAIN Cost Gate safety thresholds.
    """
    sql = clean_sql(sql)
    engine = get_engine()
    if engine is None:
        return {"success": False, "error": "No database connection"}
    
    max_rows = int(os.getenv("MAX_EXPLAIN_ROWS", "10000000"))
    
    try:
        with engine.connect() as conn:
            explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
            result = conn.execute(text(explain_sql))
            row = result.fetchone()
            if row and row[0]:
                import json
                try:
                    plan = json.loads(row[0])
                    cost = 0.0
                    total_rows = 0
                    
                    if "query_block" in plan:
                        qb = plan["query_block"]
                        if "cost_info" in qb:
                            cost = float(qb["cost_info"].get("query_cost", 0.0))
                        
                        # Helper to estimate total rows from query_block tables
                        if "table" in qb:
                            total_rows += int(qb["table"].get("rows_examined_per_scan", 0) or qb["table"].get("rows_produced_per_join", 0) or 0)
                        elif "nested_loop" in qb:
                            for item in qb["nested_loop"]:
                                if "table" in item:
                                    total_rows += int(item["table"].get("rows_examined_per_scan", 0) or item["table"].get("rows_produced_per_join", 0) or 0)

                    if max_rows > 0 and total_rows > max_rows:
                        return {
                            "success": False,
                            "error": f"Query execution cost exceeds safety threshold ({total_rows:,} estimated rows > limit {max_rows:,}). Please narrow the date range or add specific filters.",
                            "exceeds_cost_gate": True,
                            "estimated_rows": total_rows,
                            "cost": cost
                        }

                    return {"success": True, "plan": plan, "cost": cost, "estimated_rows": total_rows}
                except json.JSONDecodeError:
                    return {"success": True, "plan": row[0], "cost": 0.0}
            return {"success": False, "error": "No execution plan returned"}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    test_sql = "SELECT id, name, email FROM users LIMIT 5;"
    print("Test Query Result:", execute_read_query(test_sql))
