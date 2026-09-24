"""
Agentic-Analyst (JGH Intelligence Engine) — Executive Summary PDF Generator
Generates a polished, executive-ready PDF document summarizing the project architecture,
subsystems, security controls, and operational workflows.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import datetime

# ── Color Palette ───────────────────────────────────────────────────────────
PRIMARY_DARK    = colors.HexColor("#0F172A")   # Deep Slate Navy
ACCENT_BLUE     = colors.HexColor("#2563EB")   # Royal Blue
ACCENT_TEAL     = colors.HexColor("#0D9488")   # Emerald Teal
TEXT_DARK       = colors.HexColor("#1E293B")   # Charcoal
TEXT_MUTED      = colors.HexColor("#64748B")   # Slate Grey
BG_LIGHT        = colors.HexColor("#F8FAFC")   # Light Card Background
BG_CALLOUT      = colors.HexColor("#EFF6FF")   # Light Blue Tint
BORDER_COLOR    = colors.HexColor("#E2E8F0")   # Soft Grey Border
BORDER_BLUE     = colors.HexColor("#BFDBFE")   # Soft Blue Border
TAG_BG          = colors.HexColor("#DBEAFE")   # Badge Blue
WHITE           = colors.white

# ── Dynamic Numbered Canvas (Two-pass page numbering) ────────────────────────
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
        self.saveState()
        page = self._pageNumber
        w, h = letter

        # Running Header (pages after cover / first page)
        if page > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(ACCENT_BLUE)
            self.drawString(0.6 * inch, h - 0.45 * inch, "AGENTIC-ANALYST")
            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawString(1.7 * inch, h - 0.45 * inch, "|  JGH Intelligence Engine Architecture & Executive Summary")

            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(0.6 * inch, h - 0.52 * inch, w - 0.6 * inch, h - 0.52 * inch)

        # Running Footer
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(0.6 * inch, 0.55 * inch, w - 0.6 * inch, 0.55 * inch)

        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(0.6 * inch, 0.38 * inch, "Confidential — JGH Enterprise Analytics Engine")
        self.drawRightString(w - 0.6 * inch, 0.38 * inch, f"Page {page} of {page_count}")
        self.restoreState()


def build_pdf(output_filename="Agentic_Analyst_Project_Summary.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY_DARK,
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=ACCENT_BLUE,
        alignment=TA_LEFT
    )

    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_MUTED
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY_DARK,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        leftIndent=12,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY_DARK
    )

    tbl_header = ParagraphStyle(
        'TblHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=WHITE
    )

    tbl_cell = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=TEXT_DARK
    )

    tbl_cell_bold = ParagraphStyle(
        'TblCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=PRIMARY_DARK
    )

    callout_text = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=TEXT_DARK
    )

    story = []

    # ── HEADER BANNER ────────────────────────────────────────────────────────
    story.append(Paragraph("Agentic-Analyst", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("JGH Intelligence Engine — Enterprise AI SQL Platform Summary", subtitle_style))
    story.append(Spacer(1, 6))

    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    meta_info = f"<b>Author / Lead Engineer:</b> Sneha Nayak &nbsp;&nbsp;|&nbsp;&nbsp; <b>Model:</b> Qwen2.5-Coder:7b (Ollama) &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date:</b> {current_date}"
    story.append(Paragraph(meta_info, meta_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE, spaceBefore=2, spaceAfter=12))

    # ── 1. EXECUTIVE SUMMARY ─────────────────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "The <b>Agentic-Analyst (JGH Intelligence Engine)</b> is an enterprise-grade, read-only AI SQL agent and conversational "
        "Business Intelligence (BI) platform. It allows non-technical business users, analysts, and administrators to query "
        "complex relational databases (such as retail distributor-retailer hierarchies, wallet transactions, SKU inventories, "
        "and geographical regional data) using natural language English.",
        body_style
    ))
    story.append(Paragraph(
        "Unlike generic text-to-SQL wrappers, the platform incorporates a <b>multi-stage agentic workflow</b>: proactive ambiguity detection, "
        "semantic intent and entity routing, dynamic schema relationship mapping, multi-pass AST safety validation, an automated self-healing "
        "correction loop with database execution feedback, and automated narrative synthesis with charting recommendations.",
        body_style
    ))

    # Highlight Callout Box
    callout_content = [
        Paragraph("<b>Key System Objective:</b> Empower decision-makers with zero-latency business insights while strictly guaranteeing enterprise security, AST-level read-only isolation, credential masking, and zero database mutations.", callout_text)
    ]
    callout_table = Table([[callout_content]], colWidths=[7.3 * inch])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_CALLOUT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 10))

    # ── 2. SYSTEM ARCHITECTURE ──────────────────────────────────────────────
    story.append(Paragraph("2. End-to-End Architectural Pipeline", h1_style))
    story.append(Paragraph(
        "The application operates via an integrated 7-stage deterministic and LLM-assisted execution pipeline:",
        body_style
    ))

    arch_steps = [
        ("Step 1: Ambiguity & Policy Check", "Validates user query against restricted security keywords (passwords, master keys) and checks for underspecified business dimensions (prompts user with multiple-choice clarifying options)."),
        ("Step 2: NLP Intent & Entity Parser", "Decomposes the prompt into structured components: analytical intent (aggregation, listing, drill-down), entities (retailers, distributors, SKUs), temporal ranges, and condition filters."),
        ("Step 3: Knowledge Graph Resolution", "Traverses schema relationship metadata to identify required tables and joins (foreign key paths) without overwhelming the LLM with unnecessary schema tables."),
        ("Step 4: Prompt Construction & Generation", "Injects the selected schema subset, dynamic context, and few-shot examples into Ollama (Qwen2.5-Coder:7b) to generate clean, optimized SQL."),
        ("Step 5: AST & Semantic Safety Validation", "Parses the generated SQL Abstract Syntax Tree (AST) to ensure strict SELECT-only operations, valid table/column permissions, and absence of SQL injection vectors."),
        ("Step 6: EXPLAIN Plan & Self-Correction Loop", "Evaluates database execution cost via EXPLAIN. If syntax, AST, or execution errors occur, the error is fed back into the prompt for automated self-healing (up to 3 retries)."),
        ("Step 7: Execution & Executive Synthesis", "Executes the read-only query against MySQL/database engine, calculates confidence scores, and formats the output into natural language takeaways, interactive DataGrids, and recommended charts.")
    ]

    for title, desc in arch_steps:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))

    story.append(Spacer(1, 8))

    # Pipeline Flow Visual Table
    flow_data = [
        [Paragraph("User Input", tbl_header), Paragraph("FastAPI Gateway", tbl_header), Paragraph("Agentic Core", tbl_header), Paragraph("Validation & DB", tbl_header), Paragraph("Synthesis & UI", tbl_header)],
        [
            Paragraph("Natural Language Query<br/><i>'Top 5 retailers by wallet balance in July'</i>", tbl_cell),
            Paragraph("REST Endpoint<br/><code>/api/query</code><br/>Session & Privacy State", tbl_cell),
            Paragraph("Intent Extraction<br/>Relationship Resolver<br/>Ollama Qwen2.5-Coder", tbl_cell),
            Paragraph("AST Validator<br/>EXPLAIN Cost<br/>MySQL Read-Only DB", tbl_cell),
            Paragraph("Executive Narrative<br/>Interactive DataGrid<br/>Recharts / Bar / Pie", tbl_cell)
        ]
    ]
    flow_table = Table(flow_data, colWidths=[1.46 * inch] * 5)
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('BACKGROUND', (0, 1), (-1, 1), BG_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 14))

    # ── 3. CORE SUBSYSTEMS & COMPONENT BREAKDOWN ────────────────────────────
    story.append(Paragraph("3. Core Subsystems & Repository Structure", h1_style))

    components_data = [
        [Paragraph("Subsystem", tbl_header), Paragraph("Key Files / Modules", tbl_header), Paragraph("Technical Capabilities & Responsibility", tbl_header)],
        [
            Paragraph("<b>Agent Orchestration</b>", tbl_cell_bold),
            Paragraph("<code>app/agent/sql_agent.py</code><br/><code>app/agent/ambiguity_checker.py</code><br/><code>app/agent/nlp_understanding.py</code>", tbl_cell),
            Paragraph("Coordinates multi-step reasoning, intent parsing, clarifying question prompts, error retries, and overall query lifecycle.", tbl_cell)
        ],
        [
            Paragraph("<b>Knowledge & Schema</b>", tbl_cell_bold),
            Paragraph("<code>app/knowledge/knowledge_graph.py</code><br/><code>app/knowledge/relationship_resolver.py</code><br/><code>app/database/metadata_extractor.py</code>", tbl_cell),
            Paragraph("Maintains schema metadata, relationship mappings, foreign key graphs, and dynamic context injection to prevent hallucinations.", tbl_cell)
        ],
        [
            Paragraph("<b>Validation & Safety</b>", tbl_cell_bold),
            Paragraph("<code>app/validator/sql_ast_validator.py</code><br/><code>app/validator/semantic_sql_validator.py</code><br/><code>app/database/read_executor.py</code>", tbl_cell),
            Paragraph("Enforces read-only safety, AST token inspection, SQL injection blocking, EXPLAIN query cost checks, and table access whitelisting.", tbl_cell)
        ],
        [
            Paragraph("<b>LLM & Inference</b>", tbl_cell_bold),
            Paragraph("<code>app/llm/sql_generator.py</code><br/><code>app/prompt/prompt_builder.py</code><br/><code>cloud_gpu_setup.md</code>", tbl_cell),
            Paragraph("Interface to Ollama (qwen2.5-coder:7b). Supports local host and remote Cloud GPU endpoints via Ngrok / LocalTunnel tunnels.", tbl_cell)
        ],
        [
            Paragraph("<b>Narrative & Synthesis</b>", tbl_cell_bold),
            Paragraph("<code>app/agent/response_synthesizer.py</code><br/><code>app/agent/storyteller.py</code><br/><code>app/utils/summary_generator.py</code>", tbl_cell),
            Paragraph("Generates plain-language executive summaries, KPI extraction, insights, and recommended visualization types (bar, line, metric).", tbl_cell)
        ],
        [
            Paragraph("<b>Modern Web Frontend</b>", tbl_cell_bold),
            Paragraph("<code>frontend/src/App.jsx</code><br/><code>CenterChat.jsx</code>, <code>DataGrid.jsx</code><br/><code>AutoChart.jsx</code>, <code>ArchitectureView.jsx</code>", tbl_cell),
            Paragraph("React + Vite application with live thinking step progress loader, paginated DataGrid with CSV/Excel/PDF export, dynamic charts, and ERD viewer.", tbl_cell)
        ],
        [
            Paragraph("<b>Security & Privacy</b>", tbl_cell_bold),
            Paragraph("<code>app/database/config.py</code><br/><code>app/utils/privacy_manager.py</code><br/><code>secure_credentials.py</code>", tbl_cell),
            Paragraph("AES-256 Fernet credential encryption with master keys, SSL wire encryption, incognito modes, and schema drift monitoring.", tbl_cell)
        ]
    ]

    comp_table = Table(components_data, colWidths=[1.5 * inch, 2.3 * inch, 3.5 * inch])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 14))

    # ── 4. ENTERPRISE SECURITY & RELIABILITY ─────────────────────────────────
    story.append(Paragraph("4. Enterprise Security, Governance & Verification", h1_style))
    story.append(Paragraph(
        "To ensure production reliability in enterprise environments, the platform implements defense-in-depth safety controls:",
        body_style
    ))

    sec_points = [
        ("Restricted Credential Firewall", "Automatically scans user input and blocks any queries targeting sensitive authentication data (e.g. passwords, password hashes, encryption keys, master keys, tokens)."),
        ("Strict Read-Only Enforcement", "The database execution engine parses commands before execution, rejecting any mutation statements (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE) with an immediate security violation."),
        ("AES-256 Fernet DB Encryption", "Database connection strings and credentials are encrypted on disk via Fernet encryption and decrypted only into volatile RAM using the master secret key."),
        ("Schema Drift Monitoring", "On server startup and periodic intervals, a schema drift detector compares live database tables and columns against the baseline catalog, flagging discrepancies before queries fail."),
        ("Automated Self-Healing Loop", "If the generated SQL encounters a syntax error or semantic join failure, the error stack trace is returned to the agent, prompting the LLM to self-correct up to 3 attempts.")
    ]

    for title, desc in sec_points:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))

    story.append(Spacer(1, 10))

    # ── 5. TECHNOLOGY STACK SUMMARY ──────────────────────────────────────────
    story.append(Paragraph("5. Technology Stack", h1_style))

    tech_data = [
        [Paragraph("Category", tbl_header), Paragraph("Technologies & Frameworks", tbl_header), Paragraph("Role in System", tbl_header)],
        [Paragraph("<b>Backend API</b>", tbl_cell), Paragraph("Python 3.10+, FastAPI, Uvicorn", tbl_cell), Paragraph("High-concurrency async REST API and static server", tbl_cell)],
        [Paragraph("<b>LLM & AI</b>", tbl_cell), Paragraph("Ollama, Qwen2.5-Coder:7b", tbl_cell), Paragraph("Locally or remotely hosted code LLM for SQL generation", tbl_cell)],
        [Paragraph("<b>Database</b>", tbl_cell), Paragraph("MySQL, SQLAlchemy, PyMySQL", tbl_cell), Paragraph("Enterprise relational data store with read-only connection pooling", tbl_cell)],
        [Paragraph("<b>Frontend</b>", tbl_cell), Paragraph("React 18, Vite, Recharts, Lucide", tbl_cell), Paragraph("Interactive single-page application with dark/light themes", tbl_cell)],
        [Paragraph("<b>Reporting & Export</b>", tbl_cell), Paragraph("ReportLab, Pandas, OpenPyXL", tbl_cell), Paragraph("Document generation for CSV, Excel workbooks, and PDF reports", tbl_cell)],
        [Paragraph("<b>Security & Cryptography</b>", tbl_cell), Paragraph("Cryptography (Fernet), PyJWT", tbl_cell), Paragraph("Payload encryption, token authorization, and secret storage", tbl_cell)]
    ]

    tech_table = Table(tech_data, colWidths=[1.6 * inch, 2.5 * inch, 3.2 * inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 14))

    # ── 6. QUICK START & OPERATIONAL GUIDE ───────────────────────────────────
    story.append(Paragraph("6. Operational Quick Start", h1_style))
    story.append(Paragraph(
        "To run the complete platform locally, execute the following commands:",
        body_style
    ))

    cmd_data = [
        [Paragraph("Step", tbl_header), Paragraph("Command", tbl_header), Paragraph("Description", tbl_header)],
        [
            Paragraph("1. Pull LLM", tbl_cell_bold),
            Paragraph("<code>ollama run qwen2.5-coder:7b</code>", tbl_cell),
            Paragraph("Downloads and starts the Ollama model instance.", tbl_cell)
        ],
        [
            Paragraph("2. Start Backend", tbl_cell_bold),
            Paragraph("<code>python start_server.py</code><br/><i>(or uvicorn app.api.main:app --port 8000)</i>", tbl_cell),
            Paragraph("Initializes schema metadata, knowledge graph, and API on <code>http://localhost:8000</code>.", tbl_cell)
        ],
        [
            Paragraph("3. Launch Frontend", tbl_cell_bold),
            Paragraph("<code>cd frontend &amp;&amp; npm run dev</code>", tbl_cell),
            Paragraph("Starts Vite development server on <code>http://localhost:3000</code>.", tbl_cell)
        ],
        [
            Paragraph("4. Diagnostic Health", tbl_cell_bold),
            Paragraph("<code>GET /api/llm/health</code>", tbl_cell),
            Paragraph("Validates LLM endpoint connectivity, model availability, and response latency.", tbl_cell)
        ]
    ]

    cmd_table = Table(cmd_data, colWidths=[1.2 * inch, 3.0 * inch, 3.1 * inch])
    cmd_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BG_LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cmd_table)
    story.append(Spacer(1, 14))

    # Sign-off card
    sign_off_content = [
        Paragraph(
            f"<b>Document Generated:</b> {current_date} &nbsp;|&nbsp; <b>Project:</b> Agentic-Analyst (sneha-nayak546/Agentic-Analyst)<br/>"
            "This document is an executive technical overview reflecting the live architecture, agent pipelines, and deployment specifications.",
            meta_style
        )
    ]
    sign_off_table = Table([[sign_off_content]], colWidths=[7.3 * inch])
    sign_off_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(sign_off_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF Generated successfully: {output_filename}")


if __name__ == "__main__":
    out_file = "Agentic_Analyst_Project_Summary.pdf"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    build_pdf(out_file)
