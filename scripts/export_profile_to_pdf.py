"""
Phase 0 Comprehensive Introspection PDF Review Document Generator for JGH Intelligence Engine.
Compiles draft_db_profile.json, draft_restricted_columns.json, draft_relationship_graph.json, and business_dictionary.json
into an exhaustive multi-page PDF document (knowledge/Phase_0_Comprehensive_Expert_Review.pdf)
for domain expert review, schema validation, and formal sign-off.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
SCHEMA_DIR = KNOWLEDGE_DIR / "schema"

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# ── Color Palette ───────────────────────────────────────────────────────────
BRAND_DARK      = colors.HexColor("#0F172A")   # Slate 900
BRAND_PRIMARY   = colors.HexColor("#1E3A8A")   # Blue 900
BRAND_ACCENT    = colors.HexColor("#2563EB")   # Blue 600
BRAND_SUCCESS   = colors.HexColor("#166534")   # Green 800
BRAND_WARNING   = colors.HexColor("#9A3412")   # Amber 800
BRAND_MUTED     = colors.HexColor("#64748B")   # Slate 500
BRAND_LIGHT     = colors.HexColor("#F8FAFC")   # Slate 50
WHITE           = colors.white
BLACK           = colors.black
TABLE_HEADER_BG = colors.HexColor("#1E293B")   # Slate 800
TABLE_ALT_ROW   = colors.HexColor("#F1F5F9")   # Slate 100
TABLE_BORDER    = colors.HexColor("#CBD5E1")   # Slate 300


# ── Numbered Canvas with Dynamic Running Header & Footer ─────────────────────
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

        # Header for page 2 and onwards
        if page > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(BRAND_PRIMARY)
            self.drawString(1.5 * cm, A4[1] - 1.2 * cm, "JGH INTELLIGENCE ENGINE — PHASE 0 REVIEW")
            self.setFont("Helvetica", 8)
            self.setFillColor(BRAND_MUTED)
            self.drawRightString(A4[0] - 1.5 * cm, A4[1] - 1.2 * cm, "EXHAUSTIVE DOMAIN EXPERT SIGN-OFF")

            self.setStrokeColor(TABLE_BORDER)
            self.setLineWidth(0.5)
            self.line(1.5 * cm, A4[1] - 1.35 * cm, A4[0] - 1.5 * cm, A4[1] - 1.35 * cm)

        # Footer across all pages
        self.setFont("Helvetica", 8)
        self.setFillColor(BRAND_MUTED)
        self.drawString(1.5 * cm, 0.9 * cm, "Confidential — JGH Project Intelligence Engine Phase 0 Audit")
        self.drawRightString(A4[0] - 1.5 * cm, 0.9 * cm, f"Page {page} of {page_count}")

        self.setStrokeColor(TABLE_BORDER)
        self.setLineWidth(0.5)
        self.line(1.5 * cm, 1.15 * cm, A4[0] - 1.5 * cm, 1.15 * cm)

        self.restoreState()


def build_pdf_document():
    print("=" * 60)
    print(" 📄 JGH Intelligence Engine - Comprehensive PDF Review Generator")
    print("=" * 60)

    # 1. Load Data Files
    profile_path = KNOWLEDGE_DIR / "draft_db_profile.json"
    restricted_path = KNOWLEDGE_DIR / "draft_restricted_columns.json"
    dictionary_path = KNOWLEDGE_DIR / "business_dictionary.json"
    schema_path = SCHEMA_DIR / "draft_schema_metadata.json"
    graph_path = KNOWLEDGE_DIR / "draft_relationship_graph.json"

    with open(profile_path, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    with open(restricted_path, "r", encoding="utf-8") as f:
        restricted_data = json.load(f)

    with open(dictionary_path, "r", encoding="utf-8") as f:
        dictionary_data = json.load(f)

    total_tables = 238
    if schema_path.exists():
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
                total_tables = schema_data.get("total_tables", 238)
        except Exception:
            pass

    total_edges = 32251
    if graph_path.exists():
        try:
            with open(graph_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
                total_edges = graph_data.get("total_candidate_edges", 32251)
        except Exception:
            pass

    output_pdf_path = KNOWLEDGE_DIR / "Phase_0_Comprehensive_Expert_Review.pdf"

    # 2. Setup Page & Styles
    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )

    base_styles = getSampleStyleSheet()
    styles = {}

    styles['DocTitle'] = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=BRAND_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=3
    )

    styles['DocSubtitle'] = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=BRAND_MUTED,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    styles['SectionHeader'] = ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=BRAND_DARK,
        spaceBefore=12,
        spaceAfter=5
    )

    styles['SubSectionHeader'] = ParagraphStyle(
        'SubSectionHeader',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=BRAND_ACCENT,
        spaceBefore=7,
        spaceAfter=4
    )

    styles['Body'] = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=BRAND_DARK,
        spaceAfter=4
    )

    styles['TableCell'] = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=BRAND_DARK
    )

    styles['TableCellBold'] = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=BRAND_DARK
    )

    styles['TableHeader'] = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=WHITE,
        alignment=TA_LEFT
    )

    story = []

    # -------------------------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY & OVERVIEW
    # -------------------------------------------------------------------------
    story.append(Paragraph("JGH PROJECT INTELLIGENCE ENGINE", styles['DocTitle']))
    story.append(Paragraph("PHASE 0 COMPREHENSIVE EXPERT REVIEW SHEET & SPECIFICATION SIGN-OFF", styles['DocSubtitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BRAND_PRIMARY, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("<b>Section 1: Executive Summary & Database Scope</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "This document presents the complete Phase 0 database introspection report for <b>jghMasterDB</b>. "
        "Domain experts must review and formally approve: (1) Exhaustive user role definitions, "
        "(2) Core schema join paths, (3) Temporal date filters for time-based analytics, "
        "(4) Expanded business metrics SQL definitions, and (5) Security blacklists.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    # Overview Table
    total_profiled_cols = len(profile_data.get("all_low_cardinality_columns", {}))
    total_restricted_cols = restricted_data.get("total_restricted_columns", 16)
    gen_time = profile_data.get("generated_at", datetime.now().isoformat())[:19].replace("T", " ")

    overview_data = [
        [
            Paragraph("<b>Target Database:</b>", styles['TableCellBold']),
            Paragraph("jghMasterDB (MySQL 8.0)", styles['TableCell']),
            Paragraph("<b>Total Tables Analyzed:</b>", styles['TableCellBold']),
            Paragraph(str(total_tables), styles['TableCell'])
        ],
        [
            Paragraph("<b>Profiled Enums:</b>", styles['TableCellBold']),
            Paragraph(f"{total_profiled_cols} Columns Profiled", styles['TableCell']),
            Paragraph("<b>Restricted Security Cols:</b>", styles['TableCellBold']),
            Paragraph(f"{total_restricted_cols} Blacklisted", styles['TableCell'])
        ],
        [
            Paragraph("<b>Candidate Join Edges:</b>", styles['TableCellBold']),
            Paragraph(f"{total_edges:,} Graph Edges", styles['TableCell']),
            Paragraph("<b>Generated Timestamp:</b>", styles['TableCellBold']),
            Paragraph(gen_time, styles['TableCell'])
        ],
        [
            Paragraph("<b>Review Purpose:</b>", styles['TableCellBold']),
            Paragraph("<font color='#2563EB'><b>EXHAUSTIVE DOMAIN EXPERT SIGN-OFF</b></font>", styles['TableCell']),
            Paragraph("<b>Target Scope:</b>", styles['TableCellBold']),
            Paragraph("8 Core Target Tables + Master DB", styles['TableCell'])
        ]
    ]

    overview_table = Table(overview_data, colWidths=[4.2*cm, 4.5*cm, 4.2*cm, 4.5*cm])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 2: EXHAUSTIVE USER ROLE MAPPING & ENUM PROFILING
    # -------------------------------------------------------------------------
    story.append(Paragraph("<b>Section 2: Exhaustive User Role Mapping & Low-Cardinality Enums</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "Below is the complete inventory of all distinct <b>user_role</b> integer codes extracted from <code>users</code> table (29,063 total rows). "
        "Domain experts must confirm the exact role name and operational category for EVERY role integer.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    role_headers = [
        Paragraph("Role Code", styles['TableHeader']),
        Paragraph("User Count in DB", styles['TableHeader']),
        Paragraph("% of Users", styles['TableHeader']),
        Paragraph("Proposed Role Name / Title", styles['TableHeader']),
        Paragraph("Operational Category & Expert Sign-Off Line", styles['TableHeader'])
    ]

    all_roles_data = [
        ("user_role = 1", "6", "0.02%", "Executive / Staff", "Category: Internal Staff  [  ] Approved"),
        ("user_role = 2", "27,703", "95.32%", "Retailer / Mechanic / End User", "Category: Primary Earners  [  ] Approved"),
        ("user_role = 3", "6", "0.02%", "Area Executive / Sales Rep", "Category: Field Team  [  ] Approved"),
        ("user_role = 4", "457", "1.57%", "Distributor / Channel Partner", "Category: Supply Chain  [  ] Approved"),
        ("user_role = 5", "573", "1.97%", "Wholesaler / Stockist", "Category: Supply Chain  [  ] Approved"),
        ("user_role = 6", "248", "0.85%", "Super Distributor / Enterprise", "Category: Supply Chain  [  ] Approved"),
        ("user_role = 7", "1", "0.00%", "System Admin / Master User", "Category: System Control  [  ] Approved"),
        ("user_role = 8", "6", "0.02%", "Company Auditor / Finance", "Category: Operations  [  ] Approved"),
        ("user_role = 10", "23", "0.08%", "Field Executive", "Category: Field Team  [  ] Approved"),
        ("user_role = 11", "10", "0.03%", "Regional Manager", "Category: Management  [  ] Approved"),
        ("user_role = 13", "3", "0.01%", "Support Manager", "Category: Support  [  ] Approved"),
        ("user_role = 14", "1", "0.00%", "Test / Sandbox User", "Category: Testing  [  ] Approved"),
        ("user_role = NULL", "25", "0.09%", "Unassigned Profile", "Category: Legacy Unassigned  [  ] Approved"),
    ]

    role_rows = [role_headers]
    for rcode, rcnt, rpct, rprop, rline in all_roles_data:
        role_rows.append([
            Paragraph(f"<b>{rcode}</b>", styles['TableCellBold']),
            Paragraph(rcnt, styles['TableCell']),
            Paragraph(rpct, styles['TableCell']),
            Paragraph(rprop, styles['TableCellBold']),
            Paragraph(rline, styles['TableCell'])
        ])

    role_table = Table(role_rows, colWidths=[2.6*cm, 2.5*cm, 2.0*cm, 4.5*cm, 5.8*cm])
    role_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(role_table)
    story.append(Spacer(1, 8))

    # Low-Cardinality Enums Summary Table
    story.append(Paragraph("<b>Target Low-Cardinality Enum Summary</b>", styles['SubSectionHeader']))
    enum_summary_headers = [
        Paragraph("Table & Column Name", styles['TableHeader']),
        Paragraph("Distinct Database Values & Row Counts", styles['TableHeader']),
        Paragraph("Expert Sign-Off & Mapping Rules", styles['TableHeader'])
    ]

    enum_summary_data = [
        enum_summary_headers,
        [
            Paragraph("<b>wallet_transaction.reference_type</b>", styles['TableCellBold']),
            Paragraph("cash_point (6.36M), withdrawal (35.9K), topup (117.5K), incentive (5.0K), bonus_conversion (3.4K), referral_earning (2.6K), credit_note (511)", styles['TableCell']),
            Paragraph("Earnings: cash_point, topup, incentive, bonus_conversion, referral, credit_note<br/>Redemptions: withdrawal [  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>wallet_transaction.status</b>", styles['TableCellBold']),
            Paragraph("1 (100,000 Sampled / Active Completed Transactions)", styles['TableCell']),
            Paragraph("Status 1 = Completed / Successful Financial Transaction [  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_inventories.order_type</b>", styles['TableCellBold']),
            Paragraph("Distributor (52,106), Distributors (47,894)", styles['TableCell']),
            Paragraph("Wholesaler/Distributor Orders = 'Distributor', 'Distributors'<br/>Retailer Orders = 'Retailer' [  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_inventories.sources</b>", styles['TableCellBold']),
            Paragraph("kolkata (100,000)", styles['TableCell']),
            Paragraph("Source Warehouse = 'kolkata' (Primary Facility) [  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_qr_points_maps.gride_type</b>", styles['TableCellBold']),
            Paragraph("FG_BIG (6,724), FG_SMALL (1,250), NULL (90)", styles['TableCell']),
            Paragraph("FG_BIG = Finished Goods Big Box | FG_SMALL = Finished Goods Small Box [  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_qr_points_maps.uom</b>", styles['TableCellBold']),
            Paragraph("B10 (3,594), B5 (3,067), B6 (64), B12 (22), B3 (1,142), B1 (153), '' (22)", styles['TableCell']),
            Paragraph("B10 = 10 Pcs Box, B5 = 5 Pcs Box, B3 = 3 Pcs Box, B1 = 1 Pc Box [  ] Approved", styles['TableCell'])
        ]
    ]

    enum_summary_table = Table(enum_summary_data, colWidths=[4.2*cm, 6.2*cm, 7.0*cm])
    enum_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(enum_summary_table)

    # -------------------------------------------------------------------------
    # SECTION 3: CORE SCHEMA JOIN PATH MAP
    # -------------------------------------------------------------------------
    story.append(PageBreak())

    story.append(Paragraph("<b>Section 3: Core Schema Join Path Map</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "Below are the verified relational join paths across the 8 target scope tables. "
        "These paths define how SQL queries link user profiles, transactions, inventories, payouts, and SKU points.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    join_headers = [
        Paragraph("Source Entity", styles['TableHeader']),
        Paragraph("Join Condition & Keys", styles['TableHeader']),
        Paragraph("Target Entity", styles['TableHeader']),
        Paragraph("Business Purpose / Relationship Context", styles['TableHeader']),
        Paragraph("Expert Sign-Off", styles['TableHeader'])
    ]

    join_paths_data = [
        join_headers,
        [
            Paragraph("<b>users</b>", styles['TableCellBold']),
            Paragraph("<code>users.id = wallet_transaction.user_id</code>", styles['TableCell']),
            Paragraph("<b>wallet_transaction</b>", styles['TableCellBold']),
            Paragraph("User financial ledger transactions (credits & debits)", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>users</b>", styles['TableCellBold']),
            Paragraph("<code>users.id = sku_inventories.status_retailer_id</code>", styles['TableCell']),
            Paragraph("<b>sku_inventories</b>", styles['TableCellBold']),
            Paragraph("Retailer scan history & product box assignment", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>users</b>", styles['TableCellBold']),
            Paragraph("<code>users.id = sku_inventories.status_wholeseller_id</code>", styles['TableCell']),
            Paragraph("<b>sku_inventories</b>", styles['TableCellBold']),
            Paragraph("Wholesaler scan history & box movement", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>users</b>", styles['TableCellBold']),
            Paragraph("<code>users.id = sku_inventories.distributer_id</code>", styles['TableCell']),
            Paragraph("<b>sku_inventories</b>", styles['TableCellBold']),
            Paragraph("Distributor inventory allocation & dispatch", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_inventories</b>", styles['TableCellBold']),
            Paragraph("<code>sku_inventories.sku_code = sku_qr_points_maps.sku_code</code>", styles['TableCell']),
            Paragraph("<b>sku_qr_points_maps</b>", styles['TableCellBold']),
            Paragraph("Product UOM box count, cash points, & extra points lookup", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>users</b>", styles['TableCellBold']),
            Paragraph("<code>users.id = withdrawal_request.user_id</code>", styles['TableCell']),
            Paragraph("<b>withdrawal_request</b>", styles['TableCellBold']),
            Paragraph("User cash payout withdrawal requests", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>withdrawal_request</b>", styles['TableCellBold']),
            Paragraph("<code>withdrawal_request.automatic_transaction_id = automatic_transactions.id</code>", styles['TableCell']),
            Paragraph("<b>automatic_transactions</b>", styles['TableCellBold']),
            Paragraph("Bank API payout execution status & bank reference number", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>companies</b>", styles['TableCellBold']),
            Paragraph("<code>companies.business_info_id = users.business_info_id</code>", styles['TableCell']),
            Paragraph("<b>users</b>", styles['TableCellBold']),
            Paragraph("Enterprise business unit & company user grouping", styles['TableCell']),
            Paragraph("[  ] Approved", styles['TableCell'])
        ]
    ]

    join_table = Table(join_paths_data, colWidths=[2.5*cm, 4.8*cm, 2.8*cm, 5.0*cm, 2.3*cm])
    join_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(join_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 4: TEMPORAL & DATE COLUMN DEFINITIONS
    # -------------------------------------------------------------------------
    story.append(Paragraph("<b>Section 4: Temporal & Date Column Definitions</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "Standard temporal date columns used for time-filtered queries (e.g. 'July 2026' or monthly reporting). "
        "Domain experts must verify these columns are the canonical date filters for time-based metrics.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    date_headers = [
        Paragraph("Table Name", styles['TableHeader']),
        Paragraph("Date Column Name", styles['TableHeader']),
        Paragraph("Data Type", styles['TableHeader']),
        Paragraph("Analytics Usage & Time Filtering Purpose", styles['TableHeader']),
        Paragraph("Verification", styles['TableHeader'])
    ]

    date_columns_data = [
        date_headers,
        [
            Paragraph("<b>wallet_transaction</b>", styles['TableCellBold']),
            Paragraph("<code>created_at</code>", styles['TableCellBold']),
            Paragraph("TIMESTAMP", styles['TableCell']),
            Paragraph("Transaction execution timestamp (Standard date filter for monthly Earnings & Redemptions)", styles['TableCell']),
            Paragraph("[  ] Verified", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_inventories</b>", styles['TableCellBold']),
            Paragraph("<code>retailer_scanned_at</code>", styles['TableCellBold']),
            Paragraph("TIMESTAMP", styles['TableCell']),
            Paragraph("Retailer QR scan timestamp (Standard filter for Retailer Box Scans in month X)", styles['TableCell']),
            Paragraph("[  ] Verified", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_inventories</b>", styles['TableCellBold']),
            Paragraph("<code>wholeseller_scanned_at</code>", styles['TableCellBold']),
            Paragraph("TIMESTAMP", styles['TableCell']),
            Paragraph("Wholesaler QR scan timestamp (Standard filter for Wholesaler Box Scans in month X)", styles['TableCell']),
            Paragraph("[  ] Verified", styles['TableCell'])
        ],
        [
            Paragraph("<b>sku_inventories</b>", styles['TableCellBold']),
            Paragraph("<code>created_at</code>", styles['TableCellBold']),
            Paragraph("TIMESTAMP", styles['TableCell']),
            Paragraph("Inventory batch generation timestamp", styles['TableCell']),
            Paragraph("[  ] Verified", styles['TableCell'])
        ],
        [
            Paragraph("<b>users</b>", styles['TableCellBold']),
            Paragraph("<code>created_at</code>", styles['TableCellBold']),
            Paragraph("TIMESTAMP", styles['TableCell']),
            Paragraph("User registration & onboarding timestamp", styles['TableCell']),
            Paragraph("[  ] Verified", styles['TableCell'])
        ],
        [
            Paragraph("<b>withdrawal_request</b>", styles['TableCellBold']),
            Paragraph("<code>created_at</code>", styles['TableCellBold']),
            Paragraph("TIMESTAMP", styles['TableCell']),
            Paragraph("Payout request initiation timestamp", styles['TableCell']),
            Paragraph("[  ] Verified", styles['TableCell'])
        ]
    ]

    date_table = Table(date_columns_data, colWidths=[3.2*cm, 3.5*cm, 2.2*cm, 6.2*cm, 2.3*cm])
    date_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(date_table)

    # -------------------------------------------------------------------------
    # SECTION 5: EXPANDED BUSINESS METRICS CATALOGUE
    # -------------------------------------------------------------------------
    story.append(PageBreak())

    story.append(Paragraph("<b>Section 5: Expanded Business Metrics Catalogue</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "Below is the complete specification of core business metrics, comparing static profile columns against dynamic ledger expressions. "
        "Domain experts must confirm the exact SQL logic and business definitions.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    metric_headers = [
        Paragraph("Metric Name", styles['TableHeader']),
        Paragraph("Target Table & Column", styles['TableHeader']),
        Paragraph("Proposed SQL Expression", styles['TableHeader']),
        Paragraph("Business Definition & Expert Sign-Off", styles['TableHeader'])
    ]

    metrics_catalogue_data = [
        metric_headers,
        [
            Paragraph("<b>1. Static Profile Balance</b>", styles['TableCellBold']),
            Paragraph("<code>users.wallet_balance</code>", styles['TableCell']),
            Paragraph("<code>SUM(wallet_balance)</code>", styles['TableCell']),
            Paragraph("Current stored wallet cash balance snapshot<br/>[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>2. Dynamic Ledger Balance</b>", styles['TableCellBold']),
            Paragraph("<code>wallet_transaction.amount</code>", styles['TableCell']),
            Paragraph("<code>SUM(CASE WHEN reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN amount ELSE -amount END)</code>", styles['TableCell']),
            Paragraph("Net calculated ledger balance from financial transactions<br/>[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>3. Gross Earnings</b>", styles['TableCellBold']),
            Paragraph("<code>wallet_transaction.amount</code>", styles['TableCell']),
            Paragraph("<code>SUM(amount) WHERE reference_type IN ('cash_point', 'topup', 'incentive', 'bonus_conversion', 'referral_earning', 'credit_note')</code>", styles['TableCell']),
            Paragraph("Total monetary credits earned by users<br/>[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>4. Total Redemptions</b>", styles['TableCellBold']),
            Paragraph("<code>wallet_transaction.amount</code>", styles['TableCell']),
            Paragraph("<code>SUM(amount) WHERE reference_type = 'withdrawal'</code>", styles['TableCell']),
            Paragraph("Total cash payouts redeemed via withdrawal<br/>[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>5. Retailer Box Scans</b>", styles['TableCellBold']),
            Paragraph("<code>sku_inventories.order_type</code>", styles['TableCell']),
            Paragraph("<code>COUNT(*) WHERE order_type = 'Retailer' AND retailer_scanned_at IS NOT NULL</code>", styles['TableCell']),
            Paragraph("Verified product box scans completed by retailers<br/>[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>6. Wholesaler Box Scans</b>", styles['TableCellBold']),
            Paragraph("<code>sku_inventories.order_type</code>", styles['TableCell']),
            Paragraph("<code>COUNT(*) WHERE order_type IN ('Distributor', 'Distributors') AND wholeseller_scanned_at IS NOT NULL</code>", styles['TableCell']),
            Paragraph("Verified product box scans completed by wholesalers<br/>[  ] Approved", styles['TableCell'])
        ],
        [
            Paragraph("<b>7. Total Points Earned</b>", styles['TableCellBold']),
            Paragraph("<code>sku_qr_points_maps.retailer_cash_points</code>", styles['TableCell']),
            Paragraph("<code>SUM(q.retailer_cash_points + q.wholeseller_cash_points) FROM sku_inventories i JOIN sku_qr_points_maps q ON i.sku_code = q.sku_code</code>", styles['TableCell']),
            Paragraph("Total reward points generated from box scans<br/>[  ] Approved", styles['TableCell'])
        ]
    ]

    metrics_table = Table(metrics_catalogue_data, colWidths=[3.2*cm, 3.8*cm, 5.4*cm, 5.0*cm])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECTION 6: RESTRICTED SECURITY BLACKLIST
    # -------------------------------------------------------------------------
    story.append(Paragraph("<b>Section 6: Restricted & Sensitive Column Security Blacklist</b>", styles['SectionHeader']))
    story.append(Paragraph(
        "Complete list of 16 detected sensitive columns blacklisted from LLM context prompts and query response outputs.",
        styles['Body']
    ))
    story.append(Spacer(1, 4))

    restricted_headers = [
        Paragraph("Table Name", styles['TableHeader']),
        Paragraph("Column Name", styles['TableHeader']),
        Paragraph("Data Type", styles['TableHeader']),
        Paragraph("Keyword Matched", styles['TableHeader']),
        Paragraph("Security Policy & Approval", styles['TableHeader'])
    ]

    restricted_rows = [restricted_headers]
    for col in restricted_data.get("restricted_columns", []):
        keywords = ", ".join(col.get("matched_keywords", []))
        restricted_rows.append([
            Paragraph(f"<b>{col['table_name']}</b>", styles['TableCellBold']),
            Paragraph(col['column_name'], styles['TableCellBold']),
            Paragraph(col['data_type'], styles['TableCell']),
            Paragraph(f"<font color='#EF4444'><b>{keywords}</b></font>", styles['TableCell']),
            Paragraph("[  ] Blacklist Approved", styles['TableCell'])
        ])

    restricted_table = Table(restricted_rows, colWidths=[3.8*cm, 4.2*cm, 2.5*cm, 3.1*cm, 3.8*cm])
    restricted_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, TABLE_BORDER),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(restricted_table)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------------------
    # SECTION 7: FORMAL DOMAIN EXPERT SIGN-OFF BOX
    # -------------------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("<b>Section 7: Formal Domain Expert Sign-Off & Approval</b>", styles['SectionHeader']),
        Spacer(1, 4),
        Table([
            [Paragraph("<b>JGH INTELLIGENCE ENGINE — PHASE 0 FORMAL SIGN-OFF</b>", styles['TableHeader'])],
            [Paragraph(
                "<br/>"
                "I hereby confirm that I have reviewed the database profile, user roles, join paths, date filters, "
                "business metrics, and security blacklists contained in this document.<br/><br/>"
                "<b>[  ] Section 2: User Roles Approved</b> &nbsp;&nbsp;&nbsp;&nbsp; "
                "<b>[  ] Section 3: Join Paths Approved</b> &nbsp;&nbsp;&nbsp;&nbsp; "
                "<b>[  ] Section 4: Date Filters Verified</b><br/>"
                "<b>[  ] Section 5: Metrics Approved</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; "
                "<b>[  ] Section 6: Security Blacklist Approved</b><br/><br/>"
                "<b>Domain Expert Name:</b> ____________________________________________________<br/><br/>"
                "<b>Title / Designation:</b> _______________________________________________________________<br/><br/>"
                "<b>Signature:</b> ________________________________________   <b>Date:</b> ____________________<br/>",
                styles['TableCell']
            )]
        ], colWidths=[17.4*cm], style=[
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
            ('BACKGROUND', (0, 1), (-1, 1), BRAND_LIGHT),
            ('GRID', (0, 0), (-1, -1), 1, BRAND_PRIMARY),
            ('PADDING', (0, 0), (-1, -1), 7),
        ])
    ]))

    # 3. Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Generated Comprehensive PDF Review Document at: {output_pdf_path.relative_to(PROJECT_ROOT)}")
    print("\n" + "=" * 60)
    print(" ✅ Comprehensive Phase 0 PDF Export Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    build_pdf_document()
