import json
import logging
import re
from typing import Dict, Any, List, Optional
from app.agent.execution_plan import ExecutionPlan
from app.knowledge.business_rule_index import get_selective_business_rules

logger = logging.getLogger(__name__)

class SemanticValidationError(Exception):
    pass

def evaluate_semantic_sql(query: str, plan: ExecutionPlan) -> Dict[str, Any]:
    """
    Stage 6 Semantic SQL Verification (Section 8).
    Strictly verifies that the generated SQL satisfies:
    - entity_correct
    - metric_correct
    - date_correct
    - aggregation_correct
    - business_rule_correct
    - grouping_correct
    - ordering_correct
    - limit_correct
    """
    if not query or not plan:
        return {
            "is_semantically_correct": True,
            "issues": [],
            "checks": {
                "entity_correct": True,
                "metric_correct": True,
                "date_correct": True,
                "aggregation_correct": True,
                "business_rule_correct": True,
                "grouping_correct": True,
                "ordering_correct": True,
                "limit_correct": True
            }
        }

    q_upper = query.upper()
    q_lower = query.lower()
    req = plan.business_requirement
    issues: List[str] = []
    checks = {
        "entity_correct": True,
        "metric_correct": True,
        "date_correct": True,
        "aggregation_correct": True,
        "business_rule_correct": True,
        "grouping_correct": True,
        "ordering_correct": True,
        "limit_correct": True
    }

    req_ents = [e.lower() for e in (req.entities or [])]
    req_mets = [m.lower() for m in (req.metrics or [])]

    # 1. Entity & Business Rule Correctness
    has_retailer = "retailer" in req_ents
    has_distributor = "distributor" in req_ents
    has_wholesaler = "wholesaler" in req_ents

    if has_retailer and has_distributor:
        # Both entities involved (e.g. distributor by retailer box scans, or combination queries)
        if "USER_ROLE" in q_upper and not any(r in query for r in ["= 2", "=2", "= 4", "=4"]):
            checks["entity_correct"] = False
            checks["business_rule_correct"] = False
            issues.append("Query targets retailer/distributor but does not filter valid user_role (2 or 4)")
    elif has_retailer:
        if "USER_ROLE" in q_upper and "= 2" not in query and "=2" not in query:
            checks["entity_correct"] = False
            checks["business_rule_correct"] = False
            issues.append("Query targets retailer but does not filter user_role = 2")
    elif has_distributor:
        if "USER_ROLE" in q_upper and "= 4" not in query and "=4" not in query:
            checks["entity_correct"] = False
            checks["business_rule_correct"] = False
            issues.append("Query targets distributor but does not filter user_role = 4")
    elif has_wholesaler:
        if "USER_ROLE" in q_upper and "= 5" not in query and "=5" not in query:
            checks["entity_correct"] = False
            checks["business_rule_correct"] = False
            issues.append("Query targets wholesaler but does not filter user_role = 5")

    # Earnings business rule: credit amounts > 0 or transaction_type = 1
    if any("earning" in m for m in req_mets) or "earning" in (getattr(req, "original_question", "") or "").lower():
        if "AMOUNT" in q_upper:
            has_positive_rule = ("AMOUNT > 0" in q_upper or "AMOUNT>0" in q_upper or
                                 "TRANSACTION_TYPE = 1" in q_upper or "TRANSACTION_TYPE=1" in q_upper or
                                 "REFERENCE_TYPE" in q_upper)
            if not has_positive_rule:
                checks["business_rule_correct"] = False
                issues.append("Earnings queries must filter positive credit amounts (amount > 0 or transaction_type = 1)")

    # 2. Metric Source Correctness (Requirement 6)
    is_box_scan = (req.metric == "box_scan_count") or (getattr(req, "metric_source", None) and ("sku_inventories" in str(req.metric_source) or "qr_point_map" in str(req.metric_source))) or any("box" in m or "scan" in m for m in req_mets) or any(w in (getattr(req, "original_question", "") or "").lower() for w in ["box", "scan", "boxes"])
    if is_box_scan and not any(w in (getattr(req, "original_question", "") or "").lower() for w in ["earning", "earnings", "wallet", "balance"]):
        if "sku_inventories" not in q_lower:
            checks["metric_correct"] = False
            issues.append("METRIC_SOURCE_MISMATCH: Metric 'box_scan_count' requires table 'sku_inventories', but query used an incorrect table")
        if "wallet_transaction" in q_lower:
            checks["metric_correct"] = False
            issues.append("METRIC_SOURCE_MISMATCH: Metric substitution detected! Box scans must query 'sku_inventories', not 'wallet_transaction'")
        if any(c in q_upper for c in ["COUNT(SI.ID)", "COUNT(SKU_INVENTORIES.ID)", "COUNT( SI.ID )", "COUNT( SKU_INVENTORIES.ID )"]):
            checks["metric_correct"] = False
            issues.append("BUSINESS_RULE_MISMATCH: Authoritative JGH box quantity is SUM(qr_point_map.box_calulation_um), NEVER COUNT(sku_inventories.id)")
        if "qr_point_map" not in q_lower and "sku_qr_points_map" not in q_lower and "box_calulation_um" not in q_lower:
            checks["metric_correct"] = False
            issues.append("METRIC_SOURCE_MISMATCH: Box scans must join 'qr_point_map' on sku_code and calculate SUM(qr_point_map.box_calulation_um)")

    if any("earning" in m for m in req_mets):
        if "AMOUNT" not in q_upper and "SUM(" not in q_upper:
            checks["metric_correct"] = False
            issues.append("Earnings metric requested but amount column is missing")
        if "wallet_transaction" not in q_lower:
            checks["metric_correct"] = False
            issues.append("METRIC_SOURCE_MISMATCH: Metric 'earnings' requires table 'wallet_transaction', but query used an incorrect table")

    # 3. Aggregation Correctness
    if req.aggregation and any("SUM" in a.upper() for a in req.aggregation):
        if "SUM(" not in q_upper and "SUM (" not in q_upper:
            checks["aggregation_correct"] = False
            issues.append("SUM aggregation requested, but SUM() is missing from query")
    elif req.aggregation and any("COUNT" in a.upper() for a in req.aggregation):
        if "COUNT(" not in q_upper and "COUNT (" not in q_upper and "SUM(" not in q_upper and "SUM (" not in q_upper:
            checks["aggregation_correct"] = False
            issues.append("COUNT aggregation requested, but COUNT() or conditional SUM() is missing from query")
    elif req.aggregation and any("AVG" in a.upper() for a in req.aggregation):
        if "AVG(" not in q_upper and "AVG (" not in q_upper:
            checks["aggregation_correct"] = False
            issues.append("AVG aggregation requested, but AVG() is missing from query")

    # 4. Temporal Source & Date Correctness (Requirement 7)
    has_time_requirement = bool(req.date_period or req.periods or getattr(req, "time_range", None) or any(w in (getattr(req, "original_question", "") or "").lower() for w in ["this month", "last month", "current month", "month", "2026"]))
    if is_box_scan and has_time_requirement:
        if "retailer_scanned_at" not in q_lower and "wholesaler_scanned_at" not in q_lower:
            checks["date_correct"] = False
            issues.append("TEMPORAL_SOURCE_MISMATCH: Box scan temporal filtering must use 'retailer_scanned_at', not 'created_at'")
        if "users.created_at" in q_lower or "u.created_at" in q_lower:
            checks["date_correct"] = False
            issues.append("TEMPORAL_SOURCE_MISMATCH: Cannot filter user registration 'users.created_at' when box scan event timestamp 'retailer_scanned_at' is requested")

    p_raw = (req.date_period or (req.periods[0] if req.periods else "")).lower()
    if p_raw:
        month_patterns = {
            "july 2026": ["2026-07", "MONTH", "7"],
            "june 2026": ["2026-06", "MONTH", "6"],
            "august 2026": ["2026-08", "MONTH", "8"],
            "may 2026": ["2026-05", "MONTH", "5"],
            "april 2026": ["2026-04", "MONTH", "4"],
            "march 2026": ["2026-03", "MONTH", "3"],
            "february 2026": ["2026-02", "MONTH", "2"],
            "january 2026": ["2026-01", "MONTH", "1"],
        }
        for p_name, indicators in month_patterns.items():
            if p_name in p_raw:
                has_date_match = any(ind in query or ind in q_upper for ind in indicators)
                if not has_date_match:
                    checks["date_correct"] = False
                    issues.append(f"Timeframe '{p_raw}' requested, but query lacks date filtering for this period")
                break

    # 5. Grouping & Ranking Correctness (Requirement 5)
    is_ranking = bool(getattr(req, "ranking_direction", None) or req.ranking or (req.intent and "ranking" in req.intent.lower()) or req.limit or any(w in (getattr(req, "original_question", "") or "").lower() for w in ["highest", "lowest", "top", "bottom", "most", "least"]))
    if is_ranking:
        if "ORDER BY" not in q_upper:
            checks["ordering_correct"] = False
            issues.append("RANKING_REQUIREMENT_MISMATCH: Ranking query requires an ORDER BY clause")
        else:
            is_bottom = (getattr(req, "ranking_direction", "") == "ASC" or (req.ranking and "bottom" in str(req.ranking).lower()) or any(w in (getattr(req, "original_question", "") or "").lower() for w in ["lowest", "least", "bottom", "minimum"]))
            if is_bottom:
                if "DESC" in q_upper and "ASC" not in q_upper:
                    checks["ordering_correct"] = False
                    issues.append("RANKING_REQUIREMENT_MISMATCH: Lowest/minimum ranking query requires ORDER BY ... ASC (found DESC)")
            else:
                if "ORDER BY" in q_upper and "DESC" not in q_upper and "ASC" in q_upper:
                    checks["ordering_correct"] = False
                    issues.append("RANKING_REQUIREMENT_MISMATCH: Highest/top ranking query requires ORDER BY ... DESC (found ASC)")

        # Limit enforcement for ranking
        expected_limit = getattr(req, "ranking_limit", None) or req.limit or (1 if any(w in (getattr(req, "original_question", "") or "").lower() for w in ["highest", "lowest", "most", "least"]) else None)
        if expected_limit:
            if not re.search(rf"\bLIMIT\s+{expected_limit}\b", q_upper):
                checks["limit_correct"] = False
                issues.append(f"RANKING_REQUIREMENT_MISMATCH: Missing required LIMIT {expected_limit}")

        # Group By check for entity/dimension ranking
        if len(req_ents) > 0 or len(getattr(req, "dimensions", []) or []) > 0:
            if "GROUP BY" not in q_upper:
                checks["grouping_correct"] = False
                issues.append("RANKING_REQUIREMENT_MISMATCH: Entity/dimension ranking query requires GROUP BY identifier")

    # Pure scalar check: if global scalar total requested without entities, GROUP BY should not be present
    if req.query_type == "scalar" and not req_ents and not getattr(req, "dimensions", []) and not req.grouping:
        if "GROUP BY" in q_upper and "LIMIT" not in q_upper:
            checks["grouping_correct"] = False
            issues.append("Global scalar query should not include GROUP BY")

    # Specific IDs Check
    for id_k, id_v in (req.specific_ids or {}).items():
        if str(id_v) not in query:
            checks["entity_correct"] = False
            issues.append(f"Missing filter for specific ID {id_k} = {id_v}")

    is_correct = len(issues) == 0 and all(checks.values())

    return {
        "is_semantically_correct": is_correct,
        "checks": checks,
        "issues": issues
    }


def validate_semantic_sql(query: str, plan: ExecutionPlan) -> bool:
    """
    Validates semantic correctness and raises SemanticValidationError if failed.
    """
    res = evaluate_semantic_sql(query, plan)
    if not res["is_semantically_correct"]:
        err_msg = "; ".join(res["issues"])
        logger.warning(f"[SEMANTIC VALIDATION REJECTED]: {err_msg}")
        raise SemanticValidationError(err_msg)
    return True
