"""
Result Accuracy Validator for JGH Intelligence Engine.

Post-execution validation layer that verifies the generated SQL actually answers
the user's question correctly, not just that it executes without error.

Pipeline position:
  Question → Context → SQL → SQL Safety Validation → Execute
             → Result Accuracy Validation → Response

Confidence statuses:
  VERIFIED_RESULT   — filters correct, records returned
  VERIFIED_EMPTY    — filters correct, database genuinely has no matching records
  SUSPICIOUS_RESULT — filters appear wrong (wrong state/role/id/date) or empty
                      result caused by incorrect filter
  UNABLE_TO_VERIFY  — accuracy check itself failed; result is shown with caveat

Design constraints:
  - Deterministic only (no LLM calls)
  - Read-only probe queries via existing execute_read_query
  - Never modifies SQL or user filters
  - Never fabricates records
  - Does NOT block the response — falls back gracefully on exceptions
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

# ── Business Mappings (source of truth for validation) ────────────────────────
STATE_MAP: Dict[str, int] = {
    "andhra pradesh": 1,
    "arunachal pradesh": 2,
    "assam": 3,
    "bihar": 4,
    "chhattisgarh": 5,
    "goa": 6,
    "gujarat": 7,
    "haryana": 8,
    "himachal pradesh": 9,
    "jharkhand": 10,
    "karnataka": 11,
    "kerala": 12,
    "madhya pradesh": 13,
    "maharashtra": 14,
    "manipur": 15,
    "meghalaya": 16,
    "mizoram": 17,
    "nagaland": 18,
    "odisha": 19,
    "punjab": 20,
    "rajasthan": 21,
    "sikkim": 22,
    "tamil nadu": 23,
    "telangana": 24,
    "tripura": 25,
    "uttarakhand": 26,
    "uttar pradesh": 27,
    "west bengal": 28,
    "andaman and nicobar islands": 29,
    "chandigarh": 30,
    "dadra and nagar haveli": 31,
    "daman and diu": 32,
    "jammu & kashmir": 33,
    "jammu and kashmir": 33,
    "ladakh": 34,
    "lakshadweep": 35,
    "delhi": 40,
    "delhi ncr": 40,
    "puducherry": 37
}

# Mirrors context_resolver.py role extraction
ROLE_MAP: Dict[str, int] = {
    "retailer": 2,
    "retailers": 2,
    "retailor": 2,
    "retailors": 2,
    "distributor": 4,
    "distributors": 4,
    "distributer": 4,
    "distributers": 4,
    "wholesaler": 5,
    "wholesalers": 5,
    "mechanic": 3,
    "mechanics": 3,
}

# Confidence status constants
VERIFIED_RESULT = "VERIFIED_RESULT"
VERIFIED_EMPTY = "VERIFIED_EMPTY"
SUSPICIOUS_RESULT = "SUSPICIOUS_RESULT"
UNABLE_TO_VERIFY = "UNABLE_TO_VERIFY"

# UI messages for each confidence status
STATUS_MESSAGES: Dict[str, str] = {
    VERIFIED_RESULT: "Result verified — the returned data matches your requested filters.",
    VERIFIED_EMPTY: "No matching records were found after verification. The query filters are correct but no data exists for this combination.",
    SUSPICIOUS_RESULT: "I couldn't confidently verify this result. The query may not fully reflect your request — please review the SQL or refine your question.",
    UNABLE_TO_VERIFY: "Result accuracy could not be confirmed. The query executed but I was unable to verify that it answers your question.",
}


class ResultAccuracyValidator:
    """
    Validates that a generated SQL result actually answers the user's question.

    Does NOT validate SQL safety (that is handled upstream by sql_ast_validator).
    Only validates semantic/business correctness of the result.
    """

    def validate(
        self,
        question: str,
        sql: str,
        context: Dict[str, Any],
        execution_result: Dict[str, Any],
        plan: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Main validation entry point.

        Args:
            question: Original user question (cleaned).
            sql: The validated+optimized SQL that was executed.
            context: Resolved context dict from ContextResolver / session.
            execution_result: Dict with keys: success, data, columns, row_count.

        Returns:
            Dict with keys:
              - result_confidence: VERIFIED_RESULT | VERIFIED_EMPTY |
                                   SUSPICIOUS_RESULT | UNABLE_TO_VERIFY
              - accuracy_message: Human-readable explanation for the user.
              - checks_performed: List of check names that were run.
              - issues_found: List of issue descriptions (empty if none).
              - probe_performed: bool — whether a verification probe was executed.
              - probe_result: Optional dict from probe execution.
        """
        try:
            return self._run_validation(question, sql, context, execution_result)
        except Exception as exc:
            logger.warning(
                "[ResultAccuracyValidator] Validation raised an exception: %s", exc
            )
            return self._build_result(
                status=UNABLE_TO_VERIFY,
                issues=["Internal validation error — see server logs."],
                checks=[],
                probe_performed=False,
                probe_result=None,
            )

    # ── Internal orchestration ────────────────────────────────────────────────

    def _run_validation(
        self,
        question: str,
        sql: str,
        context: Dict[str, Any],
        execution_result: Dict[str, Any],
        plan: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if plan is None:
            plan = {}
        sql_upper = sql.upper() if sql else ""
        sql_lower = sql.lower() if sql else ""
        q_lower = question.lower() if question else ""
        rows: List[Dict] = execution_result.get("data", []) or []
        row_count: int = len(rows)
        checks_performed: List[str] = []
        issues_found: List[str] = []

        # ── Check 0: Sensitive / Restricted Credential Request Guard ─────────
        restricted_terms = ["password", "passwords", "encryption key", "master key", "private key", "secret key", "auth token"]
        if any(term in q_lower for term in restricted_terms):
            checks_performed.append("security_credential_guard")
            issues_found.append(
                "Requested attributes (passwords / encryption keys) are restricted by enterprise privacy policy and cannot be disclosed."
            )
            return self._build_result(
                status=SUSPICIOUS_RESULT,
                issues=issues_found,
                checks=checks_performed,
                probe_performed=False,
                probe_result=None,
                accuracy_message="Access Denied: Enterprise Security Policy strictly prohibits retrieving passwords, authentication credentials, or encryption keys.",
            )

        # ── Check 1: Entity / Role mapping ───────────────────────────────────
        entity = plan.get("primary_entity") or context.get("entity") or context.get("role")
        expected_role_id = plan.get("role_id") or context.get("role_id") or (
            ROLE_MAP.get(entity.lower()) if entity else None
        )
        entity_ok = True
        if expected_role_id is not None:
            checks_performed.append("entity_role_mapping")
            pattern = rf"\buser_role\s*=\s*{expected_role_id}\b"
            if not re.search(pattern, sql_lower):
                entity_ok = False
                issues_found.append(
                    f"SQL does not filter on the correct role: expected user_role = {expected_role_id} "
                    f"for entity '{entity}'."
                )

        # ── Check 2: Region / State mapping ──────────────────────────────────
        region = (plan.get("region") or context.get("region") or context.get("location") or "").lower().strip()
        expected_state_id = STATE_MAP.get(region) if region else None
        region_ok = True
        if region and expected_state_id is not None:
            checks_performed.append("region_state_mapping")
            pattern = rf"\bstate_id\s*=\s*{expected_state_id}\b"
            if not re.search(pattern, sql_lower):
                region_ok = False
                issues_found.append(
                    f"SQL does not filter on the correct state: expected state_id = {expected_state_id} "
                    f"for region '{region.title()}'."
                )

        # ── Check 3: Status filter ────────────────────────────────────────────
        status_filter = plan.get("status_filter") or context.get("status_filter")
        status_ok = True
        if status_filter:
            checks_performed.append("status_filter")
            status_value_map = {
                "approved": "approved",
                "active": "approved",
                "pending": "pending",
                "rejected": "rejected",
                "inactive": "inactive",
            }
            expected_status_val = status_value_map.get(status_filter.lower())
            if expected_status_val:
                pattern = rf"status\s*=\s*['\"]?{re.escape(expected_status_val)}['\"]?"
                if not re.search(pattern, sql_lower):
                    status_ok = False
                    issues_found.append(
                        f"SQL does not include the requested status filter: '{status_filter}'."
                    )

        # ── Check 4: Specific ID filter ───────────────────────────────────────
        specific_id = plan.get("identifier_value") or context.get("specific_id")
        id_ok = True
        if specific_id:
            checks_performed.append("specific_id_filter")
            str_id = str(specific_id).strip()
            # Look for the ID value appearing in a WHERE context
            pattern = rf"=\s*['\"]?{re.escape(str_id)}['\"]?\b"
            if not re.search(pattern, sql_lower):
                id_ok = False
                issues_found.append(
                    f"SQL does not appear to filter on the requested ID: {str_id}."
                )

        # ── Check 5: Structural Output Validation ─────────────────────────────
        output_format = plan.get("output_format")
        if output_format == "table" and row_count <= 1:
            pass
            
        group_by = plan.get("group_by", [])
        if group_by and row_count == 1:
            if "group by" not in sql_lower:
                issues_found.append("Requested individual records (grouped) but query returns a single aggregate.")
                
        # Zero-Result Handling
        if row_count == 0:
            checks_performed.append("zero_result_validation")
            if not entity_ok or not region_ok or not status_ok or not id_ok:
                issues_found.append("Zero results likely caused by incorrect filter generation.")
                return self._build_result(
                    status=SUSPICIOUS_RESULT,
                    issues=issues_found,
                    checks=checks_performed,
                    probe_performed=False,
                    probe_result=None,
                    accuracy_message="0 rows returned, possibly due to a filter mismatch."
                )
            else:
                return self._build_result(
                    status=VERIFIED_EMPTY,
                    issues=issues_found,
                    checks=checks_performed,
                    probe_performed=False,
                    probe_result=None,
                    accuracy_message="Result verified — the database genuinely has no matching records for your filters."
                )

        # ── Check 6: Temporal / date filter ──────────────────────────────────
        date_range = plan.get("date_range")
        date_ok = True
        if date_range:
            checks_performed.append("temporal_filter")
            has_date_filter = any(
                kw in sql_lower
                for kw in [
                    "created_at", "updated_at", "transaction_date", "date(",
                    "year(", "month(", "between", "date_format", ">=", "<"
                ]
            )
            if not has_date_filter:
                date_ok = False
                issues_found.append(
                    f"SQL does not contain a date/time filter despite the request "
                    f"specifying period '{date_range.get('label')}'."
                )

        # ── Determine preliminary confidence ─────────────────────────────────
        filter_checks_ok = entity_ok and region_ok and status_ok and id_ok and date_ok

        # ── Check 6: Empty result handling ───────────────────────────────────
        probe_performed = False
        probe_result = None

        if row_count == 0 and filter_checks_ok and checks_performed:
            # Filters look correct but result is empty — run a probe to distinguish
            # VERIFIED_EMPTY from a silent failure
            probe_performed = True
            probe_result = self._run_verification_probe(
                entity=entity,
                expected_role_id=expected_role_id,
                region=region,
                expected_state_id=expected_state_id,
                context=context,
                sql=sql_lower,
            )
            checks_performed.append("empty_result_probe")

            if probe_result and probe_result.get("probe_count", 0) > 0:
                # Probe found records matching the exact target filters → main query had an issue
                issues_found.append(
                    f"Verification probe found {probe_result['probe_count']} record(s) "
                    f"in the database matching the requested entity and region, but the "
                    f"main query returned 0 rows. The SQL filter may be too restrictive."
                )
                filter_checks_ok = False

        # ── Final confidence determination ────────────────────────────────────
        if not filter_checks_ok or issues_found:
            status = SUSPICIOUS_RESULT
        elif row_count > 0:
            status = VERIFIED_RESULT
        elif row_count == 0:
            status = VERIFIED_EMPTY
        else:
            status = UNABLE_TO_VERIFY

        # Build user-facing accuracy message
        if issues_found:
            base_msg = STATUS_MESSAGES[SUSPICIOUS_RESULT]
            detail = " Issue(s): " + "; ".join(issues_found[:2])  # cap at 2 for UI
            accuracy_message = base_msg + detail
        else:
            accuracy_message = STATUS_MESSAGES[status]

        return self._build_result(
            status=status,
            issues=issues_found,
            checks=checks_performed,
            probe_performed=probe_performed,
            probe_result=probe_result,
            accuracy_message=accuracy_message,
        )

    # ── Probe query ───────────────────────────────────────────────────────────

    def _run_verification_probe(
        self,
        entity: Optional[str],
        expected_role_id: Optional[int],
        region: Optional[str],
        expected_state_id: Optional[int],
        context: Optional[Dict[str, Any]] = None,
        sql: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Runs a safe COUNT(*) probe to check whether data exists for the
        requested entity+region+temporal combination, independent of complex SQL joins.

        Returns a dict with 'probe_count' or None on failure.
        """
        try:
            from app.database.read_executor import execute_read_query

            ctx = context or {}
            metric = ctx.get("metric")
            start_date = ctx.get("start_date")
            end_date = ctx.get("end_date")

            user_conditions: List[str] = []
            if expected_role_id is not None:
                user_conditions.append(f"u.user_role = {expected_role_id}")
            if expected_state_id is not None:
                user_conditions.append(f"u.state_id = {expected_state_id}")

            # Case A: Earnings / Wallet Transaction query
            if metric == "earnings" or "wallet_transaction" in sql:
                tx_conditions = ["(wt.reference_type <> 'withdrawal' OR wt.reference_type IS NULL)"]
                if start_date and end_date:
                    tx_conditions.append(f"wt.created_at >= '{start_date}' AND wt.created_at < '{end_date}'")
                all_conditions = user_conditions + tx_conditions
                where_clause = " AND ".join(all_conditions) if all_conditions else "1=1"
                probe_sql = (
                    f"SELECT COUNT(*) AS probe_count "
                    f"FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id "
                    f"WHERE {where_clause}"
                )
            # Case B: Withdrawal query
            elif entity == "withdrawal_request" or "withdrawal_request" in sql:
                wr_conditions = []
                if start_date and end_date:
                    wr_conditions.append(f"wr.created_at >= '{start_date}' AND wr.created_at < '{end_date}'")
                all_conditions = user_conditions + wr_conditions
                where_clause = " AND ".join(all_conditions) if all_conditions else "1=1"
                probe_sql = (
                    f"SELECT COUNT(*) AS probe_count "
                    f"FROM users u JOIN withdrawal_request wr ON u.id = wr.user_id "
                    f"WHERE {where_clause}"
                )
            # Case C: Standard Users query
            else:
                simple_conditions: List[str] = []
                if expected_role_id is not None:
                    simple_conditions.append(f"user_role = {expected_role_id}")
                if expected_state_id is not None:
                    simple_conditions.append(f"state_id = {expected_state_id}")

                if not simple_conditions:
                    return None

                where_clause = " AND ".join(simple_conditions)
                probe_sql = f"SELECT COUNT(*) AS probe_count FROM users WHERE {where_clause}"

            probe_exec = execute_read_query(probe_sql, limit=1)
            if probe_exec.get("success") and probe_exec.get("data"):
                row = probe_exec["data"][0]
                count_val = row.get("probe_count", 0)
                return {"probe_count": int(count_val or 0), "probe_sql": probe_sql}
            return {"probe_count": 0, "probe_sql": probe_sql}
        except Exception as e:
            logger.warning("[ResultAccuracyValidator] Probe query failed: %s", e)
            return None

    # ── Result builder ────────────────────────────────────────────────────────

    @staticmethod
    def _build_result(
        status: str,
        issues: List[str],
        checks: List[str],
        probe_performed: bool,
        probe_result: Optional[Dict],
        accuracy_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "result_confidence": status,
            "accuracy_message": accuracy_message or STATUS_MESSAGES.get(status, ""),
            "checks_performed": checks,
            "issues_found": issues,
            "probe_performed": probe_performed,
            "probe_result": probe_result,
        }


# Singleton instance
result_accuracy_validator = ResultAccuracyValidator()
