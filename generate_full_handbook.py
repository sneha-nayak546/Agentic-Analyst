import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to add running headers and total page counts (Page X of Y).
    """
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress running header/footer on cover page

        self.saveState()
        
        # Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawString(40, 762, "ENTERPRISE AI SQL AGENT — FULL PROJECT HANDBOOK & SYSTEM ARCHITECTURE")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(40, 754, 572, 754)

        # Footer
        self.line(40, 42, 572, 42)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(40, 30, "System Handbook | Enterprise AI SQL Intelligence Platform")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_str)
        
        self.restoreState()


def build_pdf(filename="FULL_PROJECT_HANDBOOK.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F172A")      # Dark Slate
    ACCENT = colors.HexColor("#1D4ED8")       # Rich Blue
    SECONDARY = colors.HexColor("#2563EB")    # Bright Blue
    TEXT_MAIN = colors.HexColor("#334155")    # Charcoal
    BG_LIGHT = colors.HexColor("#F8FAFC")     # Soft Gray
    BG_CODE = colors.HexColor("#1E293B")      # Code Block Dark
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    style_cover_title = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=PRIMARY,
        spaceAfter=12
    )

    style_cover_subtitle = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=ACCENT,
        spaceAfter=30
    )

    style_cover_meta = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#64748B")
    )

    style_h1 = ParagraphStyle(
        'CustomH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        'CustomH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=ACCENT,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    style_h3 = ParagraphStyle(
        'CustomH3',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_MAIN,
        spaceAfter=6
    )

    style_bullet = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_MAIN,
        leftIndent=15,
        spaceAfter=4
    )

    style_code = ParagraphStyle(
        'CustomCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#F1F5F9"),
        backColor=BG_CODE,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=8
    )

    style_callout = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
        backColor=colors.HexColor("#EFF6FF"),
        borderColor=colors.HexColor("#93C5FD"),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=8
    )

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("Enterprise AI SQL Agent", style_cover_title))
    story.append(Paragraph("Intelligence Platform & Full System Handbook", style_cover_subtitle))
    story.append(HRFlowable(width="100%", thickness=3, color=ACCENT, spaceBefore=0, spaceAfter=20))
    
    cover_desc = (
        "<b>Comprehensive Architectural Specification, Implementation Handbook, "
        "Component Guide, Security Guardrails, API Reference, and Operational Runbook.</b><br/><br/>"
        "This document serves as the single source of truth for the Enterprise AI SQL Agent, "
        "a production-ready system capable of translating natural-language queries into safe, "
        "optimized MySQL SELECT statements with interactive data analysis, natural language summaries, "
        "and automated multi-format report exports."
    )
    story.append(Paragraph(cover_desc, style_body))
    story.append(Spacer(1, 30))

    meta_table_data = [
        [Paragraph("<b>System Name:</b>", style_body), Paragraph("Enterprise AI SQL Agent Intelligence Platform", style_body)],
        [Paragraph("<b>Version:</b>", style_body), Paragraph("2.0 Production Release", style_body)],
        [Paragraph("<b>Backend Stack:</b>", style_body), Paragraph("Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, PyMySQL, Pandas, ReportLab", style_body)],
        [Paragraph("<b>Frontend Stack:</b>", style_body), Paragraph("React 19, Vite 8, Recharts, Lucide-React, Oxlint", style_body)],
        [Paragraph("<b>LLM Engine:</b>", style_body), Paragraph("Ollama Local Model (qwen2.5-coder:7b / Llama3) + Deterministic Fallback", style_body)],
        [Paragraph("<b>Database:</b>", style_body), Paragraph("MySQL (Read-Only Persistent Pool)", style_body)],
        [Paragraph("<b>Vector Search:</b>", style_body), Paragraph("ChromaDB + SentenceTransformers (all-MiniLM-L6-v2)", style_body)],
        [Paragraph("<b>Document Date:</b>", style_body), Paragraph("August 2026", style_body)],
    ]
    t_meta = Table(meta_table_data, colWidths=[120, 412])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 40))

    toc_box = (
        "<b>Table of Contents:</b><br/>"
        "1. Executive Summary & Core Objectives<br/>"
        "2. High-Level Architecture & End-to-End Workflow<br/>"
        "3. Backend Architecture & Subsystem Deep Dive<br/>"
        "4. Database Safety, EXPLAIN Validation & Read-Only Guardrails<br/>"
        "5. Knowledge Graph & RAG Vector Engine<br/>"
        "6. Frontend Architecture & User Interface Manual<br/>"
        "7. Complete REST API Specification<br/>"
        "8. Report Generation & Export Capabilities<br/>"
        "9. Installation, Configuration & Deployment Runbook<br/>"
        "10. System Maintenance, Benchmarking & Troubleshooting"
    )
    story.append(Paragraph(toc_box, style_callout))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 1: EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Core Objectives", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))
    
    story.append(Paragraph(
        "The <b>Enterprise AI SQL Agent Intelligence Platform</b> is designed to bridge the gap between non-technical business stakeholders "
        "and complex enterprise SQL databases. In traditional enterprise environments, querying relational databases requires specialized SQL "
        "knowledge, leading to slow reporting turnarounds and heavy engineering backlogs.",
        style_body
    ))
    story.append(Paragraph(
        "This platform solves the problem by converting plain, natural-language questions (e.g., <i>'What are top 5 selling products by revenue?'</i>) "
        "into executable, highly accurate, and validated MySQL queries in milliseconds, rendering dynamic data tables, visual charts, and executive narrative summaries.",
        style_body
    ))

    story.append(Paragraph("Key System Pillars:", style_h2))
    story.append(Paragraph("• <b>Zero Hallucination SQL Generation:</b> Combines deterministic query planning, business terminology knowledge graphs, and RAG retrieval to prevent invalid table/column references.", style_bullet))
    story.append(Paragraph("• <b>Strict Read-Only Guardrails:</b> Enforces database connection safety with AST keyword parsing, blocking destructive operations (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE).", style_bullet))
    story.append(Paragraph("• <b>Local & Offline First:</b> Utilizes local LLM inference via Ollama (qwen2.5-coder:7b), ensuring zero sensitive enterprise schema data leaves the corporate firewall.", style_bullet))
    story.append(Paragraph("• <b>Self-Correcting & EXPLAIN Validation:</b> Evaluates query cost using MySQL EXPLAIN execution plans and auto-corrects syntax errors prior to final response delivery.", style_bullet))
    story.append(Paragraph("• <b>Multi-Format Export:</b> Enables one-click exports to PDF, Excel, CSV, and streaming CSV formats for seamless executive reporting.", style_bullet))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 2: HIGH-LEVEL ARCHITECTURE & FLOW
    # =========================================================================
    story.append(Paragraph("2. High-Level Architecture & End-to-End Workflow", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "The system follows a modular, decoupled micro-architecture consisting of a high-performance React frontend, a FastAPI asynchronous gateway, "
        "a multi-stage agentic pipeline, a vector retriever, and a read-only database execution layer.",
        style_body
    ))

    story.append(Paragraph("End-to-End Request Trajectory:", style_h2))

    flow_table_data = [
        [Paragraph("<b>Stage</b>", style_h3), Paragraph("<b>Component</b>", style_h3), Paragraph("<b>Action & Processing Details</b>", style_h3)],
        [
            Paragraph("1. Ingress", style_body),
            Paragraph("React Frontend / FastAPI Gateway", style_body),
            Paragraph("User enters a natural language question. The request hits <code>POST /query</code> or <code>POST /query/stream</code> on the FastAPI backend.", style_body)
        ],
        [
            Paragraph("2. Ambiguity Check", style_body),
            Paragraph("app/agent/ambiguity_checker.py", style_body),
            Paragraph("Scans query for vague phrasing (e.g., 'recent sales' without dates). Returns clarification options if ambiguous.", style_body)
        ],
        [
            Paragraph("3. Entity Resolution", style_body),
            Paragraph("app/knowledge/knowledge_graph.py", style_body),
            Paragraph("Maps business terms (e.g., 'customers', 'revenue', 'orders') to exact schema tables, primary keys, and foreign key join paths.", style_body)
        ],
        [
            Paragraph("4. Context RAG", style_body),
            Paragraph("app/retriever/retriever.py", style_body),
            Paragraph("Queries ChromaDB for semantically similar past SQL queries and table schemas to inject into the LLM prompt.", style_body)
        ],
        [
            Paragraph("5. Query Planning", style_body),
            Paragraph("app/agent/query_planner.py", style_body),
            Paragraph("Constructs a deterministic execution plan outlining targeted tables, required JOIN clauses, filters, and aggregations.", style_body)
        ],
        [
            Paragraph("6. SQL Generation", style_body),
            Paragraph("app/llm/sql_generator.py", style_body),
            Paragraph("Sends schema-constrained prompt to Ollama (qwen2.5-coder:7b). Applies regex fallback if LLM is offline.", style_body)
        ],
        [
            Paragraph("7. AST & EXPLAIN Validation", style_body),
            Paragraph("app/validator/sql_ast_validator.py", style_body),
            Paragraph("Parses SQL syntax tree, checks read-only rules, and executes <code>EXPLAIN</code> to estimate query execution cost.", style_body)
        ],
        [
            Paragraph("8. Read Execution", style_body),
            Paragraph("app/database/read_executor.py", style_body),
            Paragraph("Executes the sanitized query on MySQL via SQLAlchemy connection pool with strict row limits (default 500 rows).", style_body)
        ],
        [
            Paragraph("9. Synthesis & Delivery", style_body),
            Paragraph("app/utils/summary_generator.py", style_body),
            Paragraph("Generates natural-language executive summary of data, logs history, and returns JSON payload to React UI.", style_body)
        ],
    ]

    t_flow = Table(flow_table_data, colWidths=[70, 130, 332])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 15))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 3: BACKEND ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("3. Backend Architecture & Subsystem Deep Dive", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "The Python backend is organized cleanly under the <code>app/</code> package. Each module has strict single-responsibility boundaries:",
        style_body
    ))

    # Module breakdown table
    backend_modules = [
        [Paragraph("<b>Directory / Module</b>", style_h3), Paragraph("<b>Core Responsibility</b>", style_h3), Paragraph("<b>Key Functions / Classes</b>", style_h3)],
        [
            Paragraph("<code>app/api/main.py</code>", style_body),
            Paragraph("FastAPI Gateway & Static File Server", style_body),
            Paragraph("<code>root()</code>, <code>query_endpoint()</code>, <code>query_stream()</code>, <code>get_history()</code>, <code>admin_*</code>", style_body)
        ],
        [
            Paragraph("<code>app/agent/sql_agent.py</code>", style_body),
            Paragraph("Pipeline Orchestrator & Self-Correction", style_body),
            Paragraph("<code>run_agent()</code>, <code>explain_sql()</code>, <code>compute_confidence()</code>", style_body)
        ],
        [
            Paragraph("<code>app/agent/query_planner.py</code>", style_body),
            Paragraph("Deterministic Execution Plan Builder", style_body),
            Paragraph("<code>create_plan()</code>, <code>extract_intent()</code>, <code>map_joins()</code>", style_body)
        ],
        [
            Paragraph("<code>app/agent/ambiguity_checker.py</code>", style_body),
            Paragraph("Heuristic & LLM Clarification Engine", style_body),
            Paragraph("<code>check_ambiguity()</code>, <code>detect_missing_filters()</code>", style_body)
        ],
        [
            Paragraph("<code>app/llm/sql_generator.py</code>", style_body),
            Paragraph("Ollama Connector & SQL Prompt Engineering", style_body),
            Paragraph("<code>generate_sql()</code>, <code>ollama_chat()</code>, <code>fallback_pattern_generator()</code>", style_body)
        ],
        [
            Paragraph("<code>app/prompt/prompt_builder.py</code>", style_body),
            Paragraph("Schema & Few-Shot Prompt Assembler", style_body),
            Paragraph("<code>build_sql_prompt()</code>, <code>format_schema_context()</code>", style_body)
        ],
        [
            Paragraph("<code>app/retriever/retriever.py</code>", style_body),
            Paragraph("Semantic Schema & History RAG Engine", style_body),
            Paragraph("<code>retrieve_schema()</code>, <code>retrieve_sql_history()</code>", style_body)
        ],
        [
            Paragraph("<code>app/embedding/chroma_builder.py</code>", style_body),
            Paragraph("Vector Index Generator for Schema", style_body),
            Paragraph("<code>build_chroma_index()</code>, <code>get_collection()</code>", style_body)
        ],
        [
            Paragraph("<code>app/database/read_executor.py</code>", style_body),
            Paragraph("MySQL Connection Pool & Read Executor", style_body),
            Paragraph("<code>execute_read_query()</code>, <code>get_engine()</code>, <code>get_execution_plan()</code>", style_body)
        ],
        [
            Paragraph("<code>app/knowledge/knowledge_graph.py</code>", style_body),
            Paragraph("Entity Relationship & Profiler Base", style_body),
            Paragraph("<code>KnowledgeGraph</code> class, <code>resolve_business_query()</code>", style_body)
        ],
        [
            Paragraph("<code>app/utils/report_generator.py</code>", style_body),
            Paragraph("ReportLab & Pandas Multi-Format Exporter", style_body),
            Paragraph("<code>generate_pdf()</code>, <code>generate_csv()</code>, <code>generate_excel()</code>", style_body)
        ],
        [
            Paragraph("<code>app/utils/summary_generator.py</code>", style_body),
            Paragraph("Natural Language Insight Summarizer", style_body),
            Paragraph("<code>generate_natural_summary()</code>", style_body)
        ],
    ]

    t_backend = Table(backend_modules, colWidths=[140, 160, 232])
    t_backend.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_backend)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Pipeline Execution Logic in <code>sql_agent.py</code>:", style_h2))
    story.append(Paragraph(
        "When <code>run_agent(question)</code> is invoked, it runs a synchronized 6-phase process:<br/>"
        "1. <b>Ambiguity Guard:</b> If question matches known vague patterns, immediately halts and asks user to specify scope.<br/>"
        "2. <b>Knowledge Graph Resolution:</b> Resolves table relationships (e.g. <i>orders JOIN customers ON orders.customer_id = customers.id</i>).<br/>"
        "3. <b>RAG Context Injection:</b> Retrieves top-k matching schemas and past successful queries using vector similarity.<br/>"
        "4. <b>Prompt Synthesis & Generation:</b> Constructs a system prompt with strict rules ('Use only standard MySQL, output ONLY valid SQL code').<br/>"
        "5. <b>AST Validation & Cost Check:</b> Validates SQL against regex and AST parsers. Performs <code>EXPLAIN</code> on live MySQL to compute execution cost.<br/>"
        "6. <b>Execution & Confidence Scoring:</b> Executes query safely, calculates a confidence score (0-100), and generates narrative explanations.",
        style_body
    ))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 4: DATABASE SAFETY & SECURITY
    # =========================================================================
    story.append(Paragraph("4. Database Safety, EXPLAIN Validation & Read-Only Guardrails", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "Security is paramount when connecting an AI model to enterprise databases. "
        "The platform employs defense-in-depth security principles to guarantee database integrity.",
        style_body
    ))

    story.append(Paragraph("Security Architecture Layers:", style_h2))

    story.append(Paragraph("1. <b>Strict Read-Only Connection:</b> The SQLAlchemy engine connects with database credentials granted solely <code>SELECT</code> privileges.", style_bullet))
    story.append(Paragraph("2. <b>AST & Keyword Guardrail:</b> Any generated query containing blacklisted words (<code>INSERT</code>, <code>UPDATE</code>, <code>DELETE</code>, <code>DROP</code>, <code>ALTER</code>, <code>CREATE</code>, <code>TRUNCATE</code>, <code>GRANT</code>, <code>REVOKE</code>, <code>EXEC</code>) is rejected immediately before hitting the database driver.", style_bullet))
    story.append(Paragraph("3. <b>EXPLAIN Pre-Execution Check:</b> Before running the actual query, the backend executes <code>EXPLAIN &lt;generated_sql&gt;</code>. If MySQL returns a syntax error or an estimated row cost exceeding safe thresholds (&gt;1,000,000 rows), the agent intercepts the query and triggers self-correction.", style_bullet))
    story.append(Paragraph("4. <b>Automatic Row Truncation:</b> Queries are automatically appended with <code>LIMIT 500</code> if no limit is explicitly set, preventing memory overload.", style_bullet))

    story.append(Paragraph("Sample Guardrail Validator Code Pattern:", style_h3))
    code_snippet = (
        "def validate_sql(sql: str) -> dict:\n"
        "    sql_upper = sql.upper().strip()\n"
        "    forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE', 'EXEC']\n"
        "    for kw in forbidden:\n"
        "        if f' {kw} ' in f' {sql_upper} ':\n"
        "            raise SQLValidationError(f'Forbidden DML/DDL operation: {kw}')\n"
        "    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):\n"
        "        raise SQLValidationError('Only SELECT or CTE queries are permitted.')\n"
        "    return {'status': 'valid'}"
    )
    story.append(Paragraph(code_snippet, style_code))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 5: KNOWLEDGE GRAPH & RAG
    # =========================================================================
    story.append(Paragraph("5. Knowledge Graph & RAG Vector Engine", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "To achieve near-100% SQL accuracy, the platform uses a hybrid knowledge representation: a <b>Structural Knowledge Graph</b> combined with a <b>Dense Vector Retriever</b>.",
        style_body
    ))

    story.append(Paragraph("1. Schema Metadata Profiler (<code>app/knowledge/db_profiler.py</code>)", style_h2))
    story.append(Paragraph(
        "On initial system startup, the database profiler automatically inspects the MySQL information schema, building three structured JSON knowledge bases under <code>knowledge/</code>:<br/>"
        "• <code>knowledge/schema/schema_metadata.json</code>: Contains table definitions, column names, data types, primary keys, and sample distinct values.<br/>"
        "• <code>knowledge/graph/relationship_metadata.json</code>: Contains explicit foreign key constraints and inferred entity linkages.<br/>"
        "• <code>knowledge/business_metadata.json</code>: Maps business jargon (e.g. <i>'MRR'</i>, <i>'churn rate'</i>, <i>'active clients'</i>) to exact SQL formulas and column definitions.",
        style_body
    ))

    story.append(Paragraph("2. ChromaDB RAG Vector Store (<code>app/retriever/retriever.py</code>)", style_h2))
    story.append(Paragraph(
        "The RAG engine uses <code>SentenceTransformers (all-MiniLM-L6-v2)</code> to convert database table descriptions and historical user queries into 384-dimensional vector embeddings stored inside a local persistent ChromaDB instance (<code>app/chroma/</code>).",
        style_body
    ))
    story.append(Paragraph(
        "When a user asks a question, Chroma retrieves the top-k most relevant table schemas and similar past queries, appending them into the prompt. "
        "This ensures that even for large enterprise databases with hundreds of tables, only the 3-5 relevant tables are passed into the LLM context window, minimizing latency and hallucinations.",
        style_body
    ))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 6: FRONTEND ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("6. Frontend Architecture & User Interface Manual", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "The frontend is built with <b>React 19</b> and <b>Vite 8</b>, featuring a modern dark-mode aesthetic with glassmorphism visual effects, responsive data grids, and live visualization engines.",
        style_body
    ))

    story.append(Paragraph("Frontend Component Structure (<code>frontend/src/</code>):", style_h2))

    fe_components = [
        [Paragraph("<b>Component File</b>", style_h3), Paragraph("<b>UI Description & Feature Capabilities</b>", style_h3)],
        [
            Paragraph("<code>src/App.jsx</code>", style_body),
            Paragraph("Main application container holding active navigation tabs (Console, History, Schema, Admin, Settings). Handles state management for active queries and global notifications.", style_body)
        ],
        [
            Paragraph("<code>src/components/QueryConsole.jsx</code>", style_body),
            Paragraph("Primary user interface featuring a natural language prompt input box, quick example prompts, execution step spinners, confidence score badge, formatted SQL code view, dynamic data table with column sorting, and natural language summary panel.", style_body)
        ],
        [
            Paragraph("<code>src/components/VisualizationPanel.jsx</code>", style_body),
            Paragraph("Uses <b>Recharts</b> to dynamically render Bar Charts, Line Charts, Pie Charts, or Area Charts based on response column types (e.g. category vs numeric vs datetime).", style_body)
        ],
        [
            Paragraph("<code>src/components/SchemaViewer.jsx</code>", style_body),
            Paragraph("Interactive visual database schema browser allowing developers and analysts to explore tracked tables, column types, primary keys, and foreign key relationships.", style_body)
        ],
        [
            Paragraph("<code>src/components/QueryHistory.jsx</code>", style_body),
            Paragraph("Audit trail console rendering past executed queries, execution latency in milliseconds, row counts, confidence scores, and one-click 'Rerun Query' actions.", style_body)
        ],
        [
            Paragraph("<code>src/components/AdminPanel.jsx</code>", style_body),
            Paragraph("System health dashboard displaying real-time metrics: database connection status, total tables tracked, relationships mapped, vocabulary size, average latency, and single-click buttons to rebuild embeddings or refresh metadata.", style_body)
        ],
    ]

    t_fe = Table(fe_components, colWidths=[160, 372])
    t_fe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_fe)
    story.append(Spacer(1, 15))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 7: API SPECIFICATION
    # =========================================================================
    story.append(Paragraph("7. Complete REST API Specification", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "The FastAPI backend exposes a comprehensive set of RESTful endpoints. The OpenAPI schema is automatically generated and accessible at <code>http://localhost:8000/docs</code>.",
        style_body
    ))

    api_endpoints = [
        [Paragraph("<b>Method & Path</b>", style_h3), Paragraph("<b>Request Payload / Params</b>", style_h3), Paragraph("<b>Description & Response Summary</b>", style_h3)],
        [
            Paragraph("<code>GET /health</code>", style_body),
            Paragraph("None", style_body),
            Paragraph("Health check endpoint. Returns database connection status, total table count, and active LLM model.", style_body)
        ],
        [
            Paragraph("<code>POST /query</code>", style_body),
            Paragraph("<code>{\"question\": \"...\", \"execute\": true}</code>", style_body),
            Paragraph("Main AI query execution endpoint. Returns generated SQL, data rows, column names, execution time, confidence score, thinking steps, and natural summary.", style_body)
        ],
        [
            Paragraph("<code>POST /query/stream</code>", style_body),
            Paragraph("<code>{\"question\": \"...\"}</code>", style_body),
            Paragraph("Server-Sent Events (SSE) streaming endpoint delivering real-time thinking steps as the agent reasons.", style_body)
        ],
        [
            Paragraph("<code>GET /history</code>", style_body),
            Paragraph("<code>limit=100</code> (query param)", style_body),
            Paragraph("Fetches logged query execution history with timestamp, latency, row count, and confidence rating.", style_body)
        ],
        [
            Paragraph("<code>GET /admin/stats</code>", style_body),
            Paragraph("None", style_body),
            Paragraph("Returns system administration metrics (tracked tables, mapped relationships, vocabulary size, avg latency).", style_body)
        ],
        [
            Paragraph("<code>GET /admin/schema</code>", style_body),
            Paragraph("None", style_body),
            Paragraph("Returns full schema metadata map JSON for all database tables and columns.", style_body)
        ],
        [
            Paragraph("<code>POST /admin/rebuild-embeddings</code>", style_body),
            Paragraph("None", style_body),
            Paragraph("Triggers complete re-indexing of ChromaDB vector store based on updated schema metadata.", style_body)
        ],
        [
            Paragraph("<code>POST /export/pdf</code>", style_body),
            Paragraph("<code>{\"sql\": \"...\", \"filename\": \"report\"}</code>", style_body),
            Paragraph("Generates a formatted PDF report file from query results and returns download URL.", style_body)
        ],
        [
            Paragraph("<code>POST /export/excel</code>", style_body),
            Paragraph("<code>{\"columns\": [...], \"data\": [...]}</code>", style_body),
            Paragraph("Generates `.xlsx` spreadsheet report file and returns static file access link.", style_body)
        ],
        [
            Paragraph("<code>POST /export/csv</code>", style_body),
            Paragraph("<code>{\"columns\": [...], \"data\": [...]}</code>", style_body),
            Paragraph("Generates `.csv` file download or raw stream.", style_body)
        ],
    ]

    t_api = Table(api_endpoints, colWidths=[130, 150, 252])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 4.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 15))

    # =========================================================================
    # CHAPTER 8: REPORT GENERATION
    # =========================================================================
    story.append(Paragraph("8. Report Generation & Export Capabilities", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "The platform includes an automated reporting engine located in <code>app/utils/report_generator.py</code>. "
        "When users execute queries or request export downloads, the engine formats raw SQL query results into professional tabular reports.",
        style_body
    ))
    story.append(Paragraph("Supported Export Formats:", style_h2))
    story.append(Paragraph("• <b>PDF Reports (ReportLab):</b> Creates clean, styled PDF documents with automated page numbering, title blocks, header summaries, and grid-aligned data tables.", style_bullet))
    story.append(Paragraph("• <b>Excel Worksheets (OpenPyXL / Pandas):</b> Exports formatted `.xlsx` workbooks with auto-fitted column widths, styled header rows, and raw numeric values for further modeling.", style_bullet))
    story.append(Paragraph("• <b>CSV & Streaming CSV:</b> Produces standard RFC-4180 CSV files or chunked HTTP stream streams for large dataset downloads.", style_bullet))
    story.append(Paragraph("All generated reports are stored locally in the <code>reports/</code> directory and exposed via the FastAPI static mount <code>/reports/{filename}</code>.", style_body))

    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 9: INSTALLATION & DEPLOYMENT RUNBOOK
    # =========================================================================
    story.append(Paragraph("9. Installation, Configuration & Deployment Runbook", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "Follow this operational runbook to set up, configure, and execute the system in a production or development environment.",
        style_body
    ))

    story.append(Paragraph("1. Prerequisites & Environment Setup", style_h2))
    story.append(Paragraph("• Python 3.10+ installed and available on PATH.<br/>• Node.js 18+ and npm installed.<br/>• MySQL 8.0+ instance running with read permissions.<br/>• Ollama running locally at <code>http://127.0.0.1:11434</code> with model <code>qwen2.5-coder:7b</code>.", style_body))

    story.append(Paragraph("2. Environment File Configuration (<code>.env</code>)", style_h2))
    env_sample = (
        "# Database Credentials\n"
        "DB_HOST=127.0.0.1\n"
        "DB_PORT=3306\n"
        "DB_NAME=enterprise_db\n"
        "DB_USER=ai_agent_user\n"
        "DB_PASSWORD=SecurePassword123!\n\n"
        "# Model Configuration\n"
        "OLLAMA_BASE_URL=http://127.0.0.1:11434\n"
        "DEFAULT_MODEL=qwen2.5-coder:7b\n"
        "MAX_ROWS=500"
    )
    story.append(Paragraph(env_sample, style_code))

    story.append(Paragraph("3. Step-by-Step Launch Commands", style_h2))
    
    cmd_box = (
        "# Step A: Setup Python Virtual Environment\n"
        "python -m venv venv\n"
        ".\\venv\\Scripts\\activate   # On Windows PowerShell\n"
        "pip install -r requirements.txt\n\n"
        "# Step B: Launch Backend API Server (Port 8000)\n"
        "python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload\n\n"
        "# Step C: Launch Frontend Development Server (Port 3000)\n"
        "cd frontend\n"
        "npm install\n"
        "npm run dev\n\n"
        "# Step D: Production Build (Bundles React into app/static)\n"
        "cd frontend && npm run build"
    )
    story.append(Paragraph(cmd_box, style_code))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 10: MAINTENANCE & TROUBLESHOOTING
    # =========================================================================
    story.append(Paragraph("10. System Maintenance, Benchmarking & Troubleshooting", style_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph("Common Issues & Diagnostic Procedures:", style_h2))

    trouble_table = [
        [Paragraph("<b>Symptom / Issue</b>", style_h3), Paragraph("<b>Root Cause</b>", style_h3), Paragraph("<b>Resolution Procedure</b>", style_h3)],
        [
            Paragraph("Database connection failure on startup", style_body),
            Paragraph("Missing `.env` file or invalid MySQL host/password.", style_body),
            Paragraph("Verify credentials using <code>python test_tables.py</code>. Ensure MySQL service is running and user has SELECT rights.", style_body)
        ],
        [
            Paragraph("Slow SQL Generation (&gt;5s latency)", style_body),
            Paragraph("Ollama model fallback or CPU-only inference execution.", style_body),
            Paragraph("Ensure Ollama is running with GPU acceleration enabled. Alternatively switch model setting to <code>qwen2.5-coder:1.5b</code> in Settings.", style_body)
        ],
        [
            Paragraph("Unknown table or column in generated SQL", style_body),
            Paragraph("Stale vector index or unindexed schema changes.", style_body),
            Paragraph("Run <code>python -m app.knowledge.db_profiler</code> to update metadata, then trigger <code>POST /admin/rebuild-embeddings</code>.", style_body)
        ],
        [
            Paragraph("Frontend 502 Bad Gateway / Proxy error", style_body),
            Paragraph("Backend Uvicorn server is stopped.", style_body),
            Paragraph("Restart backend with <code>python -m uvicorn app.api.main:app --port 8000</code>.", style_body)
        ],
    ]

    t_trouble = Table(trouble_table, colWidths=[140, 150, 242])
    t_trouble.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_trouble)
    story.append(Spacer(1, 20))

    # Concluding Sign-off Box
    concl_box = (
        "<b>Document Sign-off & Verification:</b><br/>"
        "This handbook represents the complete operational and technical baseline for the Enterprise AI SQL Agent Intelligence Platform v2.0. "
        "All components, API endpoints, security mechanisms, and build runbooks described herein have been verified against active source code."
    )
    story.append(Paragraph(concl_box, style_callout))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Handbook PDF successfully created at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    build_pdf()
