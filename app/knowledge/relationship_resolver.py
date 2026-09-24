import json
import logging
import os
import re
from typing import Dict, Any, List, Optional

from app.agent.business_requirement import BusinessRequirement
from app.agent.execution_plan import ExecutionPlan
from app.agent.logical_plan import build_logical_query_plan
from app.knowledge.value_linker import value_linker
from app.knowledge.semantic_metadata import (
    BUSINESS_SEMANTIC_METADATA,
    find_metric_source,
    find_dimension_source,
    calculate_dynamic_time_range,
    get_semantic_schema_context
)

from app.retriever.retriever import retrieve_schema

logger = logging.getLogger(__name__)

class RelationshipResolver:
    """
    Dynamic Schema & Relationship Grounding Engine.
    Dynamically identifies:
    1. Metric source table and column (e.g. sku_inventories for box scans, wallet_transaction for earnings)
    2. Dimension source table and column (e.g. users for retailer/distributor/state, sku_inventories for category)
    3. Physical foreign-key join paths connecting dimensions to metrics
    4. Deterministic business rules and filtering constraints
    """

    def resolve(self, req: BusinessRequirement) -> ExecutionPlan:
        plan = ExecutionPlan(
            business_requirement=req,
            filters=req.filters,
            metrics=req.metrics,
            aggregations=req.aggregation,
            grouping=req.grouping,
            sorting=req.sorting,
            limit=req.limit
        )

        # 1. Link Database Values (State IDs, Role IDs, Specific IDs, Date Boundaries)
        linked_values = value_linker.link_values(req.original_question, req.entities)
        if linked_values.get("date_range"):
            plan.date_boundaries = linked_values["date_range"]

        # 2. Retrieve grounded schema context
        search_terms = f"{req.original_question} {' '.join(req.entities)}"
        context = retrieve_schema(search_terms, k=5)
        plan.rag_evidence = context

        # 3. Dynamic Business Semantic Grounding
        try:
            req_ents = [e.lower() for e in (req.entities or [])]
            req_mets = [m.lower() for m in (req.metrics or [])]
            q_text = (getattr(req, "raw_question", "") or getattr(req, "original_question", "")).lower()

            resolved_tables: List[str] = []
            resolved_joins: List[str] = []
            resolved_entities: List[str] = []
            business_rules: List[str] = []

            # A. Identify Metric Concept & Source Table
            metric_concept = req.metric if req.metric else (req_mets[0] if req_mets else "")
            metric_info = find_metric_source(metric_concept) if metric_concept else None

            # Fallback if metric was not parsed in req_mets but mentioned in question
            if not metric_info:
                if any(w in q_text for w in [
                    "box scan", "box scans", "boxes scanned", "scanned box", "scanned boxes",
                    "scanned", "box", "boxes", "scan", "scans", "retailer scans", "retailer scan"
                ]):
                    metric_info = find_metric_source("box_scans")
                elif any(w in q_text for w in ["earning", "earnings", "earned", "revenue"]):
                    metric_info = find_metric_source("earnings")
                elif "balance" in q_text:
                    metric_info = find_metric_source("wallet balance")

            is_box_scan = bool(req.metric == "box_scan_count" or (metric_info and metric_info.get("table") == "sku_inventories"))
            is_earnings = bool(req.metric == "earnings" or (metric_info and metric_info.get("table") == "wallet_transaction"))
            is_wallet_balance = bool(metric_info and metric_info.get("table") == "users")

            # Ground metric and temporal specifications
            if metric_info:
                req.metric = metric_info.get("metric", "unknown_metric")
                req.metric_source = metric_info.get("metric_source", f"{metric_info.get('table')}.{metric_info.get('column')}")
                req.time_column = metric_info.get("temporal_column")
                plan.metric_source = req.metric_source
                plan.time_column = req.time_column

            # Dynamic Time Range Calculation
            p_raw = req.date_period or (req.periods[0] if req.periods else None) or req.original_question
            time_range_obj = calculate_dynamic_time_range(p_raw)
            req.time_range = time_range_obj
            plan.time_range = time_range_obj
            plan.date_boundaries = {"start": time_range_obj["start"], "end": time_range_obj["end"]}

            # Check if mapping relationship is requested
            has_mapping = any(w in q_text for w in ["map", "mapping", "mapped", "linked", "assigned", "under"]) or ("distributor" in q_text and "retailer" in q_text)
            has_companies = any(e in ["company", "companies"] for e in req_ents) or any(w in q_text for w in ["company", "companies"])
            is_comparison = any(w in q_text for w in ["versus", "vs", "compare", "comparison"])

            # Detect dimensions and dimension sources
            has_retailer = any(e in ["retailer", "retailers"] for e in req_ents) or "retailer" in q_text
            has_distributor = any(e in ["distributor", "distributors"] for e in req_ents) or "distributor" in q_text
            has_state = any(e in ["state", "states", "region"] for e in req_ents) or "state" in q_text
            has_category = any(e in ["category", "categories"] for e in req_ents) or "category" in q_text

            dimension_sources = {}
            if has_retailer:
                dimension_sources["retailer"] = "users.id"
            if has_distributor:
                dimension_sources["distributor"] = "users.id"
            if has_state:
                dimension_sources["state"] = "users.state_id"
            if has_category:
                dimension_sources["category"] = "sku_inventories.sku_description"
            if has_companies:
                dimension_sources["company"] = "companies.id"

            req.dimension_sources = dimension_sources
            plan.dimension_sources = dimension_sources

            # Ranking Direction & Limits
            is_ranking = bool(req.ranking or req.limit or any(w in q_text for w in ["highest", "lowest", "top", "bottom", "most", "least", "minimum", "maximum", "fewest"]))
            if is_ranking:
                is_lowest = any(w in q_text for w in ["lowest", "least", "bottom", "minimum", "fewest"])
                req.ranking_direction = "ASC" if is_lowest else "DESC"
                req.ranking_limit = req.limit or 1
                plan.ranking_direction = req.ranking_direction
                plan.sorting = [req.ranking_direction]
                if not req.limit:
                    req.limit = 1
                    plan.limit = 1

            # B. Ground Tables & Relationships
            if is_box_scan:
                if "sku_inventories" not in resolved_tables:
                    resolved_tables.append("sku_inventories")
                if "qr_point_map" not in resolved_tables:
                    resolved_tables.append("qr_point_map")
                resolved_joins.append("sku_inventories JOIN qr_point_map ON sku_inventories.sku_code = qr_point_map.sku_code")
                business_rules.append("JGH BOX QUANTITY: Authoritative calculation is SUM(qr_point_map.box_calulation_um) joined on sku_inventories.sku_code = qr_point_map.sku_code. NEVER use COUNT(sku_inventories.id) as box quantity.")
                business_rules.append("Date filter: Filter scan event timestamp using sku_inventories.retailer_scanned_at (half-open interval: >= start AND < next_period_start).")

                if has_category and has_state:
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                    if "state" not in resolved_tables:
                        resolved_tables.append("state")
                    resolved_joins.append("sku_inventories JOIN users ON sku_inventories.status_retailer_id = users.id")
                    resolved_joins.append("users JOIN state ON users.state_id = state.id")
                    resolved_entities.append("category -> sku_inventories.sku_description")
                    resolved_entities.append("state -> state.sname AS state_name via users.state_id")
                    plan.grouping = ["sku_inventories.sku_description", "state.sname"]
                    business_rules.append("Join `sku_inventories.status_retailer_id = users.id` and `users.state_id = state.id` and select `state.sname AS state_name`.")

                elif has_category and has_retailer:
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                    resolved_joins.append("sku_inventories JOIN users ON sku_inventories.status_retailer_id = users.id")
                    resolved_entities.append("category -> sku_inventories.sku_description")
                    resolved_entities.append("retailer -> users via sku_inventories.status_retailer_id")
                    plan.grouping = ["sku_inventories.sku_description"]
                    business_rules.append("Join `sku_inventories.status_retailer_id = users.id` (user_role = 2) for retailer scans and group by `sku_inventories.sku_description`.")

                elif has_category:
                    resolved_entities.append("category -> sku_inventories.sku_description")
                    plan.grouping = ["sku_inventories.sku_description"]
                    business_rules.append("Box category is represented by `sku_inventories.sku_description`. Group by `sku_inventories.sku_description`.")

                elif has_mapping or (has_retailer and has_distributor):
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                    resolved_joins.append("sku_inventories JOIN users retailer ON sku_inventories.status_retailer_id = retailer.id")
                    resolved_joins.append("sku_inventories JOIN users distributor ON sku_inventories.distributer_id = distributor.id")
                    resolved_entities.append("retailer -> retailer.id, retailer.name (user_role = 2)")
                    resolved_entities.append("distributor -> distributor.id, distributor.name (user_role = 4)")
                    plan.grouping = ["retailer.id", "retailer.name", "distributor.id", "distributor.name"]
                    business_rules.append("Join retailer on `si.status_retailer_id = retailer.id` (user_role = 2) and distributor on `si.distributer_id = distributor.id` (user_role = 4).")

                elif has_state:
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                    if "state" not in resolved_tables:
                        resolved_tables.append("state")
                    resolved_joins.append("sku_inventories JOIN users ON sku_inventories.status_retailer_id = users.id")
                    resolved_joins.append("users JOIN state ON users.state_id = state.id")
                    resolved_entities.append("state -> state.sname AS state_name via users.state_id")
                    plan.grouping = ["state.sname"]
                    business_rules.append("Join `sku_inventories.status_retailer_id = users.id` and `users.state_id = state.id` and select `state.sname AS state_name`.")

                elif has_distributor:
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                    resolved_joins.append("sku_inventories JOIN users ON sku_inventories.distributer_id = users.id")
                    resolved_entities.append("distributor -> users via sku_inventories.distributer_id")
                    is_scalar = any(w in q_text for w in ["how many", "total number", "total count", "overall"]) and not any(w in q_text for w in ["for each", "by each", "per ", "top ", "bottom "])
                    if not is_scalar and (is_ranking or any(w in q_text for w in ["each", "per", "all", "every", "group"])):
                        plan.grouping = ["users.id", "users.name"]
                        business_rules.append("Join `sku_inventories.distributer_id = users.id` (user_role = 4) and group by distributor identifier to rank or aggregate box scans by distributor.")
                    else:
                        plan.grouping = []
                        business_rules.append("Join `sku_inventories.distributer_id = users.id` (user_role = 4) to filter for distributor scans.")

                elif has_retailer:
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                    resolved_joins.append("sku_inventories JOIN users ON sku_inventories.status_retailer_id = users.id")
                    resolved_entities.append("retailer -> users via sku_inventories.status_retailer_id")
                    is_scalar = any(w in q_text for w in ["how many", "total number", "total count", "overall"]) and not any(w in q_text for w in ["for each", "by each", "per ", "top ", "bottom "])
                    if not is_scalar and (is_ranking or any(w in q_text for w in ["each", "per", "all", "every", "group", "scanned at least"])):
                        plan.grouping = ["users.id", "users.name"]
                        business_rules.append("Join `sku_inventories.status_retailer_id = users.id` (user_role = 2) and group by retailer identifier to rank or aggregate box scans by retailer.")
                    else:
                        plan.grouping = []
                        business_rules.append("Join `sku_inventories.status_retailer_id = users.id` (user_role = 2) to filter for retailer scans without entity grouping.")

                if is_comparison or ("previous month" in q_text and "current month" in q_text):
                    business_rules.append("Compare box scans across the two periods using either conditional aggregation or by grouping by month.")

                if any(w in q_text for w in ["at least", "minimum one", "more than"]):
                    business_rules.append("Filter aggregate counts using a HAVING clause (e.g. HAVING COUNT(si.id) >= 1).")

            elif is_earnings:
                if "wallet_transaction" not in resolved_tables:
                    resolved_tables.append("wallet_transaction")
                business_rules.append("Earnings are credit transactions in `wallet_transaction` where `transaction_type = 1 AND amount > 0`.")

                has_user = any(e in ["retailer", "distributor", "user", "wholesaler"] for e in req_ents) or any(w in q_text for w in ["retailer", "distributor", "user"])
                if has_user:
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                    resolved_joins.append("users JOIN wallet_transaction ON users.id = wallet_transaction.user_id")
                    plan.grouping = ["users.id", "users.name"] if is_ranking else []
                    if has_mapping:
                        if "retailer_distributor_mappings" not in resolved_tables:
                            resolved_tables.append("retailer_distributor_mappings")
                        resolved_joins.append("wallet_transaction JOIN retailer_distributor_mappings ON wallet_transaction.user_id = retailer_distributor_mappings.retailer_id")

            elif has_mapping:
                for t in ["retailer_distributor_mappings", "users", "sku_inventories"]:
                    if t not in resolved_tables:
                        resolved_tables.append(t)
                resolved_joins.append("retailer_distributor_mappings JOIN users ON retailer_distributor_mappings.retailer_id = users.id")
                resolved_joins.append("sku_inventories JOIN users ON sku_inventories.status_retailer_id = users.id")
                business_rules.append("retailer_distributor_mappings links retailer_id to distributor_id; users table contains user details.")

            elif has_companies:
                resolved_tables.append("companies")
                resolved_entities.append("companies -> companies table")
                business_rules.append("Company profiles and business units are stored in the companies table.")

            else:
                # Direct Entity Listing or Filtering
                if any(e in ["retailer", "distributor", "user", "wholesaler", "state"] for e in req_ents) or any(w in q_text for w in ["retailer", "distributor", "user", "wholesaler"]):
                    if "users" not in resolved_tables:
                        resolved_tables.append("users")
                elif "wallet_transaction" in req_ents or "transaction" in q_text:
                    if "wallet_transaction" not in resolved_tables:
                        resolved_tables.append("wallet_transaction")
                elif any(w in q_text for w in ["sku", "inventory", "product", "box", "carton"]):
                    if "sku_inventories" not in resolved_tables:
                        resolved_tables.append("sku_inventories")
                else:
                    resolved_tables.append("users")

            # Final check on existing database tables
            existing_tables = {"users", "wallet_transaction", "retailer_distributor_mappings", "sku_inventories", "companies"}
            resolved_tables = [t for t in resolved_tables if t in existing_tables]

            req.relationship_path = resolved_joins
            plan.relationship_path = resolved_joins
            plan.relevant_tables = resolved_tables
            plan.required_joins = resolved_joins
            plan.resolved_entities = resolved_entities
            plan.business_rules = business_rules
            plan.missing_information = []


            # 4. Construct Intermediate Logical Query Plan
            plan.logical_query_plan = build_logical_query_plan(
                requirement=req,
                relevant_tables=plan.relevant_tables,
                required_joins=plan.required_joins,
                linked_values=linked_values
            )

        except Exception as e:
            logger.error(f"[RELATIONSHIP RESOLVER ERROR]: {e}")
            plan.relevant_tables = ["users"]
            plan.required_joins = []

        return plan

relationship_resolver = RelationshipResolver()
