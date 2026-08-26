import os
import json
from typing import List, Dict, Any, Optional

_schema_cache: Optional[Dict[str, Any]] = None

def get_full_schema_metadata() -> Dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        schema_file = "knowledge/schema/schema_metadata.json"
        if os.path.exists(schema_file):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    _schema_cache = json.load(f)
            except Exception:
                _schema_cache = {}
        else:
            _schema_cache = {}
    return _schema_cache

IGNORED_COLUMNS = {
    "password", "two_factor_secret", "two_factor_recovery_codes", "remember_token",
    "fcm_token", "device_id", "deleted_at", "email_verified_at"
}

def get_selective_schema_context(tables: List[str]) -> str:
    """
    Returns a compact, targeted schema definition containing ONLY the tables
    and columns necessary for the detected query tables.
    Uses dynamic comments and foreign keys instead of hardcoded logic.
    """
    if not tables:
        tables = ["users"]

    full_schema = get_full_schema_metadata()
    lines = []
    
    relevant_joins = []
    tbl_set = set(tables)

    for tbl in tables:
        tbl_clean = tbl.strip()
        if tbl_clean in full_schema:
            tbl_info = full_schema[tbl_clean]
            summary = tbl_info.get("comment", "")
            lines.append(f"TABLE `{tbl_clean}`" + (f" ({summary})" if summary else "") + ":")

            cols = tbl_info.get("columns", {})
            col_entries = []
            cols_iterable = cols.values() if isinstance(cols, dict) else (cols if isinstance(cols, list) else [])
            for c in cols_iterable:
                c_name = c.get("name", "")
                if c_name in IGNORED_COLUMNS:
                    continue
                c_type = c.get("datatype", "")
                
                # Dynamic Foreign Key Joins
                if c.get("foreign_key"):
                    fk_tbl = c["foreign_key"].get("table")
                    fk_col = c["foreign_key"].get("column")
                    if fk_tbl in tbl_set and fk_tbl != tbl_clean:
                        relevant_joins.append(f"{tbl_clean}.{c_name} = {fk_tbl}.{fk_col}")

                if c.get("is_enum") and c.get("enum_values"):
                    enums = ", ".join([f"'{v}'" for v in c["enum_values"][:6]])
                    col_entries.append(f"  - {c_name} ({c_type}) [ENUM: {enums}]")
                else:
                    col_entries.append(f"  - {c_name} ({c_type})")
            lines.extend(col_entries)
        else:
            lines.append(f"TABLE `{tbl_clean}`:\n  - (Standard table schema applies)")

        lines.append("")

    if relevant_joins:
        lines.append("RELEVANT DYNAMIC JOINS:")
        lines.extend([f"- {j}" for j in set(relevant_joins)])

    return "\n".join(lines).strip()
