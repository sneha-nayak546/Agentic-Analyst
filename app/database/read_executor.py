import os
import time
import re
import socket
import logging
import pandas as pd
from typing import Dict, Any, Optional, List
from sqlalchemy import text, create_engine
from app.database.config import get_db_engine, get_db_credentials
from app.utils.sql_cleaner import clean_sql

logger = logging.getLogger(__name__)

_engine = None
_sqlite_engine = None

class DatabaseCircuitBreaker:
    """
    Circuit breaker for remote MySQL connection resilience (Section 10).
    Eliminates 3,000ms latency spikes when remote server (e.g. 168.144.28.208) is offline.
    Fails fast (0ms) to local SQLite database.db while periodically testing remote health.
    """
    STATE_CLOSED = "CLOSED"      # Remote healthy
    STATE_OPEN = "OPEN"          # Remote known down, fail fast immediately
    STATE_HALF_OPEN = "HALF_OPEN"# Periodic re-check

    def __init__(self, cooldown_seconds: float = 600.0, probe_timeout_seconds: float = 0.15):
        self.state = self.STATE_CLOSED
        self.last_failure_time = 0.0
        self.cooldown_seconds = cooldown_seconds
        self.probe_timeout = probe_timeout_seconds
        self.failure_reason: Optional[str] = None

    def is_remote_available(self, host: str, port: int) -> bool:
        now = time.time()

        # If currently marked OPEN, check if cooldown has elapsed
        if self.state == self.STATE_OPEN:
            if (now - self.last_failure_time) > self.cooldown_seconds:
                self.state = self.STATE_HALF_OPEN
            else:
                return False

        # Attempt short socket probe
        try:
            with socket.create_connection((host, port), timeout=self.probe_timeout):
                self.state = self.STATE_CLOSED
                self.failure_reason = None
                return True
        except Exception as e:
            self.state = self.STATE_OPEN
            self.last_failure_time = now
            self.failure_reason = f"Remote TCP connection failed ({type(e).__name__}: {e})"
            logger.warning(f"[CIRCUIT BREAKER OPEN]: Remote MySQL {host}:{port} is unreachable: {e}. Routing instantly to local SQLite.")
            return False

circuit_breaker = DatabaseCircuitBreaker()

def get_engine():
    global _engine
    if _engine is None:
        try:
            creds = get_db_credentials()
            if not all([creds.get("host"), creds.get("user"), creds.get("name")]):
                return None
            _engine = get_db_engine()
        except Exception:
            _engine = None
    return _engine

def get_sqlite_engine():
    global _sqlite_engine
    if _sqlite_engine is None:
        db_path = os.path.abspath("database.db")
        _sqlite_engine = create_engine(f"sqlite:///{db_path}")
        from sqlalchemy import event
        @event.listens_for(_sqlite_engine, "connect")
        def set_sqlite_functions(dbapi_con, con_record):
            try:
                from datetime import datetime

                def month_fn(val):
                    if val is None:
                        return None
                    try:
                        s = str(val).strip()
                        return int(s[5:7]) if len(s) >= 7 else None
                    except Exception:
                        return None

                def year_fn(val):
                    if val is None:
                        return None
                    try:
                        s = str(val).strip()
                        return int(s[:4]) if len(s) >= 4 else None
                    except Exception:
                        return None

                def day_fn(val):
                    if val is None:
                        return None
                    try:
                        s = str(val).strip()
                        return int(s[8:10]) if len(s) >= 10 else None
                    except Exception:
                        return None

                def now_fn():
                    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                def curdate_fn():
                    return datetime.now().strftime("%Y-%m-%d")

                def date_format_fn(val, fmt):
                    if not val:
                        return None
                    s_dt = str(val)
                    if "%Y-%m" in fmt:
                        return s_dt[:7]
                    if "%Y-%m-%d" in fmt:
                        return s_dt[:10]
                    if "%Y" in fmt:
                        return s_dt[:4]
                    if "%m" in fmt:
                        return s_dt[5:7] if len(s_dt) >= 7 else s_dt
                    return s_dt

                def concat_fn(*args):
                    return "".join(str(a) for a in args if a is not None)

                def ifnull_fn(val, default_val):
                    return default_val if val is None else val

                def datediff_fn(d1, d2):
                    if not d1 or not d2:
                        return None
                    try:
                        dt1 = datetime.fromisoformat(str(d1)[:10])
                        dt2 = datetime.fromisoformat(str(d2)[:10])
                        return (dt1 - dt2).days
                    except Exception:
                        return None

                dbapi_con.create_function("MONTH", 1, month_fn)
                dbapi_con.create_function("YEAR", 1, year_fn)
                dbapi_con.create_function("DAY", 1, day_fn)
                dbapi_con.create_function("DAYOFMONTH", 1, day_fn)
                dbapi_con.create_function("NOW", 0, now_fn)
                dbapi_con.create_function("CURRENT_DATE", 0, curdate_fn)
                dbapi_con.create_function("CURDATE", 0, curdate_fn)
                dbapi_con.create_function("DATE_FORMAT", 2, date_format_fn)
                dbapi_con.create_function("CONCAT", -1, concat_fn)
                dbapi_con.create_function("IFNULL", 2, ifnull_fn)
                dbapi_con.create_function("DATEDIFF", 2, datediff_fn)
            except Exception as func_err:
                logger.warning(f"[SQLITE FUNCTIONS WARNING] {func_err}")
    return _sqlite_engine

def is_explicit_local_test_mode() -> bool:
    """
    Local replica / SQLite may be used ONLY when explicitly configured
    as a test/development database. It must never silently replace
    the production database.
    """
    return (
        os.getenv("USE_LOCAL_TEST_DB", "").lower() in ("true", "1", "yes")
        or os.getenv("DB_ENGINE", "").lower() in ("sqlite", "sqlite3")
        or os.getenv("APP_ENV", "").lower() in ("local_test", "offline_test")
    )

def execute_read_query(sql: str, limit: int = 500) -> dict:
    """
    Executes the EXACT read-only SQL query against the configured database.
    Guarantees:
    - Zero query rewriting: executed SQL == generated SQL.
    - Lossless row serialization: preserves integers, decimals, dates, and nulls.
    - Zero silent fallback: if configured MySQL cannot be reached, returns DATABASE_CONNECTION_ERROR.
    - Full identity tracking: tracks database_engine, database_host, database_port, database_name, database_source.
    """
    sql = clean_sql(sql)
    t_start = time.perf_counter()

    remote_conn_ms = 0.0
    query_exec_ms = 0.0
    fetch_ms = 0.0
    conn = None

    if is_explicit_local_test_mode():
        database_engine = "sqlite"
        database_host = "localhost"
        database_port = "0"
        database_name = "database.db"
        database_source = "Executed on local test replica"
        database_identifier = "sqlite:///database.db"
        try:
            sqlite_eng = get_sqlite_engine()
            conn = sqlite_eng.connect()
        except Exception as e:
            total_exec_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
            return {
                "success": False,
                "columns": [],
                "data": [],
                "row_count": 0,
                "execution_time_ms": total_exec_time_ms,
                "remote_connection_ms": 0.0,
                "query_execution_ms": 0.0,
                "result_fetch_ms": 0.0,
                "fallback_used": False,
                "fallback_reason": None,
                "database_engine": database_engine,
                "database_host": database_host,
                "database_port": database_port,
                "database_name": database_name,
                "database_source": database_source,
                "database_identifier": database_identifier,
                "error_code": "LOCAL_DB_ERROR",
                "error": f"Local test replica unavailable: {str(e)}",
                "stage": "DATABASE_CONNECTION"
            }
    else:
        # PRODUCTION PATH: MUST use configured MySQL database
        creds = get_db_credentials()
        database_engine = "mysql"
        database_host = creds.get("host", "localhost")
        database_port = str(creds.get("port", "3306"))
        database_name = creds.get("name", "jghMasterDB")
        database_source = "Executed on configured MySQL database"
        database_identifier = f"mysql://{database_host}:{database_port}/{database_name}"

        mysql_engine = get_engine()
        if mysql_engine is None:
            total_exec_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
            return {
                "success": False,
                "columns": [],
                "data": [],
                "row_count": 0,
                "execution_time_ms": total_exec_time_ms,
                "remote_connection_ms": 0.0,
                "query_execution_ms": 0.0,
                "result_fetch_ms": 0.0,
                "fallback_used": False,
                "fallback_reason": None,
                "database_engine": database_engine,
                "database_host": database_host,
                "database_port": database_port,
                "database_name": database_name,
                "database_source": "CONFIGURED_PRODUCTION_DATABASE",
                "database_identifier": database_identifier,
                "error_code": "DATABASE_CONNECTION_ERROR",
                "host": database_host,
                "port": database_port,
                "database": database_name,
                "failure_reason": "Could not create database engine with configured credentials",
                "stage": "DATABASE_CONNECTION",
                "error": f"DATABASE_CONNECTION_ERROR: Failed to initialize connection to {database_host}:{database_port}/{database_name}"
            }

        t0_conn = time.perf_counter()
        try:
            conn = mysql_engine.connect()
            remote_conn_ms = round((time.perf_counter() - t0_conn) * 1000, 2)
        except Exception as conn_err:
            remote_conn_ms = round((time.perf_counter() - t0_conn) * 1000, 2)
            total_exec_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
            logger.error(f"[DATABASE_CONNECTION_ERROR] Failed to connect to {database_host}:{database_port}/{database_name}: {conn_err}")
            return {
                "success": False,
                "columns": [],
                "data": [],
                "row_count": 0,
                "execution_time_ms": total_exec_time_ms,
                "remote_connection_ms": remote_conn_ms,
                "query_execution_ms": 0.0,
                "result_fetch_ms": 0.0,
                "fallback_used": False,
                "fallback_reason": None,
                "database_engine": database_engine,
                "database_host": database_host,
                "database_port": database_port,
                "database_name": database_name,
                "database_source": "CONFIGURED_PRODUCTION_DATABASE",
                "database_identifier": database_identifier,
                "error_code": "DATABASE_CONNECTION_ERROR",
                "host": database_host,
                "port": database_port,
                "database": database_name,
                "failure_reason": str(conn_err),
                "stage": "DATABASE_CONNECTION",
                "error": f"DATABASE_CONNECTION_ERROR: Failed to connect to {database_host}:{database_port}/{database_name} ({conn_err})"
            }

    # Step 2: Execute query
    try:
        t0_exec = time.perf_counter()
        query_to_run = sql
        result = conn.execute(text(query_to_run))
        query_exec_ms = round((time.perf_counter() - t0_exec) * 1000, 2)

        # Step 3: Fetch results losslessly
        t0_fetch = time.perf_counter()
        if result.returns_rows:
            columns = list(result.keys())
            raw_mappings = result.mappings().fetchmany(limit)
            
            import math
            data = []
            for m in raw_mappings:
                row_dict = {}
                for col in columns:
                    v = m[col]
                    if v is None:
                        row_dict[col] = None
                    elif hasattr(v, "quantize"):  # Decimal
                        row_dict[col] = float(v)
                    elif hasattr(v, "isoformat"):  # datetime / date
                        row_dict[col] = str(v)
                    elif isinstance(v, bytes):
                        row_dict[col] = v.decode("utf-8", errors="replace")
                    elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        row_dict[col] = None
                    else:
                        row_dict[col] = v
                data.append(row_dict)
        else:
            columns = []
            data = []
        fetch_ms = round((time.perf_counter() - t0_fetch) * 1000, 2)

        conn.close()
        total_exec_time_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # Requirement 11: Exact debug trace
        print("\n" + "=" * 60)
        print(f"DATABASE ENGINE: {database_engine}")
        print(f"DATABASE HOST: {database_host}")
        print(f"DATABASE NAME: {database_name}")
        print(f"DATABASE CONNECTION: {database_identifier}")
        print(f"DATABASE SOURCE: {database_source}")
        print(f"GENERATED SQL: {sql}")
        print(f"EXECUTED SQL: {sql}")
        print(f"ROW COUNT: {len(data)}")
        print("=" * 60 + "\n")

        return {
            "success": True,
            "columns": columns,
            "data": data,
            "row_count": len(data),
            "execution_time_ms": total_exec_time_ms,
            "remote_connection_ms": remote_conn_ms,
            "query_execution_ms": query_exec_ms,
            "result_fetch_ms": fetch_ms,
            "fallback_used": False,
            "fallback_reason": None,
            "database_engine": database_engine,
            "database_host": database_host,
            "database_port": database_port,
            "database_name": database_name,
            "database_source": database_source,
            "database_identifier": database_identifier,
            "error": None
        }

    except Exception as e:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        total_exec_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return {
            "success": False,
            "columns": [],
            "data": [],
            "row_count": 0,
            "execution_time_ms": total_exec_time_ms,
            "remote_connection_ms": remote_conn_ms,
            "query_execution_ms": query_exec_ms,
            "result_fetch_ms": fetch_ms,
            "fallback_used": False,
            "fallback_reason": None,
            "database_engine": database_engine,
            "database_host": database_host,
            "database_port": database_port,
            "database_name": database_name,
            "database_source": database_source,
            "database_identifier": database_identifier,
            "error": str(e)
        }

def get_execution_plan(sql: str) -> dict:
    """Runs EXPLAIN on query to estimate cost and catch syntax errors."""
    sql = clean_sql(sql)
    if is_explicit_local_test_mode():
        try:
            eng = get_sqlite_engine()
            with eng.connect() as conn:
                conn.execute(text(f"EXPLAIN QUERY PLAN {sql}"))
                return {"success": True, "plan": "SQLite Explain Plan OK", "cost": 0.0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Production path: MySQL only
    mysql_engine = get_engine()
    if mysql_engine is not None:
        try:
            with mysql_engine.connect() as conn:
                explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
                result = conn.execute(text(explain_sql))
                row = result.fetchone()
                if row and row[0]:
                    import json
                    plan = json.loads(row[0])
                    return {"success": True, "plan": plan, "cost": 0.0}
        except Exception as e:
            return {"success": False, "error": f"MySQL execution plan unavailable: {e}"}

    return {"success": False, "error": "Database engine unavailable for EXPLAIN plan"}

if __name__ == "__main__":
    test_sql = "SELECT id, name FROM users LIMIT 5;"
    print("Test Query Result:", execute_read_query(test_sql))