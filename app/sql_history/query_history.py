import json
import os
import time
from typing import List, Dict

HISTORY_FILE = "knowledge/sql_history/query_audit_history.json"

def log_query_history(question: str, generated_sql: str, status: str, execution_time_ms: float, row_count: int, optimized_sql: str = None, affected_tables: List[str] = None, error: str = None, confidence_score: int = None, execution_plan: dict = None, explanation: str = None, thinking_steps: List[str] = None):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    
    history_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "question": question,
        "generated_sql": generated_sql,
        "optimized_sql": optimized_sql or generated_sql,
        "status": status,
        "execution_time_ms": execution_time_ms,
        "row_count": row_count,
        "affected_tables": affected_tables or [],
        "confidence_score": confidence_score,
        "explanation": explanation,
        "execution_plan_cost": execution_plan.get("cost", 0.0) if execution_plan else 0.0,
        "thinking_steps": thinking_steps or [],
        "error": error
    }

    if status == "success" and execution_plan:
        from app.knowledge.knowledge_graph import get_knowledge_graph
        kg = get_knowledge_graph()
        kg.enrich_from_success(question, optimized_sql or generated_sql, execution_plan)

    history = get_query_history(limit=200)
    history.insert(0, history_entry)

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[:200], f, indent=2)
    except Exception as e:
        print("Failed to save query audit history:", e)


def get_query_history(limit: int = 50, search: str = None) -> List[Dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if search and search.strip():
                s_lower = search.strip().lower()
                data = [
                    item for item in data
                    if s_lower in item.get("question", "").lower() or s_lower in item.get("generated_sql", "").lower()
                ]
            return data[:limit]
    except Exception:
        return []

def toggle_favorite_history(timestamp: str) -> bool:
    if not os.path.exists(HISTORY_FILE):
        return False
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            if item.get("timestamp") == timestamp:
                item["favorite"] = not item.get("favorite", False)
                break
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

def delete_history_item(timestamp: str) -> bool:
    if not os.path.exists(HISTORY_FILE):
        return False
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data = [item for item in data if item.get("timestamp") != timestamp]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


