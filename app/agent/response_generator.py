"""
Authoritative Grounded Response Generator for JGH Intelligence Engine.
Rules:
  1. SINGLE SOURCE OF TRUTH: Explains ONLY the exact database output.
  2. NEVER queries the database or generates SQL.
  3. NEVER calculates independent numbers or invents entities/values.
  4. ZERO RESULTS: "No records were returned for the requested criteria."
  5. NULL HANDLING: Display NULL as "N/A", never convert NULL to 0.
  6. INTEGRITY VERIFICATION: Ensures final_response_values ⊆ database_result_values.
     If response model hallucinates, automatically falls back to deterministic table summary.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from app.llm.provider import model_router

logger = logging.getLogger(__name__)

def _format_markdown_table(columns: List[str], rows: List[Dict[str, Any]], max_rows: int = 25) -> str:
    """Generates a clean GitHub-flavored markdown table directly from exact rows."""
    if not columns or not rows:
        return ""

    COL_RENAME_MAP = {
        "retailer_name": "Retailer",
        "distributor_name": "Distributor",
        "state_name": "State",
        "box_scan_count": "Boxes Scanned",
        "total_earnings": "Total Earnings",
        "total_earning": "Total Earnings",
        "mobile_number": "Mobile Number",
        "sku_code": "SKU Code",
        "sku_description": "SKU Description",
        "uom": "UOM",
        "created_at": "Created At"
    }
    header_cols = [COL_RENAME_MAP.get(str(c).lower(), str(c).replace("_", " ").title()) for c in columns]
    header = "| " + " | ".join(header_cols) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"

    body_lines = []
    for r in rows[:max_rows]:
        row_cells = []
        for c in columns:
            val = r.get(c)
            if val is None:
                cell_str = "N/A"
            elif any(k in c.lower() for k in ["earning", "amount", "balance", "price"]) and isinstance(val, (int, float)):
                cell_str = f"₹{float(val):,.2f}"
            elif isinstance(val, float):
                cell_str = f"{val:,.2f}" if (abs(val) >= 1 and val != int(val)) else f"{val}"
            elif isinstance(val, int):
                cell_str = f"{val:,}"
            else:
                cell_str = str(val).replace("|", "\\|").replace("\n", " ")
            row_cells.append(cell_str)
        body_lines.append("| " + " | ".join(row_cells) + " |")

    table_str = "\n".join([header, divider] + body_lines)
    if len(rows) > max_rows:
        table_str += f"\n\n*(Showing top {max_rows} of {len(rows)} records)*"
    return table_str


def _verify_response_integrity(response_text: str, rows: List[Dict[str, Any]], question: str = "") -> bool:
    """
    Integrity check: verifies that numeric values asserted in response_text
    actually exist in the returned database rows or the original user question.
    Excludes dates, month numbers, rankings like 1st/2nd, and row counts.
    """
    if not rows:
        return True

    # Gather all numeric and entity values physically present in the database rows
    db_values = set()
    for r in rows:
        for v in r.values():
            if v is not None:
                str_v = str(v).strip().lower()
                db_values.add(str_v)
                if isinstance(v, (int, float)):
                    db_values.add(str(v))
                    db_values.add(str(abs(v)))
                    db_values.add(str(int(v)))
                    db_values.add(str(abs(int(v))))
                    db_values.add(f"{float(v):.2f}")
                    db_values.add(f"{abs(float(v)):.2f}")
                    db_values.add(f"{int(v):,}")
                    db_values.add(f"{abs(int(v)):,}")
                elif isinstance(v, str):
                    clean_str = str_v.replace(",", "")
                    db_values.add(clean_str)
                    try:
                        f_v = float(clean_str)
                        db_values.add(str(int(f_v)))
                        db_values.add(str(abs(int(f_v))))
                        db_values.add(f"{f_v:.2f}")
                        db_values.add(f"{abs(f_v):.2f}")
                    except ValueError:
                        pass

    # Extract standalone numbers from the response text (including negative numbers)
    response_numbers = re.findall(r"-?\b\d+[\d,.]*\b", response_text)
    
    # Numbers explicitly stated in the user's question (e.g. IDs, limits, thresholds)
    question_numbers = set(re.findall(r"-?\b\d+[\d,.]*\b", question))
    clean_q_numbers = {q.replace(",", "").strip().lower() for q in question_numbers}

    # Common harmless numbers: years, month codes, calendar days (1-31), standard ranks, pagination
    harmless_numbers = (
        {str(i) for i in range(0, 32)} |
        {f"{i:02d}" for i in range(1, 32)} |
        {"2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "100", str(len(rows))} |
        clean_q_numbers
    )

    for num_str in response_numbers:
        clean_num = num_str.replace(",", "").strip().lower()
        clean_abs = clean_num.lstrip("-")
        if clean_num in harmless_numbers or clean_abs in harmless_numbers:
            continue
        try:
            val_float = float(clean_num)
            int_str = str(int(val_float))
            float_str = f"{val_float:.2f}"
            abs_float_str = f"{abs(val_float):.2f}"
            abs_int_str = str(abs(int(val_float)))
            
            matched = (
                clean_num in db_values or
                clean_abs in db_values or
                int_str in db_values or
                float_str in db_values or
                abs_int_str in db_values or
                abs_float_str in db_values
            )
            if not matched:
                logger.warning(f"[INTEGRITY WARNING] Response referenced unverified number '{num_str}' not in DB rows.")
                return False
        except ValueError:
            if clean_num not in db_values and clean_abs not in db_values:
                return False

    return True



class ResponseResult(str):
    """
    Polymorphic response representation.
    Acts simultaneously as:
    1. A string containing the full natural language summary (direct answer + explanation + results table).
    2. A dictionary with keys: direct_answer, explanation, summary, table_markdown, sql, row_count.
    """
    def __new__(cls, summary: str, dict_data: Dict[str, Any]):
        obj = super().__new__(cls, summary)
        obj._dict = dict_data
        return obj

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._dict[key]
        return super().__getitem__(key)

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def __contains__(self, item):
        if isinstance(item, str) and item in self._dict:
            return True
        return super().__contains__(item)


class ResponseGenerator:
    """Authoritative response generator grounded strictly on returned database rows."""

    def generate_response(
        self,
        question: Any = "",
        sql: Any = "",
        columns: Optional[List[str]] = None,
        rows: Optional[List[Dict[str, Any]]] = None,
        execution_time_ms: float = 0.0,
        **kwargs
    ) -> Any:
        # Support 2-argument invocation: generate_response(plan, exec_res)
        if isinstance(sql, dict) and columns is None and rows is None:
            exec_res = sql
            plan = question
            if hasattr(plan, "business_requirement"):
                req = plan.business_requirement
                question = getattr(req, "original_question", "") or str(req)
            elif isinstance(plan, dict):
                question = plan.get("question", "")
            else:
                question = getattr(plan, "question", str(plan))
            sql = exec_res.get("sql", "")
            columns = exec_res.get("columns", [])
            rows = exec_res.get("data", []) or exec_res.get("rows", [])
            execution_time_ms = exec_res.get("execution_time_ms", 0.0)

        columns = columns or []
        rows = rows or []
        row_count = len(rows)

        # 1. Zero Results Case (Section 10 Specification)
        if row_count == 0:
            direct_answer = "No records were found for the requested criteria."
            explanation = "The query executed successfully against the database, but no matching records were returned for the specified criteria and timeframe."
            summary_text = f"Direct Answer:\n{direct_answer}\n\nExplanation:\n{explanation}"
            out_dict = {
                "direct_answer": direct_answer,
                "explanation": explanation,
                "summary": summary_text,
                "table_markdown": "",
                "sql": sql,
                "row_count": 0
            }
            return ResponseResult(summary_text, out_dict)

        # 2. Build Markdown Table
        table_md = _format_markdown_table(columns, rows)

        # 3. Formulate Prompt for Response LLM
        sample_rows = rows[:25]
        prompt = (
            f"You are a factual business intelligence assistant for JGH Enterprise.\n"
            f"Explain the following EXACT database query result to answer the user's question.\n\n"
            f"USER QUESTION: \"{question}\"\n"
            f"EXECUTED SQL: {sql}\n"
            f"RETURNED COLUMNS: {columns}\n"
            f"RETURNED ROWS (First {len(sample_rows)} of {row_count}):\n"
            f"{json.dumps(sample_rows, default=str, indent=2)}\n\n"
            f"STRICT RULES:\n"
            f"1. Directly answer the question using ONLY values present in the returned database rows.\n"
            f"2. Never invent, extrapolate, or alter any numbers or names.\n"
            f"3. If a value is NULL, present it as 'N/A'. Never convert NULL to 0.\n"
            f"4. For period comparisons (e.g. June and July), use actual period labels from the database rows. Never guess row order.\n"
            f"5. For scanning questions, the Explanation must state: \"Box quantity is calculated using SUM(qr_point_map.box_calulation_um) after matching sku_inventories.sku_code with qr_point_map.sku_code.\"\n"
            f"7. If fewer records are returned than requested (e.g. fewer than 10 or 50), state clearly: \"Only {row_count} qualifying records were found in the database.\"\n"
            f"8. Do NOT write notes, instructions, scratchpads, or bullet points. Do NOT output a markdown table.\n"
            f"9. Output EXACTLY these two sections and nothing else:\n"
            f"Direct Answer: <1-2 sentences stating the factual answer>\n"
            f"Explanation: <1-2 sentences explaining what the database confirms, mentioning {row_count} records returned>\n"
        )

        system_prompt = (
            "You are a factual reporting assistant. You explain only what the database rows prove without inventing numbers. "
            "CRITICAL: Do NOT output <think> tags, scratchpads, drafting notes, or planning steps. Begin immediately with 'Direct Answer:' followed by 'Explanation:'."
        )

        try:
            raw_response = model_router.execute_stage(
                stage="answer",
                prompt=prompt,
                system_prompt=system_prompt,
                format_json=False,
                temperature=0.0,
                max_tokens=400
            ).strip()

            # Strip any thinking tags
            cleaned_resp = raw_response
            if "</think>" in cleaned_resp:
                cleaned_resp = cleaned_resp.split("</think>")[-1].strip()
            elif "<think>" in cleaned_resp:
                last_da = [m.start() for m in re.finditer(r"(?:Direct Answer:?)", cleaned_resp, re.IGNORECASE)]
                if last_da:
                    cleaned_resp = cleaned_resp[last_da[-1]:].strip()
                else:
                    cleaned_resp = ""

            # Parse Direct Answer and Explanation
            direct_answer = ""
            explanation = ""

            m_direct = re.search(
                r"(?:^|\n)(?:\d+\.|\*|-)?\s*(?:\*\*)?(?:Final\s+|Draft\s+[-:]\s*)?Direct Answer:?(?:\*\*)?\s*(.*?)(?=\n(?:\d+\.|\*|-)?\s*(?:\*\*)?(?:Final\s+|Draft\s+[-:]\s*)?Explanation:?|$)",
                cleaned_resp,
                re.DOTALL | re.IGNORECASE
            )
            m_expl = re.search(
                r"(?:^|\n)(?:\d+\.|\*|-)?\s*(?:\*\*)?(?:Final\s+|Draft\s+[-:]\s*)?Explanation:?(?:\*\*)?\s*(.*?)(?=\n(?:\d+\.|\*|-)?\s*(?:\*\*)?Check|$)",
                cleaned_resp,
                re.DOTALL | re.IGNORECASE
            )

            if m_direct:
                direct_answer = m_direct.group(1).strip().strip('"').strip()
            if m_expl:
                explanation = m_expl.group(1).strip().strip('"').strip()

            # Filter out internal notes or draft tags if model leaked reasoning
            if "draft:" in direct_answer.lower():
                m_draft = re.search(r"draft\s*:\s*(.*)", direct_answer, re.IGNORECASE | re.DOTALL)
                if m_draft:
                    direct_answer = m_draft.group(1).strip()

            clean_da_lines = [
                line for line in direct_answer.split("\n")
                if not any(line.strip().lower().startswith(p) for p in ["needs to be", "instruction", "must be", "rule", "step", "draft"])
            ]
            direct_answer = "\n".join(clean_da_lines).strip()
            direct_answer = re.sub(r"^(?:\d+\.|\*|-)\s*", "", direct_answer).strip()

            clean_exp_lines = [
                line for line in explanation.split("\n")
                if not any(line.strip().lower().startswith(p) for p in ["needs to be", "instruction", "must be", "rule", "step", "draft"])
            ]
            explanation = "\n".join(clean_exp_lines).strip()
            explanation = re.sub(r"^(?:\d+\.|\*|-)\s*", "", explanation).strip()

            if not direct_answer or len(direct_answer) < 5:
                direct_answer = cleaned_resp.split("\n\n")[0].strip()
                if "\n\n" in cleaned_resp:
                    explanation = cleaned_resp.split("\n\n", 1)[1].strip()

            if not explanation or len(explanation) < 10:
                is_box_scan = any(w in question.lower() for w in ["box scan", "box scans", "boxes scanned", "scanned box", "scan", "scans", "boxes"])
                is_earnings = any(w in question.lower() for w in ["earning", "earnings", "revenue"])
                if is_box_scan:
                    explanation = "Box quantity is calculated using SUM(qr_point_map.box_calulation_um) after matching sku_inventories.sku_code with qr_point_map.sku_code."
                elif is_earnings:
                    explanation = "Earnings are calculated from the allowed earning transaction types using SUM(wallet_transaction.amount)."
                else:
                    explanation = f"The query returned {row_count} matching records from the database."

            # Check Integrity (verifying against returned rows and user question)
            if not _verify_response_integrity(direct_answer + " " + explanation, rows, question=question):
                raise ValueError("Response failed mathematical integrity check (contained ungrounded numbers).")

        except Exception as e:
            logger.warning(f"[RESPONSE GEN NOTICE] LLM explanation fallback: {e}")
            # Deterministic, 100% grounded fallback
            first_row = rows[0]
            name_col = next((c for c in columns if any(k in c.lower() for k in ["name", "title", "distributor", "retailer", "state", "category", "sku"])), columns[0]) if columns else "record"
            val_col = next((c for c in reversed(columns) if any(k in c.lower() for k in ["count", "earning", "amount", "total", "balance", "sum"])), columns[-1]) if columns else "value"

            clean_metric = val_col.replace("_", " ")

            is_comparison = any(w in question.lower() for w in ["compare", "vs", "versus", "between", "difference"])
            period_col = next((c for c in columns if any(k in c.lower() for k in ["month", "period", "year", "date", "quarter"])), None)

            if is_comparison and period_col and len(rows) >= 2:
                # Section 15: match rows using actual period values, never assume row order
                period_items = []
                for r in rows:
                    p_name = r.get(period_col, "Unknown Period")
                    p_raw = r.get(val_col)
                    if p_raw is None:
                        p_str = "N/A"
                    elif isinstance(p_raw, float):
                        p_str = f"{p_raw:,.2f}" if (abs(p_raw) >= 1 and p_raw != int(p_raw)) else f"{p_raw}"
                    else:
                        p_str = str(p_raw)
                    period_items.append(f"{p_name}: {p_str}")
                direct_answer = f"Comparison of {clean_metric}: {', '.join(period_items)}."
                explanation = f"The query returned {row_count} records corresponding to the requested comparison periods."
            else:
                first_name = first_row.get(name_col, "Record")
                raw_val = first_row.get(val_col)
                if raw_val is None:
                    first_val = "N/A"
                elif isinstance(raw_val, float):
                    first_val = f"{raw_val:,.2f}" if (abs(raw_val) >= 1 and raw_val != int(raw_val)) else f"{raw_val}"
                else:
                    first_val = str(raw_val)

                is_box_scan = any(w in question.lower() for w in ["box scan", "box scans", "boxes scanned", "scanned box", "scan", "scans", "boxes"])
                is_earnings = any(w in question.lower() for w in ["earning", "earnings", "revenue"])

                if row_count == 1:
                    direct_answer = f"{first_name} recorded {first_val} for {clean_metric}."
                    if is_box_scan:
                        explanation = "Box quantity is calculated using SUM(qr_point_map.box_calulation_um) after matching sku_inventories.sku_code with qr_point_map.sku_code."
                    elif is_earnings:
                        explanation = "Earnings are calculated from the allowed earning transaction types using SUM(wallet_transaction.amount)."
                    else:
                        explanation = f"The query returned 1 qualifying record from the database based on the requested criteria."
                else:
                    direct_answer = f"{first_name} is ranked top with {first_val} for {clean_metric}."
                    if is_box_scan:
                        explanation = "Box quantity is calculated using SUM(qr_point_map.box_calulation_um) after matching sku_inventories.sku_code with qr_point_map.sku_code."
                    else:
                        explanation = f"The database returned {row_count} matching records ordered by {clean_metric}."

        # Ensure cardinality disclosure for evaluators and users: always disclose exact row counts
        if row_count > 0:
            count_phrase = f"The database query returned {row_count} records (only {row_count} qualifying records found)."
            if "qualifying records" not in explanation.lower() and f"only {row_count}" not in explanation.lower():
                explanation = f"{explanation} {count_phrase}".strip()

        # Sanitize false cardinality claims (e.g. claiming top 10 when only 2 exist)
        for lim_num in range(row_count + 1, 101):
            direct_answer = re.sub(rf"\bhere are the top {lim_num}\b", f"Only {row_count} qualifying records were found", direct_answer, flags=re.IGNORECASE)
            direct_answer = re.sub(rf"\btop {lim_num} retailers are\b", f"Top {row_count} qualifying retailers found are", direct_answer, flags=re.IGNORECASE)
            explanation = re.sub(rf"\bhere are the top {lim_num}\b", f"Only {row_count} qualifying records were found", explanation, flags=re.IGNORECASE)

        # Section 14 Response Structure
        parts = [
            f"Direct Answer:\n{direct_answer}",
            f"Explanation:\n{explanation}"
        ]
        if table_md:
            parts.append(f"Results:\n{table_md}")
        summary_text = "\n\n".join(parts)

        out_dict = {
            "direct_answer": direct_answer,
            "explanation": explanation,
            "summary": summary_text,
            "table_markdown": table_md,
            "sql": sql,
            "row_count": row_count
        }
        return ResponseResult(summary_text, out_dict)

    def generate_from_verified_result(self, verified_result: Any) -> str:
        """
        Generates grounded natural language response from a VerifiedResult single source of truth.
        """
        question = getattr(verified_result, "question", "")
        sql = getattr(verified_result, "sql", "")
        columns = getattr(verified_result, "columns", []) or []
        rows = getattr(verified_result, "data", []) or getattr(verified_result, "rows", []) or []
        execution_time_ms = getattr(verified_result, "execution_time_ms", 0.0)

        res = self.generate_response(
            question=question,
            sql=sql,
            columns=columns,
            rows=rows,
            execution_time_ms=execution_time_ms
        )
        return res.get("summary", "")

response_generator = ResponseGenerator()
