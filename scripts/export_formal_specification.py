"""
Formal IEEE Std 830-1998 SRS & System Ground-Truth Specification Generator.
Compiles Phase 0 introspection findings into two formal deliverables:
  1. knowledge/IEEE_830_JGH_System_Specification.docx (Editable Word Document)
  2. knowledge/IEEE_830_JGH_System_Specification.pdf (Formal IEEE SRS PDF Report)
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
SCHEMA_DIR = KNOWLEDGE_DIR / "schema"

# -----------------------------------------------------------------------------
# 1. LOAD PHASE 0 DATASET FINDINGS
# -----------------------------------------------------------------------------
def load_phase0_data():
    profile_path = KNOWLEDGE_DIR / "draft_db_profile.json"
    restricted_path = KNOWLEDGE_DIR / "draft_restricted_columns.json"
    dictionary_path = KNOWLEDGE_DIR / "business_dictionary.json"
    schema_path = SCHEMA_DIR / "draft_schema_metadata.json"
    graph_path = KNOWLEDGE_DIR / "draft_relationship_graph.json"

    profile_data = json.load(open(profile_path, "r", encoding="utf-8")) if profile_path.exists() else {}
    restricted_data = json.load(open(restricted_path, "r", encoding="utf-8")) if restricted_path.exists() else {}
    dictionary_data = json.load(open(dictionary_path, "r", encoding="utf-8")) if dictionary_path.exists() else {}
    schema_data = json.load(open(schema_path, "r", encoding="utf-8")) if schema_path.exists() else {}
    graph_data = json.load(open(graph_path, "r", encoding="utf-8")) if graph_path.exists() else {}

    total_tables = schema_data.get("total_tables", 238)
    total_edges = graph_data.get("total_candidate_edges", 32251)
    total_restricted = restricted_data.get("total_restricted_columns", 16)
    total_profiled = len(profile_data.get("all_low_cardinality_columns", {}))

    return {
        "total_tables": total_tables,
        "total_edges": total_edges,
        "total_restricted": total_restricted,
        "total_profiled": total_profiled,
        "profile_data": profile_data,
        "restricted_data": restricted_data,
        "dictionary_data": dictionary_data,
        "schema_data": schema_data,
        "graph_data": graph_data
    }


# -----------------------------------------------------------------------------
# 2. DOCX GENERATION FUNCTION (python-docx)
# -----------------------------------------------------------------------------
def generate_docx_specification(data):
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn

    doc = docx.Document()

    # Set page margins to 1 inch
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Color Palette Constants
    COLOR_NAVY = RGBColor(30, 58, 138)       # #1E3A8A
    COLOR_ACCENT = RGBColor(37, 99, 235)     # #2563EB
    COLOR_DARK = RGBColor(15, 23, 42)        # #0F172A
    COLOR_MUTED = RGBColor(100, 116, 139)    # #64748B
    HEX_HEADER_BG = "1E293B"
    HEX_ALT_ROW = "F1F5F9"

    def set_cell_background(cell, hex_color):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    def format_paragraph(p, space_before=4, space_after=4, line_spacing=1.15):
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing

    def add_heading_1(text):
        p = doc.add_paragraph()
        format_paragraph(p, space_before=14, space_after=6)
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = COLOR_NAVY
        return p

    def add_heading_2(text):
        p = doc.add_paragraph()
        format_paragraph(p, space_before=10, space_after=4)
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = COLOR_ACCENT
        return p

    def add_body_p(text, bold_prefix=""):
        p = doc.add_paragraph()
        format_paragraph(p, space_before=3, space_after=4)
        if bold_prefix:
            run_b = p.add_run(bold_prefix)
            run_b.font.name = 'Calibri'
            run_b.font.size = Pt(10)
            run_b.font.bold = True
            run_b.font.color.rgb = COLOR_DARK
        run_t = p.add_run(text)
        run_t.font.name = 'Calibri'
        run_t.font.size = Pt(10)
        run_t.font.color.rgb = COLOR_DARK
        return p

    def style_table(table, header_bg=HEX_HEADER_BG, col_widths=None):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for idx, row in enumerate(table.rows):
            is_header = (idx == 0)
            bg = header_bg if is_header else (HEX_ALT_ROW if idx % 2 == 1 else "FFFFFF")
            for c_idx, cell in enumerate(row.cells):
                set_cell_background(cell, bg)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                if col_widths and c_idx < len(col_widths):
                    cell.width = Inches(col_widths[c_idx])
                for p in cell.paragraphs:
                    format_paragraph(p, space_before=2, space_after=2)
                    for run in p.runs:
                        run.font.name = 'Calibri'
                        run.font.size = Pt(9)
                        if is_header:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)

    # -------------------------------------------------------------------------
    # COVER TITLE & CONTROL TABLE
    # -------------------------------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    format_paragraph(title_p, space_before=10, space_after=4)
    trun = title_p.add_run("SOFTWARE REQUIREMENTS SPECIFICATION (SRS)\n& SYSTEM GROUND-TRUTH DATA DICTIONARY")
    trun.font.name = 'Calibri'
    trun.font.size = Pt(22)
    trun.font.bold = True
    trun.font.color.rgb = COLOR_NAVY

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    format_paragraph(sub_p, space_before=0, space_after=14)
    srun = sub_p.add_run("IEEE Std 830-1998 Compliant Ground-Truth Specification for JGH Project Intelligence Engine")
    srun.font.name = 'Calibri'
    srun.font.size = Pt(12)
    srun.font.color.rgb = COLOR_MUTED

    # Document Control Table
    ctrl_table = doc.add_table(rows=5, cols=4)
    ctrl_data = [
        ["Document ID:", "IEEE-SRS-JGH-2026-V1.0", "Target Database:", "jghMasterDB (MySQL 8.0)"],
        ["Compliance Std:", "IEEE Std 830-1998", "Total Tables:", str(data['total_tables'])],
        ["Profiled Enums:", f"{data['total_profiled']} Columns", "Security Blacklist:", f"{data['total_restricted']} Sensitive Columns"],
        ["Candidate Joins:", f"{data['total_edges']:,} Edges", "Revision Date:", "August 12, 2026"],
        ["Document Status:", "Pending Domain Expert Approval", "Licensing:", "100% FOSS & On-Premises Ready"]
    ]

    for r_idx, row_vals in enumerate(ctrl_data):
        for c_idx, val in enumerate(row_vals):
            p = ctrl_table.cell(r_idx, c_idx).paragraphs[0]
            is_lbl = (c_idx % 2 == 0)
            p.add_run(val).bold = is_lbl

    style_table(ctrl_table, col_widths=[1.5, 1.8, 1.5, 1.8])
    doc.add_paragraph()

    # -------------------------------------------------------------------------
    # SECTION 1: INTRODUCTION & SYSTEM SCOPE
    # -------------------------------------------------------------------------
    add_heading_1("1. INTRODUCTION & SYSTEM SCOPE")

    add_heading_2("1.1 Purpose")
    add_body_p(
        "This Software Requirements Specification (SRS) establishes the formal, deterministic ground-truth specification "
        "bridging raw MySQL schema structures in jghMasterDB with the JGH AI Intelligence Engine. "
        "It serves as the definitive reference for intent routing, SQL synthesis, PII privacy enforcement, and domain expert sign-off."
    )

    add_heading_2("1.2 Scope & Intent Capabilities")
    add_body_p(
        "The system governs 238 tables in jghMasterDB and supports multi-intent conversational AI processing: "
        "\n1. Conversational SQL Data Analytics (Sargable AST SQL execution & reporting)"
        "\n2. Database Tutor & Onboarding Coach ('Teach Me' schema explanations)"
        "\n3. Visual Architecture & ER Diagram Generation (Mermaid.js diagramming)"
        "\n4. Dynamic Dashboard Specification Builder (JSON UI specs)"
        "\n5. Executive Business Storytelling (Plain-English executive summaries)"
        "\nAll capabilities operate under 100% FOSS, on-premises privacy constraints."
    )

    add_heading_2("1.3 Definitions, Acronyms, and Abbreviations")
    acronyms_table = doc.add_table(rows=9, cols=2)
    acronym_vals = [
        ["Term / Acronym", "IEEE SRS Definition & Context"],
        ["AST", "Abstract Syntax Tree - Structured node tree used by SQLGlot to validate SQL queries without execution."],
        ["Sargable", "Search Argument Able - SQL predicate design ensuring index utilization (avoiding functions on indexed columns)."],
        ["Enum", "Low-cardinality discrete value set (<= 50 distinct values) mapped to domain business meanings."],
        ["PII", "Personally Identifiable Information & sensitive secrets (passwords, tokens, keys) hard-blocked from LLM prompts."],
        ["RAG", "Retrieval-Augmented Generation - Schema & relationship vector retrieval augmenting LLM prompts."],
        ["FOSS", "Free & Open Source Software - Self-contained offline deployment stack (FastAPI, Ollama, ChromaDB, MySQL)."],
        ["ERD", "Entity-Relationship Diagram - Architectural visualization of database schemas and foreign key edges."],
        ["Incognito Ephemeral", "Zero-history transient state mode where chat sessions leave no persistent logs."]
    ]
    for r_idx, rvals in enumerate(acronym_vals):
        for c_idx, val in enumerate(rvals):
            ctrl_table.cell(0, 0) # touch
            acronyms_table.cell(r_idx, c_idx).paragraphs[0].add_run(val)
    style_table(acronyms_table, col_widths=[2.0, 4.6])
    doc.add_paragraph()

    add_heading_2("1.4 References")
    add_body_p("1. IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.")
    add_body_p("2. MySQL 8.0 Reference Manual: Information Schema & InnoDB Storage Engine Architecture.")
    add_body_p("3. JGH Intelligence Engine Phase 0 Database Profiling & Relationship Graph Artifacts (August 2026).")

    # -------------------------------------------------------------------------
    # SECTION 2: SYSTEM ARCHITECTURE & OVERALL DESCRIPTION
    # -------------------------------------------------------------------------
    add_heading_1("2. SYSTEM ARCHITECTURE & OVERALL DESCRIPTION")

    add_heading_2("2.1 Product Perspective & Layer Flow")
    add_body_p(
        "The JGH Intelligence Engine follows a decoupled, 6-stage execution pipeline: "
        "\n• Stage 1: React + Vite Frontend UI (Chat, Data Tables, Charts, History, Admin Panel)"
        "\n• Stage 2: Security & Privacy Gateway (Input Sanitization, PII Redaction, Token Scrubbing)"
        "\n• Stage 3: Multi-Intent Classification & Router (SQL Analytics vs Tutor vs ERD vs Storyteller)"
        "\n• Stage 4: Execution Engine (SQLGlot AST Validation -> EXPLAIN Cost Check -> Read-Only MySQL Execution)"
        "\n• Stage 5: Gemini-Style Response Synthesizer (Natural language narratives + Markdown data tables)"
        "\n• Stage 6: Ephemeral Privacy Controller (Zero-history logging for sensitive mode)"
    )

    add_heading_2("2.2 Operating Constraints")
    add_body_p("1. Read-Only Execution: Database user is granted strictly SELECT permissions. Write queries are blocked at AST parser.")
    add_body_p("2. EXPLAIN Cost Threshold: Queries evaluating > 100,000 estimated rows are automatically blocked or capped with LIMIT 100.")
    add_body_p("3. Zero-History Ephemeral Mode: When is_private=true, no memory buffers or logs are persisted to disk.")

    # -------------------------------------------------------------------------
    # SECTION 3: SYSTEM TAXONOMY & USER ROLE GROUND TRUTH
    # -------------------------------------------------------------------------
    add_heading_1("3. SYSTEM TAXONOMY & USER ROLE GROUND TRUTH")
    add_body_p(
        "Complete mapping of all 13 distinct user_role integer codes extracted from 29,063 profile records in the users table. "
        "Domain experts must confirm the exact role titles and operational category definitions below."
    )

    roles_table = doc.add_table(rows=14, cols=5)
    roles_vals = [
        ["Role Code", "User Count", "% Share", "Role Name / Title", "Operational Category & Expert Sign-Off"],
        ["user_role = 1", "6", "0.02%", "Executive / Staff", "Internal Operations Staff  [  ] Approved"],
        ["user_role = 2", "27,703", "95.32%", "Retailer / Mechanic", "Primary Loyalty Earners  [  ] Approved"],
        ["user_role = 3", "6", "0.02%", "Area Executive", "Field Sales Team  [  ] Approved"],
        ["user_role = 4", "457", "1.57%", "Distributor Partner", "Supply Chain Channel  [  ] Approved"],
        ["user_role = 5", "573", "1.97%", "Wholesaler / Stockist", "Supply Chain Channel  [  ] Approved"],
        ["user_role = 6", "248", "0.85%", "Super Distributor", "Enterprise Distribution  [  ] Approved"],
        ["user_role = 7", "1", "0.00%", "System Master Admin", "Platform Governance  [  ] Approved"],
        ["user_role = 8", "6", "0.02%", "Finance Auditor", "Audit & Compliance  [  ] Approved"],
        ["user_role = 10", "23", "0.08%", "Field Executive", "Field Sales & Scans  [  ] Approved"],
        ["user_role = 11", "10", "0.03%", "Regional Manager", "Regional Management  [  ] Approved"],
        ["user_role = 13", "3", "0.01%", "Support Manager", "Customer Helpdesk  [  ] Approved"],
        ["user_role = 14", "1", "0.00%", "Sandbox / Test User", "QA & Integration Testing  [  ] Approved"],
        ["user_role = NULL", "25", "0.09%", "Unassigned Profile", "Legacy Unassigned  [  ] Approved"]
    ]
    for r_idx, rvals in enumerate(roles_vals):
        for c_idx, val in enumerate(rvals):
            roles_table.cell(r_idx, c_idx).paragraphs[0].add_run(val)
    style_table(roles_table, col_widths=[1.2, 0.9, 0.8, 1.8, 1.9])
    doc.add_paragraph()

    # -------------------------------------------------------------------------
    # SECTION 4: DOMAIN SEMANTICS & CALCULATED METRICS
    # -------------------------------------------------------------------------
    add_heading_1("4. DOMAIN SEMANTICS & CALCULATED METRICS")
    add_body_p(
        "Formal SQL expressions and business logic rules comparing static profile column snapshots against dynamic ledger calculation expressions."
    )

    metrics_table = doc.add_table(rows=8, cols=4)
    metrics_vals = [
        ["Metric Name", "Target Table & Column", "Proposed SQL Expression", "Business Definition & Expert Sign-Off"],
        ["1. Static Profile Balance", "users.wallet_balance", "SUM(wallet_balance)", "Stored wallet balance snapshot  [  ] Approved"],
        ["2. Dynamic Ledger Balance", "wallet_transaction.amount", "SUM(CASE WHEN reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN amount ELSE -amount END)", "Net calculated financial balance  [  ] Approved"],
        ["3. Gross Earnings", "wallet_transaction.amount", "SUM(amount) WHERE reference_type IN ('cash_point', 'topup', 'incentive', 'bonus_conversion', 'referral_earning', 'credit_note')", "Total monetary credits earned  [  ] Approved"],
        ["4. Total Redemptions", "wallet_transaction.amount", "SUM(amount) WHERE reference_type = 'withdrawal'", "Total cash payouts redeemed  [  ] Approved"],
        ["5. Retailer Box Scans", "sku_inventories.order_type", "COUNT(*) WHERE order_type = 'Retailer' AND retailer_scanned_at IS NOT NULL", "Retailer QR box scans completed  [  ] Approved"],
        ["6. Wholesaler Box Scans", "sku_inventories.order_type", "COUNT(*) WHERE order_type IN ('Distributor', 'Distributors') AND wholeseller_scanned_at IS NOT NULL", "Wholesaler box scans completed  [  ] Approved"],
        ["7. Total Points Earned", "sku_qr_points_maps.retailer_cash_points", "SUM(q.retailer_cash_points + q.wholeseller_cash_points) via sku_code join", "Total reward points generated  [  ] Approved"]
    ]
    for r_idx, rvals in enumerate(metrics_vals):
        for c_idx, val in enumerate(rvals):
            metrics_table.cell(r_idx, c_idx).paragraphs[0].add_run(val)
    style_table(metrics_table, col_widths=[1.5, 1.5, 2.0, 1.6])
    doc.add_paragraph()

    # -------------------------------------------------------------------------
    # SECTION 5: RELATIONAL DATA ARCHITECTURE & TEMPORAL BOUNDS
    # -------------------------------------------------------------------------
    add_heading_1("5. RELATIONAL DATA ARCHITECTURE & TEMPORAL BOUNDS")

    add_heading_2("5.1 Dual-Role Schema Join Graph")
    join_table = doc.add_table(rows=9, cols=4)
    join_vals = [
        ["Source Entity", "Join Condition & Foreign Keys", "Target Entity", "Business Purpose & Expert Sign-Off"],
        ["users", "users.id = wallet_transaction.user_id", "wallet_transaction", "User financial ledger history  [  ] Approved"],
        ["users", "users.id = sku_inventories.status_retailer_id", "sku_inventories", "Retailer product scan assignment  [  ] Approved"],
        ["users", "users.id = sku_inventories.status_wholeseller_id", "sku_inventories", "Wholesaler product scan movement  [  ] Approved"],
        ["users", "users.id = sku_inventories.distributer_id", "sku_inventories", "Distributor inventory allocation  [  ] Approved"],
        ["sku_inventories", "sku_inventories.sku_code = sku_qr_points_maps.sku_code", "sku_qr_points_maps", "Product UOM & Cash Points lookup  [  ] Approved"],
        ["users", "users.id = withdrawal_request.user_id", "withdrawal_request", "Cash payout withdrawal requests  [  ] Approved"],
        ["withdrawal_request", "withdrawal_request.automatic_transaction_id = automatic_transactions.id", "automatic_transactions", "Bank API payout execution log  [  ] Approved"],
        ["companies", "companies.business_info_id = users.business_info_id", "users", "Enterprise business unit grouping  [  ] Approved"]
    ]
    for r_idx, rvals in enumerate(join_vals):
        for c_idx, val in enumerate(rvals):
            join_table.cell(r_idx, c_idx).paragraphs[0].add_run(val)
    style_table(join_table, col_widths=[1.2, 2.3, 1.3, 1.8])
    doc.add_paragraph()

    add_heading_2("5.2 Canonical Timestamp Bounds")
    date_table = doc.add_table(rows=7, cols=4)
    date_vals = [
        ["Table Name", "Timestamp Column", "Data Type", "Time-Filtered Analytics Purpose & Verification"],
        ["wallet_transaction", "created_at", "TIMESTAMP", "Standard filter for monthly Earnings & Redemptions  [  ] Verified"],
        ["sku_inventories", "retailer_scanned_at", "TIMESTAMP", "Standard filter for Retailer Box Scans in month X  [  ] Verified"],
        ["sku_inventories", "wholeseller_scanned_at", "TIMESTAMP", "Standard filter for Wholesaler Box Scans in month X  [  ] Verified"],
        ["sku_inventories", "created_at", "TIMESTAMP", "Inventory batch creation timestamp  [  ] Verified"],
        ["users", "created_at", "TIMESTAMP", "User registration & onboarding timestamp  [  ] Verified"],
        ["withdrawal_request", "created_at", "TIMESTAMP", "Cash payout request initiation timestamp  [  ] Verified"]
    ]
    for r_idx, rvals in enumerate(date_vals):
        for c_idx, val in enumerate(rvals):
            date_table.cell(r_idx, c_idx).paragraphs[0].add_run(val)
    style_table(date_table, col_widths=[1.5, 1.5, 1.0, 2.6])
    doc.add_paragraph()

    # -------------------------------------------------------------------------
    # SECTION 6: COMPLETE PROFILED ENUMS CATALOGUE
    # -------------------------------------------------------------------------
    add_heading_1("6. COMPLETE PROFILED ENUMS CATALOGUE")

    enum_cat_table = doc.add_table(rows=7, cols=3)
    enum_cat_vals = [
        ["Target Column", "Raw Database Distinct Values & Frequencies", "Mapped Business Category & Sign-Off"],
        ["wallet_transaction.reference_type", "cash_point (6.36M), withdrawal (35.9K), topup (117.5K), incentive (5.0K), bonus_conversion (3.4K), referral_earning (2.6K), credit_note (511)", "Earnings vs Redemptions  [  ] Approved"],
        ["wallet_transaction.status", "1 (100,000 Sampled / Active Completed)", "Completed Financial Transaction  [  ] Approved"],
        ["sku_inventories.order_type", "Distributor (52,106), Distributors (47,894)", "Wholesaler / Distributor Scan  [  ] Approved"],
        ["sku_inventories.sources", "kolkata (100,000)", "Primary Warehouse Location  [  ] Approved"],
        ["sku_qr_points_maps.gride_type", "FG_BIG (6,724), FG_SMALL (1,250), NULL (90)", "Finished Goods Box Size  [  ] Approved"],
        ["sku_qr_points_maps.uom", "B10 (3,594), B5 (3,067), B6 (64), B12 (22), B3 (1,142), B1 (153), '' (22)", "Package UOM Box Count  [  ] Approved"]
    ]
    for r_idx, rvals in enumerate(enum_cat_vals):
        for c_idx, val in enumerate(rvals):
            enum_cat_table.cell(r_idx, c_idx).paragraphs[0].add_run(val)
    style_table(enum_cat_table, col_widths=[2.0, 2.6, 2.0])
    doc.add_paragraph()

    # -------------------------------------------------------------------------
    # SECTION 7: SECURITY, PRIVACY & GOVERNANCE COMPLIANCE
    # -------------------------------------------------------------------------
    add_heading_1("7. SECURITY, PRIVACY & GOVERNANCE COMPLIANCE")
    add_body_p(
        "Complete blacklist of 16 detected sensitive columns hard-blocked from LLM prompts and query response outputs."
    )

    sec_table = doc.add_table(rows=17, cols=5)
    sec_vals = [
        ["Table Name", "Column Name", "Data Type", "Keyword Matched", "Security Policy & Sign-Off"],
        ["campaign_logs", "device_token", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["company_controls", "key", "varchar", "key", "Blacklisted from LLM  [  ] Approved"],
        ["connection_request", "auth_code", "varchar", "auth", "Blacklisted from LLM  [  ] Approved"],
        ["employees", "password", "varchar", "password", "Blacklisted from LLM  [  ] Approved"],
        ["notification_logs", "device_token", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["notifications", "device_token", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["password_resets", "token", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["personal_access_tokens", "tokenable_type", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["personal_access_tokens", "tokenable_id", "bigint", "token", "Blacklisted from LLM  [  ] Approved"],
        ["personal_access_tokens", "token", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["tripur_api_tokens", "access_token", "text", "token", "Blacklisted from LLM  [  ] Approved"],
        ["tripur_api_tokens", "token_type", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["users", "password", "varchar", "password", "Blacklisted from LLM  [  ] Approved"],
        ["users", "two_factor_secret", "text", "secret", "Blacklisted from LLM  [  ] Approved"],
        ["users", "remember_token", "varchar", "token", "Blacklisted from LLM  [  ] Approved"],
        ["users", "fcm_token", "varchar", "token", "Blacklisted from LLM  [  ] Approved"]
    ]
    for r_idx, rvals in enumerate(sec_vals):
        for c_idx, val in enumerate(rvals):
            sec_table.cell(r_idx, c_idx).paragraphs[0].add_run(val)
    style_table(sec_table, col_widths=[1.5, 1.5, 0.9, 1.0, 1.7])
    doc.add_paragraph()

    # -------------------------------------------------------------------------
    # SECTION 8: FORMAL DOMAIN EXPERT SIGN-OFF MATRIX
    # -------------------------------------------------------------------------
    add_heading_1("8. FORMAL DOMAIN EXPERT SIGN-OFF MATRIX")

    sign_table = doc.add_table(rows=2, cols=1)
    p_hdr = sign_table.cell(0, 0).paragraphs[0]
    p_hdr.add_run("JGH INTELLIGENCE ENGINE — IEEE STD 830-1998 FORMAL SPECIFICATION APPROVAL").bold = True
    set_cell_background(sign_table.cell(0, 0), HEX_HEADER_BG)

    p_body = sign_table.cell(1, 0).paragraphs[0]
    p_body.add_run(
        "I hereby confirm that I have reviewed the ground-truth specification, user roles taxonomy, "
        "relational join paths, temporal date bounds, business metric definitions, and security blacklists in this document.\n\n"
        "[  ] Section 3: User Roles Approved         [  ] Section 4: Calculated Metrics Approved\n"
        "[  ] Section 5: Join Paths & Dates Verified  [  ] Section 6: Profiled Enums Approved\n"
        "[  ] Section 7: Security Blacklist Approved\n\n"
        "Domain Expert Name: ____________________________________________________\n\n"
        "Title / Designation: _______________________________________________________________\n\n"
        "Signature: ________________________________________   Date: ____________________"
    )
    set_cell_background(sign_table.cell(1, 0), "F8FAFC")
    format_paragraph(p_body, space_before=6, space_after=6)

    docx_path = KNOWLEDGE_DIR / "IEEE_830_JGH_System_Specification.docx"
    doc.save(str(docx_path))
    print(f"[OK] Generated Word Specification at: {docx_path.relative_to(PROJECT_ROOT)}")


# -----------------------------------------------------------------------------
# 3. PDF GENERATION FUNCTION (reportlab)
# -----------------------------------------------------------------------------
def generate_pdf_specification(data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.pdfgen import canvas

    BRAND_DARK      = colors.HexColor("#0F172A")
    BRAND_PRIMARY   = colors.HexColor("#1E3A8A")
    BRAND_ACCENT    = colors.HexColor("#2563EB")
    BRAND_MUTED     = colors.HexColor("#64748B")
    BRAND_LIGHT     = colors.HexColor("#F8FAFC")
    WHITE           = colors.white
    TABLE_HEADER_BG = colors.HexColor("#1E293B")
    TABLE_ALT_ROW   = colors.HexColor("#F1F5F9")
    TABLE_BORDER    = colors.HexColor("#CBD5E1")

    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_decorations(num_pages)
                super().showPage()
            super().save()

        def draw_page_decorations(self, page_count):
            page = self._pageNumber
            self.saveState()
            if page > 1:
                self.setFont("Helvetica-Bold", 8)
                self.setFillColor(BRAND_PRIMARY)
                self.drawString(1.5 * cm, A4[1] - 1.2 * cm, "JGH INTELLIGENCE ENGINE — IEEE 830-1998 SRS")
                self.setFont("Helvetica", 8)
                self.setFillColor(BRAND_MUTED)
                self.drawRightString(A4[0] - 1.5 * cm, A4[1] - 1.2 * cm, "GROUND-TRUTH SYSTEM SPECIFICATION")

                self.setStrokeColor(TABLE_BORDER)
                self.setLineWidth(0.5)
                self.line(1.5 * cm, A4[1] - 1.35 * cm, A4[0] - 1.5 * cm, A4[1] - 1.35 * cm)

            self.setFont("Helvetica", 8)
            self.setFillColor(BRAND_MUTED)
            self.drawString(1.5 * cm, 0.9 * cm, "Confidential — IEEE 830-1998 Formal Specification Deliverable")
            self.drawRightString(A4[0] - 1.5 * cm, 0.9 * cm, f"Page {page} of {page_count}")

            self.setStrokeColor(TABLE_BORDER)
            self.setLineWidth(0.5)
            self.line(1.5 * cm, 1.15 * cm, A4[0] - 1.5 * cm, 1.15 * cm)
            self.restoreState()

    pdf_path = KNOWLEDGE_DIR / "IEEE_830_JGH_System_Specification.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )

    base_styles = getSampleStyleSheet()
    styles = {}

    styles['DocTitle'] = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=BRAND_PRIMARY, alignment=TA_CENTER, spaceAfter=3)
    styles['DocSubtitle'] = ParagraphStyle('DocSubtitle', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=BRAND_MUTED, alignment=TA_CENTER, spaceAfter=12)
    styles['SectionHeader'] = ParagraphStyle('SectionHeader', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=BRAND_DARK, spaceBefore=12, spaceAfter=4)
    styles['SubSectionHeader'] = ParagraphStyle('SubSectionHeader', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=BRAND_ACCENT, spaceBefore=6, spaceAfter=3)
    styles['Body'] = ParagraphStyle('Body', fontName='Helvetica', fontSize=7.5, leading=10, textColor=BRAND_DARK, spaceAfter=4)
    styles['TableCell'] = ParagraphStyle('TableCell', fontName='Helvetica', fontSize=7, leading=9, textColor=BRAND_DARK)
    styles['TableCellBold'] = ParagraphStyle('TableCellBold', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=BRAND_DARK)
    styles['TableHeader'] = ParagraphStyle('TableHeader', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=WHITE, alignment=TA_LEFT)

    story = []

    # -------------------------------------------------------------------------
    # COVER TITLE & CONTROL TABLE
    # -------------------------------------------------------------------------
    story.append(Paragraph("SOFTWARE REQUIREMENTS SPECIFICATION (SRS)<br/>& SYSTEM GROUND-TRUTH DATA DICTIONARY", styles['DocTitle']))
    story.append(Paragraph("IEEE Std 830-1998 Compliant Specification for JGH Project Intelligence Engine", styles['DocSubtitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_PRIMARY, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("<b>Section 1: Introduction & Executive Overview</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "This IEEE Std 830-1998 compliant document establishes the ground-truth technical specification "
        "for the JGH AI Intelligence Engine operating on <b>jghMasterDB</b> (MySQL 8.0, 238 tables). "
        "It defines taxonomy, schema join graphs, timestamp bounds, business metrics, and PII security controls.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    gen_time = datetime.now().isoformat()[:10]
    overview_data = [
        [Paragraph("<b>Document ID:</b>", styles['TableCellBold']), Paragraph("IEEE-SRS-JGH-2026-V1.0", styles['TableCell']), Paragraph("<b>Target Database:</b>", styles['TableCellBold']), Paragraph("jghMasterDB (MySQL 8.0)", styles['TableCell'])],
        [Paragraph("<b>Compliance Std:</b>", styles['TableCellBold']), Paragraph("IEEE Std 830-1998", styles['TableCell']), Paragraph("<b>Total Tables:</b>", styles['TableCellBold']), Paragraph(str(data['total_tables']), styles['TableCell'])],
        [Paragraph("<b>Profiled Enums:</b>", styles['TableCellBold']), Paragraph(f"{data['total_profiled']} Columns", styles['TableCell']), Paragraph("<b>Security Blacklist:</b>", styles['TableCellBold']), Paragraph(f"{data['total_restricted']} Columns", styles['TableCell'])],
        [Paragraph("<b>Candidate Joins:</b>", styles['TableCellBold']), Paragraph(f"{data['total_edges']:,} Edges", styles['TableCell']), Paragraph("<b>Revision Date:</b>", styles['TableCellBold']), Paragraph(gen_time, styles['TableCell'])],
        [Paragraph("<b>Document Status:</b>", styles['TableCellBold']), Paragraph("<font color='#2563EB'><b>PENDING DOMAIN EXPERT SIGN-OFF</b></font>", styles['TableCell']), Paragraph("<b>Licensing:</b>", styles['TableCellBold']), Paragraph("100% FOSS On-Premises Stack", styles['TableCell'])]
    ]
    overview_table = Table(overview_data, colWidths=[4.2*cm, 4.5*cm, 4.2*cm, 4.5*cm])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 8))

    # Definitions Table
    story.append(Paragraph("<b>IEEE 830 Terminology & Acronyms</b>", styles['SubSectionHeader']))
    acronym_headers = [Paragraph("Term / Acronym", styles['TableHeader']), Paragraph("IEEE SRS Definition & Context", styles['TableHeader'])]
    acronym_rows = [
        acronym_headers,
        [Paragraph("<b>AST</b>", styles['TableCellBold']), Paragraph("Abstract Syntax Tree - Structured node tree used by SQLGlot to validate SQL queries without execution.", styles['TableCell'])],
        [Paragraph("<b>Sargable</b>", styles['TableCellBold']), Paragraph("Search Argument Able - SQL predicate design ensuring index utilization (avoiding functions on indexed columns).", styles['TableCell'])],
        [Paragraph("<b>Enum</b>", styles['TableCellBold']), Paragraph("Low-cardinality discrete value set (<= 50 distinct values) mapped to domain business meanings.", styles['TableCell'])],
        [Paragraph("<b>PII</b>", styles['TableCellBold']), Paragraph("Personally Identifiable Information & sensitive secrets (passwords, tokens, keys) hard-blocked from LLM prompts.", styles['TableCell'])],
        [Paragraph("<b>RAG</b>", styles['TableCellBold']), Paragraph("Retrieval-Augmented Generation - Schema & relationship vector retrieval augmenting LLM prompts.", styles['TableCell'])],
        [Paragraph("<b>FOSS</b>", styles['TableCellBold']), Paragraph("Free & Open Source Software - Self-contained offline deployment stack (FastAPI, Ollama, ChromaDB, MySQL).", styles['TableCell'])],
        [Paragraph("<b>ERD</b>", styles['TableCellBold']), Paragraph("Entity-Relationship Diagram - Architectural visualization of database schemas and foreign key edges.", styles['TableCell'])],
        [Paragraph("<b>Incognito Ephemeral</b>", styles['TableCellBold']), Paragraph("Zero-history transient state mode where chat sessions leave no persistent logs.", styles['TableCell'])]
    ]
    acronym_table = Table(acronym_rows, colWidths=[4.2*cm, 13.2*cm])
    acronym_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
    ]))
    story.append(acronym_table)

    # -------------------------------------------------------------------------
    # SECTION 2: SYSTEM ARCHITECTURE & OVERALL DESCRIPTION
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Section 2: System Architecture & Overall Description</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "<b>Product Perspective:</b> Decoupled 6-stage execution flow:<br/>"
        "1. React + Vite Frontend UI (Chat, Data Tables, Recharts, History Drawer, Admin Dashboard)<br/>"
        "2. Security & Privacy Gateway (Input Sanitization, PII Redaction, Password/Token Scrubbing)<br/>"
        "3. Multi-Intent Router (Conversational Analytics vs Schema Tutor vs Mermaid ERD vs Executive Storyteller)<br/>"
        "4. Execution Engine (SQLGlot AST Validation -> EXPLAIN Cost Check -> Read-Only MySQL Execution)<br/>"
        "5. Response Synthesizer (Gemini-Style markdown text + tabular output rendering)<br/>"
        "6. Ephemeral Privacy Controller (Zero-history mode when is_private=true)",
        styles['Body']
    ))

    # -------------------------------------------------------------------------
    # SECTION 3: SYSTEM TAXONOMY & USER ROLE GROUND TRUTH
    # -------------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("<b>Section 3: System Taxonomy & User Role Ground Truth</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "Complete mapping of all 13 distinct user_role integer codes extracted from 29,063 profile records in the users table.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    role_headers = [Paragraph("Role Code", styles['TableHeader']), Paragraph("User Count", styles['TableHeader']), Paragraph("% Share", styles['TableHeader']), Paragraph("Role Name / Title", styles['TableHeader']), Paragraph("Operational Category & Expert Sign-Off", styles['TableHeader'])]
    role_rows = [
        role_headers,
        [Paragraph("<b>user_role = 1</b>", styles['TableCellBold']), Paragraph("6", styles['TableCell']), Paragraph("0.02%", styles['TableCell']), Paragraph("Executive / Staff", styles['TableCellBold']), Paragraph("Internal Operations Staff  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 2</b>", styles['TableCellBold']), Paragraph("27,703", styles['TableCell']), Paragraph("95.32%", styles['TableCell']), Paragraph("Retailer / Mechanic", styles['TableCellBold']), Paragraph("Primary Loyalty Earners  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 3</b>", styles['TableCellBold']), Paragraph("6", styles['TableCell']), Paragraph("0.02%", styles['TableCell']), Paragraph("Area Executive", styles['TableCellBold']), Paragraph("Field Sales Team  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 4</b>", styles['TableCellBold']), Paragraph("457", styles['TableCell']), Paragraph("1.57%", styles['TableCell']), Paragraph("Distributor Partner", styles['TableCellBold']), Paragraph("Supply Chain Channel  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 5</b>", styles['TableCellBold']), Paragraph("573", styles['TableCell']), Paragraph("1.97%", styles['TableCell']), Paragraph("Wholesaler / Stockist", styles['TableCellBold']), Paragraph("Supply Chain Channel  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 6</b>", styles['TableCellBold']), Paragraph("248", styles['TableCell']), Paragraph("0.85%", styles['TableCell']), Paragraph("Super Distributor", styles['TableCellBold']), Paragraph("Enterprise Distribution  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 7</b>", styles['TableCellBold']), Paragraph("1", styles['TableCell']), Paragraph("0.00%", styles['TableCell']), Paragraph("System Master Admin", styles['TableCellBold']), Paragraph("Platform Governance  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 8</b>", styles['TableCellBold']), Paragraph("6", styles['TableCell']), Paragraph("0.02%", styles['TableCell']), Paragraph("Finance Auditor", styles['TableCellBold']), Paragraph("Audit & Compliance  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 10</b>", styles['TableCellBold']), Paragraph("23", styles['TableCell']), Paragraph("0.08%", styles['TableCell']), Paragraph("Field Executive", styles['TableCellBold']), Paragraph("Field Sales & Scans  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 11</b>", styles['TableCellBold']), Paragraph("10", styles['TableCell']), Paragraph("0.03%", styles['TableCell']), Paragraph("Regional Manager", styles['TableCellBold']), Paragraph("Regional Management  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 13</b>", styles['TableCellBold']), Paragraph("3", styles['TableCell']), Paragraph("0.01%", styles['TableCell']), Paragraph("Support Manager", styles['TableCellBold']), Paragraph("Customer Helpdesk  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = 14</b>", styles['TableCellBold']), Paragraph("1", styles['TableCell']), Paragraph("0.00%", styles['TableCell']), Paragraph("Sandbox / Test User", styles['TableCellBold']), Paragraph("QA & Integration Testing  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>user_role = NULL</b>", styles['TableCellBold']), Paragraph("25", styles['TableCell']), Paragraph("0.09%", styles['TableCell']), Paragraph("Unassigned Profile", styles['TableCellBold']), Paragraph("Legacy Unassigned  [  ] Approved", styles['TableCell'])]
    ]
    role_table = Table(role_rows, colWidths=[2.6*cm, 2.2*cm, 1.8*cm, 4.5*cm, 6.3*cm])
    role_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(role_table)

    # -------------------------------------------------------------------------
    # SECTION 4: DOMAIN SEMANTICS & CALCULATED METRICS
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Section 4: Domain Semantics & Calculated Metrics</b>", styles['SectionHeader']))
    metrics_headers = [Paragraph("Metric Name", styles['TableHeader']), Paragraph("Target Table & Column", styles['TableHeader']), Paragraph("Proposed SQL Expression", styles['TableHeader']), Paragraph("Business Definition & Expert Sign-Off", styles['TableHeader'])]
    metrics_rows = [
        metrics_headers,
        [Paragraph("<b>1. Static Profile Balance</b>", styles['TableCellBold']), Paragraph("<code>users.wallet_balance</code>", styles['TableCell']), Paragraph("<code>SUM(wallet_balance)</code>", styles['TableCell']), Paragraph("Stored wallet balance snapshot  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>2. Dynamic Ledger Balance</b>", styles['TableCellBold']), Paragraph("<code>wallet_transaction.amount</code>", styles['TableCell']), Paragraph("<code>SUM(CASE WHEN reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN amount ELSE -amount END)</code>", styles['TableCell']), Paragraph("Net calculated financial balance  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>3. Gross Earnings</b>", styles['TableCellBold']), Paragraph("<code>wallet_transaction.amount</code>", styles['TableCell']), Paragraph("<code>SUM(amount) WHERE reference_type IN ('cash_point', 'topup', 'incentive', 'bonus_conversion', 'referral_earning', 'credit_note')</code>", styles['TableCell']), Paragraph("Total monetary credits earned  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>4. Total Redemptions</b>", styles['TableCellBold']), Paragraph("<code>wallet_transaction.amount</code>", styles['TableCell']), Paragraph("<code>SUM(amount) WHERE reference_type = 'withdrawal'</code>", styles['TableCell']), Paragraph("Total cash payouts redeemed  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>5. Retailer Box Scans</b>", styles['TableCellBold']), Paragraph("<code>sku_inventories.order_type</code>", styles['TableCell']), Paragraph("<code>COUNT(*) WHERE order_type = 'Retailer' AND retailer_scanned_at IS NOT NULL</code>", styles['TableCell']), Paragraph("Retailer QR box scans completed  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>6. Wholesaler Box Scans</b>", styles['TableCellBold']), Paragraph("<code>sku_inventories.order_type</code>", styles['TableCell']), Paragraph("<code>COUNT(*) WHERE order_type IN ('Distributor', 'Distributors') AND wholeseller_scanned_at IS NOT NULL</code>", styles['TableCell']), Paragraph("Wholesaler box scans completed  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>7. Total Points Earned</b>", styles['TableCellBold']), Paragraph("<code>sku_qr_points_maps.retailer_cash_points</code>", styles['TableCell']), Paragraph("<code>SUM(q.retailer_cash_points + q.wholeseller_cash_points) via sku_code join</code>", styles['TableCell']), Paragraph("Total reward points generated  [  ] Approved", styles['TableCell'])]
    ]
    metrics_table = Table(metrics_rows, colWidths=[3.2*cm, 3.8*cm, 5.4*cm, 5.0*cm])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(metrics_table)

    # -------------------------------------------------------------------------
    # SECTION 5: RELATIONAL DATA ARCHITECTURE & TEMPORAL BOUNDS
    # -------------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("<b>Section 5: Relational Data Architecture & Temporal Bounds</b>", styles['SectionHeader']))

    story.append(Paragraph("<b>5.1 Dual-Role Schema Join Graph</b>", styles['SubSectionHeader']))
    join_headers = [Paragraph("Source Entity", styles['TableHeader']), Paragraph("Join Condition & Keys", styles['TableHeader']), Paragraph("Target Entity", styles['TableHeader']), Paragraph("Business Purpose & Expert Sign-Off", styles['TableHeader'])]
    join_rows = [
        join_headers,
        [Paragraph("<b>users</b>", styles['TableCellBold']), Paragraph("<code>users.id = wallet_transaction.user_id</code>", styles['TableCell']), Paragraph("<b>wallet_transaction</b>", styles['TableCellBold']), Paragraph("User financial ledger history  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>users</b>", styles['TableCellBold']), Paragraph("<code>users.id = sku_inventories.status_retailer_id</code>", styles['TableCell']), Paragraph("<b>sku_inventories</b>", styles['TableCellBold']), Paragraph("Retailer product scan assignment  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>users</b>", styles['TableCellBold']), Paragraph("<code>users.id = sku_inventories.status_wholeseller_id</code>", styles['TableCell']), Paragraph("<b>sku_inventories</b>", styles['TableCellBold']), Paragraph("Wholesaler product scan movement  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>users</b>", styles['TableCellBold']), Paragraph("<code>users.id = sku_inventories.distributer_id</code>", styles['TableCell']), Paragraph("<b>sku_inventories</b>", styles['TableCellBold']), Paragraph("Distributor inventory allocation  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>sku_inventories</b>", styles['TableCellBold']), Paragraph("<code>sku_inventories.sku_code = sku_qr_points_maps.sku_code</code>", styles['TableCell']), Paragraph("<b>sku_qr_points_maps</b>", styles['TableCellBold']), Paragraph("Product UOM & Cash Points lookup  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>users</b>", styles['TableCellBold']), Paragraph("<code>users.id = withdrawal_request.user_id</code>", styles['TableCell']), Paragraph("<b>withdrawal_request</b>", styles['TableCellBold']), Paragraph("Cash payout withdrawal requests  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>withdrawal_request</b>", styles['TableCellBold']), Paragraph("<code>withdrawal_request.automatic_transaction_id = automatic_transactions.id</code>", styles['TableCell']), Paragraph("<b>automatic_transactions</b>", styles['TableCellBold']), Paragraph("Bank API payout execution log  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>companies</b>", styles['TableCellBold']), Paragraph("<code>companies.business_info_id = users.business_info_id</code>", styles['TableCell']), Paragraph("<b>users</b>", styles['TableCellBold']), Paragraph("Enterprise business unit grouping  [  ] Approved", styles['TableCell'])]
    ]
    join_table = Table(join_rows, colWidths=[2.5*cm, 5.0*cm, 3.0*cm, 6.9*cm])
    join_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(join_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>5.2 Canonical Timestamp Bounds</b>", styles['SubSectionHeader']))
    date_headers = [Paragraph("Table Name", styles['TableHeader']), Paragraph("Timestamp Column", styles['TableHeader']), Paragraph("Data Type", styles['TableHeader']), Paragraph("Analytics Purpose & Verification", styles['TableHeader'])]
    date_rows = [
        date_headers,
        [Paragraph("<b>wallet_transaction</b>", styles['TableCellBold']), Paragraph("<code>created_at</code>", styles['TableCellBold']), Paragraph("TIMESTAMP", styles['TableCell']), Paragraph("Standard filter for monthly Earnings & Redemptions  [  ] Verified", styles['TableCell'])],
        [Paragraph("<b>sku_inventories</b>", styles['TableCellBold']), Paragraph("<code>retailer_scanned_at</code>", styles['TableCellBold']), Paragraph("TIMESTAMP", styles['TableCell']), Paragraph("Standard filter for Retailer Box Scans in month X  [  ] Verified", styles['TableCell'])],
        [Paragraph("<b>sku_inventories</b>", styles['TableCellBold']), Paragraph("<code>wholeseller_scanned_at</code>", styles['TableCellBold']), Paragraph("TIMESTAMP", styles['TableCell']), Paragraph("Standard filter for Wholesaler Box Scans in month X  [  ] Verified", styles['TableCell'])],
        [Paragraph("<b>sku_inventories</b>", styles['TableCellBold']), Paragraph("<code>created_at</code>", styles['TableCellBold']), Paragraph("TIMESTAMP", styles['TableCell']), Paragraph("Inventory batch creation timestamp  [  ] Verified", styles['TableCell'])],
        [Paragraph("<b>users</b>", styles['TableCellBold']), Paragraph("<code>created_at</code>", styles['TableCellBold']), Paragraph("TIMESTAMP", styles['TableCell']), Paragraph("User registration & onboarding timestamp  [  ] Verified", styles['TableCell'])],
        [Paragraph("<b>withdrawal_request</b>", styles['TableCellBold']), Paragraph("<code>created_at</code>", styles['TableCellBold']), Paragraph("TIMESTAMP", styles['TableCell']), Paragraph("Cash payout request initiation timestamp  [  ] Verified", styles['TableCell'])]
    ]
    date_table = Table(date_rows, colWidths=[3.5*cm, 3.8*cm, 2.2*cm, 7.9*cm])
    date_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(date_table)

    # -------------------------------------------------------------------------
    # SECTION 6 & 7: PROFILED ENUMS CATALOGUE & SECURITY BLACKLIST
    # -------------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("<b>Section 6: Profiled Enums & Security Blacklist</b>", styles['SectionHeader']))

    story.append(Paragraph("<b>6.1 Target Profiled Enums Catalogue</b>", styles['SubSectionHeader']))
    enum_headers = [Paragraph("Target Column", styles['TableHeader']), Paragraph("Distinct Database Values & Row Frequencies", styles['TableHeader']), Paragraph("Mapped Category & Expert Sign-Off", styles['TableHeader'])]
    enum_rows = [
        enum_headers,
        [Paragraph("<b>wallet_transaction.reference_type</b>", styles['TableCellBold']), Paragraph("cash_point (6.36M), withdrawal (35.9K), topup (117.5K), incentive (5.0K), bonus_conversion (3.4K), referral_earning (2.6K), credit_note (511)", styles['TableCell']), Paragraph("Earnings vs Redemptions  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>wallet_transaction.status</b>", styles['TableCellBold']), Paragraph("1 (100,000 Sampled / Active Completed)", styles['TableCell']), Paragraph("Completed Financial Transaction  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>sku_inventories.order_type</b>", styles['TableCellBold']), Paragraph("Distributor (52,106), Distributors (47,894)", styles['TableCell']), Paragraph("Wholesaler / Distributor Scan  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>sku_inventories.sources</b>", styles['TableCellBold']), Paragraph("kolkata (100,000)", styles['TableCell']), Paragraph("Primary Warehouse Location  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>sku_qr_points_maps.gride_type</b>", styles['TableCellBold']), Paragraph("FG_BIG (6,724), FG_SMALL (1,250), NULL (90)", styles['TableCell']), Paragraph("Finished Goods Box Size  [  ] Approved", styles['TableCell'])],
        [Paragraph("<b>sku_qr_points_maps.uom</b>", styles['TableCellBold']), Paragraph("B10 (3,594), B5 (3,067), B6 (64), B12 (22), B3 (1,142), B1 (153), '' (22)", styles['TableCell']), Paragraph("Package UOM Box Count  [  ] Approved", styles['TableCell'])]
    ]
    enum_table = Table(enum_rows, colWidths=[4.5*cm, 7.5*cm, 5.4*cm])
    enum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(enum_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>6.2 Sensitive Column Security Blacklist</b>", styles['SubSectionHeader']))
    sec_headers = [Paragraph("Table Name", styles['TableHeader']), Paragraph("Column Name", styles['TableHeader']), Paragraph("Data Type", styles['TableHeader']), Paragraph("Keyword Matched", styles['TableHeader']), Paragraph("Security Policy & Sign-Off", styles['TableHeader'])]
    sec_rows = [sec_headers]
    for col in data['restricted_data'].get("restricted_columns", []):
        keywords = ", ".join(col.get("matched_keywords", []))
        sec_rows.append([
            Paragraph(f"<b>{col['table_name']}</b>", styles['TableCellBold']),
            Paragraph(col['column_name'], styles['TableCellBold']),
            Paragraph(col['data_type'], styles['TableCell']),
            Paragraph(f"<font color='#EF4444'><b>{keywords}</b></font>", styles['TableCell']),
            Paragraph("Blacklisted from LLM  [  ] Approved", styles['TableCell'])
        ])
    sec_table = Table(sec_rows, colWidths=[3.8*cm, 4.2*cm, 2.3*cm, 3.0*cm, 4.1*cm])
    sec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 2.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(sec_table)

    # -------------------------------------------------------------------------
    # SECTION 8: FORMAL DOMAIN EXPERT SIGN-OFF MATRIX
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(KeepTogether([
        Paragraph("<b>Section 7: Formal Domain Expert Sign-Off & Approval Matrix</b>", styles['SectionHeader']),
        Spacer(1, 4),
        Table([
            [Paragraph("<b>JGH INTELLIGENCE ENGINE — IEEE STD 830-1998 FORMAL SIGN-OFF</b>", styles['TableHeader'])],
            [Paragraph(
                "<br/>"
                "I hereby confirm that I have reviewed the IEEE Std 830-1998 SRS specification, user role taxonomy, "
                "relational join paths, temporal date bounds, business metric definitions, and security blacklists in this document.<br/><br/>"
                "<b>[  ] Section 3: User Roles Approved</b> &nbsp;&nbsp;&nbsp;&nbsp; "
                "<b>[  ] Section 4: Metrics Approved</b> &nbsp;&nbsp;&nbsp;&nbsp; "
                "<b>[  ] Section 5: Join Paths & Dates Verified</b><br/>"
                "<b>[  ] Section 6: Profiled Enums Approved</b> &nbsp;&nbsp;&nbsp;&nbsp; "
                "<b>[  ] Section 7: Security Blacklist Approved</b><br/><br/>"
                "<b>Domain Expert Name:</b> ____________________________________________________<br/><br/>"
                "<b>Title / Designation:</b> _______________________________________________________________<br/><br/>"
                "<b>Signature:</b> ________________________________________   <b>Date:</b> ____________________<br/>",
                styles['TableCell']
            )]
        ], colWidths=[17.4*cm], style=[
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('BACKGROUND', (0, 1), (-1, 1), BRAND_LIGHT),
            ('GRID', (0, 0), (-1, -1), 1, BRAND_PRIMARY),
            ('PADDING', (0, 0), (-1, -1), 6),
        ])
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated IEEE SRS PDF Document at: {pdf_path.relative_to(PROJECT_ROOT)}")


# -----------------------------------------------------------------------------
# MAIN EXECUTION ENTRYPOINT
# -----------------------------------------------------------------------------
def run_formal_specification_export():
    print("=" * 65)
    print(" 📜 JGH Intelligence Engine - Formal IEEE SRS Export Tool")
    print("=" * 65)

    data = load_phase0_data()
    print(f"[+] Loaded Phase 0 Dataset: {data['total_tables']} tables, {data['total_profiled']} enums, {data['total_restricted']} security columns.")

    print("\n[1/2] Generating Word Document (knowledge/IEEE_830_JGH_System_Specification.docx)...")
    generate_docx_specification(data)

    print("\n[2/2] Generating PDF Report (knowledge/IEEE_830_JGH_System_Specification.pdf)...")
    generate_pdf_specification(data)

    print("\n" + "=" * 65)
    print(" ✅ IEEE Std 830-1998 Formal Specification Export Completed!")
    print("=" * 65)

if __name__ == "__main__":
    run_formal_specification_export()
