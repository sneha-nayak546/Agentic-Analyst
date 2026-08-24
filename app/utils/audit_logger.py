import os
import json
import time
from typing import Optional, Dict, Any

AUDIT_LOG_FILE = "logs/query_audit.json"

def log_audit_event(
    prompt: str,
    sql: str,
    status: str,
    latency_ms: float,
    row_count: int,
    affected_tables: Optional[list] = None,
    error: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    is_private: bool = False
):
    if is_private:
        return # Incognito Ephemeral Mode: Suppress disk logging
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    
    event = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch_time": time.time(),
        "prompt": prompt,
        "sql": sql,
        "status": status,
        "latency_ms": latency_ms,
        "row_count": row_count,
        "affected_tables": affected_tables or [],
        "error": error,
        "metadata": extra_metadata or {}
    }

    logs = []
    if os.path.exists(AUDIT_LOG_FILE):
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = []
        except Exception:
            logs = []

    logs.insert(0, event)
    # Keep last 1000 audit log entries
    logs = logs[:1000]

    try:
        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"[AUDIT LOG ERROR] Failed to record audit log: {e}")

def get_audit_logs(limit: int = 100) -> list:
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            return logs[:limit]
    except Exception:
        return []
