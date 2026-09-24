import re
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Standard 16 Response Accuracy Failure Categories
WRONG_ENTITY = "WRONG_ENTITY"
WRONG_METRIC = "WRONG_METRIC"
WRONG_DATE = "WRONG_DATE"
WRONG_FILTER = "WRONG_FILTER"
WRONG_RANKING = "WRONG_RANKING"
WRONG_COUNT = "WRONG_COUNT"
WRONG_TOTAL = "WRONG_TOTAL"
WRONG_RECORDS = "WRONG_RECORDS"
MISSING_INFORMATION = "MISSING_INFORMATION"
HALLUCINATED_INFORMATION = "HALLUCINATED_INFORMATION"
INCORRECT_SUMMARY = "INCORRECT_SUMMARY"
CONTRADICTS_DATABASE_RESULT = "CONTRADICTS_DATABASE_RESULT"
INCORRECT_ZERO_RESULT_HANDLING = "INCORRECT_ZERO_RESULT_HANDLING"
INCORRECT_FEWER_THAN_REQUESTED_HANDLING = "INCORRECT_FEWER_THAN_REQUESTED_HANDLING"
FORMAT_ERROR = "FORMAT_ERROR"
OTHER_RESPONSE_ERROR = "OTHER_RESPONSE_ERROR"

RESPONSE_FAILURE_CATEGORIES = [
    WRONG_ENTITY,
    WRONG_METRIC,
    WRONG_DATE,
    WRONG_FILTER,
    WRONG_RANKING,
    WRONG_COUNT,
    WRONG_TOTAL,
    WRONG_RECORDS,
    MISSING_INFORMATION,
    HALLUCINATED_INFORMATION,
    INCORRECT_SUMMARY,
    CONTRADICTS_DATABASE_RESULT,
    INCORRECT_ZERO_RESULT_HANDLING,
    INCORRECT_FEWER_THAN_REQUESTED_HANDLING,
    FORMAT_ERROR,
    OTHER_RESPONSE_ERROR,
]


class ResponseAccuracyValidator:
    """
    Dedicated Result-to-Response Validator.
    Compares the generated natural language response against:
    - Original user question
    - Business requirement contract (entities, metrics, filters, dates, limits)
    - Executed SQL
    - Actual database results (rows, columns, totals)
    
    Verifies factual consistency, truthful cardinality, zero-result handling,
    and classifies any failure into the standard 16 response accuracy categories.
    """

    def validate(
        self,
        question: str,
        requirement: Any,
        sql: str,
        execution_result: Dict[str, Any],
        final_response: str,
        expected: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        issues = []
        categories = []
        resp_lower = final_response.lower()

        rows = execution_result.get("data", []) or []
        row_count = len(rows)
        columns = execution_result.get("columns", []) or []

        # Helper to extract from either dict or BusinessRequirement object
        def _get_req(key: str, default: Any = None) -> Any:
            if not requirement:
                return default
            if isinstance(requirement, dict):
                return requirement.get(key, default)
            return getattr(requirement, key, default)

        # Extract requirements
        req_entities = _get_req("entities", [])
        req_metrics = _get_req("metrics", [])
        req_periods = _get_req("periods", [])
        req_limit = _get_req("limit", None)
        req_intent = _get_req("intent", "data_retrieval")
        is_ranking = bool(_get_req("ranking", None) or req_intent in ["ranking", "top_n"])
        is_comparison = bool(_get_req("comparison", False) or _get_req("comparisons", []))

        # 1. Zero-result handling
        if row_count == 0:
            zero_indicators = [
                "no qualifying", "no records", "no transactions", "not found",
                "0 records", "none found", "zero", "did not return any",
                "no distributors", "no retailers", "no users", "no data", "none are"
            ]
            has_zero_indicator = any(ind in resp_lower for ind in zero_indicators) or bool(
                re.search(r"\bno\s+\w+\s+(?:were|are|exist|was|found|recorded|registered)\b", resp_lower)
            )
            if not has_zero_indicator:
                issues.append("Response fails to clearly communicate that zero qualifying records were found.")
                categories.append(INCORRECT_ZERO_RESULT_HANDLING)

            # Check for invented records in zero-result cases
            invented_numbers = re.findall(r"₹\s*[\d,]+(?:\.\d+)?|\b\d+\s+(?:retailers|distributors|transactions)\b", final_response)
            if invented_numbers and not any("0" in n for n in invented_numbers):
                issues.append(f"Response invents quantities or amounts for an empty result: {invented_numbers}")
                categories.append(CONTRADICTS_DATABASE_RESULT)

        # 2. Fewer-than-requested results (Partial Top-N handling)
        if req_limit and 0 < row_count < req_limit:
            # Check if response clearly indicates the partial count
            has_partial_indicator = any(
                ind in resp_lower
                for ind in [
                    f"only {row_count}",
                    f"exactly {row_count}",
                    f"{row_count} qualifying",
                    f"{row_count} records were found",
                    f"{row_count} retailers were found",
                    f"{row_count} distributors were found"
                ]
            )

            # A false claim is explicitly presenting the list as the complete requested set without acknowledging fewer records
            false_claim_patterns = [
                rf"^here are the top\s+{req_limit}\b",
                rf"\bshowing all\s+{req_limit}\b",
                rf"\bthe top\s+{req_limit}\s+(?:retailers|distributors|users)\s+(?:are|earned)\b"
            ]
            has_false_claim = any(re.search(pat, resp_lower) for pat in false_claim_patterns)

            if has_false_claim and not has_partial_indicator:
                issues.append(f"Response incorrectly claims {req_limit} results when only {row_count} qualifying records were returned by the database.")
                categories.append(INCORRECT_FEWER_THAN_REQUESTED_HANDLING)
                categories.append(WRONG_COUNT)

            if not has_partial_indicator:
                issues.append(f"Response does not state that only {row_count} records were found (out of requested {req_limit}).")
                categories.append(INCORRECT_FEWER_THAN_REQUESTED_HANDLING)

        # 3. Entity consistency check
        ents_lower = [e.lower() for e in req_entities]
        if "distributor" in ents_lower and "retailer" not in ents_lower:
            if "retailer" in resp_lower and "distributor" not in resp_lower:
                issues.append("Response discusses retailers when distributors were requested.")
                categories.append(WRONG_ENTITY)
        elif "retailer" in ents_lower and "distributor" not in ents_lower:
            if "distributor" in resp_lower and "retailer" not in resp_lower:
                issues.append("Response discusses distributors when retailers were requested.")
                categories.append(WRONG_ENTITY)

        # 4. Period / Date consistency check
        if req_periods:
            for p in req_periods:
                p_clean = p.lower()
                month_name = p_clean.split()[0] if " " in p_clean else p_clean
                if month_name not in resp_lower and row_count > 0:
                    issues.append(f"Response omits the requested time period '{p}'.")
                    categories.append(WRONG_DATE)

        # 5. Database result factual consistency
        # Verify that numbers mentioned in response actually match returned data
        if row_count == 1 and len(columns) == 1:
            first_val = rows[0].get(columns[0])
            if isinstance(first_val, (int, float)):
                val_str = f"{first_val:.2f}" if isinstance(first_val, float) else str(first_val)
                val_int_str = str(int(first_val))
                # Check if this scalar value appears in response
                if val_int_str not in final_response and f"{first_val:,.2f}" not in final_response and f"{first_val:,.0f}" not in final_response:
                    issues.append(f"Response does not contain the database aggregate value {first_val}.")
                    categories.append(CONTRADICTS_DATABASE_RESULT)

        elif row_count > 0 and row_count <= 5:
            # Check for top record name in response
            first_row = rows[0]
            name_val = first_row.get("name") or first_row.get("retailer") or first_row.get("distributor_name") or first_row.get("retailer_name")
            if name_val and str(name_val).lower() not in resp_lower:
                issues.append(f"Response omits top qualifying entity '{name_val}'.")
                categories.append(MISSING_INFORMATION)

        # 6. Currency Symbol on Count / Box Scan Metrics
        is_box_scan = (_get_req("metric") == "box_scan_count") or any("box" in str(m).lower() or "scan" in str(m).lower() for m in req_metrics) or any(w in question.lower() for w in ["box scan", "box scans", "boxes"])
        if is_box_scan and "₹" in final_response:
            issues.append("Response adds currency symbol '₹' to a box count metric.")
            categories.append(FORMAT_ERROR)

        # 7. NULL values silently converted to 0
        if any(r.get(c) is None for r in rows for c in columns if any(m in c.lower() for m in ["amount", "earning", "total", "scan", "count"])):
            if "= 0" in final_response or "was 0" in final_response or "were 0" in final_response or "₹0.00" in final_response or "₹0 " in final_response or "was \u20b90" in final_response:
                issues.append("Response silently converts database NULL value into zero (0).")
                categories.append(CONTRADICTS_DATABASE_RESULT)

        # 8. Ranking Direction Consistency
        ranking_dir = _get_req("ranking_direction") or ("ASC" if any(w in question.lower() for w in ["lowest", "least", "bottom", "minimum"]) else "DESC")
        if ranking_dir == "ASC" and any(w in resp_lower for w in ["highest number", "most number", "ranked highest", "highest box"]):
            issues.append("Response claims 'highest' when lowest/minimum ranking was requested.")
            categories.append(WRONG_RANKING)
        elif ranking_dir == "DESC" and any(w in resp_lower for w in ["lowest number", "least number", "ranked lowest", "lowest box"]):
            issues.append("Response claims 'lowest' when highest/maximum ranking was requested.")
            categories.append(WRONG_RANKING)

        # 9. Period Comparison Value Reversal Check (Problem F)
        if is_comparison and row_count >= 1:
            period_col = next((c for c in columns if c.lower() in ["period", "month", "time_period"]), None)
            val_col = next((c for c in columns if any(m in c.lower() for m in ["earning", "amount", "total", "sum", "scan", "count"])), None)
            if period_col and val_col:
                for r in rows:
                    actual_p = str(r.get(period_col, "")).lower()
                    r_val = r.get(val_col)
                    if r_val is not None and isinstance(r_val, (int, float)):
                        for req_p in req_periods:
                            req_clean = req_p.split()[0].lower()
                            # If another period is mentioned in response right next to this row's value, check for reversal
                            if req_clean not in actual_p:
                                pat = rf"{re.escape(req_clean)}[^\n\.,]*?{r_val:,.2f}"
                                if re.search(pat, resp_lower):
                                    issues.append(f"Value reversal: Period '{req_p}' attributed with {r_val:,.2f} belonging to '{actual_p}'.")
                                    categories.append(CONTRADICTS_DATABASE_RESULT)
        prohibited_phrases = [
            "actionable business takeaways",
            "executive brief",
            "strategic recommendations",
            "top contributors across",
            "partner records analysis"
        ]
        for phrase in prohibited_phrases:
            if phrase in resp_lower and phrase not in question.lower():
                issues.append(f"Response contains ungrounded marketing template phrase '{phrase}'.")
                categories.append(HALLUCINATED_INFORMATION)

        is_valid = len(issues) == 0
        primary_category = categories[0] if categories else None

        return {
            "is_valid": is_valid,
            "issues": issues,
            "categories": categories,
            "primary_failure_category": primary_category,
            "evaluation_details": {
                "question": question,
                "row_count": row_count,
                "requested_limit": req_limit,
                "is_zero_result": row_count == 0,
                "is_partial_result": bool(req_limit and 0 < row_count < req_limit),
                "response_length": len(final_response)
            }
        }

response_accuracy_validator = ResponseAccuracyValidator()
