"""
Agentic Analyst — Full Project Handbook PDF Generator
Generates a comprehensive, professionally formatted PDF handbook.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Flowable
from reportlab.pdfgen import canvas
import datetime
import os

# ── Color Palette ───────────────────────────────────────────────────────────
BRAND_DARK      = colors.HexColor("#0F172A")   # dark navy
BRAND_PRIMARY   = colors.HexColor("#6366F1")   # indigo
BRAND_ACCENT    = colors.HexColor("#22D3EE")   # cyan
BRAND_SUCCESS   = colors.HexColor("#22C55E")   # green
BRAND_WARNING   = colors.HexColor("#F59E0B")   # amber
BRAND_DANGER    = colors.HexColor("#EF4444")   # red
BRAND_SURFACE   = colors.HexColor("#1E293B")   # slate-800
BRAND_MUTED     = colors.HexColor("#64748B")   # slate-500
BRAND_LIGHT     = colors.HexColor("#F1F5F9")   # slate-100
WHITE           = colors.white
BLACK           = colors.black
SECTION_BG      = colors.HexColor("#EEF2FF")   # very light indigo
CODE_BG         = colors.HexColor("#0F172A")   # dark for code blocks
TABLE_HEADER_BG = colors.HexColor("#4F46E5")   # deep indigo
TABLE_ALT_ROW   = colors.HexColor("#F8FAFC")
TABLE_BORDER    = colors.HexColor("#E2E8F0")


# ── Page Number Canvas ───────────────────────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        page = self._pageNumber
        self.setFont("Helvetica", 8)
        self.setFillColor(BRAND_MUTED)
        self.drawRightString(A4[0] - 1.5*cm, 0.8*cm, f"Page {page} of {page_count}")
        self.drawString(1.5*cm, 0.8*cm, "Agentic Analyst — Project Handbook  |  Confidential")
        # Footer line
        self.setStrokeColor(TABLE_BORDER)
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.1*cm, A4[0] - 1.5*cm, 1.1*cm)


# ── Style Definitions ────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles['cover_title'] = ParagraphStyle(
        'cover_title',
        fontName='Helvetica-Bold',
        fontSize=36,
        textColor=WHITE,
        leading=44,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    styles['cover_subtitle'] = ParagraphStyle(
        'cover_subtitle',
        fontName='Helvetica',
        fontSize=15,
        textColor=colors.HexColor("#CBD5E1"),
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles['cover_version'] = ParagraphStyle(
        'cover_version',
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.HexColor("#94A3B8"),
        leading=16,
        alignment=TA_CENTER,
    )
    styles['h1'] = ParagraphStyle(
        'h1',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=BRAND_DARK,
        leading=28,
        spaceBefore=18,
        spaceAfter=8,
    )
    styles['h2'] = ParagraphStyle(
        'h2',
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=BRAND_PRIMARY,
        leading=20,
        spaceBefore=14,
        spaceAfter=5,
    )
    styles['h3'] = ParagraphStyle(
        'h3',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=BRAND_SURFACE,
        leading=17,
        spaceBefore=10,
        spaceAfter=4,
    )
    styles['body'] = ParagraphStyle(
        'body',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leading=16,
        spaceAfter=5,
        alignment=TA_JUSTIFY,
    )
    styles['body_bold'] = ParagraphStyle(
        'body_bold',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=BRAND_DARK,
        leading=16,
        spaceAfter=4,
    )
    styles['code'] = ParagraphStyle(
        'code',
        fontName='Courier',
        fontSize=9,
        textColor=colors.HexColor("#38BDF8"),
        leading=13,
        spaceAfter=2,
        backColor=CODE_BG,
        leftIndent=8,
        rightIndent=8,
    )
    styles['code_label'] = ParagraphStyle(
        'code_label',
        fontName='Courier-Bold',
        fontSize=9,
        textColor=colors.HexColor("#A78BFA"),
        leading=13,
        backColor=CODE_BG,
        leftIndent=8,
    )
    styles['caption'] = ParagraphStyle(
        'caption',
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=BRAND_MUTED,
        leading=13,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    styles['note'] = ParagraphStyle(
        'note',
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor("#1E40AF"),
        leading=14,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6,
    )
    styles['toc_title'] = ParagraphStyle(
        'toc_title',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=BRAND_DARK,
        leading=16,
        spaceAfter=2,
    )
    styles['toc_entry'] = ParagraphStyle(
        'toc_entry',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        leading=15,
        leftIndent=12,
        spaceAfter=1,
    )
    styles['pill'] = ParagraphStyle(
        'pill',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=WHITE,
        leading=13,
        backColor=BRAND_PRIMARY,
        leftIndent=6,
        rightIndent=6,
        spaceAfter=2,
    )
    return styles


# ── Helper Builders ──────────────────────────────────────────────────────────

def section_divider(s, label):
    """Returns a visually distinct section header block."""
    return [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=2, color=BRAND_PRIMARY, spaceAfter=4),
        Paragraph(label, s['h1']),
        HRFlowable(width="60%", thickness=1, color=BRAND_ACCENT, spaceAfter=8),
    ]


def sub_heading(s, label):
    return [Paragraph(label, s['h2'])]


def sub_sub_heading(s, label):
    return [Paragraph(label, s['h3'])]


def body(s, text):
    return [Paragraph(text, s['body'])]


def code_block(s, lines, label=""):
    items = []
    if label:
        items.append(Paragraph(f"# {label}", s['code_label']))
    for line in lines:
        items.append(Paragraph(line.replace(" ", "&nbsp;").replace("<", "&lt;").replace(">", "&gt;"), s['code']))
    # Wrap in a table for background
    tbl = Table([[item] for item in items], colWidths=[16*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (0,0), 8),
        ('BOTTOMPADDING', (-1,-1), (-1,-1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    return [tbl, Spacer(1, 6)]


def info_table(s, headers, rows, col_widths=None):
    if col_widths is None:
        col_widths = [16*cm / len(headers)] * len(headers)
    data = [headers] + rows
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9.5),
        ('TEXTCOLOR', (0,1), (-1,-1), BRAND_DARK),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, TABLE_ALT_ROW]),
        ('GRID', (0,0), (-1,-1), 0.5, TABLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]
    tbl.setStyle(TableStyle(style))
    return [tbl, Spacer(1, 8)]


def highlight_box(s, text, color=SECTION_BG, text_color=BRAND_PRIMARY):
    p = Paragraph(text, ParagraphStyle(
        'hbox', fontName='Helvetica', fontSize=10,
        textColor=text_color, leading=15, leftIndent=6, rightIndent=6
    ))
    tbl = Table([[p]], colWidths=[16*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LINEBEFOREBEFORE', (0,0), (0,-1), 4, BRAND_PRIMARY),
    ]))
    return [tbl, Spacer(1, 6)]


def two_col_table(s, left_content, right_content):
    """Side-by-side two column layout."""
    tbl = Table([[left_content, right_content]], colWidths=[8*cm, 8*cm])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    return [tbl]


# ── Cover Page ───────────────────────────────────────────────────────────────
def draw_cover_page(canvas_obj, doc):
    """Draw the cover page using canvas directly (called via onFirstPage)."""
    now = datetime.datetime.now()
    date_str = now.strftime("%B %d, %Y")
    w, h = A4

    canvas_obj.saveState()

    # Background
    canvas_obj.setFillColor(BRAND_DARK)
    canvas_obj.rect(0, 0, w, h, fill=True, stroke=False)

    # Top bar
    canvas_obj.setFillColor(BRAND_PRIMARY)
    canvas_obj.rect(0, h - 1.4*cm, w, 1.4*cm, fill=True, stroke=False)

    # Bottom bar
    canvas_obj.setFillColor(BRAND_PRIMARY)
    canvas_obj.rect(0, 0, w, 1.4*cm, fill=True, stroke=False)

    # Decorative circles
    canvas_obj.setFillColor(colors.HexColor("#312E81"))
    canvas_obj.circle(w*0.82, h*0.72, 130, fill=True, stroke=False)
    canvas_obj.setFillColor(colors.HexColor("#1E3A5F"))
    canvas_obj.circle(w*0.12, h*0.28, 90, fill=True, stroke=False)

    # Accent left bar
    canvas_obj.setFillColor(BRAND_ACCENT)
    canvas_obj.rect(1.4*cm, h*0.42, 0.4*cm, 5*cm, fill=True, stroke=False)

    # Title
    canvas_obj.setFont("Helvetica-Bold", 42)
    canvas_obj.setFillColor(WHITE)
    canvas_obj.drawCentredString(w/2, h*0.65, "Agentic Analyst")

    # Subtitle
    canvas_obj.setFont("Helvetica", 16)
    canvas_obj.setFillColor(colors.HexColor("#A5B4FC"))
    canvas_obj.drawCentredString(w/2, h*0.59, "Enterprise AI SQL Intelligence Platform")

    # Divider line
    canvas_obj.setStrokeColor(BRAND_ACCENT)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(w*0.25, h*0.565, w*0.75, h*0.565)

    # Tagline
    canvas_obj.setFont("Helvetica-Oblique", 12)
    canvas_obj.setFillColor(colors.HexColor("#CBD5E1"))
    canvas_obj.drawCentredString(w/2, h*0.525, "Natural Language  \u2192  SQL  \u2192  Instant Insights")

    # Metadata box
    canvas_obj.setFillColor(colors.HexColor("#1E293B"))
    canvas_obj.roundRect(w*0.18, h*0.31, w*0.64, h*0.17, 8, fill=True, stroke=False)
    canvas_obj.setStrokeColor(BRAND_PRIMARY)
    canvas_obj.setLineWidth(1)
    canvas_obj.roundRect(w*0.18, h*0.31, w*0.64, h*0.17, 8, fill=False, stroke=True)

    meta = [
        ("Document Type", "Full Project Handbook"),
        ("Version",       "2.0"),
        ("Date",          date_str),
        ("Status",        "Active / Production"),
        ("Author",        "Engineering Team"),
    ]
    y_meta = h*0.445
    for label, val in meta:
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.setFillColor(colors.HexColor("#94A3B8"))
        canvas_obj.drawString(w*0.21, y_meta, f"{label}:")
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(WHITE)
        canvas_obj.drawString(w*0.41, y_meta, val)
        y_meta -= 0.42*cm

    # Bottom text
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.setFillColor(colors.HexColor("#64748B"))
    canvas_obj.drawCentredString(w/2, h*0.04, "CONFIDENTIAL  \u00b7  For Internal Use Only")

    canvas_obj.restoreState()


def build_cover(s):
    """Returns empty list; cover is drawn via onFirstPage canvas callback."""
    return [PageBreak()]


# ── Table of Contents ────────────────────────────────────────────────────────
def build_toc(s):
    items = []
    items += section_divider(s, "Table of Contents")

    toc_data = [
        ("1", "Project Overview", "3"),
        ("2", "System Architecture", "4"),
        ("3", "Technology Stack", "5"),
        ("4", "Project Structure & File Reference", "6"),
        ("5", "Backend — Python / FastAPI", "7"),
        ("   5.1", "API Endpoints Reference", "7"),
        ("   5.2", "AI Agent Pipeline", "9"),
        ("   5.3", "Knowledge Graph & Business Logic", "10"),
        ("   5.4", "SQL Generator & LLM Integration", "11"),
        ("   5.5", "Prompt Engineering", "12"),
        ("   5.6", "SQL Validator (AST)", "13"),
        ("   5.7", "Database Layer", "13"),
        ("   5.8", "Embedding & Vector Store (ChromaDB)", "14"),
        ("   5.9", "Query History & Audit Log", "14"),
        ("   5.10", "Report Generator (CSV, Excel, PDF)", "15"),
        ("6", "Frontend — React / Vite", "16"),
        ("   6.1", "Application Screens", "16"),
        ("   6.2", "Component Reference", "17"),
        ("7", "Environment Configuration (.env)", "18"),
        ("8", "Installation & Setup Guide", "19"),
        ("   8.1", "Prerequisites", "19"),
        ("   8.2", "Backend Setup", "19"),
        ("   8.3", "Frontend Setup", "20"),
        ("   8.4", "Ollama LLM Setup", "21"),
        ("9", "Running the Application", "22"),
        ("   9.1", "Start Backend Server", "22"),
        ("   9.2", "Start Frontend Dev Server", "22"),
        ("   9.3", "Build & Serve Frontend (Production)", "22"),
        ("10", "API Usage Examples", "23"),
        ("11", "Data Flow Walkthrough", "24"),
        ("12", "Security & Read-Only Enforcement", "25"),
        ("13", "Troubleshooting & FAQ", "26"),
        ("14", "Glossary", "27"),
    ]

    tbl_data = [[
        Paragraph(f"<b>{sec}</b>", s['toc_entry']),
        Paragraph(f"<b>{title}</b>", s['toc_entry']),
        Paragraph(f"<b>{pg}</b>", s['toc_entry'])
    ] for sec, title, pg in toc_data]

    tbl = Table(tbl_data, colWidths=[1.8*cm, 12*cm, 2.2*cm])
    tbl.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (-1,-1), BRAND_DARK),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, TABLE_ALT_ROW]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    items.append(tbl)
    items.append(PageBreak())
    return items


# ── Section 1: Project Overview ──────────────────────────────────────────────
def build_overview(s):
    items = []
    items += section_divider(s, "1. Project Overview")

    items += body(s, """
    <b>Agentic Analyst</b> is a production-grade, enterprise-level AI-powered SQL intelligence platform. 
    It allows non-technical business users to query a live MySQL database using plain English. 
    The system translates natural language questions into valid, optimized SQL queries, executes them 
    in real time, and presents results as rich data tables, auto-generated charts, and downloadable reports — 
    all through a modern conversational web interface.
    """)
    items.append(Spacer(1, 8))

    items += sub_heading(s, "Core Capabilities")
    features = [
        ("<b>Natural Language Querying</b>", "Type business questions in plain English; the system generates the SQL automatically."),
        ("<b>AI-Powered SQL Generation</b>", "Uses a local Ollama LLM (qwen2.5-coder:7b) with a deterministic fallback synthesizer for offline resilience."),
        ("<b>Business Knowledge Graph</b>", "An in-memory graph maps business terms, table aliases, column relationships, and entity dictionaries."),
        ("<b>Multi-Step Agent Pipeline</b>", "Intent detection → Execution planning → SQL generation → AST validation → EXPLAIN check → DB execution → Self-correction loop (up to 3 retries)."),
        ("<b>Ambiguity Detection</b>", "Vague or underspecified queries prompt clarification options backed by real DB enum values."),
        ("<b>Read-Only Enforcement</b>", "AST-level validation rejects any non-SELECT query — INSERT, UPDATE, DELETE, DROP, etc. are blocked."),
        ("<b>Report Export</b>", "Results can be exported as CSV, Excel (XLSX), PDF, or JSON directly from the UI."),
        ("<b>Auto-Charting</b>", "Recharts-powered automatic visualization of query results."),
        ("<b>Query History & Audit</b>", "Every query is logged with SQL, status, execution time, affected tables, and confidence score."),
        ("<b>Admin Dashboard</b>", "Schema browser, embedding rebuild, metadata refresh, and system status monitoring."),
        ("<b>Settings Panel</b>", "Runtime configuration of LLM model, embedding model, temperature, top-k, and row limits."),
        ("<b>ChromaDB Vector Store</b>", "Semantic search on schema embeddings for RAG-powered schema retrieval."),
    ]
    feat_tbl = Table(
        [[Paragraph(f, s['body_bold']), Paragraph(d, s['body'])] for f, d in features],
        colWidths=[5.5*cm, 10.5*cm]
    )
    feat_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, TABLE_ALT_ROW]),
        ('GRID', (0,0), (-1,-1), 0.3, TABLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    items.append(feat_tbl)
    items.append(Spacer(1, 10))

    items += sub_heading(s, "Target Database Domain")
    items += body(s, """
    The platform is configured for a <b>JGH enterprise database</b> containing tables covering 
    users/roles, wallet transactions, SKU inventories, company/brand information, mechanic profiles, 
    withdrawal requests, and automatic bank transactions. All queries are scoped to this defined target table set.
    """)
    items.append(PageBreak())
    return items


# ── Section 2: Architecture ──────────────────────────────────────────────────
def build_architecture(s):
    items = []
    items += section_divider(s, "2. System Architecture")

    items += body(s, """
    The application follows a <b>clean, layered architecture</b> with a React frontend, 
    FastAPI backend, and a modular Python AI agent pipeline. Each layer has clear 
    separation of concerns, making it maintainable and extensible.
    """)
    items.append(Spacer(1, 8))

    arch_text = [
        "┌─────────────────────────────────────────────────────────────────┐",
        "│                     BROWSER (React + Vite)                      │",
        "│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │",
        "│  │ CenterChat│  │HistoryView│  │AdminPanel│  │   Settings   │  │",
        "│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │",
        "│         ↕ HTTP REST API (localhost:8000)                        │",
        "├─────────────────────────────────────────────────────────────────┤",
        "│                  FastAPI Backend (Python)                        │",
        "│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐ │",
        "│  │/query   │  │/export/* │  │/history   │  │ /admin/*      │ │",
        "│  └────┬────┘  └──────────┘  └───────────┘  └───────────────┘ │",
        "│       │                                                          │",
        "│  ┌────▼──────────────────────────────────────────────────────┐ │",
        "│  │                   AI Agent Pipeline                        │ │",
        "│  │  Ambiguity → KG Resolve → Query Planner → Prompt Builder  │ │",
        "│  │  → LLM (Ollama) → SQL Cleaner → AST Validator → EXPLAIN  │ │",
        "│  │  → Execute → Self-Correct (3 retries) → Response         │ │",
        "│  └─────────────────────────────────────────────────────────── ┘ │",
        "├─────────────────────────────────────────────────────────────────┤",
        "│   Knowledge Layer          │  Embedding Layer (ChromaDB)         │",
        "│   BusinessKnowledgeGraph   │  Sentence Transformers              │",
        "│   Schema / Entity / Column │  all-MiniLM-L6-v2                  │",
        "│   Business Dictionary      │  Vector Similarity Search           │",
        "├─────────────────────────────────────────────────────────────────┤",
        "│                  MySQL Database (Read-Only)                      │",
        "│   SQLAlchemy + PyMySQL  ·  Connection Pool (10/20 overflow)     │",
        "└─────────────────────────────────────────────────────────────────┘",
    ]
    items += code_block(s, arch_text, label="System Architecture Diagram")

    items += sub_heading(s, "Communication Flow")
    flow_data = [
        ["Step", "Component", "Description"],
        ["1", "React Frontend", "User types a natural language question in the chat interface"],
        ["2", "HTTP POST /query", "Frontend sends question JSON to FastAPI backend"],
        ["3", "Ambiguity Checker", "Validates query is not vague; requests clarification if needed"],
        ["4", "Knowledge Graph", "Resolves business entities, table aliases, and join paths"],
        ["5", "Query Planner", "Builds a deterministic execution plan with table/column/join details"],
        ["6", "Prompt Builder", "Constructs a structured LLM prompt from the execution plan"],
        ["7", "SQL Generator", "Calls Ollama LLM or deterministic synthesizer fallback"],
        ["8", "SQL Cleaner", "Strips markdown artifacts, truncates at first semicolon"],
        ["9", "AST Validator", "Parses SQL AST via sqlglot — blocks non-SELECT statements"],
        ["10", "EXPLAIN Check", "Runs MySQL EXPLAIN to validate query cost and structure"],
        ["11", "DB Executor", "Executes query via SQLAlchemy connection pool, fetches up to 500 rows"],
        ["12", "Self-Correction", "On any failure, feeds error back to LLM for up to 3 retries"],
        ["13", "Report Generator", "Generates CSV, Excel, PDF report files saved to /reports/"],
        ["14", "Summary Generator", "Creates natural language summary of results"],
        ["15", "Response JSON", "Returns standardized result object to frontend"],
        ["16", "React Rendering", "Displays SQL, table, chart, summary, and download buttons"],
    ]
    items += info_table(s, flow_data[0], flow_data[1:], [0.8*cm, 4*cm, 11.2*cm])
    items.append(PageBreak())
    return items


# ── Section 3: Technology Stack ──────────────────────────────────────────────
def build_tech_stack(s):
    items = []
    items += section_divider(s, "3. Technology Stack")

    items += sub_heading(s, "Backend")
    items += info_table(s, ["Technology", "Version", "Purpose"], [
        ["Python", "3.10+", "Primary backend language"],
        ["FastAPI", "0.141.1", "High-performance REST API framework with async support"],
        ["Uvicorn", "0.52.1", "ASGI server for production-grade HTTP handling"],
        ["SQLAlchemy", "2.0.51", "ORM and connection pooling for MySQL"],
        ["PyMySQL", "1.2.0", "MySQL driver for Python"],
        ["Ollama", "0.6.2", "Local LLM server client (qwen2.5-coder:7b model)"],
        ["ChromaDB", "1.5.9", "In-process vector database for semantic schema search"],
        ["Sentence-Transformers", "5.6.1", "Embedding model (all-MiniLM-L6-v2) for RAG"],
        ["sqlglot", "≥30.0.0", "SQL AST parser and validator (dialect-aware)"],
        ["pandas", "3.0.5", "Data manipulation, serialization, and report generation"],
        ["openpyxl", "≥3.1.0", "Excel report generation (.xlsx)"],
        ["ReportLab", "≥5.0.0", "PDF report generation"],
        ["python-dotenv", "1.2.2", "Environment variable management via .env file"],
        ["Pydantic", "2.13.4", "Request/response validation and data modeling"],
        ["tenacity", "9.1.4", "Retry logic for resilient LLM calls"],
        ["rich", "15.0.0", "Enhanced console output and logging"],
    ], [3.5*cm, 3*cm, 9.5*cm])

    items += sub_heading(s, "Frontend")
    items += info_table(s, ["Technology", "Version", "Purpose"], [
        ["React", "19.2.8", "UI component library"],
        ["Vite", "8.2.0", "Ultra-fast build tool and dev server"],
        ["Recharts", "3.10.1", "Auto-chart visualization of query results"],
        ["Lucide React", "1.28.0", "Icon library"],
        ["Vanilla CSS", "—", "Custom styling (no framework, full control)"],
        ["oxlint", "1.75.0", "Fast JavaScript linter"],
    ], [3.5*cm, 3*cm, 9.5*cm])

    items += sub_heading(s, "Infrastructure & Tools")
    items += info_table(s, ["Tool", "Purpose"], [
        ["MySQL", "Primary relational database (read-only access)"],
        ["Ollama", "Local LLM inference server running qwen2.5-coder:7b"],
        ["ChromaDB", "Vector store for schema embeddings"],
        ["knowledge/ directory", "JSON-based knowledge base for schema, entities, and business terms"],
        ["reports/ directory", "Auto-generated query report files (CSV, Excel, PDF)"],
    ], [5*cm, 11*cm])
    items.append(PageBreak())
    return items


# ── Section 4: Project Structure ─────────────────────────────────────────────
def build_project_structure(s):
    items = []
    items += section_divider(s, "4. Project Structure & File Reference")

    tree = [
        "Agent/                          ← Project root",
        "├── .env                        ← Database credentials (never commit)",
        "├── requirements.txt            ← Python dependencies",
        "├── app/",
        "│   ├── main.py                 ← Backend entry point (uvicorn runner)",
        "│   ├── api/",
        "│   │   └── main.py             ← FastAPI app, all REST endpoints",
        "│   ├── agent/",
        "│   │   ├── sql_agent.py        ← Core AI agent pipeline orchestrator",
        "│   │   ├── ambiguity_checker.py← Query clarity validation",
        "│   │   └── query_planner.py    ← Deterministic execution plan builder",
        "│   ├── llm/",
        "│   │   ├── sql_generator.py    ← Ollama LLM + deterministic fallback",
        "│   │   └── qwen.py             ← Qwen model helper",
        "│   ├── prompt/",
        "│   │   └── prompt_builder.py   ← Structured SQL prompt construction",
        "│   ├── database/",
        "│   │   ├── connection.py       ← MySQL connection test script",
        "│   │   ├── read_executor.py    ← Read-only query executor + EXPLAIN",
        "│   │   ├── metadata_extractor.py← Enterprise schema metadata builder",
        "│   │   ├── schema_extractor.py ← Table/column schema introspection",
        "│   │   └── allowed_tables.py   ← TARGET_SCOPE_TABLES whitelist",
        "│   ├── knowledge/",
        "│   │   ├── knowledge_graph.py  ← BusinessKnowledgeGraph core class",
        "│   │   ├── db_profiler.py      ← Enum/sample value profiler",
        "│   │   ├── knowledge_builder.py← Orchestrates knowledge base build",
        "│   │   ├── relationship_builder.py← FK and inferred relationship mapping",
        "│   │   └── schema_builder.py   ← Schema JSON builder",
        "│   ├── embedding/",
        "│   │   ├── chroma_builder.py   ← ChromaDB vector store builder",
        "│   │   ├── embedding_builder.py← Sentence transformer embedding wrapper",
        "│   │   └── sql_history_embedding.py← Historical SQL embedding",
        "│   ├── retriever/",
        "│   │   └── retriever.py        ← Schema/history retrieval functions",
        "│   ├── validator/",
        "│   │   ├── sql_ast_validator.py← sqlglot-based AST SQL validation",
        "│   │   ├── sql_optimizer.py    ← SQL optimization rules",
        "│   │   └── sql_validator.py    ← Rule-based SQL pre-validation",
        "│   ├── sql_history/",
        "│   │   └── query_history.py    ← Query history CRUD (JSON file-based)",
        "│   ├── utils/",
        "│   │   ├── report_generator.py ← CSV/Excel/PDF report generators",
        "│   │   ├── sql_cleaner.py      ← Raw LLM output SQL sanitizer",
        "│   │   └── summary_generator.py← Natural language result summary",
        "│   └── static/                 ← Built frontend assets (Vite output)",
        "├── frontend/",
        "│   ├── src/",
        "│   │   ├── App.jsx             ← Root React component + routing",
        "│   │   ├── index.css           ← Global design system CSS",
        "│   │   └── components/",
        "│   │       ├── CenterChat.jsx  ← Main chat interface",
        "│   │       ├── DataGrid.jsx    ← Results table renderer",
        "│   │       ├── AutoChart.jsx   ← Auto-charting with Recharts",
        "│   │       ├── DatabaseSchemaPanel.jsx← Right panel schema browser",
        "│   │       ├── HistoryView.jsx ← Query history & audit tab",
        "│   │       ├── AdminPanel.jsx  ← Admin dashboard",
        "│   │       ├── Settings.jsx    ← Settings configuration panel",
        "│   │       └── Sidebar.jsx     ← Navigation sidebar",
        "│   ├── package.json            ← Node.js dependencies",
        "│   └── vite.config.js          ← Vite configuration + API proxy",
        "├── knowledge/                  ← Auto-generated knowledge base JSON files",
        "│   ├── schema/                 ← schema_metadata.json, enum_dictionary.json",
        "│   ├── graph/                  ← entity/column/business dictionaries",
        "│   ├── patterns/               ← query_patterns.json (learned patterns)",
        "│   └── history/                ← execution_history.json",
        "├── reports/                    ← Auto-generated query reports",
        "└── logs/                       ← Application logs",
    ]
    items += code_block(s, tree, label="Project Directory Tree")
    items.append(PageBreak())
    return items


# ── Section 5: Backend ────────────────────────────────────────────────────────
def build_backend(s):
    items = []
    items += section_divider(s, "5. Backend — Python / FastAPI")

    # 5.1 API Endpoints
    items += sub_heading(s, "5.1  API Endpoints Reference")
    items += body(s, "The backend exposes a REST API on <b>http://localhost:8000</b>. All endpoints return JSON.")

    endpoints = [
        ["Method", "Endpoint", "Description", "Auth"],
        ["GET",  "/",                    "Serve React frontend SPA",                   "None"],
        ["GET",  "/health",              "System health check (DB + LLM status)",      "None"],
        ["GET",  "/schema",              "Return {table: [columns]} schema map",        "None"],
        ["POST", "/query",               "Main NL→SQL query endpoint (synchronous)",   "None"],
        ["POST", "/query/stream",        "Streaming SSE version with step events",     "None"],
        ["POST", "/export/csv",          "Export result data as CSV file",             "None"],
        ["POST", "/export/excel",        "Export result data as Excel (.xlsx)",        "None"],
        ["POST", "/export/pdf",          "Export result data as PDF",                  "None"],
        ["POST", "/export/json",         "Export result data as JSON file",            "None"],
        ["POST", "/export/sql",          "Download the generated SQL as .sql file",   "None"],
        ["GET",  "/history",             "Fetch query history (limit, search params)", "None"],
        ["POST", "/history/favorite",    "Toggle favorite on a history entry",         "None"],
        ["POST", "/history/delete",      "Delete a history entry by timestamp",        "None"],
        ["GET",  "/admin/tables",        "List all tracked tables with row counts",    "None"],
        ["GET",  "/admin/schema",        "Full raw schema metadata JSON",              "None"],
        ["GET",  "/admin/knowledge-graph","Knowledge graph nodes and edges",           "None"],
        ["GET",  "/admin/status",        "Comprehensive system status",                "None"],
        ["GET",  "/admin/stats",         "Query analytics stats (latency, confidence)","None"],
        ["GET",  "/admin/settings",      "Get current LLM/embedding settings",         "None"],
        ["POST", "/admin/settings",      "Update LLM model, temperature, top_k, etc.", "None"],
        ["POST", "/admin/rebuild-embeddings","Rebuild ChromaDB vector embeddings",    "None"],
        ["POST", "/admin/refresh-metadata",  "Re-extract database schema metadata",   "None"],
    ]
    items += info_table(s, endpoints[0], endpoints[1:], [1.5*cm, 4.5*cm, 8*cm, 2*cm])

    items += sub_heading(s, "5.1.1  POST /query — Request & Response")
    items += body(s, "The primary endpoint used by the chat interface:")
    items += code_block(s, [
        "# Request Body",
        '{',
        '  "question": "Show all wallet transactions for July 2026",',
        '  "execute": true',
        '}',
    ], label="POST /query Request")
    items += code_block(s, [
        "# Successful Response",
        '{',
        '  "status": "success",',
        '  "question": "Show all wallet transactions for July 2026",',
        '  "sql_query": "SELECT id, user_id, amount, ... FROM wallet_transaction WHERE ...",',
        '  "execution_time": 128.5,',
        '  "rows_returned": 47,',
        '  "summary": "There were 47 transactions in July 2026 with total ₹1,23,450.",',
        '  "results": [{...}, ...],',
        '  "columns": ["id", "user_id", "amount", "transaction_type", "created_at"],',
        '  "report_urls": {"csv": "/reports/abc12345.csv", "excel": "...", "pdf": "..."},',
        '  "generated_sql": "...",',
        '  "explanation": "...",',
        '  "confidence_score": 95,',
        '  "thinking_steps": ["Step 1: ...", "Step 2: ..."],',
        '  "affected_tables": ["wallet_transaction"],',
        '  "benchmarks": {"total_ms": 4200, "llm_generation_ms": 3100, ...}',
        '}',
    ], label="POST /query Response")

    items += sub_heading(s, "5.1.2  Ambiguous Query Response")
    items += code_block(s, [
        '{',
        '  "status": "ambiguous",',
        '  "clarification": "Your prompt is underspecified. Please clarify:",',
        '  "options": [',
        '    "Today\'s Transactions",',
        '    "Last 7 days Transactions",',
        '    "Show Wallet Transactions"',
        '  ]',
        '}',
    ], label="Ambiguous Query Response")

    # 5.2 Agent Pipeline
    items += sub_heading(s, "5.2  AI Agent Pipeline (app/agent/sql_agent.py)")
    items += body(s, """
    The <b>run_agent()</b> function is the core orchestrator. It implements a 
    multi-step reasoning pipeline with up to 3 self-correction retries:
    """)
    pipeline_steps = [
        ["Step", "Function", "Description"],
        ["1", "check_ambiguity()", "Validates query clarity against DB enum values and term vocabulary"],
        ["2", "kg.resolve_business_query()", "Detects relevant tables, joins, date ranges from the Knowledge Graph"],
        ["3", "create_plan()", "Builds a structured execution plan dict with tables, columns, joins, terms"],
        ["4", "build_sql_prompt()", "Constructs a tight, structured LLM prompt from the execution plan"],
        ["5", "generate_sql()", "Calls Ollama LLM or deterministic synthesizer; extracts SQL from response"],
        ["6", "clean_sql()", "Strips markdown code fences, truncates at semicolon"],
        ["7", "validate_sql()", "AST validation via sqlglot — blocks non-SELECT, checks table/column names"],
        ["8", "get_execution_plan()", "Runs EXPLAIN FORMAT=JSON to validate and estimate query cost"],
        ["9", "execute_read_query()", "Executes SQL via connection pool; fetches max 500 rows"],
        ["10", "compute_confidence()", "Calculates 0-100 confidence score from validation and plan data"],
        ["11", "generate_natural_summary()", "Creates human-readable results summary with totals/counts"],
        ["12", "save_reports_to_disk()", "Generates and saves CSV/Excel/PDF report files"],
        ["13", "log_query_history()", "Persists query metadata to history JSON store"],
    ]
    items += info_table(s, pipeline_steps[0], pipeline_steps[1:], [0.8*cm, 4.5*cm, 10.7*cm])

    items += sub_heading(s, "5.3  Knowledge Graph (app/knowledge/knowledge_graph.py)")
    items += body(s, """
    The <b>BusinessKnowledgeGraph</b> is a singleton in-memory graph built from JSON metadata files 
    at startup. It provides:
    """)
    kg_features = [
        ("<b>Table Node Registry</b>", "All target tables registered as graph nodes with metadata."),
        ("<b>Explicit FK Edges</b>", "Foreign key constraints from DB schema stored as directed edges."),
        ("<b>Inferred FK Edges</b>", "Columns ending in _id infer relationships via column dictionary."),
        ("<b>BFS Join Resolution</b>", "Finds shortest join path between any two tables using BFS traversal."),
        ("<b>Alias Resolution</b>", "60+ business term aliases mapped to target tables (e.g. 'retailer' → users)."),
        ("<b>Date Range Parsing</b>", "Extracts 'July 2026', 'last month', 'this month' into start/end date filters."),
        ("<b>Enum Value Mapping</b>", "DB enum values loaded for ambiguity checking and business term filters."),
        ("<b>Pattern Learning</b>", "Successful queries are saved as learned patterns to improve future generation."),
    ]
    feat_tbl = Table(
        [[Paragraph(f, s['body_bold']), Paragraph(d, s['body'])] for f, d in kg_features],
        colWidths=[5*cm, 11*cm]
    )
    feat_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, TABLE_ALT_ROW]),
        ('GRID', (0,0), (-1,-1), 0.3, TABLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    items.append(feat_tbl)
    items.append(Spacer(1, 8))

    items += body(s, "Knowledge base JSON files loaded at startup:")
    items += info_table(s, ["File", "Contents"], [
        ["knowledge/schema/schema_metadata.json", "Full table/column metadata extracted from MySQL"],
        ["knowledge/schema/enum_dictionary.json", "Enum/distinct values for categorical columns"],
        ["knowledge/schema/sample_values.json", "Sample values for context-aware prompting"],
        ["knowledge/graph/entity_dictionary.json", "Entity-to-table mappings"],
        ["knowledge/graph/column_dictionary.json", "Column-to-table cross-reference"],
        ["knowledge/graph/business_dictionary.json", "Business terminology with SQL filter conditions"],
        ["knowledge/graph/join_graph.json", "Computed join adjacency list"],
        ["knowledge/graph/relationship_metadata.json", "All FK and inferred edges"],
        ["knowledge/patterns/query_patterns.json", "Learned successful query patterns"],
        ["knowledge/history/execution_history.json", "Historical execution records"],
    ], [7*cm, 9*cm])

    items += sub_heading(s, "5.4  SQL Generator & LLM Integration (app/llm/sql_generator.py)")
    items += body(s, """
    The generator first checks if <b>Ollama is online</b> (HTTP ping to port 11434 with 0.5s timeout). 
    If online, it calls the <b>qwen2.5-coder:7b</b> model with strict options. 
    If offline, it instantly falls back to a <b>deterministic rule-based SQL synthesizer</b>.
    """)
    items += info_table(s, ["Parameter", "Value", "Description"], [
        ["Model", "qwen2.5-coder:7b", "Default local LLM model (configurable via settings)"],
        ["temperature", "0.0", "Deterministic output, no randomness"],
        ["top_p", "0.9", "Nucleus sampling threshold"],
        ["num_predict", "200", "Max token output limit"],
        ["stop tokens", "['```\\n\\n', 'Explanation:']", "Stop generation at these tokens"],
        ["keep_alive", "60m", "Keep model loaded in memory for 60 minutes"],
        ["system role", "Expert MySQL Analyst", "System message constraining the model to SQL-only output"],
    ], [3*cm, 5*cm, 8*cm])

    items += sub_heading(s, "5.4.1  Deterministic SQL Synthesizer (Fallback)")
    items += body(s, """
    When Ollama is offline, the synthesizer parses the structured execution plan prompt using regex 
    to extract tables, columns, joins, filters, and date ranges — then builds a valid SQL query 
    programmatically without any LLM involvement. This ensures <b>100% uptime</b> even without a 
    running LLM server.
    """)

    items += sub_heading(s, "5.5  Prompt Engineering (app/prompt/prompt_builder.py)")
    items += body(s, """
    The prompt builder converts a structured execution plan into a tightly constrained LLM prompt:
    """)
    items += code_block(s, [
        "You are a Senior MySQL Enterprise Data Analyst for JGH.",
        "Translate this business question into a valid MySQL SELECT query.",
        "",
        "Business Question:",
        "{intent}",
        "",
        "Available Tables & Allowed Columns:",
        "Table `users` with columns: [id, name, email, mobile_number, ...]",
        "Table `role` with columns: [id, name, created_at]",
        "",
        "Business Term Mappings:",
        "- 'retailer': use filter `users.user_role = 2` (User role 2 means retailer)",
        "",
        "Required Joins:",
        "users.user_role = role.id",
        "",
        "CRITICAL RULES:",
        "1. ONLY SELECT columns that exist in the Allowed Columns list above.",
        "2. If business term mappings are provided, use their exact filter.",
        "3. NEVER invent imaginary columns.",
        "4. ALWAYS apply LIMIT 500 unless calculating aggregates.",
        "5. Output ONLY the query in ```sql ``` codeblock.",
    ], label="LLM Prompt Template")

    items += sub_heading(s, "5.6  SQL AST Validator (app/validator/sql_ast_validator.py)")
    items += body(s, """
    Uses <b>sqlglot</b> to parse SQL into an Abstract Syntax Tree. Validation steps:
    """)
    validator_rules = [
        "Root statement MUST be SELECT (no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.)",
        "Forbidden node types are scanned: Insert, Update, Delete, Drop, Alter, Create, Commit, Rollback, Execute, Command",
        "All referenced tables must be in the TARGET_SCOPE_TABLES allowlist",
        "All referenced columns must exist in the schema metadata for those tables",
        "Any validation failure raises SQLValidationError — triggering a retry with error feedback",
    ]
    for rule in validator_rules:
        items.append(Paragraph(f"• {rule}", s['body']))
    items.append(Spacer(1, 6))

    items += sub_heading(s, "5.7  Database Layer (app/database/)")
    db_files = [
        ["File", "Purpose"],
        ["read_executor.py", "execute_read_query(): SQLAlchemy connection pool, EXPLAIN support, Decimal/datetime serialization, NaN/Inf sanitization"],
        ["metadata_extractor.py", "generate_enterprise_knowledge_base(): Deep schema introspection with column types, FKs, enums, samples"],
        ["schema_extractor.py", "Lightweight schema extraction helpers"],
        ["allowed_tables.py", "TARGET_SCOPE_TABLES: whitelist of 8 target enterprise tables"],
        ["connection.py", "Standalone MySQL connection test and database lister"],
    ]
    items += info_table(s, db_files[0], db_files[1:], [5*cm, 11*cm])

    items += body(s, "Connection pool configuration:")
    items += code_block(s, [
        "engine = create_engine(",
        "    db_url,",
        "    pool_size=10,       # Base pool connections",
        "    max_overflow=20,    # Extra connections on demand",
        "    pool_recycle=3600,  # Recycle connections after 1 hour",
        "    pool_pre_ping=True  # Test connections before use",
        ")",
    ], label="SQLAlchemy Pool Config")

    items += sub_heading(s, "5.8  Embedding & Vector Store (app/embedding/)")
    items += body(s, """
    ChromaDB is used as an in-process vector database. Schema descriptions are embedded using 
    <b>all-MiniLM-L6-v2</b> (Sentence Transformers) and stored as vector embeddings. 
    The retriever performs cosine similarity search to find the most relevant schema context 
    for a given query — enabling RAG (Retrieval-Augmented Generation) for schema lookups.
    """)
    items += info_table(s, ["File", "Purpose"], [
        ["chroma_builder.py", "Builds and persists ChromaDB vector store from schema metadata"],
        ["embedding_builder.py", "Sentence transformer embedding wrapper (all-MiniLM-L6-v2)"],
        ["sql_history_embedding.py", "Embeds historical SQL for similar-query retrieval"],
    ], [5*cm, 11*cm])

    items += sub_heading(s, "5.9  Query History & Audit (app/sql_history/query_history.py)")
    items += body(s, """
    Every query execution is logged to a JSON file. The history record includes:
    question, generated_sql, optimized_sql, status (success/error/ambiguous/blocked), 
    execution_time_ms, row_count, affected_tables, error message, confidence_score, 
    execution_plan, explanation, and thinking_steps.
    History supports filtering by search term and toggling favorites.
    """)

    items += sub_heading(s, "5.10  Report Generator (app/utils/report_generator.py)")
    items += body(s, """
    The report generator creates downloadable output files from query results. 
    All reports are saved to the <b>reports/</b> directory with a UUID-based filename:
    """)
    items += info_table(s, ["Format", "Library", "Details"], [
        ["CSV", "Python csv module (streaming)", "Streaming response for large datasets; UTF-8 BOM for Excel compatibility"],
        ["Excel", "openpyxl", "Styled header row, auto-column widths, worksheet named 'Query Results'"],
        ["PDF", "ReportLab", "Branded header, auto-wrapped table, styled column headers, page breaks"],
        ["JSON", "json.dumps", "Pretty-printed JSON array of result rows"],
    ], [2.5*cm, 3.5*cm, 10*cm])

    items.append(PageBreak())
    return items


# ── Section 6: Frontend ───────────────────────────────────────────────────────
def build_frontend(s):
    items = []
    items += section_divider(s, "6. Frontend — React / Vite")

    items += body(s, """
    The frontend is a <b>React 19 single-page application</b> built with Vite 8. 
    It features a dark-themed, glassmorphic design system with smooth animations. 
    The app communicates with the FastAPI backend via HTTP REST calls. 
    In development mode, Vite proxies API calls to localhost:8000.
    """)

    items += sub_heading(s, "6.1  Application Screens")
    screens = [
        ["Screen", "Route/Tab", "Description"],
        ["Query Interface (CenterChat)", "chat", "Main conversational AI chat interface with SQL display, data table, charts, and download buttons"],
        ["History & Audit", "history", "Full query history with search, re-run, favorite, delete, and SQL preview"],
        ["Schema Admin", "admin", "Admin dashboard: system status, table list, knowledge graph viewer, rebuild controls"],
        ["Settings", "settings", "Configure LLM model, embedding model, temperature, top_k, max_rows at runtime"],
    ]
    items += info_table(s, screens[0], screens[1:], [4*cm, 2.5*cm, 9.5*cm])

    items += sub_heading(s, "6.2  Component Reference")
    components = [
        ["Component File", "Description"],
        ["App.jsx", "Root component: sidebar navigation, tab routing, message state management, API call handler"],
        ["CenterChat.jsx", "Full chat interface: message list, SQL code block, execution status card, download buttons, DataGrid, AutoChart"],
        ["DataGrid.jsx", "Paginated data table with column sorting, overflow handling, and sticky headers"],
        ["AutoChart.jsx", "Recharts-based auto-charting: detects numeric/categorical columns and renders bar/line/pie charts automatically"],
        ["DatabaseSchemaPanel.jsx", "Right panel: live schema browser showing tables and their columns fetched from /schema endpoint"],
        ["HistoryView.jsx", "Query history list with search, re-run, favorite toggle, delete, and expandable SQL/result preview"],
        ["AdminPanel.jsx", "Admin dashboard: system stats, table browser, knowledge graph, rebuild embeddings, refresh metadata"],
        ["Settings.jsx", "Full settings form: model name, embedding model, temperature slider, top_k, max_rows"],
        ["Sidebar.jsx", "Navigation sidebar: logo, 'New Query' button, nav items, backend status indicator"],
    ]
    items += info_table(s, components[0], components[1:], [5*cm, 11*cm])

    items += sub_heading(s, "6.3  Design System")
    items += body(s, """
    The application uses a custom CSS design system defined in <b>index.css</b> and component-level 
    CSS files. Key design tokens:
    """)
    design_tokens = [
        ["Token", "Value", "Usage"],
        ["--bg-primary", "#0F172A", "Main background (dark navy)"],
        ["--bg-surface", "#1E293B", "Card/panel surface"],
        ["--accent-indigo", "#6366F1", "Primary brand color"],
        ["--accent-cyan", "#22D3EE", "Secondary accent"],
        ["--text-primary", "#F1F5F9", "Primary text color"],
        ["--text-muted", "#64748B", "Muted/secondary text"],
        ["Font", "System UI / Segoe UI", "System font stack for performance"],
    ]
    items += info_table(s, design_tokens[0], design_tokens[1:], [3.5*cm, 4*cm, 8.5*cm])

    items.append(PageBreak())
    return items


# ── Section 7: Environment Configuration ─────────────────────────────────────
def build_env_config(s):
    items = []
    items += section_divider(s, "7. Environment Configuration (.env)")

    items += body(s, """
    The application is configured via a <b>.env</b> file in the project root. 
    This file must NEVER be committed to version control (it is in .gitignore).
    """)
    items += code_block(s, [
        "# ── Database Configuration ──────────────────────────────",
        "DB_HOST=your_mysql_host",
        "DB_PORT=3306",
        "DB_NAME=your_database_name",
        "DB_USER=your_mysql_username",
        "DB_PASSWORD=your_mysql_password",
        "",
        "# ── LLM Configuration (Optional) ─────────────────────────",
        "LLM_MODEL=qwen2.5-coder:7b",
    ], label=".env File Template")

    items += info_table(s, ["Variable", "Required", "Default", "Description"], [
        ["DB_HOST", "Yes", "—", "MySQL server hostname or IP address"],
        ["DB_PORT", "Yes", "3306", "MySQL server port number"],
        ["DB_NAME", "Yes", "—", "Target database name"],
        ["DB_USER", "Yes", "—", "MySQL username with SELECT privileges"],
        ["DB_PASSWORD", "Yes", "—", "MySQL user password"],
        ["LLM_MODEL", "No", "qwen2.5-coder:7b", "Ollama model to use for SQL generation"],
    ], [3*cm, 2*cm, 4*cm, 7*cm])

    items += highlight_box(s,
        "⚠ SECURITY: The database user must have READ-ONLY access (SELECT only). "
        "Never use a user with write permissions. The .env file must never be "
        "committed to Git.",
        color=colors.HexColor("#FFF7ED"), text_color=colors.HexColor("#92400E")
    )
    items.append(PageBreak())
    return items


# ── Section 8: Installation & Setup ──────────────────────────────────────────
def build_setup(s):
    items = []
    items += section_divider(s, "8. Installation & Setup Guide")

    items += sub_heading(s, "8.1  Prerequisites")
    items += info_table(s, ["Requirement", "Version", "Notes"], [
        ["Python", "3.10+", "Required for the backend"],
        ["Node.js", "18+", "Required for the frontend build"],
        ["npm", "9+", "Node package manager"],
        ["MySQL", "5.7+ or 8.0+", "Target database server (read access required)"],
        ["Ollama", "Latest", "Optional — provides local LLM inference (install from ollama.ai)"],
        ["Git", "Any", "For cloning the repository"],
    ], [3.5*cm, 3*cm, 9.5*cm])

    items += sub_heading(s, "8.2  Backend Setup (Step-by-Step)")
    steps = [
        ("Step 1: Clone the repository",
         ["git clone <repository-url>", "cd Agent"]),
        ("Step 2: Create Python virtual environment",
         ["python -m venv venv",
          "# Windows:", "venv\\Scripts\\activate",
          "# Linux/Mac:", "source venv/bin/activate"]),
        ("Step 3: Install Python dependencies",
         ["pip install -r requirements.txt",
          "",
          "# NOTE: This installs ~107 packages including:",
          "# FastAPI, SQLAlchemy, ChromaDB, Sentence-Transformers,",
          "# Ollama client, pandas, ReportLab, openpyxl, sqlglot, etc."]),
        ("Step 4: Configure environment variables",
         ["# Create .env file in project root:",
          "DB_HOST=your_mysql_host",
          "DB_PORT=3306",
          "DB_NAME=your_database_name",
          "DB_USER=readonly_user",
          "DB_PASSWORD=your_password"]),
        ("Step 5: Verify database connection",
         ["python app/database/connection.py",
          "# Should print: ✅ Connected Successfully to MySQL Server!"]),
        ("Step 6: Generate knowledge base (first run only)",
         ["# This runs automatically at startup, or manually:",
          "python -c \"from app.database.metadata_extractor import generate_enterprise_knowledge_base; generate_enterprise_knowledge_base()\""]),
    ]
    for step_label, step_cmds in steps:
        items += sub_sub_heading(s, step_label)
        items += code_block(s, step_cmds)

    items += sub_heading(s, "8.3  Frontend Setup")
    frontend_steps = [
        ("Step 1: Navigate to frontend directory",
         ["cd frontend"]),
        ("Step 2: Install Node.js dependencies",
         ["npm install",
          "",
          "# Installs: React 19, Vite 8, Recharts, Lucide React, oxlint"]),
        ("Step 3: Verify Vite config proxy",
         ["# vite.config.js proxies /query, /schema, /history,",
          "# /admin, /export, /reports, /health → http://127.0.0.1:8000"]),
    ]
    for step_label, step_cmds in frontend_steps:
        items += sub_sub_heading(s, step_label)
        items += code_block(s, step_cmds)

    items += sub_heading(s, "8.4  Ollama LLM Setup (Optional but Recommended)")
    items += code_block(s, [
        "# 1. Download Ollama from https://ollama.ai",
        "#    and install for your OS (Windows/Mac/Linux)",
        "",
        "# 2. Pull the qwen2.5-coder model (~4GB download):",
        "ollama pull qwen2.5-coder:7b",
        "",
        "# 3. Verify it works:",
        "ollama run qwen2.5-coder:7b",
        "",
        "# 4. Ollama runs as a background service on port 11434.",
        "#    The app auto-detects Ollama availability.",
        "#    If offline, the deterministic SQL synthesizer is used.",
    ], label="Ollama Setup")
    items.append(PageBreak())
    return items


# ── Section 9: Running the Application ───────────────────────────────────────
def build_running(s):
    items = []
    items += section_divider(s, "9. Running the Application")

    items += sub_heading(s, "9.1  Start the Backend Server")
    items += code_block(s, [
        "# Navigate to project root",
        "cd Agent",
        "",
        "# Activate virtual environment",
        "venv\\Scripts\\activate        # Windows",
        "source venv/bin/activate     # Linux/Mac",
        "",
        "# Start FastAPI backend (auto-reload mode for development)",
        "python app/main.py",
        "",
        "# Or directly with uvicorn:",
        "uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload",
        "",
        "# Expected startup output:",
        "[STARTUP] Pre-loading Knowledge Graph...",
        "[STARTUP COMPLETE] Enterprise AI SQL Agent ready on http://localhost:8000",
        "",
        "# API docs available at:",
        "# http://localhost:8000/docs        (Swagger UI)",
        "# http://localhost:8000/redoc       (ReDoc)",
    ], label="Backend Startup")

    items += sub_heading(s, "9.2  Start the Frontend Dev Server")
    items += code_block(s, [
        "# In a NEW terminal, navigate to frontend:",
        "cd Agent/frontend",
        "",
        "# Start Vite development server:",
        "npm run dev",
        "",
        "# Expected output:",
        "  VITE v8.2.0  ready in 350 ms",
        "  ➜  Local:   http://localhost:3000/",
        "  ➜  Network: http://0.0.0.0:3000/",
        "",
        "# Open browser to: http://localhost:3000",
    ], label="Frontend Dev Server")

    items += sub_heading(s, "9.3  Build & Serve Frontend (Production / Embedded Mode)")
    items += code_block(s, [
        "# Build the frontend (outputs to app/static/)",
        "cd Agent/frontend",
        "npm run build",
        "",
        "# The FastAPI backend serves the built files at root /",
        "# So you only need to run:",
        "python app/main.py",
        "",
        "# And access the full app at:",
        "# http://localhost:8000",
        "",
        "# This is the PRODUCTION deployment mode —",
        "# single process, no separate frontend server needed.",
    ], label="Production Build & Serve")

    items += sub_heading(s, "9.4  Health Check")
    items += code_block(s, [
        "# Verify the backend is running:",
        "curl http://localhost:8000/health",
        "",
        "# Expected response:",
        '{',
        '  "status": "online",',
        '  "database_connected": true,',
        '  "target_tables_count": 8,',
        '  "llm_model": "qwen2.5-coder:7b"',
        '}',
    ], label="Health Check")

    items += sub_heading(s, "9.5  Rebuild Vector Embeddings (after schema changes)")
    items += code_block(s, [
        "# Via API:",
        "curl -X POST http://localhost:8000/admin/rebuild-embeddings",
        "",
        "# Via Admin UI:",
        "# Navigate to Schema Admin tab → click 'Rebuild Embeddings'",
        "",
        "# Refresh schema metadata (after adding new tables):",
        "curl -X POST http://localhost:8000/admin/refresh-metadata",
    ], label="Rebuild Embeddings")
    items.append(PageBreak())
    return items


# ── Section 10: API Usage Examples ───────────────────────────────────────────
def build_api_examples(s):
    items = []
    items += section_divider(s, "10. API Usage Examples")

    examples = [
        ("Query: Show all retailers",
         ["curl -X POST http://localhost:8000/query \\",
          "  -H 'Content-Type: application/json' \\",
          "  -d '{\"question\": \"Show all retailers\", \"execute\": true}'"]),
        ("Query: Wallet transactions for July 2026",
         ["curl -X POST http://localhost:8000/query \\",
          "  -H 'Content-Type: application/json' \\",
          "  -d '{\"question\": \"Show wallet transactions for July 2026\"}'"]),
        ("Query: Count of users by role",
         ["curl -X POST http://localhost:8000/query \\",
          "  -H 'Content-Type: application/json' \\",
          "  -d '{\"question\": \"How many users are there by role?\"}'"]),
        ("Export results as CSV",
         ["curl -X POST http://localhost:8000/export/csv \\",
          "  -H 'Content-Type: application/json' \\",
          "  -d '{\"columns\": [\"id\",\"name\"], \"data\": [{...}], \"filename\": \"users_report\"}'"]),
        ("Fetch query history (last 50)",
         ["curl 'http://localhost:8000/history?limit=50'"]),
        ("Rebuild schema embeddings",
         ["curl -X POST http://localhost:8000/admin/rebuild-embeddings"]),
        ("Update LLM settings",
         ["curl -X POST http://localhost:8000/admin/settings \\",
          "  -H 'Content-Type: application/json' \\",
          "  -d '{\"model_name\": \"qwen2.5-coder:14b\", \"temperature\": 0.1, \"top_k\": 6}'"]),
        ("Get system status",
         ["curl http://localhost:8000/admin/status"]),
    ]
    for title, cmd in examples:
        items += sub_sub_heading(s, title)
        items += code_block(s, cmd)

    items.append(PageBreak())
    return items


# ── Section 11: Data Flow Walkthrough ─────────────────────────────────────────
def build_data_flow(s):
    items = []
    items += section_divider(s, "11. Data Flow Walkthrough")

    items += body(s, """
    This section traces a complete end-to-end example: 
    <b>"Show me all withdrawal requests in July 2026"</b>
    """)
    items.append(Spacer(1, 6))

    flow = [
        ("1. User Input", "User types 'Show me all withdrawal requests in July 2026' in the chat and presses Enter."),
        ("2. Frontend POST", "React calls POST /query with {question: '...', execute: true}."),
        ("3. Ambiguity Check", "check_ambiguity() scans enum values — 'withdrawal requests' matches known DB terms → NOT ambiguous → continues."),
        ("4. Knowledge Graph Resolution", "resolve_business_query() maps 'withdrawal' → withdrawal_request table. 'July 2026' → date range 2026-07-01 to 2026-08-01."),
        ("5. Execution Plan", "create_plan() returns: {intent: '...', tables: ['withdrawal_request'], table_columns: {withdrawal_request: [id, user_id, amount, ...]}, date_filters: {start: '2026-07-01', end: '2026-08-01'}, relationships_required: []}."),
        ("6. Prompt Building", "build_sql_prompt() creates a structured prompt with table columns, date range, and 5 CRITICAL RULES."),
        ("7. LLM Generation", "generate_sql() calls Ollama qwen2.5-coder:7b. Response includes SQL in ```sql blocks. SQL is extracted and cleaned."),
        ("8. AST Validation (Attempt 1)", "validate_sql() parses the SQL with sqlglot. Confirms SELECT statement, checks withdrawal_request is in allowed tables, verifies all columns exist."),
        ("9. EXPLAIN Check", "get_execution_plan() runs EXPLAIN FORMAT=JSON — query is valid, cost estimated at 45.2 → continues."),
        ("10. DB Execution", "execute_read_query() runs SQL via SQLAlchemy pool. Returns 23 rows in 85ms."),
        ("11. Report Generation", "save_reports_to_disk() saves report_abc12345.csv, .xlsx, .pdf to /reports/"),
        ("12. Summary", "generate_natural_summary() sees 'amount' column, sums to ₹4,56,200 → 'There were 23 withdrawal requests in July 2026 with total ₹4,56,200.'"),
        ("13. History Log", "log_query_history() saves full record including SQL, execution time, confidence=100, affected_tables=['withdrawal_request']."),
        ("14. Response JSON", "FastAPI returns status='success', sql_query, results, columns, summary, report_urls, benchmarks."),
        ("15. Frontend Render", "React renders: AI message with summary, SQL block (copy button), ExecutionStatus card (85ms, 23 rows), DataGrid (paginated table), AutoChart (bar chart), download buttons (CSV/Excel/PDF)."),
    ]
    flow_tbl = Table(
        [[Paragraph(f"<b>{step}</b>", s['body_bold']), Paragraph(desc, s['body'])]
         for step, desc in flow],
        colWidths=[4.5*cm, 11.5*cm]
    )
    flow_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, TABLE_ALT_ROW]),
        ('GRID', (0,0), (-1,-1), 0.3, TABLE_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    items.append(flow_tbl)
    items.append(PageBreak())
    return items


# ── Section 12: Security ──────────────────────────────────────────────────────
def build_security(s):
    items = []
    items += section_divider(s, "12. Security & Read-Only Enforcement")

    items += body(s, """
    Agentic Analyst enforces strict read-only access at multiple independent layers:
    """)

    security_layers = [
        ("Layer 1: Database User Permissions", 
         "The MySQL user configured in .env should have SELECT-only privileges. "
         "No INSERT, UPDATE, DELETE, DROP, or DDL permissions should be granted."),
        ("Layer 2: AST-Level SQL Validation",
         "Every generated SQL is parsed into an AST by sqlglot before execution. "
         "Non-SELECT root nodes immediately raise SQLValidationError, triggering a retry. "
         "Forbidden node types: Insert, Update, Delete, Drop, Alter, Create, Commit, Rollback, Execute, Command."),
        ("Layer 3: Table Allowlist",
         "TARGET_SCOPE_TABLES in allowed_tables.py defines exactly which tables can be queried. "
         "Any SQL referencing tables outside this list is rejected."),
        ("Layer 4: Column Allowlist",
         "The AST validator cross-references every column reference against the schema metadata. "
         "Columns that don't exist in the target table are rejected."),
        ("Layer 5: EXPLAIN Validation",
         "MySQL EXPLAIN FORMAT=JSON validates the query structure before execution. "
         "Invalid queries that pass AST checks are caught here."),
        ("Layer 6: Prompt Constraints",
         "The LLM system prompt explicitly instructs the model to output only SELECT statements. "
         "The prompt is structured to minimize SQL injection risks."),
        ("Layer 7: SQL Cleaner",
         "The SQL cleaner strips markdown, truncates after the first semicolon, "
         "and sanitizes the raw LLM output before any validation."),
        ("Layer 8: Row Limits",
         "All queries are subject to LIMIT 500 (configurable via settings). "
         "Aggregate queries are exempt from LIMIT but are COUNT/SUM only."),
    ]

    for layer, desc in security_layers:
        items += sub_sub_heading(s, layer)
        items += body(s, desc)

    items += highlight_box(s,
        "✅ SECURITY SUMMARY: A malicious or incorrect LLM output would need to bypass "
        "all 8 independent security layers to cause any data modification. "
        "Each layer independently blocks non-SELECT operations.",
        color=colors.HexColor("#F0FDF4"), text_color=colors.HexColor("#14532D")
    )
    items.append(PageBreak())
    return items


# ── Section 13: Troubleshooting ───────────────────────────────────────────────
def build_troubleshooting(s):
    items = []
    items += section_divider(s, "13. Troubleshooting & FAQ")

    issues = [
        ("Backend won't start",
         "Ensure the virtual environment is activated. Run: venv\\Scripts\\activate (Windows). "
         "Check that all dependencies are installed: pip install -r requirements.txt"),
        ("Database connection failed",
         "Verify .env variables are correct. Test directly: python app/database/connection.py. "
         "Ensure MySQL server is running and the user has SELECT access to DB_NAME."),
        ("LLM not generating SQL",
         "Check if Ollama is running: curl http://localhost:11434/api/tags. "
         "If offline, the deterministic synthesizer will be used automatically. "
         "Pull the model: ollama pull qwen2.5-coder:7b"),
        ("'Table X not allowed' validation error",
         "The table is not in TARGET_SCOPE_TABLES (allowed_tables.py). "
         "Add the table name to the allowlist and restart the backend."),
        ("'Column X does not exist' error",
         "The schema metadata may be stale. Run: POST /admin/refresh-metadata "
         "to re-extract the latest schema from the database."),
        ("Frontend shows 'Failed to connect to backend'",
         "Ensure the backend is running on port 8000. "
         "The frontend dev server proxies API calls to 127.0.0.1:8000."),
        ("ChromaDB / embedding errors on startup",
         "Run: POST /admin/rebuild-embeddings from the Admin panel or via curl. "
         "Delete the app/chroma directory and restart if corruption is suspected."),
        ("Slow SQL generation",
         "The LLM model is loading. After the first query, the model is kept in memory "
         "for 60 minutes (keep_alive=60m). Subsequent queries are fast (~1-3s)."),
        ("Knowledge base JSON files missing",
         "Start the backend — knowledge base is auto-generated on first startup. "
         "Or manually: from app.database.metadata_extractor import generate_enterprise_knowledge_base; generate_enterprise_knowledge_base()"),
        ("Reports directory not found",
         "The /reports directory is auto-created by the API on startup. "
         "Ensure the process has write permissions to the project root."),
        ("Ambiguous query keeps firing",
         "Edit knowledge/business_metadata.json to add or refine business terms. "
         "Run POST /admin/refresh-metadata to reload."),
    ]
    for issue, solution in issues:
        items += sub_sub_heading(s, f"❓ {issue}")
        items += body(s, f"<b>Solution:</b> {solution}")

    items.append(PageBreak())
    return items


# ── Section 14: Glossary ──────────────────────────────────────────────────────
def build_glossary(s):
    items = []
    items += section_divider(s, "14. Glossary")

    terms = [
        ["Term", "Definition"],
        ["AI Agent", "Autonomous software that perceives input, reasons about it, and takes actions to achieve a goal"],
        ["AST (Abstract Syntax Tree)", "A tree representation of the grammatical structure of SQL used for validation"],
        ["ChromaDB", "Open-source, in-process vector database for storing and searching embeddings"],
        ["EXPLAIN", "MySQL command that shows the query execution plan without running the query"],
        ["FastAPI", "Modern Python web framework for building APIs with automatic validation and docs"],
        ["Hallucination", "When an LLM generates incorrect or fabricated information (e.g., non-existent columns)"],
        ["Knowledge Graph", "An in-memory network of entities (tables, columns) and their relationships"],
        ["LLM (Large Language Model)", "AI model trained on text data; here used as qwen2.5-coder:7b via Ollama"],
        ["NL2SQL", "Natural Language to SQL — converting English questions to database queries"],
        ["Ollama", "Local LLM server that runs models on your machine without internet dependency"],
        ["Prompt Engineering", "The craft of structuring LLM input to guide desired output"],
        ["RAG (Retrieval-Augmented Generation)", "Enhancing LLM prompts with retrieved contextual data (schema embeddings)"],
        ["Self-Correction", "The agent's ability to detect errors and retry with error feedback (up to 3 times)"],
        ["Sentence Transformers", "ML models that convert text into semantic vector embeddings for similarity search"],
        ["sqlglot", "Python library for parsing, analyzing, and transforming SQL across dialects"],
        ["SQLAlchemy", "Python SQL toolkit and ORM with connection pooling"],
        ["SSE (Server-Sent Events)", "HTTP streaming protocol used by /query/stream endpoint"],
        ["TARGET_SCOPE_TABLES", "The allowlist of 8 enterprise tables that the agent is permitted to query"],
        ["Vector Embedding", "A numerical vector representation of text capturing semantic meaning"],
        ["Vite", "Next-generation frontend build tool and dev server used for the React app"],
    ]
    items += info_table(s, terms[0], terms[1:], [5.5*cm, 10.5*cm])

    items.append(Spacer(1, 16))
    items += highlight_box(s,
        f"📄 Agentic Analyst — Full Project Handbook  |  Version 2.0  |  "
        f"Generated: {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}  |  "
        f"Status: Active / Production  |  © Engineering Team",
        color=BRAND_DARK, text_color=colors.HexColor("#94A3B8")
    )
    return items


# ── Main PDF Builder ──────────────────────────────────────────────────────────
def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.8*cm,
        leftMargin=1.8*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="Agentic Analyst — Full Project Handbook",
        author="Engineering Team",
        subject="Enterprise AI SQL Intelligence Platform",
    )

    s = build_styles()
    story = []

    # Build all sections
    story += build_cover(s)
    story += build_toc(s)
    story += build_overview(s)
    story += build_architecture(s)
    story += build_tech_stack(s)
    story += build_project_structure(s)
    story += build_backend(s)
    story += build_frontend(s)
    story += build_env_config(s)
    story += build_setup(s)
    story += build_running(s)
    story += build_api_examples(s)
    story += build_data_flow(s)
    story += build_security(s)
    story += build_troubleshooting(s)
    story += build_glossary(s)

    class HandbookCanvas(NumberedCanvas):
        """Extended canvas that draws the cover page on page 1."""
        def draw_page_number(self, page_count):
            page = self._pageNumber
            if page == 1:
                draw_cover_page(self, None)
            else:
                self.setFont("Helvetica", 8)
                self.setFillColor(BRAND_MUTED)
                self.drawRightString(A4[0] - 1.5*cm, 0.8*cm, f"Page {page-1} of {page_count-1}")
                self.drawString(1.5*cm, 0.8*cm, "Agentic Analyst - Project Handbook  |  Confidential")
                self.setStrokeColor(TABLE_BORDER)
                self.setLineWidth(0.5)
                self.line(1.5*cm, 1.1*cm, A4[0] - 1.5*cm, 1.1*cm)

    # Build with cover-aware numbered pages
    doc.build(story, canvasmaker=HandbookCanvas)
    print(f"\nHandbook PDF generated: {output_path}")
    print(f"   File size: {os.path.getsize(output_path) / 1024:.1f} KB")


if __name__ == "__main__":
    output = r"c:\Users\nayak_o7hopi6\Desktop\Agent\Agentic_Analyst_Handbook.pdf"
    build_pdf(output)
