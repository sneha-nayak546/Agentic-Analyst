"""
Unknown Query Audit Logger for JGH Intelligence Engine.
Logs queries that fail validation or trigger clarification fallbacks into knowledge/unmapped_queries.json
so domain experts can review new business terms and expand business_dictionary.json over time.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UNMAPPED_LOG_FILE = PROJECT_ROOT / "knowledge" / "unmapped_queries.json"

class QueryLogger:
    @staticmethod
    def log_unmapped_query(prompt: str, reason: str, mode: Optional[str] = None, meta: Optional[Dict[str, Any]] = None):
        """
        Appends an unmapped query event to knowledge/unmapped_queries.json.
        """
        UNMAPPED_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prompt": prompt,
            "reason": reason,
            "mode": mode or "UNKNOWN",
            "meta": meta or {}
        }

        existing_entries = []
        if UNMAPPED_LOG_FILE.exists():
            try:
                with open(UNMAPPED_LOG_FILE, "r", encoding="utf-8") as f:
                    existing_entries = json.load(f)
            except Exception:
                existing_entries = []

        existing_entries.insert(0, entry)

        try:
            with open(UNMAPPED_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(existing_entries[:200], f, indent=2)
        except Exception as e:
            print(f"[QUERY LOGGER WARNING] Could not log unmapped query: {e}")

query_logger = QueryLogger()
