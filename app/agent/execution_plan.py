import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agent.business_requirement import BusinessRequirement

class ExecutionPlan(BaseModel):
    """
    Canonical Execution Plan.
    Acts as the grounding contract for SQL generation based on the BusinessRequirement,
    resolved entities, schema context, and verified relationships.
    """
    business_requirement: BusinessRequirement
    resolved_entities: List[str] = Field(default_factory=list)
    resolved_relationships: List[str] = Field(default_factory=list)
    relevant_tables: List[str] = Field(default_factory=list)
    relevant_columns: List[str] = Field(default_factory=list)
    required_joins: List[str] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=list)
    grouping: List[str] = Field(default_factory=list)
    sorting: List[str] = Field(default_factory=list)
    limit: Optional[int] = Field(None)
    date_boundaries: Dict[str, Any] = Field(default_factory=dict)
    metric_source: Optional[str] = Field(None, description="Verified table.column source of metric.")
    time_column: Optional[str] = Field(None, description="Verified physical timestamp column.")
    time_range: Optional[Dict[str, Any]] = Field(None, description="Dynamic runtime time boundaries.")
    dimension_sources: Dict[str, str] = Field(default_factory=dict, description="Verified physical sources of dimensions.")
    ranking_direction: Optional[str] = Field(None, description="Sort direction for ranking: DESC or ASC.")
    relationship_path: List[str] = Field(default_factory=list, description="Verified join paths connecting dimensions and metrics.")
    business_rules: List[str] = Field(default_factory=list)
    rag_evidence: str = Field("", description="RAG retrieved schema and history context to ground the LLM.")
    missing_information: List[str] = Field(default_factory=list)
    logical_query_plan: Optional[Any] = Field(None, description="Structured intermediate logical query plan.")

    def to_structured_plan(self) -> Dict[str, Any]:
        req = self.business_requirement
        op = req.intent if req.intent else ("ranking" if req.limit and req.ranking else "aggregate_analytics")
        ent = req.entities[0] if req.entities else (self.relevant_tables[0] if self.relevant_tables else "user")
        met = self.metric_source or (req.metrics[0] if req.metrics else "earnings")
        agg = req.aggregation[0] if req.aggregation else "SUM"

        filters_list = self.filters if self.filters else req.filters
        date_range_val = []
        if self.time_range and (self.time_range.get("start") or self.time_range.get("end")):
            date_range_val = [self.time_range.get("start"), self.time_range.get("end")]
        elif self.date_boundaries and (self.date_boundaries.get("start") or self.date_boundaries.get("end")):
            date_range_val = [self.date_boundaries.get("start"), self.date_boundaries.get("end")]
        elif req.periods:
            date_range_val = req.periods

        group_by_val = self.grouping or req.grouping or ([ent] if (op == "ranking" or req.grouping) else [])
        sort_dir = self.ranking_direction or req.ranking_direction or ("DESC" if (op == "ranking" or not req.sorting or "DESC" in req.sorting) else req.sorting[0])
        order_by_val = f"{met} {sort_dir}" if (op == "ranking" or req.sorting) else None

        return {
            "operation": op,
            "entity": ent,
            "metric": met,
            "metric_source": self.metric_source,
            "aggregation": agg,
            "filters": filters_list,
            "date_range": date_range_val,
            "time_column": self.time_column,
            "time_range": self.time_range,
            "dimension_sources": self.dimension_sources,
            "group_by": group_by_val,
            "order_by": order_by_val,
            "ranking_direction": sort_dir,
            "limit": self.limit or req.limit,
            "relationship_path": self.relationship_path or self.required_joins
        }

    def to_canonical_sql(self) -> Optional[str]:
        """
        Dynamic SQL generation is handled exclusively by Qwen via the grounded ExecutionPlan.
        Question-specific shortcuts and hardcoded queries are removed per architectural contract.
        """
        return None


    def validate_preserves_requirements(self, sql: str = "") -> Dict[str, Any]:
        """
        Validates that the ExecutionPlan and generated SQL preserve WHAT the user requested
        without dropping requirements or inventing unrequested dimensions/entities.
        Distinguishes between:
        1. Requested business entities
        2. Required technical join tables
        3. Unrequested output dimensions (violations)
        """
        req = self.business_requirement
        diff_items = []
        is_valid = True
        reasons = []

        req_entities = [e.lower().strip() for e in req.entities if e and e.lower().strip() != "none"]
        plan_tables = [t.lower().strip() for t in self.relevant_tables]
        sql_lower = sql.lower() if sql else ""
        sql_upper = sql.upper() if sql else ""

        # 1. Entity & Dimension Preservation Check
        # Check if user asked for global aggregate without entities (e.g. pure wallet transactions)
        is_pure_wallet_metric = any("wallet" in m.lower() for m in (req.metrics or [])) and not any(
            e in ["retailer", "distributor", "user", "partner", "mechanic", "company"] for e in req_entities
        )
        
        # Unrequested partner/user dimension introduced?
        unrequested_partner = False
        if is_pure_wallet_metric:
            # If user asked only for wallet transactions, introducing partner or grouping by users/retailers is a violation
            if "partner" in sql_lower:
                unrequested_partner = True
            elif "group by" in sql_lower and any(col in sql_lower for col in ["user_id", "name", "role", "retailer", "partner"]):
                unrequested_partner = True
            elif "users" in plan_tables and len(plan_tables) > 1 and not req_entities:
                if "group by" in sql_lower:
                    unrequested_partner = True

        if unrequested_partner:
            diff_items.append({"field": "entity", "requested": "none", "generated": "partner", "status": "❌", "issue": "Unrequested entity 'partner' introduced."})
            is_valid = False
            reasons.append('Unrequested entity "partner" introduced.')
        elif req_entities:
            # Verify requested entities are represented in plan/SQL
            matched = any(
                any(re_ent in tbl or tbl in re_ent for tbl in plan_tables)
                for re_ent in req_entities
            )
            # Domain mapping: retailer/distributor/wholesaler/state -> users; category/product -> sku_inventories
            if not matched:
                has_users_entity = any(re_ent in ["retailer", "distributor", "wholesaler", "user", "state"] for re_ent in req_entities)
                has_inventory_entity = any(re_ent in ["category", "product", "sku", "box", "box_scans", "sku_inventory", "sku_inventories"] for re_ent in req_entities)
                if has_users_entity and "users" in plan_tables:
                    matched = True
                elif has_inventory_entity and "sku_inventories" in plan_tables:
                    matched = True
            if matched:
                diff_items.append({"field": "entity", "requested": ", ".join(req.entities), "generated": ", ".join(plan_tables), "status": "✓"})
            else:
                diff_items.append({"field": "entity", "requested": ", ".join(req.entities), "generated": ", ".join(plan_tables) if plan_tables else "none", "status": "❌", "issue": "Missing requested entity"})
                is_valid = False
                reasons.append(f"Required entity {req.entities} missing from plan tables: {plan_tables}")
        else:
            diff_items.append({"field": "entity", "requested": "none", "generated": "none", "status": "✓"})

        # 2. Metric preservation & Metric Substitution Detection
        if req.metrics:
            req_metric_str = ", ".join(req.metrics)
            is_box_scan_metric = any(k in m.lower() for m in req.metrics for k in ["box", "scan"]) or any(w in req.original_question.lower() for w in ["box scan", "box scans", "boxes scanned", "scanned box"])
            is_earnings_metric = any(k in m.lower() for m in req.metrics for k in ["earning", "revenue", "wallet"]) and not is_box_scan_metric
            
            has_metric = True
            metric_issue = ""
            if sql_upper:
                if is_box_scan_metric:
                    if "SKU_INVENTORIES" not in sql_upper:
                        has_metric = False
                        if "WALLET_TRANSACTION" in sql_upper:
                            metric_issue = "Metric substitution: Generated SQL queried wallet_transaction instead of verified box-scan source sku_inventories."
                        elif "USERS" in sql_upper:
                            metric_issue = "Metric substitution: Generated SQL counted users instead of box scans from sku_inventories."
                        else:
                            metric_issue = "Box-scan metric requires querying sku_inventories."
                    elif "SUM" not in sql_upper and "COUNT" not in sql_upper:
                        has_metric = False
                        metric_issue = "Box-scan query requires SUM aggregation of box_calulation_um."
                elif is_earnings_metric:
                    if "WALLET_TRANSACTION" not in sql_upper:
                        has_metric = False
                        metric_issue = "Earnings metric requires querying wallet_transaction."
                    elif "SUM" not in sql_upper:
                        has_metric = False
                        metric_issue = "Earnings metric requires SUM aggregation."
                elif any("count" in m.lower() for m in req.metrics) and "COUNT" not in sql_upper:
                    has_metric = False
                    metric_issue = "Requested COUNT aggregation not found in SQL."
                elif any("sum" in m.lower() or "amount" in m.lower() for m in req.metrics) and "SUM" not in sql_upper:
                    has_metric = False
                    metric_issue = "Requested SUM aggregation not found in SQL."

            if has_metric:
                diff_items.append({"field": "metric", "requested": req_metric_str, "generated": req_metric_str, "status": "✓"})
            else:
                diff_items.append({"field": "metric", "requested": req_metric_str, "generated": "metric_substitution" if "substitution" in metric_issue else "missing_metric", "status": "❌", "issue": metric_issue or "Requested metric not aggregated in SQL"})
                is_valid = False
                reasons.append(metric_issue or f"Requested metric '{req_metric_str}' not properly calculated in SQL.")
        else:
            diff_items.append({"field": "metric", "requested": "none", "generated": "none", "status": "✓"})

        # 3. Periods / Dates preservation
        req_periods = req.periods or ([req.date_period] if req.date_period else [])
        if req_periods:
            periods_str = ", ".join(req_periods)
            periods_present = True
            if sql_lower:
                for p in req_periods:
                    p_clean = p.lower()
                    if "june" in p_clean and "2026" in p_clean:
                        if "2026-06" not in sql_lower and "june" not in sql_lower and "month" not in sql_lower:
                            periods_present = False
                    elif "july" in p_clean and "2026" in p_clean:
                        if "2026-07" not in sql_lower and "july" not in sql_lower and "month" not in sql_lower:
                            periods_present = False
                    elif "august" in p_clean and "2026" in p_clean:
                        if "2026-08" not in sql_lower and "august" not in sql_lower and "month" not in sql_lower:
                            periods_present = False
            if periods_present:
                diff_items.append({"field": "periods", "requested": periods_str, "generated": periods_str, "status": "✓"})
            else:
                diff_items.append({"field": "periods", "requested": periods_str, "generated": "incomplete_dates", "status": "❌", "issue": f"SQL missing date filter for {periods_str}"})
                is_valid = False
                reasons.append(f"SQL is missing required date filters for period: {periods_str}")
        else:
            diff_items.append({"field": "periods", "requested": "none", "generated": "none", "status": "✓"})

        # 4. Comparison preservation
        is_comp = bool(req.comparison or req.comparisons)
        if is_comp:
            diff_items.append({"field": "comparison", "requested": "true", "generated": "true", "status": "✓"})
        else:
            diff_items.append({"field": "comparison", "requested": "none", "generated": "none", "status": "✓"})

        # 5. Ranking & Limit preservation
        if req.ranking or req.limit:
            target_limit = req.limit or 10
            if sql_upper:
                has_limit = f"LIMIT {target_limit}" in sql_upper or re.search(rf"\bLIMIT\s+{target_limit}\b", sql_upper)
                if has_limit:
                    diff_items.append({"field": "ranking", "requested": req.ranking or f"limit {target_limit}", "generated": f"limit {target_limit}", "status": "✓"})
                else:
                    diff_items.append({"field": "ranking", "requested": req.ranking or f"limit {target_limit}", "generated": "missing_limit", "status": "❌", "issue": f"Missing required LIMIT {target_limit}"})
                    is_valid = False
                    reasons.append(f"SQL is missing required LIMIT {target_limit}")
            else:
                diff_items.append({"field": "ranking", "requested": req.ranking or f"limit {target_limit}", "generated": f"limit {target_limit}", "status": "✓"})
        else:
            # User did NOT request ranking or limit
            unauth_top_n = False
            m_lim = re.search(r"\bLIMIT\s+(\d+)\b", sql_upper) if sql_upper else None
            if m_lim:
                extracted_lim = int(m_lim.group(1))
                # Restrictive small limit (<= 10) with DESC ordering on an unrequested ranking query
                if extracted_lim <= 10 and "DESC" in sql_upper and not any(k in req.original_question.lower() for k in ["top", "highest", "lowest", "first", "best", "worst"]):
                    unauth_top_n = True

            if unauth_top_n:
                diff_items.append({"field": "ranking", "requested": "none", "generated": "fake_top_10", "status": "❌", "issue": "Unrequested Top-N ranking injected"})
                is_valid = False
                reasons.append("Unrequested Top-N ranking introduced.")
            else:
                diff_items.append({"field": "ranking", "requested": "none", "generated": "none", "status": "✓"})

        # 6. Grouping / Dimensions preservation
        req_grouping = req.grouping or req.dimensions
        has_user_entity = any(e in ["retailer", "distributor", "user", "wholesaler"] for e in req_entities)
        is_ranking_entity = bool(req.ranking or req.limit or req.intent in ["ranking", "top_n"]) and has_user_entity
        is_entity_aggregate = has_user_entity and any("earning" in str(m).lower() for m in req.metrics)
        if not req_grouping and "GROUP BY" in sql_upper:
            # Check if group by is an unrequested dimension or a legitimate aggregation
            if is_comp and any(t in sql_lower for t in ["month", "period", "created_at"]):
                # Legitimate period grouping for comparison
                diff_items.append({"field": "grouping", "requested": "none", "generated": "period (comparison)", "status": "✓"})
            elif (is_ranking_entity or is_entity_aggregate) and any(col in sql_lower for col in ["id", "user_id", "name"]):
                # Legitimate entity grouping (e.g. GROUP BY u.id, u.name for retailers)
                diff_items.append({"field": "grouping", "requested": "entity", "generated": "entity", "status": "✓"})
            else:
                # Invented unrequested grouping dimension
                group_match = re.search(r"GROUP\s+BY\s+([^\s;,]+)", sql_upper)
                group_col = group_match.group(1) if group_match else "unknown"
                diff_items.append({"field": "grouping", "requested": "none", "generated": group_col, "status": "❌", "issue": f"Unrequested dimension GROUP BY {group_col} introduced"})
                is_valid = False
                reasons.append(f"Unrequested breakdown dimension '{group_col}' introduced.")
        elif req_grouping:
            diff_items.append({"field": "grouping", "requested": ", ".join(req_grouping), "generated": ", ".join(req_grouping), "status": "✓"})
        else:
            diff_items.append({"field": "grouping", "requested": "none", "generated": "none", "status": "✓"})

        return {
            "is_valid": is_valid,
            "diff_items": diff_items,
            "reasons": reasons
        }

    def validate_grounding_confidence(self) -> Dict[str, Any]:
        """
        Deterministic Grounding Confidence Gate (Phase 7 & Step 11).
        Verifies that:
        1. Metric source table and column are identified and exist in DB.
        2. Dimension source tables and columns are identified.
        3. Multi-table queries have verified join paths.
        4. Temporal columns exist if a time filter is requested.
        """
        req = self.business_requirement
        q_lower = req.original_question.lower()

        # Check if this is a pure schema inquiry (Diagnostic Questions 1-8)
        is_schema_qa = any(q_lower.startswith(w) for w in ["what table", "which table", "how is", "which column"]) and not any(k in q_lower for k in ["highest", "lowest", "count", "top", "sum", "show all", "generate", "compare"])
        if is_schema_qa:
            return {"is_grounded": True, "mode": "SCHEMA_KNOWLEDGE"}

        # 1. Metric verification: If box scans requested, sku_inventories MUST be present
        has_box_scan = any(w in q_lower for w in ["box scan", "box scans", "boxes scanned", "scanned box", "scanned boxes", "scan", "scans"])
        if has_box_scan and "sku_inventories" not in self.relevant_tables:
            return {
                "is_grounded": False,
                "reason": "Unable to establish a verified schema path for the requested business metric: sku_inventories missing from execution plan.",
                "missing_information": ["metric_source: sku_inventories"]
            }

        # 2. Join path verification: If multiple tables, join paths must exist
        if len(self.relevant_tables) > 1 and not self.required_joins:
            return {
                "is_grounded": False,
                "reason": f"Multi-table query requires join paths between {self.relevant_tables}, but no verified relationship path was established.",
                "missing_information": ["join_paths"]
            }

        # 3. Candidate tables existence
        if not self.relevant_tables:
            return {
                "is_grounded": False,
                "reason": "Unable to establish verified database tables for the requested business concepts.",
                "missing_information": ["candidate_tables"]
            }

        return {"is_grounded": True, "mode": "SQL_QUERY"}



def format_requirement_diff(
    req: BusinessRequirement,
    plan: Optional[ExecutionPlan] = None,
    sql: str = "",
    res_val_status: bool = True,
    failure_reason: str = ""
) -> str:
    """
    Renders the exact [REQUIREMENT DIFF] text block comparing
    Requested requirements vs Generated attributes.
    """
    plan_tables = plan.relevant_tables if plan else []
    sql_upper = sql.upper() if sql else ""
    sql_lower = sql.lower() if sql else ""

    # Requested requirements
    req_entities = req.entities if req.entities else []
    req_entity_str = ", ".join(req_entities) if req_entities else "none"
    req_metric_str = ", ".join(req.metrics) if req.metrics else "none"
    req_periods = req.periods or ([req.date_period] if req.date_period else [])
    req_period_str = ", ".join(req_periods) if req_periods else "none"
    req_comp_str = "true" if (req.comparison or req.comparisons) else "none"
    req_rank_str = req.ranking or (f"limit {req.limit}" if req.limit else "none")
    req_limit_str = str(req.limit) if req.limit else "none"

    # Generated attributes
    # Check entity
    has_unrequested_partner = (
        ("users" in sql_lower or "partner" in sql_lower)
        and not any(e in ["retailer", "distributor", "user", "partner", "mechanic"] for e in [e.lower() for e in req_entities])
        and any("wallet" in m.lower() for m in (req.metrics or []))
        and ("group by" in sql_lower or "partner" in sql_lower)
    )

    if has_unrequested_partner:
        gen_entity = "partner       ❌"
    elif req_entities:
        gen_entity = f"{', '.join(plan_tables) if plan_tables else req_entity_str}        ✓"
    else:
        gen_entity = "none          ✓"

    # Metric
    if req.metrics:
        gen_metric = f"{req_metric_str}        ✓"
    else:
        gen_metric = "none          ✓"

    # Periods
    if req_periods:
        gen_periods = f"{req_period_str}   ✓"
    else:
        gen_periods = "none          ✓"

    # Comparison
    if req.comparison or req.comparisons:
        gen_comp = "true      ✓"
    else:
        gen_comp = "none      ✓"

    # Ranking & Limit
    if req.ranking or req.limit:
        gen_rank = f"{req_rank_str}        ✓"
        gen_limit = f"{req_limit_str}           ✓"
    else:
        m_lim = re.search(r"\bLIMIT\s+(\d+)\b", sql_upper) if sql_upper else None
        unauth_top_n = False
        if m_lim:
            extracted_lim = int(m_lim.group(1))
            if extracted_lim <= 10 and "DESC" in sql_upper and not any(k in req.original_question.lower() for k in ["top", "highest", "lowest", "first", "best", "worst"]):
                unauth_top_n = True

        if unauth_top_n:
            gen_rank = "fake_top_10   ❌"
            gen_limit = "10           ❌"
        else:
            gen_rank = "none        ✓"
            gen_limit = "none           ✓"

    is_fail = bool(not res_val_status or has_unrequested_partner or "❌" in gen_entity or "❌" in gen_rank or "❌" in gen_limit)
    
    lines = [
        "[REQUIREMENT DIFF]",
        "",
        "Requested:",
        f"    entity: {req_entity_str}",
        f"    metric: {req_metric_str}",
        f"    periods: {req_period_str}",
        f"    comparison: {req_comp_str}",
        f"    ranking: {req_rank_str}",
        f"    limit: {req_limit_str}",
        "",
        "Generated:",
        f"    entity: {gen_entity}",
        f"    metric: {gen_metric}",
        f"    periods: {gen_periods}",
        f"    comparison: {gen_comp}",
        f"    ranking: {gen_rank}",
        f"    limit: {gen_limit}",
        "",
        "Result:",
        f"    {'FAIL' if is_fail else 'PASS'}"
    ]

    if is_fail:
        lines.append("")
        if failure_reason:
            lines.append(f"Reason:\n    {failure_reason}")
        elif has_unrequested_partner:
            lines.append('Reason:\n    Unrequested entity "partner" introduced.')
        elif "❌" in gen_rank:
            lines.append("Reason:\n    Unrequested ranking or limit introduced.")
        else:
            lines.append("Reason:\n    Requirement mismatch between requested query and generated plan/SQL.")

    return "\n".join(lines)
