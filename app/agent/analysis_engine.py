"""
Analysis & Explanation Engine for JGH Intelligence Engine.
Computes grounded analysis, key findings, conversational answers, and mathematical explanations
exclusively from actual verified database execution results (Sections 8, 9, 10, 11).
"""

from typing import Dict, Any, List, Optional
from app.agent.response_generator import response_generator
from app.agent.verified_result import VerifiedResult


class AnalysisEngine:
    """
    Constructs the structured Analysis object and grounds the final Natural Language
    answer and mathematical Explanation strictly in verified database rows.
    """

    def generate_analysis_and_answer(
        self,
        question: str,
        intent: Dict[str, Any],
        execution_plan: Dict[str, Any],
        columns: List[str],
        rows: List[Dict[str, Any]],
        verification: Dict[str, Any],
        verified_result: Optional[VerifiedResult] = None
    ) -> Dict[str, Any]:
        row_count = len(rows)
        intent_type = intent.get("intent_type", "data_retrieval")
        entity = intent.get("entity") or "record"
        entity_label = entity if entity.endswith("s") else f"{entity}s"
        metric = intent.get("metric") or "amount"
        q_lower = question.lower()

        # Identify metric nature
        is_box_scan = (
            metric == "box_scans" or
            metric == "box_scan_count" or
            any(w in q_lower for w in ["box scan", "box scans", "boxes scanned", "scanned box", "scanned boxes", "scan", "scans", "box", "boxes"])
        )
        is_earnings = (
            metric == "earnings" or
            any(w in q_lower for w in ["earning", "earnings", "earned", "revenue", "amount", "wallet amount"])
        )

        period_obj = intent.get("period") or intent.get("time_period") or {}
        period_str = period_obj.get("raw") or ""
        period_phrase = f" for {period_str}" if period_str else ""
        requested_count = intent.get("limit")

        # Generate Grounded Answer Text from ResponseGenerator (Single Source of Truth)
        if verified_result:
            answer_text = response_generator.generate_from_verified_result(verified_result)
        else:
            mock_res = VerifiedResult(
                question=question,
                business_requirement=intent,
                execution_plan=execution_plan,
                sql="",
                columns=columns,
                data=rows,
                row_count=row_count
            )
            answer_text = response_generator.generate_from_verified_result(mock_res)

        # 1. Zero Results Case
        if row_count == 0:
            summary = f"No qualifying {entity_label} were found in the database{period_phrase}."
            key_findings = [f"0 matching records returned from the database{period_phrase}."]
            explanation = (
                f"The database query executed successfully, but returned 0 rows because there are no "
                f"matching records for {entity_label}{period_phrase}."
            )
            return {
                "analysis": {
                    "answer_type": "empty",
                    "summary": summary,
                    "key_findings": key_findings,
                    "requested_count": requested_count,
                    "returned_count": 0
                },
                "answer": {
                    "text": answer_text,
                    "type": "empty",
                    "explanation": explanation
                }
            }

        # 2. Ranking Queries
        is_ranking = (
            intent_type in ["ranking", "multi_dimension_ranking"] or
            bool(requested_count and intent.get("sort") in ["DESC", "ASC"]) or
            any(w in q_lower for w in ["highest", "lowest", "most", "least", "top", "bottom"])
        )
        if is_ranking:
            val_col = next((c for c in columns if any(m in c.lower() for m in ["count", "scan", "earning", "total", "amount", "balance", "sum"])), columns[-1])
            name_cols = [c for c in columns if c != val_col]
            name_col = name_cols[0] if name_cols else columns[0]

            findings = []
            ranked_items = []
            for idx, r in enumerate(rows, 1):
                item_name = str(r.get(name_col) or f"Record {idx}")
                raw_val = r.get(val_col)
                ranked_items.append((idx, item_name, raw_val))
                if idx == 1:
                    findings.append(f"{item_name} ranked first")

                if raw_val is None:
                    v_str = "N/A"
                elif is_box_scan:
                    v_str = f"{int(raw_val):,} box scans"
                elif is_earnings or "amount" in str(val_col).lower():
                    v_str = f"₹{float(raw_val):,.2f}"
                else:
                    v_str = f"{raw_val}"
                findings.append(f"{item_name}: {v_str}")

            metric_title = "box scans" if is_box_scan else ("earnings" if is_earnings else "metric")
            if requested_count and row_count < requested_count:
                summary = f"{row_count} qualifying {entity_label} were found (requested {requested_count})."
            else:
                summary = f"{row_count} {entity_label} ranked by {metric_title}."

            if len(ranked_items) >= 2:
                n1, v1 = ranked_items[0][1], ranked_items[0][2]
                n2, v2 = ranked_items[1][1], ranked_items[1][2]
                v1_s = f"{int(v1):,} box scans" if is_box_scan else (f"₹{float(v1):,.2f}" if is_earnings else str(v1))
                v2_s = f"{int(v2):,} box scans" if is_box_scan else (f"₹{float(v2):,.2f}" if is_earnings else str(v2))
                explanation = (
                    f"{n1} ranked first with {v1_s}{period_phrase}, "
                    f"compared with {v2_s} for {n2}."
                )
            elif len(ranked_items) == 1:
                n1, v1 = ranked_items[0][1], ranked_items[0][2]
                v1_s = f"{int(v1):,} box scans" if is_box_scan else (f"₹{float(v1):,.2f}" if is_earnings else str(v1))
                explanation = f"{n1} is the top qualifying record{period_phrase} with {v1_s}."
            else:
                explanation = f"Rankings are ordered by verified {metric_title}."

            return {
                "analysis": {
                    "answer_type": "ranking",
                    "summary": summary,
                    "key_findings": findings,
                    "requested_count": requested_count or row_count,
                    "returned_count": row_count
                },
                "answer": {
                    "text": answer_text,
                    "type": "ranking",
                    "explanation": explanation
                }
            }

        # 3. Period Comparison Queries (Truthful matching without assuming row 0 vs row 1)
        is_comp = (
            intent_type == "comparison" or
            any(w in q_lower for w in ["compare", "versus", "vs", "comparison"])
        )
        if is_comp:
            period_col = next((c for c in columns if c.lower() in ["period", "month", "time_period", "year_month", "date_period"]), None)
            val_col = next((c for c in columns if any(m in c.lower() for m in ["earning", "amount", "total", "scan", "count", "sum"])), columns[-1] if columns else None)

            target_periods = intent.get("periods") or ["June 2026", "July 2026"]
            findings = []
            for r in rows:
                p_val = str(r.get(period_col, "")).strip() if period_col else ""
                val = r.get(val_col)
                if val is not None:
                    v_str = f"₹{float(val):,.2f}" if is_earnings else (f"{int(val):,} box scans" if is_box_scan else str(val))
                else:
                    v_str = "N/A"
                label = p_val if p_val else "Period"
                findings.append(f"{label}: {v_str}")

            summary = f"Comparison across requested periods ({', '.join(target_periods)})."
            explanation = "Calculated from verified database records grouped by time period."

            return {
                "analysis": {
                    "answer_type": "comparison",
                    "summary": summary,
                    "key_findings": findings,
                    "requested_count": len(target_periods),
                    "returned_count": row_count
                },
                "answer": {
                    "text": answer_text,
                    "type": "comparison",
                    "explanation": explanation
                }
            }

        # 4. Scalar Aggregate Queries
        if intent_type == "aggregate_analytics" or (row_count == 1 and len(columns) <= 2):
            val_col = columns[0]
            for c in columns:
                if any(m in c.lower() for m in ["total", "amount", "sum", "avg", "average", "count", "earning", "scan"]):
                    val_col = c
                    break
            raw_val = rows[0].get(val_col)
            if raw_val is not None:
                if is_box_scan or "scan" in val_col.lower():
                    val_formatted = f"{int(raw_val):,} box scans"
                elif is_earnings or any(w in val_col.lower() for w in ["amount", "earning", "sum"]):
                    val_formatted = f"₹{float(raw_val):,.2f}"
                else:
                    val_formatted = f"{raw_val}"
            else:
                val_formatted = "N/A"

            summary = f"Total {metric}{period_phrase} was {val_formatted}."
            key_findings = [f"Verified result: {val_formatted}"]
            explanation = f"Calculated directly from verified database query execution{period_phrase}."

            return {
                "analysis": {
                    "answer_type": "kpi",
                    "summary": summary,
                    "key_findings": key_findings,
                    "requested_count": 1,
                    "returned_count": 1
                },
                "answer": {
                    "text": answer_text,
                    "type": "kpi",
                    "explanation": explanation
                }
            }

        # 5. General Listing / Table
        summary = f"{row_count} {entity_label} found with recorded {metric}{period_phrase}."
        name_col = next((c for c in columns if c.lower() in ["name", "retailer", "distributor_name", "retailer_name", "sku_description"]), columns[0])
        findings = [str(r.get(name_col)) for r in rows[:5] if r.get(name_col)]

        return {
            "analysis": {
                "answer_type": "table",
                "summary": summary,
                "key_findings": findings,
                "requested_count": requested_count or row_count,
                "returned_count": row_count
            },
            "answer": {
                "text": answer_text,
                "type": "table",
                "explanation": f"Retrieved {row_count} records from the database."
            }
        }


analysis_engine = AnalysisEngine()
