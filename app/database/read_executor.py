import os
import time
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        if not all([DB_HOST, DB_USER, DB_NAME]):
            return None
        db_url = URL.create(
            drivername="mysql+pymysql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=int(DB_PORT),
            database=DB_NAME
        )
        _engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True
        )
    return _engine


def execute_read_query(sql: str, limit: int = 500) -> dict:
    """
    Executes a read-only SQL query against the MySQL database using persistent connection pool.
    Returns a dictionary with columns, rows, execution time, and error status.
    """
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
    Runs EXPLAIN FORMAT=JSON on the provided SQL query to estimate execution cost.
    """
    engine = get_engine()
    if engine is None:
        return {"success": False, "error": "No database connection"}
    
    try:
        with engine.connect() as conn:
            # Check if MySQL version supports EXPLAIN FORMAT=JSON
            explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
            result = conn.execute(text(explain_sql))
            row = result.fetchone()
            if row and row[0]:
                import json
                try:
                    plan = json.loads(row[0])
                    # Extract estimated cost if available (MySQL 5.7+)
                    cost = 0.0
                    if "query_block" in plan and "cost_info" in plan["query_block"]:
                        cost = float(plan["query_block"]["cost_info"].get("query_cost", 0.0))
                    return {"success": True, "plan": plan, "cost": cost}
                except json.JSONDecodeError:
                    return {"success": True, "plan": row[0], "cost": 0.0}
            return {"success": False, "error": "No execution plan returned"}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    test_sql = "SELECT id, name, email FROM users LIMIT 5;"
    print("Test Query Result:", execute_read_query(test_sql))
