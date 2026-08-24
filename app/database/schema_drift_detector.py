"""
Automated Schema Drift Detector for JGH Intelligence Engine.
Introspects live INFORMATION_SCHEMA.COLUMNS on startup and compares live database structure
against stored metadata (knowledge/schema/draft_schema_metadata.json).
Detects added, removed, or modified columns and logs structural discrepancies.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.database.config import get_db_engine

class SchemaDriftDetector:
    def __init__(self):
        self.engine = get_db_engine()
        self.draft_schema_path = PROJECT_ROOT / "knowledge" / "schema" / "draft_schema_metadata.json"

    def check_drift(self) -> Dict[str, Any]:
        """
        Compares live MySQL INFORMATION_SCHEMA against stored schema metadata.
        Returns drift report listing added, removed, or type-changed columns.
        """
        if not self.draft_schema_path.exists():
            return {
                "status": "NO_BASELINE",
                "message": "Baseline metadata not found. Run database profiling first.",
                "discrepancies": []
            }

        try:
            with open(self.draft_schema_path, "r", encoding="utf-8") as f:
                baseline_data = json.load(f)
        except Exception as e:
            return {"status": "ERROR", "message": f"Failed to load baseline schema: {str(e)}", "discrepancies": []}

        baseline_tables = baseline_data.get("tables", {})
        discrepancies = []

        with self.engine.connect() as conn:
            db_name = conn.execute(text("SELECT DATABASE()")).scalar() or "jghMasterDB"

            # Query live schema columns
            live_cols_sql = text("""
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :db_name
            """)
            live_rows = conn.execute(live_cols_sql, {"db_name": db_name}).fetchall()

            # Group live columns: {tbl: {col: data_type}}
            live_schema = {}
            for r in live_rows:
                tbl, col, dtype = r.TABLE_NAME, r.COLUMN_NAME, r.DATA_TYPE
                if tbl not in live_schema:
                    live_schema[tbl] = {}
                live_schema[tbl][col] = dtype.lower()

            # Compare baseline vs live
            for tbl_name, tbl_info in baseline_tables.items():
                if tbl_name not in live_schema:
                    discrepancies.append({
                        "type": "TABLE_REMOVED",
                        "table": tbl_name,
                        "details": f"Table '{tbl_name}' exists in baseline but is missing from live database."
                    })
                    continue

                base_cols = {c["name"]: c["data_type"].lower() for c in tbl_info.get("columns", [])}
                live_cols = live_schema[tbl_name]

                # Check missing columns
                for col_name, dtype in base_cols.items():
                    if col_name not in live_cols:
                        discrepancies.append({
                            "type": "COLUMN_REMOVED",
                            "table": tbl_name,
                            "column": col_name,
                            "details": f"Column '{tbl_name}.{col_name}' was removed from live database."
                        })
                    elif base_cols[col_name] != live_cols[col_name]:
                        discrepancies.append({
                            "type": "TYPE_MODIFIED",
                            "table": tbl_name,
                            "column": col_name,
                            "details": f"Type mismatch on '{tbl_name}.{col_name}': baseline={base_cols[col_name]}, live={live_cols[col_name]}"
                        })

                # Check new columns added
                for col_name, dtype in live_cols.items():
                    if col_name not in base_cols:
                        discrepancies.append({
                            "type": "COLUMN_ADDED",
                            "table": tbl_name,
                            "column": col_name,
                            "details": f"New column '{tbl_name}.{col_name}' detected in live database."
                        })

        has_drift = len(discrepancies) > 0
        report = {
            "status": "DRIFT_DETECTED" if has_drift else "SYNCHRONIZED",
            "checked_at": datetime.now().isoformat(),
            "active_version": self.get_active_version(),
            "total_discrepancies": len(discrepancies),
            "discrepancies": discrepancies
        }

        if has_drift:
            print(f"[SCHEMA DRIFT WARNING] Detected {len(discrepancies)} structural discrepancies between live DB and metadata.")
            self.create_version_snapshot(report)
        else:
            print("[SCHEMA DRIFT OK] Live database structure is perfectly synchronized with schema metadata.")

        return report

    def get_active_version(self) -> str:
        version_file = PROJECT_ROOT / "knowledge" / "schema" / "active_version.json"
        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    return json.load(f).get("version", "knowledge_v1.0")
            except Exception:
                pass
        return "knowledge_v1.0"

    def create_version_snapshot(self, drift_report: dict):
        version_file = PROJECT_ROOT / "knowledge" / "schema" / "active_version.json"
        new_version = f"knowledge_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        v_data = {
            "version": new_version,
            "activated_at": datetime.now().isoformat(),
            "drift_report": drift_report
        }
        try:
            with open(version_file, "w", encoding="utf-8") as f:
                json.dump(v_data, f, indent=2)
            print(f"[KNOWLEDGE VERSIONING] Created and activated new schema version: {new_version}")
        except Exception as e:
            print(f"[KNOWLEDGE VERSIONING ERROR] {e}")

drift_detector = SchemaDriftDetector()

def run_schema_drift_check() -> Dict[str, Any]:
    return drift_detector.check_drift()

if __name__ == "__main__":
    run_schema_drift_check()
