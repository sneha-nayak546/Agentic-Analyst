"""
COMPREHENSIVE BRD Generator — Agentic Analyst / JGH Intelligence Engine
Full enterprise-grade Business Requirements Document with everything included.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon, Path
from reportlab.graphics import renderPDF
from datetime import datetime
import os
import math

# ── PALETTE ────────────────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#0D1B3E")
COBALT  = colors.HexColor("#1A56DB")
SKY     = colors.HexColor("#60A5FA")
GOLD    = colors.HexColor("#F59E0B")
SILVER  = colors.HexColor("#94A3B8")
MINT    = colors.HexColor("#10B981")
ROSE    = colors.HexColor("#F43F5E")
PURPLE  = colors.HexColor("#7C3AED")
TEAL    = colors.HexColor("#0891B2")
ORANGE  = colors.HexColor("#EA580C")
LIGHT   = colors.HexColor("#EFF6FF")
WHITE   = colors.white
INK     = colors.HexColor("#0F172A")
MUTED   = colors.HexColor("#475569")
BORDER  = colors.HexColor("#CBD5E1")
STRIPE  = colors.HexColor("#F0F6FF")

W, H = A4

# ── STYLES ─────────────────────────────────────────────────────────────────────
def S():
    def ps(name, **kw):
        return ParagraphStyle(name, **kw)
    return {
        "h1": ps("h1", fontName="Helvetica-Bold", fontSize=18, textColor=WHITE, leading=24, spaceBefore=0, spaceAfter=4),
        "h2": ps("h2", fontName="Helvetica-Bold", fontSize=12, textColor=COBALT, leading=17, spaceBefore=8, spaceAfter=4),
        "h3": ps("h3", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=14, spaceBefore=5, spaceAfter=3),
        "body": ps("body", fontName="Helvetica", fontSize=9, textColor=INK, leading=14, spaceAfter=3, alignment=TA_JUSTIFY),
        "bold": ps("bold", fontName="Helvetica-Bold", fontSize=9, textColor=INK, leading=14, spaceAfter=2),
        "bullet": ps("bullet", fontName="Helvetica", fontSize=9, textColor=INK, leading=14, leftIndent=14, spaceAfter=2),
        "sbullet": ps("sbullet", fontName="Helvetica", fontSize=8.5, textColor=MUTED, leading=13, leftIndent=28, spaceAfter=1),
        "th": ps("th", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE, alignment=TA_CENTER, leading=11),
        "td": ps("td", fontName="Helvetica", fontSize=8, textColor=INK, leading=11),
        "tdc": ps("tdc", fontName="Helvetica", fontSize=8, textColor=INK, leading=11, alignment=TA_CENTER),
        "tdb": ps("tdb", fontName="Helvetica-Bold", fontSize=8, textColor=INK, leading=11),
        "caption": ps("caption", fontName="Helvetica", fontSize=7.5, textColor=SILVER, alignment=TA_CENTER, leading=11, spaceBefore=2),
        "code": ps("code", fontName="Courier", fontSize=8, textColor=colors.HexColor("#1E40AF"), leading=12, leftIndent=10, backColor=LIGHT),
        "toc_n": ps("toc_n", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=17),
        "toc_t": ps("toc_t", fontName="Helvetica", fontSize=10, textColor=COBALT, leading=17, leftIndent=16),
        "meta": ps("meta", fontName="Helvetica", fontSize=8.5, textColor=MUTED, alignment=TA_CENTER, leading=13),
    }

STYLES = S()

# ── HELPERS ────────────────────────────────────────────────────────────────────
BW = W - 2.2 * inch   # usable body width

def sp(n=6): return Spacer(1, n)
def P(t, s="body"): return Paragraph(t, STYLES[s])
def B(t): return Paragraph(f"• {t}", STYLES["bullet"])
def SB(t): return Paragraph(f"◦ {t}", STYLES["sbullet"])
def CODE(t): return Paragraph(t, STYLES["code"])
def div(): return HRFlowable(width=BW, thickness=0.5, color=BORDER, spaceAfter=4)

def sec_hdr(num, title):
    return _SectionHeader(num, title)

def sub_hdr(title):
    return _SubHeader(title)

def table(data, col_widths, hdr_color=NAVY, stripe=True, fontsize=8):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0,0), (-1,0), hdr_color),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), fontsize),
        ("FONTSIZE", (0,1), (-1,-1), fontsize),
        ("GRID", (0,0), (-1,-1), 0.4, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]
    if stripe:
        style.append(("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, STRIPE]))
    t.setStyle(TableStyle(style))
    return t

def badge(text, color):
    hex_c = "#{:02x}{:02x}{:02x}".format(
        int(color.red * 255), int(color.green * 255), int(color.blue * 255)
    )
    return f'<font color="{hex_c}"><b>{text}</b></font>'

PRIORITY = {
    "CRITICAL": badge("CRITICAL", ROSE),
    "HIGH": badge("HIGH", MINT),
    "MEDIUM": badge("MEDIUM", GOLD),
    "LOW": badge("LOW", SILVER),
}
STATUS = {
    "Implemented": badge("✔ Implemented", MINT),
    "Resolved": badge("✔ Resolved", MINT),
    "Documented": badge("✎ Documented", GOLD),
    "Achieved": badge("✔ Achieved", MINT),
    "Enforced": badge("✔ Enforced", COBALT),
    "Monitored": badge("~ Monitored", GOLD),
}

# ── FLOWABLES ──────────────────────────────────────────────────────────────────
class _SectionHeader(Flowable):
    def __init__(self, num, title):
        Flowable.__init__(self)
        self.num = num; self.title = title
        self.height = 30
    def draw(self):
        c = self.canv
        c.setFillColor(NAVY)
        c.roundRect(0, 0, BW, self.height, 5, fill=1, stroke=0)
        c.setFillColor(GOLD); c.rect(0, 0, 5, self.height, fill=1, stroke=0)
        c.setFillColor(COBALT); c.circle(21, 15, 9, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(21, 11, str(self.num))
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 11)
        c.drawString(38, 10, self.title.upper())
    def wrap(self, aw, ah): return BW, self.height

class _SubHeader(Flowable):
    def __init__(self, title):
        Flowable.__init__(self)
        self.title = title; self.height = 20
    def draw(self):
        c = self.canv
        c.setFillColor(LIGHT); c.roundRect(0, 0, BW, self.height, 4, fill=1, stroke=0)
        c.setFillColor(COBALT); c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        c.setFillColor(COBALT); c.setFont("Helvetica-Bold", 9.5)
        c.drawString(12, 5, self.title)
    def wrap(self, aw, ah): return BW, self.height

class ArchDiagram(Flowable):
    def __init__(self): Flowable.__init__(self); self.height = 290
    def _box(self, c, x, y, w, h, bg, lbl, sub=""):
        c.setFillColor(bg); c.roundRect(x, y, w, h, 5, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(x+w/2, y+h/2+(3.5 if sub else 0), lbl)
        if sub:
            c.setFont("Helvetica", 5.5); c.setFillColor(colors.HexColor("#CBD5E1"))
            c.drawCentredString(x+w/2, y+h/2-5.5, sub)
    def _arr(self, c, x1, y1, x2, y2, col=COBALT):
        c.setStrokeColor(col); c.setLineWidth(1.2); c.line(x1,y1,x2,y2)
        angle = math.atan2(y2-y1, x2-x1); sz=5
        c.setFillColor(col)
        p = c.beginPath()
        p.moveTo(x2,y2)
        p.lineTo(x2-sz*math.cos(angle-0.4), y2-sz*math.sin(angle-0.4))
        p.lineTo(x2-sz*math.cos(angle+0.4), y2-sz*math.sin(angle+0.4))
        p.close(); c.drawPath(p, fill=1, stroke=0)
    def draw(self):
        c = self.canv; bw = BW; bh = self.height
        # bg
        c.setFillColor(colors.HexColor("#F8FAFF")); c.roundRect(0,0,bw,bh,8,fill=1,stroke=0)
        c.setStrokeColor(BORDER); c.setLineWidth(0.5); c.roundRect(0,0,bw,bh,8,fill=0,stroke=1)
        c.setFont("Helvetica-Bold",7.5); c.setFillColor(NAVY)
        c.drawCentredString(bw/2, bh-14, "SYSTEM ARCHITECTURE — AGENTIC ANALYST PIPELINE (JGH INTELLIGENCE ENGINE v2.0)")

        # L1 User
        self._box(c, 5, bh-92, 45, 38, COBALT, "USER", "React/Vue SPA")
        # L2 FastAPI
        self._box(c, 60, bh-92, 45, 38, NAVY, "FASTAPI", "REST API")
        self._arr(c, 50, bh-73, 60, bh-73)

        # Agent pipeline container
        ax = 120; c.setFillColor(colors.HexColor("#EEF4FF"))
        c.roundRect(ax-4, bh-220, 138, 185, 5, fill=1, stroke=0)
        c.setStrokeColor(COBALT); c.setLineWidth(0.7)
        c.roundRect(ax-4, bh-220, 138, 185, 5, fill=0, stroke=1)
        c.setFont("Helvetica-Bold",6); c.setFillColor(COBALT)
        c.drawCentredString(ax+65, bh-45, "AI AGENT PIPELINE")
        self._arr(c, 105, bh-73, ax, bh-73)

        boxes = [
            (ax, bh-85,  colors.HexColor("#1D4ED8"), "NLP Understanding", "Qwen2.5-Coder 7B"),
            (ax, bh-115, colors.HexColor("#2563EB"), "Intent Router", "SQL/Tutor/ERD/Story"),
            (ax, bh-145, colors.HexColor("#3B82F6"), "Context Resolver", "Session Memory"),
            (ax, bh-175, colors.HexColor("#60A5FA"), "SQL Generator", "RAG Prompt → LLM"),
            (ax, bh-205, colors.HexColor("#93C5FD"), "Validator Stack", "AST + Semantic + E2E"),
        ]
        for (bx,by,bg,lbl,sub) in boxes: self._box(c, bx, by, 130, 24, bg, lbl, sub)
        for by in [bh-89, bh-119, bh-149, bh-179]:
            c.setStrokeColor(SKY); c.setLineWidth(0.8)
            c.line(ax+65, by, ax+65, by-6)

        # LLM / Knowledge / SQL History
        lx = 265
        self._box(c, lx, bh-110, 50, 36, PURPLE, "OLLAMA LLM", "qwen2.5-coder:7b")
        self._box(c, lx, bh-147, 50, 28, TEAL,   "KNOWLEDGE", "Graph + Schema")
        self._box(c, lx, bh-177, 50, 28, colors.HexColor("#065F46"), "SQL HISTORY", "Few-Shot RAG")

        self._arr(c, ax+130, bh-133, lx, bh-133) # Context -> Knowledge
        self._arr(c, ax+130, bh-163, lx, bh-163) # SQL Gen -> SQL History

        # DB
        dx = 325
        self._box(c, dx, bh-177, 45, 42, ORANGE, "MySQL DB", "jghMasterDB")
        self._arr(c, lx+50, bh-163, dx, bh-163) # SQL History -> MySQL DB

        # Outputs
        ox = 385
        outs = [
            (bh-75, MINT, "JSON API"),
            (bh-100, GOLD, "CSV / Excel"),
            (bh-125, ROSE, "PDF Report"),
            (bh-150, PURPLE, "Dashboard"),
            (bh-175, TEAL, "Audit Logs")
        ]
        for y, color, label in outs:
            self._box(c, ox, y, 45, 18, color, label)
            self._arr(c, dx+45, bh-156, ox, y+9)

        # Legend
        items = [("User/API",COBALT),("Agent Pipeline",colors.HexColor("#3B82F6")),
                 ("LLM/Knowledge",PURPLE),("Database",ORANGE),("Outputs",MINT)]
        lx2 = 10
        for (lb, lc) in items:
            c.setFillColor(lc); c.rect(lx2, 8, 9, 9, fill=1, stroke=0)
            c.setFont("Helvetica",6.5); c.setFillColor(INK)
            c.drawString(lx2+12, 9, lb); lx2 += 80

    def wrap(self, aw, ah): return BW, self.height


# ── ON-PAGE CALLBACKS ─────────────────────────────────────────────────────────
def draw_cover(canvas, doc):
    c = canvas; c.saveState()
    c.setFillColor(NAVY); c.rect(0,0,W,H,fill=1,stroke=0)
    # gradient
    for i in range(50):
        a = i/50.0
        col = colors.HexColor("#{:02x}{:02x}{:02x}".format(
            int(13+(26-13)*a), int(27+(86-27)*a), int(62+(219-62)*a)))
        c.setFillColor(col); c.rect(0, H*(i/50.0), W, H/50.0+2, fill=1, stroke=0)
    # decorative orbs
    for (cx,cy,r,al) in [(W*.9,H*.87,180,.05),(W*.88,H*.82,110,.08),(W*.05,H*.22,130,.05),(W*.12,H*.17,70,.09)]:
        c.setFillColorRGB(.1,.33,.86,alpha=al); c.circle(cx,cy,r,fill=1,stroke=0)
    # bars
    c.setFillColor(GOLD); c.rect(0,H-9,W,9,fill=1,stroke=0)
    c.setFillColor(COBALT); c.rect(0,0,W,6,fill=1,stroke=0)
    # logo
    lx,ly = W/2, H*.73
    c.setFillColor(COBALT); c.circle(lx,ly,50,fill=1,stroke=0)
    c.setStrokeColor(colors.HexColor("#2563EB")); c.setLineWidth(2)
    c.circle(lx,ly,44,fill=0,stroke=1)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold",24); c.drawCentredString(lx,ly-9,"JGH")
    c.setFont("Helvetica",7.5); c.setFillColor(colors.HexColor("#93C5FD"))
    c.drawCentredString(lx,ly+29,"INTELLIGENCE ENGINE")
    # title
    c.setFont("Helvetica-Bold",30); c.setFillColor(WHITE)
    c.drawCentredString(W/2, H*.575, "AGENTIC ANALYST")
    c.setFont("Helvetica",15); c.setFillColor(colors.HexColor("#93C5FD"))
    c.drawCentredString(W/2, H*.535, "Business Requirements Document")
    c.setStrokeColor(GOLD); c.setLineWidth(2.5)
    c.line(W/2-90,H*.505, W/2+90,H*.505)
    c.setFont("Helvetica",10); c.setFillColor(GOLD)
    c.drawCentredString(W/2, H*.472, "Enterprise AI-Powered Natural Language SQL Intelligence Platform")
    c.setFont("Helvetica",8.5); c.setFillColor(SILVER)
    c.drawCentredString(W/2, H*.445, "JGH Enterprises  ·  v2.0  ·  Production Release  ·  August 2026")
    # meta box
    my = H*.335
    mi = [("DOCUMENT TYPE","BRD – Business Requirements Document"),
          ("PROJECT","Agentic Analyst / JGH Intelligence Engine"),
          ("VERSION","v2.0 – Production Release"),
          ("DATE",datetime.now().strftime("%B %d, %Y")),
          ("LEAD DEVELOPER","[Confidential — Not Disclosed in This Document]"),
          ("ORGANISATION","JGH Enterprises – Analytics & Technology"),
          ("STATUS","✔ Approved for Production"),
          ("CLASSIFICATION","CONFIDENTIAL – Internal Use Only"),]
    bw2=370; bh2=len(mi)*19+22; bx=(W-bw2)/2; by=my-bh2+10
    c.setFillColor(colors.HexColor("#0F2050")); c.roundRect(bx,by,bw2,bh2,7,fill=1,stroke=0)
    c.setStrokeColor(COBALT); c.setLineWidth(0.8); c.roundRect(bx,by,bw2,bh2,7,fill=0,stroke=1)
    y2=my
    for lbl,val in mi:
        c.setFont("Helvetica-Bold",7); c.setFillColor(GOLD)
        c.drawString(bx+16,y2-4,lbl+":")
        c.setFont("Helvetica",7.5); c.setFillColor(WHITE)
        c.drawString(bx+148,y2-4,val); y2-=19
    c.setFont("Helvetica",7); c.setFillColor(SILVER)
    c.drawCentredString(W/2,18,"CONFIDENTIAL  •  JGH Enterprise Analytics  •  © 2026  •  All Rights Reserved")
    c.restoreState()

def draw_header_footer(canvas, doc):
    c = canvas; c.saveState()
    c.setFillColor(NAVY); c.rect(0,H-26,W,26,fill=1,stroke=0)
    c.setFillColor(GOLD); c.rect(0,H-26,W,3,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold",8)
    c.drawString(1.1*inch,H-17,"AGENTIC ANALYST")
    c.setFont("Helvetica",7.5); c.setFillColor(SKY)
    c.drawString(1.1*inch+110,H-17,"JGH Intelligence Engine — Business Requirements Document v2.0")
    c.setFillColor(GOLD); c.drawRightString(W-1.1*inch,H-17,"CONFIDENTIAL")
    c.setFillColor(NAVY); c.rect(0,0,W,22,fill=1,stroke=0)
    c.setFillColor(COBALT); c.rect(0,22,W,1.5,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica",7.5)
    c.drawString(1.1*inch,7,f"© 2026 JGH Enterprises  |  {datetime.now().strftime('%B %d, %Y')}")
    c.setFillColor(GOLD); c.setFont("Helvetica-Bold",8)
    c.drawRightString(W-1.1*inch,7,f"Page {doc.page}")
    c.restoreState()


# ── BUILDER ────────────────────────────────────────────────────────────────────
def build():
    path = "reports/Agentic_Analyst_BRD_Complete.pdf"
    os.makedirs("reports", exist_ok=True)
    doc = SimpleDocTemplate(path, pagesize=A4,
        leftMargin=1.1*inch, rightMargin=1.1*inch,
        topMargin=0.85*inch, bottomMargin=0.85*inch,
        title="Agentic Analyst – BRD v2.0", author="JGH Intelligence Engine")

    story = []
    def sec(n,t): story.extend([sp(12), sec_hdr(n,t), sp(8)])
    def sub(t):   story.extend([sp(7),  sub_hdr(t),  sp(5)])

    # ── Page 1: Cover (blank — drawn by callback) ─────────────────────────────
    story.append(PageBreak())

    # ── Table of Contents ─────────────────────────────────────────────────────
    story.append(sp(8))
    story.append(Paragraph("TABLE OF CONTENTS", ParagraphStyle("toc_h", fontName="Helvetica-Bold",
        fontSize=16, textColor=NAVY, alignment=TA_CENTER, spaceAfter=12)))
    story.append(div())
    story.append(sp(6))
    toc = [
        ("1","Executive Summary"),
        ("2","Project Overview & Metadata"),
        ("3","Business Context & Problem Statement"),
        ("4","Stakeholders & User Personas"),
        ("5","Business Objectives & Goals"),
        ("6","System Architecture"),
        ("7","AI Agent Pipeline — Detailed Walkthrough"),
        ("8","Operational Modes & Intent Classification"),
        ("9","Functional Requirements"),
        ("10","Technical Stack & Dependencies"),
        ("11","Module & Component Reference"),
        ("12","Data Architecture & Database Schema"),
        ("13","Business Rules & Domain Logic"),
        ("14","Prompt Engineering Architecture"),
        ("15","Security, Privacy & Compliance"),
        ("16","Validation & Quality Assurance"),
        ("17","API Endpoints Reference"),
        ("18","Session Memory & Context Management"),
        ("19","Export & Reporting Capabilities"),
        ("20","Non-Functional Requirements"),
        ("21","Known Issues & Bug Resolutions"),
        ("22","Deployment Architecture"),
        ("23","Future Roadmap & Enhancements"),
        ("24","Glossary & Definitions"),
        ("25","Document Sign-Off"),
    ]
    tdata = [[Paragraph(n+".", STYLES["toc_n"]),
              Paragraph(t, STYLES["toc_t"]),
              Paragraph("· " * 18, ParagraphStyle("d", fontName="Helvetica", fontSize=8, textColor=BORDER, alignment=TA_RIGHT))]
             for n,t in toc]
    tt = Table(tdata, colWidths=[BW*.07, BW*.66, BW*.27])
    tt.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE,STRIPE]),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),5), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(tt)
    story.append(PageBreak())

    # ══ 1. EXECUTIVE SUMMARY ══════════════════════════════════════════════════
    sec(1, "Executive Summary")
    story.append(P("The <b>Agentic Analyst</b> — internally branded as the <b>JGH Intelligence Engine</b> — is a "
        "production-grade, enterprise AI-powered natural language analytics platform developed for JGH Enterprises. "
        "The platform enables business users, operations managers, analysts, and executives to obtain real-time insights "
        "from a live production MySQL database using plain conversational English — without writing a single line of SQL code."))
    story.append(sp(5))
    story.append(P("The system operates as a fully automated, multi-step AI agent pipeline: it understands user intent "
        "using a large language model, constructs accurate and validated SQL queries, executes them securely against the "
        "production database, formats results into beautifully presented tables, generates natural language summaries, "
        "and offers downloadable reports in CSV, Excel, and PDF formats — all within a single conversational interface."))
    story.append(sp(8))

    ks = [["Key Attribute","Value"],
          ["Platform Name","Agentic Analyst — JGH Intelligence Engine"],
          ["Organization","JGH Enterprises — Analytics & Technology Division"],
          ["Lead Developer","[Confidential]"],
          ["Backend Framework","FastAPI v0.141.1 (Python 3.13.14)"],
          ["AI Model","Qwen2.5-Coder 7B (via Ollama v0.6.2)"],
          ["Database","MySQL — jghMasterDB (Production)"],
          ["Allowed Tables in Scope","users, wallet_transaction, sku_inventories, withdrawal_request, companies, state, etc."],
          ["Validation Architecture","5-Layer: AST + Semantic + EXPLAIN + Execution + 10-Point E2E"],
          ["Context System","Multi-Turn Conversational Memory with Sliding Window (10 turns)"],
          ["Retry Logic","Automatic self-correction: up to 3 LLM retry attempts on failure"],
          ["Export Formats","JSON API, CSV, Excel (.xlsx), PDF"],
          ["LLM Endpoint","Configurable: Local (http://localhost:11434) or Cloud GPU via Tunnel"],
          ["Server Port","http://localhost:8000"],
          ["Security Level","Read-Only, AES-256 Encrypted Credentials, Security Firewall Active"],
          ["Current Status","Production Active — v2.0"],]
    story.append(table(
        [[Paragraph(r[0],STYLES["tdb"]), Paragraph(r[1],STYLES["td"])] if i>0
         else [Paragraph(r[0],STYLES["th"]), Paragraph(r[1],STYLES["th"])] for i,r in enumerate(ks)],
        [BW*.36, BW*.64]))

    # ══ 2. PROJECT OVERVIEW ═══════════════════════════════════════════════════
    sec(2, "Project Overview & Metadata")
    meta_rows = [
        ("Project Name","Agentic Analyst — JGH Intelligence Engine"),
        ("Internal Code Name","JGH-AI-v2.0"),
        ("Lead Developer","[Confidential — Internal Reference]"),
        ("Organisation","JGH Enterprises — Analytics & Technology"),
        ("Document Version","v2.0 — Final BRD"),
        ("Document Date",datetime.now().strftime("%B %d, %Y")),
        ("Document Status","Approved for Production"),
        ("Classification","CONFIDENTIAL — Internal Use Only"),
        ("Application URL","http://localhost:8000"),
        ("API Documentation","http://localhost:8000/docs (FastAPI Swagger)"),
        ("LLM Health Endpoint","http://localhost:8000/api/llm/health"),
        ("Schema Endpoint","http://localhost:8000/schema"),
        ("LLM Model","Qwen2.5-Coder 7B (qwen2.5-coder:7b)"),
        ("LLM Runtime","Ollama v0.6.2"),
        ("LLM Quantization","Q4_K_M — 4.68 GB"),
        ("LLM Context Window","32,768 tokens"),
        ("Database","MySQL — jghMasterDB (Production)"),
        ("DB Connector","PyMySQL 1.2.0 via SQLAlchemy 2.0.51"),
        ("Server Framework","FastAPI 0.141.1 + Uvicorn 0.52.1"),
        ("Python Version","3.13.14"),
        ("Hot Reload","WatchFiles 1.2.0 (development mode)"),
        ("Credential Storage","AES-256 Fernet encrypted in .env — key in .master.key"),
    ]
    mdata = [[Paragraph(k, STYLES["tdb"]), Paragraph(v, STYLES["td"])] for k,v in meta_rows]
    mdata.insert(0, [Paragraph("Field", STYLES["th"]), Paragraph("Value", STYLES["th"])])
    story.append(table(mdata, [BW*.35, BW*.65]))

    # ══ 3. BUSINESS CONTEXT ═══════════════════════════════════════════════════
    sec(3, "Business Context & Problem Statement")
    sub("Business Background")
    story.append(P("JGH Enterprises is a large-scale FMCG (Fast-Moving Consumer Goods) distribution company "
        "operating across multiple Indian states. The company manages a complex, multi-tier distribution network "
        "comprising distributors, retailers, wholesalers, sales executives, and mechanics — all integrated into a "
        "centralised MySQL database."))
    story.append(sp(4))
    story.append(P("The business generates large volumes of transactional data daily — wallet credits, QR code scans, "
        "withdrawal requests, SKU inventory movements, and scheme earnings — across thousands of users in multiple "
        "regions. Extracting actionable insights from this data has historically required a dedicated SQL analyst "
        "or database administrator."))
    story.append(sp(8))
    sub("Problem Statement")
    problems = [
        "Non-technical business users (operations managers, area managers, executives) cannot independently access data insights without SQL knowledge.",
        "SQL analysts spend significant time writing repetitive reports for standard business questions about earnings, user counts, distributor performance, and transaction summaries.",
        "There is no centralized conversational analytics interface — data requests require back-and-forth communication between business and technical teams.",
        "Generating region-specific, time-bound, or entity-filtered reports is slow and error-prone when done manually.",
        "There is no built-in auditability of who queried what data, making compliance and data governance difficult.",
    ]
    for p in problems: story.append(B(p))
    story.append(sp(8))
    sub("Solution Statement")
    story.append(P("The Agentic Analyst eliminates all of these barriers by providing a single, secure, conversational "
        "AI interface that: understands business questions in plain English, translates them into validated SQL, "
        "executes them securely against the production database, and returns results in business-friendly formats. "
        "All queries are read-only, validated through 5 layers of checks, and fully audited."))

    # ══ 4. STAKEHOLDERS ═══════════════════════════════════════════════════════
    sec(4, "Stakeholders & User Personas")
    sh_rows = [
        [Paragraph("Stakeholder", STYLES["th"]), Paragraph("Role", STYLES["th"]), Paragraph("Primary Use Case", STYLES["th"]), Paragraph("Benefit", STYLES["th"])],
        [P("Developer","td"), P("Internal","td"), P("System development, maintenance, debugging","td"), P("Full system ownership and control","td")],
        [P("Business Operations Manager","td"), P("Internal","td"), P("Query distributor/retailer performance data","td"), P("No SQL knowledge required","td")],
        [P("Area Sales Manager","td"), P("Internal","td"), P("Regional analytics, target tracking","td"), P("Instant region-filtered reports","td")],
        [P("Finance Team","td"), P("Internal","td"), P("Wallet transactions, withdrawal analysis","td"), P("Accurate financial summaries on demand","td")],
        [P("National Executive","td"), P("Internal","td"), P("Pan-India business overview","td"), P("Executive-level summaries","td")],
        [P("IT / Database Admin","td"), P("Technical","td"), P("Schema monitoring, drift detection","td"), P("Automated drift alerts on startup","td")],
        [P("Audit / Compliance Team","td"), P("Internal","td"), P("Data access audit logs","td"), P("Full query audit history log","td")],
    ]
    story.append(table(sh_rows, [BW*.2, BW*.18, BW*.37, BW*.25]))

    # ══ 5. BUSINESS OBJECTIVES ════════════════════════════════════════════════
    sec(5, "Business Objectives & Goals")
    obj_rows = [
        [Paragraph(h, STYLES["th"]) for h in ["ID","Objective","Priority","Status"]],
        [P("OBJ-01","tdc"), P("Enable non-technical users to query live business data using plain English","td"), P(PRIORITY["CRITICAL"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-02","tdc"), P("Generate read-only, validated, safe SQL queries from NLP — zero data mutation risk","td"), P(PRIORITY["CRITICAL"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-03","tdc"), P("Provide multi-turn conversational context for follow-up queries","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-04","tdc"), P("Export query results as CSV, Excel (.xlsx), and PDF reports","td"), P(PRIORITY["MEDIUM"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-05","tdc"), P("Enforce enterprise security — no credentials, passwords, or encryption keys exposed","td"), P(PRIORITY["CRITICAL"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-06","tdc"), P("Support cloud GPU inference (Kaggle/Colab/RunPod) for performance scalability","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-07","tdc"), P("Self-correct SQL generation errors automatically via multi-attempt retry loop","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-08","tdc"), P("Maintain full query audit history and knowledge graph for governance","td"), P(PRIORITY["MEDIUM"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-09","tdc"), P("Provide specialized modes: Tutor QA, ERD Generator, Dashboard Builder, Business Storyteller","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-10","tdc"), P("Detect and handle ambiguous or underspecified queries with clarification prompts","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-11","tdc"), P("Auto-detect and alert on database schema drift on every server startup","td"), P(PRIORITY["MEDIUM"],"td"), P(STATUS["Achieved"],"td")],
        [P("OBJ-12","tdc"), P("Implement Incognito mode to suppress query logging for sensitive sessions","td"), P(PRIORITY["LOW"],"td"), P(STATUS["Achieved"],"td")],
    ]
    story.append(table(obj_rows, [BW*.1, BW*.58, BW*.16, BW*.16]))

    # ══ 6. SYSTEM ARCHITECTURE ════════════════════════════════════════════════
    sec(6, "System Architecture")
    story.append(P("The system is built on a strictly layered, multi-agent pipeline architecture. Every user query "
        "flows sequentially through 7 processing stages before results are returned. This pipeline design ensures "
        "accuracy, security, and auditability at every step of the process."))
    story.append(sp(8))
    story.append(ArchDiagram())
    story.append(sp(4))
    story.append(P("Figure 1 — End-to-End System Architecture of the Agentic Analyst Platform (JGH Intelligence Engine v2.0)", "caption"))
    story.append(sp(10))
    sub("Architecture Layers")
    layers = [
        ("Layer 1 — User Interface","React/Vue single-page application served at http://localhost:8000. Users type natural language questions into a chat-style interface with a Schema Explorer panel."),
        ("Layer 2 — FastAPI REST Gateway","A production FastAPI v0.141.1 application with 30+ endpoints, CORS middleware, static file serving, and request routing. Runs via Uvicorn with WatchFiles hot-reload in development."),
        ("Layer 3 — Intent Router","The first agent to receive the query. It classifies the question into one of 6 modes: GREETING, SQL_ANALYTICS, TUTOR_QA, ERD_GEN, DASHBOARD_GEN, or BUSINESS_STORY using regex pattern matching."),
        ("Layer 4 — AI Agent Pipeline","A sequential multi-step chain: NLP Understanding → Context Resolver → Prompt Builder → SQL Generator (LLM) → Validator Stack → Database Executor → Response Generator."),
        ("Layer 5 — LLM & Knowledge","Ollama serving Qwen2.5-Coder 7B locally or via remote cloud GPU tunnel. Augmented with a Knowledge Graph (schema metadata, business rules, SQL history examples via RAG)."),
        ("Layer 6 — MySQL Database","Read-only connection to the jghMasterDB production MySQL database via PyMySQL/SQLAlchemy. Only SELECT queries are ever executed."),
        ("Layer 7 — Output Layer","Results formatted as JSON API responses + automatic CSV/Excel/PDF report generation + audit log recording."),
    ]
    for (t,d) in layers:
        story.append(P(f"<b>{t}</b>"))
        story.append(P(d))
        story.append(sp(4))

    # ══ 7. PIPELINE WALKTHROUGH ═══════════════════════════════════════════════
    sec(7, "AI Agent Pipeline — Detailed Walkthrough")
    story.append(P("Below is the step-by-step execution trace for a typical SQL analytics query from the moment a user "
        "submits a question to the moment they receive results."))
    story.append(sp(6))

    steps = [
        ("Step 1 — Ambiguity Check",
         "app/agent/ambiguity_checker.py",
         "Before any AI processing begins, the Ambiguity Checker scans the question for vague or underspecified patterns. "
         "If the question matches a known ambiguous pattern (e.g., 'Show August data' with no entity or metric context), "
         "the system immediately returns a clarification prompt with a list of options for the user to choose from, "
         "without invoking the LLM at all — saving latency and improving user experience."),
        ("Step 2 — Security Firewall",
         "app/api/main.py + app/agent/sql_agent.py",
         "A keyword-matching security firewall at both the API gateway and the agent layer blocks any request containing "
         "sensitive terms: 'password', 'encryption key', 'master key', 'private key', 'auth token', 'password_hash'. "
         "These queries are immediately rejected with a security denial message and never reach the LLM or database."),
        ("Step 3 — Intent Routing",
         "app/agent/intent_router.py",
         "The Intent Router classifies the query into one of 6 operational modes using regex patterns. The default mode "
         "is SQL_ANALYTICS. Special modes include TUTOR_QA (explanations), ERD_GEN (schema diagrams), DASHBOARD_GEN "
         "(dashboard specs), BUSINESS_STORY (executive summaries), and GREETING (chitchat). Non-SQL queries are routed "
         "to specialized handlers and bypass the SQL pipeline entirely."),
        ("Step 4 — NLP Understanding (LLM Call #1)",
         "app/agent/nlp_understanding.py",
         "The NLP Understanding Agent calls the Qwen2.5-Coder 7B LLM via Ollama with a structured system prompt. "
         "The LLM is instructed to parse the user's question into a strict BusinessRequirement JSON schema (Pydantic model) "
         "capturing: intent, entities, entity_roles, relationships, specific_ids, metrics, aggregation, filters, "
         "date_period, relative_dates, comparisons, grouping, sorting, ranking, limit, requested_columns, output_format, "
         "conditions, and clarification_required. The LLM is configured with temperature=0.0 and format='json' to ensure "
         "deterministic, structured output."),
        ("Step 5 — Context Resolution",
         "app/agent/memory_manager.py + app/agent/context_resolver.py",
         "The Memory Manager retrieves the active session context (up to 10 previous turns) and the Context Resolver "
         "merges it with the newly parsed BusinessRequirement. It handles: context inheritance (same entity, same region), "
         "context replacement (new entity overrides old), anaphoric references ('their', 'them', 'that person'), "
         "and explicit context reset commands. The final merged context is passed to the prompt builder."),
        ("Step 6 — Prompt Building (RAG)",
         "app/prompt/prompt_builder.py",
         "The Prompt Builder constructs a schema-aware, context-aware LLM prompt using Retrieval-Augmented Generation (RAG). "
         "It selectively retrieves: (a) only the relevant table schemas from the Knowledge Graph, (b) applicable business "
         "rules and term mappings, and (c) up to 2 relevant SQL history examples. It also injects the structured execution "
         "plan filters (entity, specific_id, region, date/time, status, metric) as explicit directives the LLM MUST follow. "
         "Low-confidence queries get the full schema."),
        ("Step 7 — SQL Generation (LLM Call #2)",
         "app/llm/sql_generator.py",
         "The SQL Generator invokes Ollama (LLM Call #2) with the assembled prompt. The model is configured with "
         "temperature=0.0, top_p=0.9, num_predict=300. The raw LLM output is passed through the SQL Cleaner "
         "(app/utils/sql_cleaner.py) which strips markdown fences, removes orphaned semicolons, deduplicates WHERE "
         "conditions, fixes trailing commas, and applies AST-level optimization via the SQL Optimizer."),
        ("Step 8 — Validation Stack (3-Pass)",
         "app/validator/sql_ast_validator.py + semantic_sql_validator.py",
         "PASS 1 (AST Validator): The SQL is parsed into an AST using sqlglot. Checks: SELECT-only enforcement, "
         "forbidden node types (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE), sensitive column blacklist, table allowlist, "
         "column existence against schema metadata, temporal filter presence for time-bound queries. "
         "PASS 2 (Semantic Validator): Validates SQL semantic alignment with the execution plan: GROUP BY presence, "
         "ORDER BY presence, specific ID filter, required aggregations, primary table inclusion. "
         "PASS 3 (EXPLAIN): MySQL EXPLAIN is run on the generated query. If it fails, the error is fed back."),
        ("Step 9 — Self-Correction Retry Loop",
         "app/agent/sql_agent.py",
         "If any validation pass fails, the system does NOT immediately return an error. It captures the specific "
         "failure reason (e.g., 'Missing GROUP BY clause') and feeds it back to the LLM as an additional PREVIOUS ERROR "
         "section in the prompt. The system retries SQL generation up to 3 times before returning a final blocked status."),
        ("Step 10 — Database Execution",
         "app/database/read_executor.py",
         "The validated SQL query is executed against the production MySQL database via PyMySQL/SQLAlchemy. "
         "Results are returned as a list of dicts with column metadata. If execution fails (e.g., database error, "
         "unknown column), the error is captured and fed back into the retry loop."),
        ("Step 11 — E2E Accuracy Validation (10-Point)",
         "app/validator/e2e_accuracy_validator.py",
         "Post-execution, a 10-point end-to-end accuracy validator checks: (1) User Intent — SQL is SELECT, "
         "(2) Entity — expected tables present in SQL, (3) ID/Identifier — specific IDs in WHERE clause, "
         "(4) Relationship — JOINs present when required, (5) Filters — role/state/status filters present, "
         "(6) Date Range — temporal filter present when required, (7) Metric — amount/sku_inventories in SQL for "
         "earnings/scans, (8) Aggregation — GROUP BY present when required, (9) SQL Completeness — SQL is not empty, "
         "(10) Actual Result — empty result handling. Any failure triggers another retry."),
        ("Step 12 — Response Generation & Export",
         "app/agent/response_generator.py + app/utils/report_generator.py",
         "The Response Generator invokes the LLM a third time (temperature=0.3) to produce a natural, "
         "business-friendly markdown narrative summarizing the results. Simultaneously, the Report Generator "
         "creates downloadable CSV, Excel, and PDF files saved to the /reports/ directory with UUID-based filenames. "
         "Report URLs are returned in the API response for direct download."),
    ]
    for (title, module, desc) in steps:
        story.append(P(f"<b>► {title}</b>"))
        story.append(P(f"<i>Module: {module}</i>", "caption"))
        story.append(P(desc))
        story.append(sp(6))

    # ══ 8. OPERATIONAL MODES ══════════════════════════════════════════════════
    sec(8, "Operational Modes & Intent Classification")
    story.append(P("The Intent Router classifies every incoming query into one of 6 distinct operational modes. "
        "Each mode has a dedicated handler with specialized logic."))
    story.append(sp(6))
    modes = [
        [Paragraph(h, STYLES["th"]) for h in ["Mode","Trigger Examples","Handler Module","Description"]],
        [P("SQL_ANALYTICS","tdb"), P("'Show retailers linked to distributor 5997', 'Top 10 earners in July'","td"), P("app/agent/sql_agent.py","td"), P("Default mode. Executes the full 12-step NLP → SQL → Validate → Execute pipeline. Handles all data queries.","td")],
        [P("GREETING","tdb"), P("'Hello', 'Hi', 'Thanks', 'What can you do?'","td"), P("app/api/main.py (inline)","td"), P("Returns a friendly greeting with example questions. No LLM or DB invocation.","td")],
        [P("TUTOR_QA","tdb"), P("'Explain how wallet_balance works', 'What is user_role?', 'Tell me about the schema'","td"), P("app/agent/tutor_agent.py","td"), P("Database Tutor & Onboarding Coach. Uses LLM to explain database concepts, table structures, and business terminology in plain language.","td")],
        [P("ERD_GEN","tdb"), P("'Show ER diagram for users and wallet', 'Draw architecture', 'Visualize schema'","td"), P("app/agent/erd_generator.py","td"), P("Generates visual Entity-Relationship diagrams showing table relationships, foreign keys, and schema architecture.","td")],
        [P("DASHBOARD_GEN","tdb"), P("'Build a dashboard for distributor performance', 'Analytics panel for July'","td"), P("app/agent/dashboard_builder.py","td"), P("Generates structured dashboard specification JSON with recommended KPIs, chart types, and metrics for a given business context.","td")],
        [P("BUSINESS_STORY","tdb"), P("'What happened this month in simple words', 'Executive summary', 'Business trends'","td"), P("app/agent/storyteller.py","td"), P("Executive Business Storyteller. Generates a natural language narrative summary of business performance for non-technical executives.","td")],
    ]
    story.append(table(modes, [BW*.15, BW*.3, BW*.22, BW*.33]))

    # ══ 9. FUNCTIONAL REQUIREMENTS ════════════════════════════════════════════
    sec(9, "Functional Requirements")
    def fr_table(rows):
        hdr = [Paragraph(h,STYLES["th"]) for h in ["FR ID","Requirement Description","Priority","Status"]]
        data = [hdr] + [[P(r[0],"tdc"), P(r[1],"td"), P(PRIORITY[r[2]],"td"), P(STATUS[r[3]],"td")] for r in rows]
        return table(data, [BW*.1, BW*.6, BW*.15, BW*.15])

    sub("Core NLP & SQL Query Engine")
    story.append(fr_table([
        ("FR-01","Accept natural language questions via REST API POST /query endpoint","CRITICAL","Implemented"),
        ("FR-02","Parse user questions into structured BusinessRequirement JSON schema via LLM (Qwen2.5-Coder 7B)","CRITICAL","Implemented"),
        ("FR-03","Generate valid MySQL SELECT queries from structured execution plans","CRITICAL","Implemented"),
        ("FR-04","Auto-detect query intent: list, count, aggregate, earnings, balance, SKU, withdrawal, mechanic, company","HIGH","Implemented"),
        ("FR-05","Self-correct SQL generation errors in up to 3 retry attempts with error feedback","HIGH","Implemented"),
        ("FR-06","Support specific ID-based queries (distributor_id, retailer_id, user_id, wholesaler_id)","HIGH","Implemented"),
        ("FR-07","Support temporal queries: current month, specific month/year, date ranges, relative dates","HIGH","Implemented"),
        ("FR-08","Support geographic/region filters by state, city, district, state_id, and pincode","HIGH","Implemented"),
        ("FR-09","Support role-based filtering by user_role (1=Admin, 2=Retailer, 3=Mechanic, 4=Distributor, 5=Wholesaler)","HIGH","Implemented"),
        ("FR-10","Support status-based filtering (active, pending, approved, rejected, inactive)","MEDIUM","Implemented"),
        ("FR-11","Support earnings queries using wallet_transaction.amount with reference_type filter","HIGH","Implemented"),
        ("FR-12","Support wallet balance queries from users.wallet_balance","MEDIUM","Implemented"),
        ("FR-13","Support SKU inventory scan volume queries from sku_inventories table","MEDIUM","Implemented"),
        ("FR-14","Support withdrawal request queries with status, amount, TDS breakdown","MEDIUM","Implemented"),
        ("FR-15","Support multi-month comparison queries (earnings July vs June)","MEDIUM","Implemented"),
        ("FR-16","Support percentage change / growth rate calculations","MEDIUM","Implemented"),
        ("FR-17","Support geographic multi-state comparison queries","MEDIUM","Implemented"),
        ("FR-18","Support reward points / QR scan queries from sku_qr_points_maps table","LOW","Implemented"),
    ]))
    story.append(sp(8))

    sub("Context & Session Management")
    story.append(fr_table([
        ("FR-19","Maintain session-level conversational memory (sliding window: 10 turns) per user session","HIGH","Implemented"),
        ("FR-20","Resolve anaphoric references: 'their', 'them', 'that person', 'in that region', 'the top one'","HIGH","Implemented"),
        ("FR-21","Detect explicit follow-up queries vs. standalone queries using 12+ regex pattern categories","HIGH","Implemented"),
        ("FR-22","Support explicit context reset commands: 'start new analysis', 'reset context', 'new query'","MEDIUM","Implemented"),
        ("FR-23","Inherit context fields (region, entity, period) from previous turns for follow-up queries","HIGH","Implemented"),
        ("FR-24","Override context fields when new information is explicitly provided","HIGH","Implemented"),
        ("FR-25","Isolate session memory per session_id — User A cannot see User B's context","CRITICAL","Implemented"),
        ("FR-26","Attach active session context to every LLM prompt to maintain coherent multi-turn dialogue","HIGH","Implemented"),
    ]))
    story.append(sp(8))

    sub("Ambiguity Detection & Clarification")
    story.append(fr_table([
        ("FR-27","Detect vague date-only queries (e.g., 'show August data') with no entity or metric specified","HIGH","Implemented"),
        ("FR-28","Detect single-word underspecified queries ('data', 'report', 'stats') and prompt clarification","MEDIUM","Implemented"),
        ("FR-29","Return a structured clarification response with a list of 4+ actionable options for the user","HIGH","Implemented"),
        ("FR-30","Skip ambiguity check for queries containing explicit entities (retailer, distributor, wallet, etc.)","HIGH","Implemented"),
    ]))
    story.append(sp(8))

    sub("Reporting & Export")
    story.append(fr_table([
        ("FR-31","Export query results as CSV file via POST /export/csv endpoint","MEDIUM","Implemented"),
        ("FR-32","Export query results as Excel (.xlsx) file via POST /export/excel endpoint","MEDIUM","Implemented"),
        ("FR-33","Export query results as PDF report via POST /export/pdf endpoint","MEDIUM","Implemented"),
        ("FR-34","Export SQL query results directly as CSV via POST /export/sql-csv endpoint","LOW","Implemented"),
        ("FR-35","Stream large CSV exports via chunked HTTP streaming for big datasets","LOW","Implemented"),
        ("FR-36","Auto-save all reports to disk under /reports/ directory with UUID-based filenames","LOW","Implemented"),
        ("FR-37","Return download URLs for all generated reports in the API response payload","MEDIUM","Implemented"),
    ]))
    story.append(sp(8))

    sub("Security & Privacy")
    story.append(fr_table([
        ("FR-38","Block all requests for passwords, encryption keys, private tokens, auth tokens via keyword firewall","CRITICAL","Implemented"),
        ("FR-39","Restrict all database operations to SELECT-only — block INSERT/UPDATE/DELETE/DROP/ALTER/CREATE via AST validator","CRITICAL","Implemented"),
        ("FR-40","Prevent access to sensitive database columns (password, secret, token, master_key, password_hash) via AST validator column blacklist","CRITICAL","Implemented"),
        ("FR-41","Validate all generated SQL against an allowed table list (TARGET_SCOPE_TABLES) — reject queries referencing unauthorized tables","CRITICAL","Implemented"),
        ("FR-42","Validate all generated SQL column references against schema metadata — reject hallucinated column names","HIGH","Implemented"),
        ("FR-43","Support Incognito / Private mode — suppress query logging for sensitive sessions","MEDIUM","Implemented"),
        ("FR-44","Log all queries to knowledge/sql_history/query_audit_history.json for full audit trail","HIGH","Implemented"),
        ("FR-45","Log security audit events via app/utils/audit_logger.py with latency, row count, and status","MEDIUM","Implemented"),
        ("FR-46","Store database credentials as AES-256 Fernet encrypted values in .env — decrypt using .master.key","CRITICAL","Implemented"),
    ]))

    # ══ 10. TECHNICAL STACK ═══════════════════════════════════════════════════
    sec(10, "Technical Stack & Dependencies")
    tech_rows = [
        [Paragraph(h,STYLES["th"]) for h in ["Category","Technology","Version","Purpose"]],
        [P("Web Framework","tdb"), P("FastAPI","td"), P("0.141.1","tdc"), P("REST API server with automatic OpenAPI/Swagger docs","td")],
        [P("ASGI Server","tdb"), P("Uvicorn + WatchFiles","td"), P("0.52.1 / 1.2.0","tdc"), P("Production ASGI server + hot reload for development","td")],
        [P("LLM Runtime","tdb"), P("Ollama","td"), P("0.6.2","tdc"), P("Local LLM serving — configurable for local or cloud GPU","td")],
        [P("LLM Model","tdb"), P("Qwen2.5-Coder 7B","td"), P("Q4_K_M","tdc"), P("AI model for NLP understanding and SQL generation","td")],
        [P("Database","tdb"), P("MySQL (jghMasterDB)","td"), P("Production","tdc"), P("Primary enterprise data store","td")],
        [P("DB Connector","tdb"), P("PyMySQL + SQLAlchemy","td"), P("1.2.0 / 2.0.51","tdc"), P("Database connection and query execution","td")],
        [P("SQL Parser","tdb"), P("sqlglot","td"), P("≥30.0.0","tdc"), P("SQL AST parsing, validation, and optimization","td")],
        [P("Data Validation","tdb"), P("Pydantic v2","td"), P("2.13.4","tdc"), P("BusinessRequirement JSON schema validation","td")],
        [P("Vector DB","tdb"), P("ChromaDB","td"), P("1.5.9","tdc"), P("Embedding store for RAG/few-shot SQL history retrieval","td")],
        [P("Embeddings","tdb"), P("sentence-transformers","td"), P("5.6.1","tdc"), P("Semantic similarity for RAG retrieval (all-MiniLM-L6-v2)","td")],
        [P("ML Framework","tdb"), P("PyTorch + scikit-learn","td"), P("2.13.0 / 1.9.0","tdc"), P("Embedding model inference backend","td")],
        [P("Crypto","tdb"), P("cryptography (Fernet)","td"), P("≥41.0.0","tdc"), P("AES-256 encryption for database credentials","td")],
        [P("Excel Export","tdb"), P("openpyxl","td"), P("≥3.1.0","tdc"), P("Excel (.xlsx) report generation","td")],
        [P("PDF Export","tdb"), P("reportlab","td"), P("≥5.0.0","tdc"), P("PDF report generation","td")],
        [P("Data Processing","tdb"), P("pandas","td"), P("3.0.5","tdc"), P("Tabular data manipulation and CSV export","td")],
        [P("Observability","tdb"), P("OpenTelemetry SDK","td"), P("1.44.0","tdc"), P("Telemetry and distributed tracing support","td")],
        [P("Config","tdb"), P("python-dotenv","td"), P("1.2.2","tdc"), P("Load .env configuration values","td")],
        [P("Containerization","tdb"), P("Docker + docker-compose","td"), P("Latest","tdc"), P("Containerized deployment (Dockerfile + docker-compose.yml included)","td")],
        [P("Python","tdb"), P("CPython","td"), P("3.13.14","tdc"), P("Core runtime environment","td")],
    ]
    story.append(table(tech_rows, [BW*.17, BW*.22, BW*.13, BW*.48]))

    # ══ 11. MODULE REFERENCE ══════════════════════════════════════════════════
    sec(11, "Module & Component Reference")
    story.append(P("Below is the complete module reference for every Python file in the application. Each module is "
        "documented with its file path, purpose, and key classes/functions."))
    story.append(sp(6))

    modules = [
        [Paragraph(h,STYLES["th"]) for h in ["Module","File Path","Responsibility","Key Classes / Functions"]],
        [P("NLP Understanding Agent","tdb"), P("app/agent/nlp_understanding.py","td"), P("Parses NL question into BusinessRequirement using LLM","td"), P("NLPUnderstandingAgent, parse_question()","td")],
        [P("BusinessRequirement Model","tdb"), P("app/agent/business_requirement.py","td"), P("Pydantic schema for structured NLP output","td"), P("BusinessRequirement (22 fields)","td")],
        [P("SQL Agent (Orchestrator)","tdb"), P("app/agent/sql_agent.py","td"), P("Orchestrates full 12-step pipeline with retry logic","td"), P("run_agent(), compute_confidence()","td")],
        [P("Intent Router","tdb"), P("app/agent/intent_router.py","td"), P("Classifies queries into 6 operational modes","td"), P("IntentRouter.classify(), route_intent()","td")],
        [P("AI Collaborator","tdb"), P("app/agent/collaborator.py","td"), P("Orchestrates multi-mode requests with query decomposition","td"), P("AICollaborator, handle_collaborative_query()","td")],
        [P("Memory Manager","tdb"), P("app/agent/memory_manager.py","td"), P("Session-level conversational memory (sliding window)","td"), P("MemoryManager, resolve_session_context(), add_turn()","td")],
        [P("Context Resolver","tdb"), P("app/agent/context_resolver.py","td"), P("Merges previous context with new query intent","td"), P("ContextResolver, is_follow_up(), resolve()","td")],
        [P("Ambiguity Checker","tdb"), P("app/agent/ambiguity_checker.py","td"), P("Detects underspecified or vague queries","td"), P("check_ambiguity()","td")],
        [P("Query Decomposer","tdb"), P("app/agent/query_decomposer.py","td"), P("Splits multi-part questions into sub-queries","td"), P("decompose_query()","td")],
        [P("NLP Intent Parser","tdb"), P("app/agent/nlp_intent_parser.py","td"), P("Lightweight deterministic intent/context extraction","td"), P("nlp_intent_parser, parse_intent()","td")],
        [P("Response Generator","tdb"), P("app/agent/response_generator.py","td"), P("LLM-powered natural language result summaries","td"), P("ResponseGenerator, generate_response()","td")],
        [P("Response Synthesizer","tdb"), P("app/agent/response_synthesizer.py","td"), P("Formats mode-specific results into unified API response","td"), P("synthesizer, synthesize()","td")],
        [P("Tutor Agent","tdb"), P("app/agent/tutor_agent.py","td"), P("Database Tutor for schema and concept explanations","td"), P("tutor_agent, explain()","td")],
        [P("ERD Generator","tdb"), P("app/agent/erd_generator.py","td"), P("Generates ER diagrams from schema metadata","td"), P("erd_generator, generate_diagram()","td")],
        [P("Dashboard Builder","tdb"), P("app/agent/dashboard_builder.py","td"), P("Builds dashboard specification JSON","td"), P("dashboard_builder, build_dashboard()","td")],
        [P("Storyteller","tdb"), P("app/agent/storyteller.py","td"), P("Executive business narrative generator","td"), P("storyteller, tell_story()","td")],
        [P("ID Search Agent","tdb"), P("app/agent/id_search.py","td"), P("Handles exact ID-based entity lookups","td"), P("id_search, search_by_id()","td")],
        [P("Document Knowledge","tdb"), P("app/agent/document_knowledge.py","td"), P("Handles document-based knowledge queries","td"), P("document_knowledge","td")],
        [P("Knowledge Chat","tdb"), P("app/agent/knowledge_chat.py","td"), P("Chat interface over indexed knowledge graph data","td"), P("knowledge_chat","td")],
        [P("SQL Generator (LLM)","tdb"), P("app/llm/sql_generator.py","td"), P("Invokes Ollama LLM to generate MySQL SELECT queries","td"), P("generate_sql(), is_ollama_online(), OLLAMA_BASE_URL","td")],
        [P("Prompt Builder","tdb"), P("app/prompt/prompt_builder.py","td"), P("Builds schema-aware, RAG-augmented LLM prompts","td"), P("build_sql_prompt()","td")],
        [P("AST Validator","tdb"), P("app/validator/sql_ast_validator.py","td"), P("SQL syntax, security, schema, and column validation","td"), P("validate_sql(), SQLValidationError","td")],
        [P("Semantic SQL Validator","tdb"), P("app/validator/semantic_sql_validator.py","td"), P("Validates SQL semantic alignment with execution plan","td"), P("validate_semantic_sql(), SemanticValidationError","td")],
        [P("E2E Accuracy Validator","tdb"), P("app/validator/e2e_accuracy_validator.py","td"), P("10-point post-execution end-to-end accuracy check","td"), P("E2EAccuracyValidator, validate()","td")],
        [P("Result Accuracy Validator","tdb"), P("app/validator/result_accuracy_validator.py","td"), P("Metadata-level accuracy scoring and warnings","td"), P("result_accuracy_validator, validate()","td")],
        [P("SQL Optimizer","tdb"), P("app/validator/sql_optimizer.py","td"), P("AST-level SQL optimization and alias normalization","td"), P("optimize_sql()","td")],
        [P("Universal Validator","tdb"), P("app/validator/universal_validator.py","td"), P("Mode-agnostic output validation gate for collaborator","td"), P("universal_validator, validate()","td")],
        [P("Plan Validator","tdb"), P("app/validator/plan_validator.py","td"), P("Query plan concept clarification checker","td"), P("plan_validator, check_concept_clarification()","td")],
        [P("SQL Cleaner","tdb"), P("app/utils/sql_cleaner.py","td"), P("Post-processes raw LLM SQL output into clean valid SQL","td"), P("clean_sql()","td")],
        [P("Read Executor","tdb"), P("app/database/read_executor.py","td"), P("Executes validated SELECT queries against MySQL","td"), P("execute_read_query(), get_execution_plan()","td")],
        [P("Allowed Tables","tdb"), P("app/database/allowed_tables.py","td"), P("Allowlist of TARGET_SCOPE_TABLES for security","td"), P("TARGET_SCOPE_TABLES, is_allowed_table()","td")],
        [P("Schema Drift Detector","tdb"), P("app/database/schema_drift_detector.py","td"), P("Detects schema changes vs cached metadata on startup","td"), P("run_schema_drift_check()","td")],
        [P("Cache Manager","tdb"), P("app/database/cache_manager.py","td"), P("In-memory query result cache with bypass support","td"), P("cache_manager, get(), set()","td")],
        [P("Knowledge Graph","tdb"), P("app/knowledge/knowledge_graph.py","td"), P("Enterprise schema relationship knowledge graph","td"), P("get_knowledge_graph()","td")],
        [P("DB Profiler","tdb"), P("app/knowledge/db_profiler.py","td"), P("Profiles live database schema into metadata","td"), P("run_database_profiler()","td")],
        [P("Relationship Resolver","tdb"), P("app/knowledge/relationship_resolver.py","td"), P("Resolves table relationships for multi-join queries","td"), P("relationship_resolver, resolve_relationships()","td")],
        [P("Table Schemas","tdb"), P("app/knowledge/table_schemas.py","td"), P("Static table schema context for prompt injection","td"), P("get_selective_schema_context(), TABLE_SUMMARIES","td")],
        [P("Business Rule Index","tdb"), P("app/knowledge/business_rule_index.py","td"), P("Business-domain rules and term mappings for prompts","td"), P("get_selective_business_rules()","td")],
        [P("RAG Retriever","tdb"), P("app/retriever/retriever.py","td"), P("Retrieves relevant SQL history and schema examples via ChromaDB","td"), P("retrieve_schema(), retrieve_sql_history()","td")],
        [P("Report Generator","tdb"), P("app/utils/report_generator.py","td"), P("Generates CSV, Excel, and PDF export files","td"), P("generate_csv(), generate_excel(), generate_pdf(), save_reports_to_disk()","td")],
        [P("Summary Generator","tdb"), P("app/utils/summary_generator.py","td"), P("Natural language summary of query results with context","td"), P("generate_natural_summary()","td")],
        [P("Date Parser","tdb"), P("app/utils/date_parser.py","td"), P("Parses temporal expressions into SQL date range conditions","td"), P("parse_temporal_expressions(), get_month_bounds()","td")],
        [P("Audit Logger","tdb"), P("app/utils/audit_logger.py","td"), P("Security and compliance audit event logging","td"), P("log_audit_event()","td")],
        [P("Privacy Manager","tdb"), P("app/utils/privacy_manager.py","td"), P("Manages incognito/private mode session handling","td"), P("privacy_manager","td")],
        [P("Query Logger","tdb"), P("app/utils/query_logger.py","td"), P("Logs unmapped / failed query events for analysis","td"), P("query_logger, log_unmapped_query()","td")],
        [P("Query History","tdb"), P("app/sql_history/query_history.py","td"), P("Persists query audit history to JSON file","td"), P("log_query_history(), get_query_history()","td")],
        [P("FastAPI Gateway","tdb"), P("app/api/main.py","td"), P("Main REST API with 30+ endpoints, middleware, routing","td"), P("app (FastAPI), /query, /health, /schema, /export/*, etc.","td")],
        [P("Export Router","tdb"), P("app/api/export_router.py","td"), P("Dedicated router for all /export/* endpoints","td"), P("export_router","td")],
        [P("Server Launcher","tdb"), P("start_server.py","td"), P("Pre-flight diagnostic checker + Uvicorn server starter","td"), P("run_diagnostics()","td")],
    ]
    story.append(table(modules, [BW*.17, BW*.26, BW*.30, BW*.27], fontsize=7.5))

    # ══ 12. DATA ARCHITECTURE ═════════════════════════════════════════════════
    sec(12, "Data Architecture & Database Schema")
    sub("Database Overview")
    story.append(P("The system operates against the <b>jghMasterDB</b> production MySQL database. The database contains "
        "the complete JGH enterprise business data spanning users, distributors, retailers, wholesalers, wallet "
        "transactions, SKU inventories, withdrawal requests, scheme management, and geographic master data."))
    story.append(sp(6))
    sub("TARGET SCOPE TABLES (In-Scope for SQL Generation)")
    story.append(P("The following tables are in the TARGET_SCOPE_TABLES allowlist and are the only tables the AI "
        "is permitted to query:"))
    story.append(sp(4))
    for tbl in ["users","companies","wallet_transaction","role","user_role","sku_inventories",
                "mechanic_details","withdrawal_request","automatic_transactions","sku_qr_points_map","state"]:
        story.append(B(tbl))
    story.append(sp(8))
    sub("Extended Database Tables (Available via JOIN)")
    ext_tables = [
        [Paragraph(h,STYLES["th"]) for h in ["Table","Description","Key Columns"]],
        [P("users","tdb"), P("All platform users: retailers, distributors, wholesalers, mechanics, executives","td"), P("id, name, mobile_number, user_role, wallet_balance, state_id, distributer_id, primary_distributor_id, status, kyc_status, created_at","td")],
        [P("wallet_transaction","tdb"), P("All wallet credit/debit transactions (earnings, referrals, redemptions)","td"), P("id, user_id, amount, transaction_type (0/1), reference_id, reference_type, status, remark, created_at","td")],
        [P("withdrawal_request","tdb"), P("Cash payout/withdrawal requests by users","td"), P("id, user_id, amount, status (0=pending/1=approved/2=rejected), tds_amount, bank_reference_number, created_at","td")],
        [P("sku_inventories","tdb"), P("Product box QR scanning and inventory tracking","td"), P("id, sku_code, sku_description, uom, mrp, invoice_number, distributer_id, status_retailer_id, status_wholeseller_id, retailer_scanned_at, wholesaler_scanned_at, created_at","td")],
        [P("mechanic_details","tdb"), P("Mechanic / garage owner profiles","td"), P("id, mechanic_id, garage_id, shop_name, owner_name, region, distributor_code","td")],
        [P("automatic_transactions","tdb"), P("System-triggered automatic bank transfer transactions","td"), P("id, user_id, amount, transfer_type, status, bank_reference_number, created_at","td")],
        [P("retailer_distributor_mappings","tdb"), P("Many-to-one mapping of retailers to their assigned distributor","td"), P("id, retailer_id, distributor_id, created_at, updated_at","td")],
        [P("executive_distributor_mappings","tdb"), P("Maps JGH sales executives to their distributor territories","td"), P("id, executive_id, distributor_id","td")],
        [P("executive_retailer_mappings","tdb"), P("Maps sales executives to individual retailers","td"), P("id, executive_id, retailer_id","td")],
        [P("distributor_targets","tdb"), P("Monthly sales targets assigned to distributors","td"), P("id, distributor_id, target_amount, month, year","td")],
        [P("distributor_teams","tdb"), P("Team composition under each distributor","td"), P("id, distributor_id, member_id, role","td")],
        [P("scheme_wallet_transactions","tdb"), P("Scheme-based wallet credit transactions","td"), P("id, user_id, amount, scheme_id, created_at","td")],
        [P("gift_scan_wallet_transactions","tdb"), P("Gift/prize scan wallet credit transactions","td"), P("id, user_id, amount, created_at","td")],
        [P("winter_scan_wallet_transactions","tdb"), P("Seasonal winter campaign scan credits","td"), P("id, user_id, amount, created_at","td")],
        [P("sku_qr_points_maps","tdb"), P("Maps SKU codes to their QR scan point values","td"), P("id, sku_code, points","td")],
        [P("state","tdb"), P("Indian states master data","td"), P("id, sname (full state name)","td")],
        [P("companies","tdb"), P("JGH partner company and business unit details","td"), P("id, name, phone, email, sap_code, business_unit, jgh_company, created_at","td")],
        [P("referral_mappings","tdb"), P("Referral network mapping between users","td"), P("id, referrer_id, referred_id, created_at","td")],
        [P("pincode_address_maps","tdb"), P("Pincode to geographic address mapping","td"), P("id, pincode, district, state","td")],
    ]
    story.append(table(ext_tables, [BW*.18, BW*.32, BW*.5]))
    story.append(sp(8))

    sub("User Role Mapping")
    roles = [
        [Paragraph(h,STYLES["th"]) for h in ["user_role value","Role Name","Description","Primary Activities"]],
        [P("1","tdc"), P("Admin","tdb"), P("Full system administrator","td"), P("System management, user oversight, full data access","td")],
        [P("2","tdc"), P("Retailer","tdb"), P("Shop/retail business owner","td"), P("Earn points via QR code scanning, request payouts","td")],
        [P("3","tdc"), P("Mechanic","tdb"), P("Service center / garage owner","td"), P("Earn points via product scan, access mechanic_details profile","td")],
        [P("4","tdc"), P("Distributor","tdb"), P("Regional product distributor","td"), P("Manage retail network, track targets, oversee earnings","td")],
        [P("5","tdc"), P("Wholesaler","tdb"), P("Bulk product distributor","td"), P("Supply products to retailers, scan boxes at wholesale stage","td")],
        [P("6","tdc"), P("Executive","tdb"), P("JGH field sales executive","td"), P("Manage distributor/retailer relationships, track performance","td")],
        [P("7","tdc"), P("National Executive","tdb"), P("National-level sales management","td"), P("Pan-India analytics, strategic oversight","td")],
    ]
    story.append(table(roles, [BW*.14, BW*.18, BW*.22, BW*.46]))
    story.append(sp(8))

    sub("Wallet Transaction Types")
    wt = [
        [Paragraph(h,STYLES["th"]) for h in ["transaction_type","reference_type","Meaning","Counted As"]],
        [P("1 (CREDIT)","tdc"), P("cash_point","td"), P("QR box scan earning credit","td"), P("Earnings","td")],
        [P("1 (CREDIT)","tdc"), P("topup","td"), P("Manual wallet top-up credit","td"), P("Earnings","td")],
        [P("1 (CREDIT)","tdc"), P("redeem_coupon","td"), P("Coupon redemption credit","td"), P("Earnings","td")],
        [P("1 (CREDIT)","tdc"), P("incentive","td"), P("Performance incentive credit","td"), P("Earnings","td")],
        [P("1 (CREDIT)","tdc"), P("bonus_conversion","td"), P("Bonus points converted to cash","td"), P("Earnings","td")],
        [P("1 (CREDIT)","tdc"), P("referral_earning","td"), P("Referral commission credit","td"), P("Earnings","td")],
        [P("0 (DEBIT)","tdc"), P("withdrawal","td"), P("User withdrawal/payout debit","td"), P("Not Earnings (Debit)","td")],
    ]
    story.append(table(wt, [BW*.18, BW*.2, BW*.37, BW*.25]))

    # ══ 13. BUSINESS RULES ════════════════════════════════════════════════════
    sec(13, "Business Rules & Domain Logic")
    rules = [
        ("Earnings Definition","User 'earnings' are computed exclusively as SUM(wallet_transaction.amount) WHERE transaction_type = 1 AND reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning'). Debit transactions (type=0) are never counted as earnings."),
        ("Distributor ID Storage","The distributor a user belongs to is stored in users.distributer_id (note: one 'r' — legacy column name, intentionally misspelled in the original schema). The primary_distributor_id column is also used in some contexts."),
        ("Retailer-Distributor Relationship","The retailer_distributor_mappings table provides the formal many-to-one mapping of retailers to distributors. This is the canonical source for 'retailers linked to distributor X' queries."),
        ("Wallet Balance","users.wallet_balance stores the current net wallet balance. Historical total balance is computed from wallet_transaction.amount SUM. These may differ due to withdrawals."),
        ("QR Scan Points","sku_qr_points_maps maps each SKU code to its point value. Total points earned by a retailer = SUM(sqm.points) for all sku_inventories rows scanned by that retailer."),
        ("SKU Box Scan Confirmation","A box is considered 'retailer-confirmed' when sku_inventories.retailer_scanned_at IS NOT NULL. A box is 'wholesaler-confirmed' when wholesaler_scanned_at IS NOT NULL."),
        ("Withdrawal Status Codes","withdrawal_request.status: 0 = Pending, 1 = Approved/Paid, 2 = Rejected."),
        ("TDS on Withdrawals","Tax Deducted at Source (TDS) is stored in withdrawal_request.tds_amount. Net payout = amount - tds_amount."),
        ("Current Month Filter","MySQL: MONTH(created_at) = MONTH(CURRENT_DATE()) AND YEAR(created_at) = YEAR(CURRENT_DATE()). Used for 'current month' earnings/transaction queries."),
        ("User Status","users.status: 'active' = currently active user, 'inactive' or NULL = inactive/blocked user. Some queries filter WHERE users.status = 'active'."),
        ("KYC Status","users.kyc_status: tracks whether the user's Know Your Customer (KYC) verification is complete. Values: 'approved', 'pending', 'rejected'."),
        ("State ID Mapping","Geographic state filtering uses users.state_id joined against the state table (state.id = users.state_id, state.sname = full state name). Example: Karnataka state_id = 29."),
        ("Automatic Transactions","automatic_transactions records system-triggered bank transfers (payouts). transfer_type field indicates the payout mechanism. status: 0=pending, 1=completed, 2=failed."),
    ]
    for (title,desc) in rules:
        story.append(P(f"<b>► {title}</b>"))
        story.append(P(desc))
        story.append(sp(4))

    # ══ 14. PROMPT ENGINEERING ════════════════════════════════════════════════
    sec(14, "Prompt Engineering Architecture")
    story.append(P("The system uses a two-stage prompt strategy with two separate LLM calls per query."))
    story.append(sp(6))
    sub("Stage 1 — NLP Understanding Prompt (LLM Call #1)")
    story.append(P("System role: 'You are the NLP Understanding Module of the JGH Business Analytics Intelligence Engine.'"))
    story.append(P("The system prompt defines the strict 22-field BusinessRequirement JSON schema the LLM must output. "
        "Key constraints: temperature=0.0 (fully deterministic), format='json' (structured output mode), no markdown. "
        "The LLM must extract specific_ids (e.g., {\"distributor_id\": 5997}), intent classification "
        "(list_entities, aggregate_analytics, comparative_analytics, profile_lookup), filters, date_period, grouping, "
        "sorting, ranking, limit, and clarification_required flag."))
    story.append(sp(6))
    sub("Stage 2 — SQL Generation Prompt (LLM Call #2)")
    story.append(P("The SQL generation prompt is dynamically assembled by the Prompt Builder using 7 sections:"))
    sections = [
        ("Section 1 — Role","You are an expert MySQL Data Analyst for JGH Enterprise."),
        ("Section 2 — Question","Current user question in quotes."),
        ("Section 3 — Explicit Filters","Structured filter breakdown: entity, specific_id (with SQL FILTER REQUIRED directive), region, date/time, status, metric. These MUST appear in the WHERE clause."),
        ("Section 4 — Structural Requirements","output_format, required_columns, target_measures_and_aggregations, group_by, order_by."),
        ("Section 5 — Relevant Schema","Selective schema context: only tables relevant to the query. Low-confidence queries get the full schema."),
        ("Section 6 — Business Rules","Selective business rules and term mappings relevant to the query intent."),
        ("Section 7 — Examples","Up to 2 relevant SQL history examples retrieved via semantic similarity from ChromaDB."),
    ]
    for (t,d) in sections:
        story.append(B(f"<b>{t}</b>: {d}"))
    story.append(sp(6))
    story.append(P("Critical prompt rules injected into every SQL generation prompt:"))
    critical = [
        "Write ONLY a valid MySQL SELECT query inside a ```sql ``` code block.",
        "Do NOT hallucinate table or column names not listed in RELEVANT SCHEMA.",
        "Do NOT add location/region or date filters unless explicitly listed in CURRENT EXPLICIT FILTERS.",
        "You MUST include ALL CURRENT EXPLICIT FILTERS (specific_id, linked_id, entity, date/time) in your WHERE clause if they are not 'none'.",
        "You MUST satisfy ALL STRUCTURAL REQUIREMENTS (group_by, order_by, required_columns, target_measures_and_aggregations).",
        "NEVER ignore 'SQL FILTER REQUIRED' directives — they must be exactly applied as written.",
    ]
    for cr in critical: story.append(B(cr))

    # ══ 15. SECURITY & COMPLIANCE ═════════════════════════════════════════════
    sec(15, "Security, Privacy & Compliance")
    security_items = [
        ("Read-Only Database Enforcement","The database connection user has only SELECT privileges on jghMasterDB. "
         "Additionally, the AST Validator programmatically blocks any SQL containing INSERT, UPDATE, DELETE, DROP, ALTER, "
         "CREATE, COMMIT, ROLLBACK, or EXECUTE node types before the query reaches the database. This double-layered "
         "read-only enforcement provides defense-in-depth against accidental or malicious data mutation."),
        ("Credential Protection Firewall (2 Layers)","Layer 1 (API Gateway): Every incoming query is scanned at the "
         "FastAPI router level (app/api/main.py) for restricted terms: 'password', 'passwords', 'encryption key', "
         "'encryption keys', 'master key', 'master keys', 'private key', 'private keys', 'secret key', 'secret keys', "
         "'auth token', 'auth tokens', 'password_hash'. Layer 2 (Agent): The same check is repeated inside run_agent() "
         "in app/agent/sql_agent.py. Both layers return an immediate denial response without invoking the LLM."),
        ("Sensitive Column Blacklist","The AST Validator maintains a programmatic blacklist of database column names "
         "that can never appear in any SELECT query: password, secret, token, master_key, auth_token, private_key, "
         "password_hash. Any LLM-generated SQL referencing these columns is immediately rejected."),
        ("Table Scope Enforcement","All generated SQL is validated against TARGET_SCOPE_TABLES "
         "(app/database/allowed_tables.py). Queries referencing any table outside this allowlist are rejected before "
         "execution."),
        ("Column Existence Validation","The AST Validator cross-references all column references in generated SQL against "
         "the cached schema metadata (knowledge/schema/schema_metadata.json). Hallucinated column names trigger "
         "a validation error and a retry attempt."),
        ("AES-256 Credential Encryption","Database connection parameters (host, port, database name, username, password) "
         "are stored as a single AES-256 Fernet-encrypted blob in the ENCRYPTED_DB_CONFIG environment variable in .env. "
         "The Fernet decryption key is stored separately in .master.key. Plain-text credentials never appear in source "
         "code or logs."),
        ("Query Audit Logging","Every successful query is logged to knowledge/sql_history/query_audit_history.json "
         "with: question, generated SQL, optimized SQL, execution status, row count, affected tables, latency, and "
         "timestamp. Incognito mode (is_private=True) suppresses this logging entirely."),
        ("Security Audit Events","A dedicated audit logger (app/utils/audit_logger.py) records security-relevant events "
         "including: prompt, SQL, status (success/error/blocked), latency_ms, row_count, affected_tables, and "
         "error details. These logs support compliance, forensics, and access governance."),
        ("CORS Policy","The FastAPI application has CORS configured via CORSMiddleware. Currently allows all origins (*) "
         "for development. Production deployment must restrict allow_origins to the specific frontend domain."),
        ("Schema Drift Detection","On every server startup, the Schema Drift Detector (app/database/schema_drift_detector.py) "
         "compares the live database schema against the cached schema_metadata.json. Any detected schema additions, "
         "removals, or column changes are printed as alerts, allowing DBAs to update the knowledge base proactively."),
        ("Private / Incognito Mode","Requests with is_private=True or incognito=True suppress all query logging "
         "and audit trail recording. Results are returned normally but no historical record is kept, supporting "
         "sensitive data access scenarios."),
    ]
    for (title, desc) in security_items:
        story.append(P(f"<b>🔒  {title}</b>"))
        story.append(P(desc))
        story.append(sp(5))

    # ══ 16. VALIDATION & QA ═══════════════════════════════════════════════════
    sec(16, "Validation & Quality Assurance")
    story.append(P("The system implements a rigorous 5-layer validation architecture. Every layer can trigger a "
        "self-correction retry (up to 3 total attempts). Only queries that pass all 5 layers are returned to the user."))
    story.append(sp(6))

    val_data2 = [
        [Paragraph(h,STYLES["th"]) for h in ["Layer","Validator Module","When Executed","Checks Performed","On Failure"]],
        [P("1","tdc"), P("AST Validator\napp/validator/sql_ast_validator.py","td"), P("After SQL cleaning","td"),
         P("SELECT-only enforcement; forbidden node types (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/COMMIT); "
           "sensitive column blacklist (password, secret, token); table allowlist validation; "
           "column existence against schema metadata; temporal filter presence for time-constrained queries","td"),
         P("Retry with error feedback to LLM","td")],
        [P("2","tdc"), P("Semantic SQL Validator\napp/validator/semantic_sql_validator.py","td"), P("After AST validation","td"),
         P("GROUP BY presence when aggregation is required; ORDER BY presence when order_by is in plan; "
           "specific ID filter in WHERE clause; required SUM/COUNT aggregations; primary table referenced in query","td"),
         P("Retry with semantic error feedback","td")],
        [P("3","tdc"), P("EXPLAIN Validator\napp/database/read_executor.py","td"), P("After semantic validation","td"),
         P("MySQL EXPLAIN executed on the validated query. Checks that the database can produce a valid execution plan "
           "(no unknown tables, invalid joins, or syntax MySQL rejects at the optimizer level)","td"),
         P("Retry with EXPLAIN error feedback","td")],
        [P("4","tdc"), P("Database Execution\napp/database/read_executor.py","td"), P("After EXPLAIN validation","td"),
         P("Actual SELECT execution against jghMasterDB. Captures database-level errors (e.g., 'Unknown column', "
           "'Table doesn't exist', timeout errors)","td"),
         P("Retry with DB error feedback","td")],
        [P("5","tdc"), P("10-Point E2E Accuracy Validator\napp/validator/e2e_accuracy_validator.py","td"), P("After execution","td"),
         P("10 dimensions: (1) User Intent — SQL starts with SELECT; (2) Entity — expected tables in SQL; "
           "(3) ID/Identifier — specific IDs present in WHERE; (4) Relationship — JOINs present when required; "
           "(5) Filters — role_id, state_id, status filters; (6) Date Range — temporal filters; "
           "(7) Metric — amount/sku_inventories for earnings/scans; (8) Aggregation — GROUP BY when required; "
           "(9) SQL Completeness — SQL is not empty; (10) Actual Result — 0 rows is allowed (not an error)","td"),
         P("Retry with accuracy failure reason","td")],
    ]
    story.append(table(val_data2, [BW*.06, BW*.22, BW*.14, BW*.42, BW*.16]))
    story.append(sp(8))

    sub("Self-Correction Retry Logic")
    story.append(P("When any validation layer fails (Layers 1–5), the system captures the specific failure reason "
        "and appends it to the next LLM prompt as: 'PREVIOUS ERROR / VALIDATION FAILURE: [reason]. Please fix the "
        "SQL query and strictly ensure it matches the requirements and uses only valid columns.'"))
    story.append(sp(4))
    story.append(P("The retry loop runs a maximum of 3 times. On each attempt, the failure reason is progressively "
        "more specific, giving the LLM exact information about what it got wrong. This self-correction mechanism "
        "significantly improves the success rate for complex queries that the LLM gets wrong on the first attempt."))

    # ══ 17. API ENDPOINTS ═════════════════════════════════════════════════════
    sec(17, "API Endpoints Reference")
    story.append(P("The FastAPI application exposes 30+ REST API endpoints. Full interactive documentation is available "
        "at http://localhost:8000/docs (Swagger UI) and http://localhost:8000/redoc."))
    story.append(sp(6))

    api_data = [
        [Paragraph(h,STYLES["th"]) for h in ["Method","Endpoint","Request Body / Params","Description"]],
        [P("GET","tdc"), P("/","td"), P("None","td"), P("Serves the frontend SPA (index.html)","td")],
        [P("GET","tdc"), P("/health","td"), P("None","td"), P("System health: DB connectivity, table count, LLM model","td")],
        [P("GET","tdc"), P("/api/llm/health","td"), P("None","td"), P("LLM health: Ollama online status, URL, model name","td")],
        [P("GET","tdc"), P("/api/llm-health","td"), P("None","td"), P("Alias for /api/llm/health","td")],
        [P("GET","tdc"), P("/schema","td"), P("None","td"), P("Returns {table: [columns]} schema map for frontend Schema Explorer","td")],
        [P("POST","tdc"), P("/query","td"), P("question, user_id, session_id, request_id, execute, bypass_cache, live, is_private, incognito","td"), P("Main NLP analytics endpoint — full 12-step pipeline. Returns: results, columns, sql_query, summary, report_urls, benchmarks","td")],
        [P("POST","tdc"), P("/agent/collaborate","td"), P("question, session_id, execute","td"), P("Collaborative multi-mode query (routes to Tutor, ERD, Dashboard, Story, or SQL)","td")],
        [P("GET","tdc"), P("/api/query-history","td"), P("limit (optional)","td"), P("Retrieves paginated query audit history from JSON log","td")],
        [P("GET","tdc"), P("/api/knowledge/profile","td"), P("None","td"), P("Returns full live database profile (table stats, row counts, column info)","td")],
        [P("GET","tdc"), P("/api/erd","td"), P("tables (optional query param)","td"), P("Generates Entity-Relationship Diagram from schema metadata","td")],
        [P("GET","tdc"), P("/api/settings","td"), P("None","td"), P("Returns current AI model name, temperature, top_k, max_rows","td")],
        [P("POST","tdc"), P("/api/settings","td"), P("model_name, embedding_model, temperature, top_k, max_rows","td"), P("Updates AI model and system settings at runtime","td")],
        [P("POST","tdc"), P("/export/csv","td"), P("columns, data, filename","td"), P("Exports provided data as CSV file — streaming download","td")],
        [P("POST","tdc"), P("/export/excel","td"), P("columns, data, filename","td"), P("Exports provided data as Excel (.xlsx) file","td")],
        [P("POST","tdc"), P("/export/pdf","td"), P("columns, data, filename","td"), P("Exports provided data as PDF report","td")],
        [P("POST","tdc"), P("/export/sql-csv","td"), P("sql, filename","td"), P("Executes SQL directly and exports results as CSV","td")],
        [P("GET","tdc"), P("/reports/{filename}","td"), P("filename","td"), P("Static file server for generated reports (CSV, Excel, PDF)","td")],
        [P("GET","tdc"), P("/static/*","td"), P("path","td"), P("Serves frontend static assets (JS, CSS, images)","td")],
        [P("GET","tdc"), P("/assets/*","td"), P("path","td"), P("Serves Vite build assets if app/static/assets/ exists","td")],
        [P("GET","tdc"), P("/favicon.svg","td"), P("None","td"), P("Serves favicon SVG icon","td")],
    ]
    story.append(table(api_data, [BW*.08, BW*.24, BW*.3, BW*.38]))
    story.append(sp(8))

    sub("Query API Request/Response Schema")
    story.append(P("Example POST /query request body:"))
    story.append(CODE('{ "question": "Show retailers linked to distributor 5997 with their current month earnings",'))
    story.append(CODE('  "user_id": "user_001", "session_id": "session_abc123",'))
    story.append(CODE('  "execute": true, "is_private": false, "bypass_cache": false }'))
    story.append(sp(5))
    story.append(P("Response payload includes:"))
    resp_fields = [
        ("status","'success' | 'error' | 'ambiguous' | 'blocked'"),
        ("question","Original user question"),
        ("generated_sql","Raw SQL from LLM"),
        ("optimized_sql","Cleaned and validated SQL actually executed"),
        ("validation","Validation status and reason"),
        ("results","Array of result row objects"),
        ("columns","Array of column name strings"),
        ("rows_returned","Integer count of rows returned"),
        ("summary","Natural language narrative summary of results"),
        ("report_urls","{csv: URL, excel: URL, pdf: URL} download links"),
        ("result_confidence","'VERIFIED_RESULT' | 'SUSPICIOUS_RESULT' | 'UNABLE_TO_VERIFY'"),
        ("accuracy_message","Human-readable accuracy assessment"),
        ("benchmarks","{intent_detection_ms, schema_lookup_ms, prompt_build_ms, llm_generation_ms, validation_ms, execution_ms, total_ms}"),
        ("understanding","{summary: string} context understanding summary"),
        ("schema","Current schema map for frontend Schema Explorer refresh"),
    ]
    rf_data = [[Paragraph("Field",STYLES["th"]), Paragraph("Description",STYLES["th"])]]
    rf_data += [[P(k,"tdb"), P(v,"td")] for k,v in resp_fields]
    story.append(table(rf_data, [BW*.28, BW*.72]))

    # ══ 18. SESSION MEMORY ════════════════════════════════════════════════════
    sec(18, "Session Memory & Context Management")
    story.append(P("The system maintains a rich multi-turn conversational memory system that enables natural "
        "follow-up queries across a session without requiring the user to repeat context."))
    story.append(sp(6))
    sub("Memory Architecture")
    story.append(P("The MemoryManager (app/agent/memory_manager.py) maintains two in-memory data structures per session:"))
    story.append(B("<b>sessions</b>: A sliding window of up to 10 conversation turns (prompt, mode, SQL, summary, entities, context)"))
    story.append(B("<b>structured_context</b>: The most recent resolved context dict (entity, region, period, role_id, specific_id, filters, status, metric)"))
    story.append(sp(6))
    sub("Context Inheritance Rules")
    inherit_rules = [
        "If the new query explicitly states a new entity (e.g., 'now show wholesalers'), the entity context is REPLACED.",
        "If the new query uses anaphoric references ('their', 'in that region', 'the same period'), the previous entity/region/period context is INHERITED.",
        "If a new date/period is mentioned, it REPLACES the previous period context.",
        "If the user types a reset command ('start new analysis', 'reset context', 'new query'), ALL context is CLEARED.",
        "Specific IDs (distributor_id=5997) are inherited only for explicit follow-up queries.",
        "If no follow-up indicators are detected and a new, standalone question is asked, a fresh context is built.",
    ]
    for r in inherit_rules: story.append(B(r))
    story.append(sp(6))
    sub("Known Anaphoric Patterns Handled")
    story.append(P("The ContextResolver handles 12+ categories of anaphoric references including:"))
    anaphora = [
        "Positional references: 'in that region', 'in that state', 'in that city', 'in the same region'",
        "Pronoun references: 'from there', 'around there', 'in there'",
        "Question follow-ups: 'what about their', 'show their', 'compare their', 'tell me their'",
        "Conjunction follow-ups: 'and their', 'with their', 'also for them'",
        "Singular entity follow-ups: 'that person', 'that retailer', 'that distributor', 'that user'",
        "Superlative follow-ups: 'who has the highest', 'who earned the most', 'which one has'",
        "Time modifier follow-ups: 'what about July', 'and for August', 'how about last month'",
        "Region modifier follow-ups: 'and in Karnataka', 'what about Maharashtra'",
        "Status follow-ups: 'how many were approved', 'only the pending ones'",
        "Approval/status set follow-ups: 'among them approved', 'of those rejected'",
    ]
    for a in anaphora: story.append(B(a))

    # ══ 19. EXPORT & REPORTING ════════════════════════════════════════════════
    sec(19, "Export & Reporting Capabilities")
    export_items = [
        ("CSV Export","POST /export/csv — Generates a comma-separated values file from provided columns and data. "
         "Also supports direct SQL-to-CSV streaming via POST /export/sql-csv for large datasets. "
         "Files saved as reports/report_{id}.csv."),
        ("Excel Export","POST /export/excel — Generates a Microsoft Excel (.xlsx) file with headers and formatted data rows "
         "using openpyxl library. Files saved as reports/report_{id}.xlsx."),
        ("PDF Report Export","POST /export/pdf — Generates a formatted PDF report with title, timestamp, and data table "
         "using reportlab library. Files saved as reports/report_{id}.pdf."),
        ("Report Storage","All reports are saved to the /reports/ directory in the project root. "
         "They are accessible via the static file server at /reports/{filename}. "
         "Report URLs are returned in the API response report_urls field for direct user download."),
        ("Automatic Report Generation","Every successful /query response automatically generates CSV, Excel, and PDF "
         "reports and returns their download URLs — no extra API call needed."),
        ("CSV Streaming","For very large result sets, POST /export/csv supports chunked HTTP streaming "
         "via StreamingResponse to avoid memory exhaustion on the server."),
    ]
    for (t,d) in export_items:
        story.append(P(f"<b>► {t}</b>"))
        story.append(P(d))
        story.append(sp(4))

    # ══ 20. NON-FUNCTIONAL REQUIREMENTS ═══════════════════════════════════════
    sec(20, "Non-Functional Requirements")
    nfr_rows = [
        [Paragraph(h,STYLES["th"]) for h in ["ID","Requirement","Priority","Status"]],
        [P("NFR-01","tdc"), P("Response time for simple queries ≤10 seconds on local LLM (7B model on GPU); ≤3s on cloud GPU","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Monitored"],"td")],
        [P("NFR-02","tdc"), P("System must never expose or mutate production data — read-only at both DB user level and AST validator level","td"), P(PRIORITY["CRITICAL"],"td"), P(STATUS["Enforced"],"td")],
        [P("NFR-03","tdc"), P("All query failures must be logged with full pipeline trace (validation reason, retry attempts, error) for debugging","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-04","tdc"), P("Application must run 4 pre-flight diagnostic checks on startup and report failures before serving requests","td"), P(PRIORITY["MEDIUM"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-05","tdc"), P("System must support hot-reload development mode via WatchFiles (file changes trigger automatic server restart)","td"), P(PRIORITY["LOW"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-06","tdc"), P("LLM endpoint must be fully configurable via OLLAMA_BASE_URL environment variable — supports local and cloud GPU endpoints","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-07","tdc"), P("Database credentials must never appear in plaintext in source code, logs, or environment variables — AES-256 Fernet encrypted","td"), P(PRIORITY["CRITICAL"],"td"), P(STATUS["Enforced"],"td")],
        [P("NFR-08","tdc"), P("System must gracefully handle LLM unavailability: return informative error 'LLM is offline' instead of crashing","td"), P(PRIORITY["HIGH"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-09","tdc"), P("Export files must be UUID-stamped to avoid filename collisions for concurrent users","td"), P(PRIORITY["LOW"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-10","tdc"), P("Database schema must auto-update if schema drift is detected on startup — alert printed, knowledge base refreshed","td"), P(PRIORITY["MEDIUM"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-11","tdc"), P("Session memory must be fully isolated per session_id — no cross-session context leakage between users","td"), P(PRIORITY["CRITICAL"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-12","tdc"), P("All generated SQL must be validated before execution — no raw LLM output ever reaches the database directly","td"), P(PRIORITY["CRITICAL"],"td"), P(STATUS["Enforced"],"td")],
        [P("NFR-13","tdc"), P("System must support Incognito mode for sensitive sessions — suppress all query logging and audit recording","td"), P(PRIORITY["MEDIUM"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-14","tdc"), P("Reports directory must auto-create on startup if it does not exist","td"), P(PRIORITY["LOW"],"td"), P(STATUS["Implemented"],"td")],
        [P("NFR-15","tdc"), P("API response must always include a schema map to keep the frontend Schema Explorer panel current","td"), P(PRIORITY["LOW"],"td"), P(STATUS["Implemented"],"td")],
    ]
    story.append(table(nfr_rows, [BW*.09, BW*.6, BW*.15, BW*.16]))

    # ══ 21. KNOWN ISSUES ══════════════════════════════════════════════════════
    sec(21, "Known Issues & Bug Resolutions")
    story.append(P("The following bugs and configuration issues were identified and resolved during the development, "
        "testing, and production stabilisation phases of the Agentic Analyst v2.0 project."))
    story.append(sp(6))

    bugs = [
        ("BUG-01","LLM offline error despite Ollama running locally",
         "OLLAMA_BASE_URL in .env was pointing to an expired Pinggy tunnel URL (https://iknwj-35-221-156-60.free.pinggy.net). The tunnel had expired and the server was returning an HTML page instead of the expected JSON /api/tags response. The is_ollama_online() health check received an HTML response, failed JSON parsing, and returned False — causing every query to be blocked with 'LLM is offline'.",
         "Updated OLLAMA_BASE_URL in .env from the expired Pinggy tunnel URL to 'http://localhost:11434' — the local Ollama instance that was already running successfully on the machine.",
         "Resolved"),
        ("BUG-02","Empty SQL query error on every valid question",
         "The generate_sql() function in app/llm/sql_generator.py had the stop parameter set to ['```', 'Explanation:']. The system prompt explicitly told the LLM to write SQL inside ```sql``` code blocks. However, the moment the LLM started to type the ``` characters to open the code block, the stop token triggered and instantly cut off the LLM's response — before it could write a single character of SQL. The application received an empty string and raised the SQLValidationError 'LLM generated an empty query. Triggering self-correction retry...'",
         "Removed '```' from the stop tokens list in generate_sql() in app/llm/sql_generator.py. The stop list now only contains ['Explanation:'].",
         "Resolved"),
        ("BUG-03","E2E Validation ID check failing on specific ID queries",
         "The 10-point E2E Accuracy Validator (app/validator/e2e_accuracy_validator.py) checks that the specific_id value requested by the user appears in the generated SQL's WHERE clause. However, the NLP Understanding Agent was passing specific_id as a Python dictionary: {'value': '5997', 'type': 'distributor_id'}. The validator called str(specific_id) which converted the entire dictionary to a string literal \"{'value': '5997', 'type': 'distributor_id'}\". It then searched the SQL for '= {\"value\": \"5997\", ...}' which obviously didn't match the simple '= 5997' in the SQL. Every query with a specific distributor_id or retailer_id was blocked.",
         "Added an isinstance(specific_id, dict) check in the E2E validator. If specific_id is a dict with a 'value' key, extract the value first: str_id = str(specific_id['value']).strip(). Otherwise use str(specific_id) as before.",
         "Resolved"),
        ("BUG-04","Slow LLM response time on local hardware",
         "When running the Qwen2.5-Coder 7B model locally on a machine without a discrete NVIDIA GPU (e.g., Intel integrated graphics), LLM inference is extremely slow — queries can take 30-120+ seconds because the model runs on CPU. The previous cloud GPU setup (Kaggle/Colab via Pinggy) was approximately 10x faster.",
         "Documented. Solution: Restart a Kaggle/Colab notebook with GPU, run Ollama, expose via Pinggy/LocalTunnel, copy the new URL into OLLAMA_BASE_URL in .env, and restart the server. Alternatively, use RunPod or AWS EC2 g4dn for persistent GPU inference.",
         "Documented"),
        ("BUG-05","'str' object has no attribute 'get' error during server startup",
         "After the E2E validator fix (BUG-03), a related runtime error 'str object has no attribute get' appeared in the server logs during startup. This was caused by a different path where specific_id was already correctly a string but downstream code was calling .get() on it expecting a dict.",
         "Investigating — WatchFiles detected the change and reloaded the server automatically. The issue is related to mixed data types of specific_id across different pipeline stages.",
         "Investigating"),
    ]

    for (bid, title, cause, resolution, status2) in bugs:
        bug_tbl = [
            [Paragraph("Bug ID", STYLES["tdb"]), Paragraph(bid, STYLES["td"])],
            [Paragraph("Title", STYLES["tdb"]), Paragraph(title, STYLES["td"])],
            [Paragraph("Root Cause", STYLES["tdb"]), Paragraph(cause, STYLES["td"])],
            [Paragraph("Resolution", STYLES["tdb"]), Paragraph(resolution, STYLES["td"])],
            [Paragraph("Status", STYLES["tdb"]), Paragraph(STATUS.get(status2, status2), STYLES["td"])],
        ]
        bt = Table(bug_tbl, colWidths=[BW*.16, BW*.84])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(0,-1), LIGHT),
            ("GRID", (0,0),(-1,-1), 0.4, BORDER),
            ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6), ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ]))
        story.append(bt)
        story.append(sp(8))

    # ══ 22. DEPLOYMENT ════════════════════════════════════════════════════════
    sec(22, "Deployment Architecture")
    sub("Pre-Flight Diagnostic Checks (run_diagnostics)")
    story.append(P("On every server start, start_server.py runs 4 mandatory diagnostic checks:"))
    diag = [
        "[1/4] Python Environment — Verifies Python version (requires 3.13+)",
        "[2/4] Credentials & Encryption — Verifies .master.key and .env files exist",
        "[3/4] Database Pool — Tests MySQL connectivity by executing SELECT 1",
        "[4/4] LLM Engine — Tests Ollama availability at configured OLLAMA_BASE_URL",
    ]
    for d in diag: story.append(B(d))
    story.append(sp(6))

    sub("Local Development Setup (Step-by-Step)")
    local_steps = [
        ("Step 1 — Clone repository", "git clone <repository_url> && cd Agent"),
        ("Step 2 — Create virtual environment", "python -m venv venv && venv\\Scripts\\activate (Windows)"),
        ("Step 3 — Install dependencies", "pip install -r requirements.txt"),
        ("Step 4 — Install Ollama", "Download from https://ollama.ai and install. Ollama runs as a local service on port 11434."),
        ("Step 5 — Pull LLM model", "ollama run qwen2.5-coder:7b (downloads ~4.68 GB Q4_K_M model)"),
        ("Step 6 — Configure .env", "Set ENCRYPTED_DB_CONFIG (AES-256 encrypted DB credentials) and OLLAMA_BASE_URL=http://localhost:11434"),
        ("Step 7 — Place master key", "Copy .master.key to project root (contains Fernet decryption key for DB credentials)"),
        ("Step 8 — Start server", "python start_server.py → Server starts at http://localhost:8000"),
        ("Step 9 — Access UI", "Open http://localhost:8000 in browser → JGH Intelligence Engine interface"),
    ]
    ls_data = [[Paragraph(s,STYLES["tdb"]), Paragraph(c,STYLES["td"])] for s,c in local_steps]
    ls_data.insert(0, [Paragraph("Step",STYLES["th"]), Paragraph("Command / Action",STYLES["th"])])
    story.append(table(ls_data, [BW*.25, BW*.75]))
    story.append(sp(8))

    sub("Cloud GPU Setup (High-Performance Mode)")
    cloud = [
        ("Step 1 — Start Kaggle/Colab", "Create new notebook with GPU accelerator (T4 or P100) and enable Internet."),
        ("Step 2 — Install Ollama", "!curl -fsSL https://ollama.com/install.sh | sh"),
        ("Step 3 — Start Ollama", "subprocess.Popen(['ollama', 'serve']); time.sleep(5)"),
        ("Step 4 — Pull model", "!ollama run qwen2.5-coder:7b"),
        ("Step 5 — Install LocalTunnel / Pinggy", "!npm install -g localtunnel OR use Pinggy (https://pinggy.io)"),
        ("Step 6 — Expose port", "!lt --port 11434 → Note the HTTPS tunnel URL generated (e.g., https://xyz.pinggy.io)"),
        ("Step 7 — Update .env", "Set OLLAMA_BASE_URL='https://xyz.pinggy.io' in .env on local machine"),
        ("Step 8 — Restart server", "Ctrl+C to stop server, then python start_server.py to restart with new URL"),
    ]
    cd_data = [[Paragraph(s,STYLES["tdb"]), Paragraph(c,STYLES["td"])] for s,c in cloud]
    cd_data.insert(0, [Paragraph("Step",STYLES["th"]), Paragraph("Action",STYLES["th"])])
    story.append(table(cd_data, [BW*.2, BW*.8]))
    story.append(sp(8))

    sub("Docker Deployment")
    story.append(P("The project includes Dockerfile and docker-compose.yml for containerized deployment:"))
    story.append(B("docker-compose.yml defines: FastAPI app container + optional MySQL container"))
    story.append(B("Build: docker-compose build"))
    story.append(B("Start: docker-compose up -d"))
    story.append(B("Note: Ollama must still be configured separately (external GPU server recommended for production)"))
    story.append(sp(6))

    sub("Production Deployment Recommendations")
    prod = [
        "Replace Pinggy/LocalTunnel with RunPod, AWS EC2 (g4dn instances), or Vultr GPU for 24/7 stable inference",
        "Secure Ollama with Nginx reverse proxy + HTTPS + Basic Auth or VPN (Tailscale/ZeroTier)",
        "Restrict FastAPI CORS allow_origins to specific production frontend domain",
        "Deploy FastAPI with Gunicorn + multiple Uvicorn worker processes for concurrent user support",
        "Use a dedicated MySQL read-replica for analytics to avoid impacting production write performance",
        "Set up log rotation for query_audit_history.json and audit logs to prevent unbounded disk growth",
        "Configure environment variables via proper secrets manager (AWS Secrets Manager, HashiCorp Vault) instead of .env in production",
        "Enable health check monitoring (e.g., UptimeRobot) for /health and /api/llm/health endpoints",
    ]
    for p in prod: story.append(B(p))

    # ══ 23. ROADMAP ═══════════════════════════════════════════════════════════
    sec(23, "Future Roadmap & Enhancements")
    road = [
        ("Persistent Cache Layer","Replace in-memory cache with Redis for persistent cross-session query result caching — dramatically reduces LLM calls for repeated common queries."),
        ("Multi-User Authentication","Add JWT-based user authentication so each user has their own authenticated session, role-based access control, and personalized query history."),
        ("Query Suggestion Engine","Proactively suggest follow-up queries based on the current result set and user history — displayed as clickable chips in the UI."),
        ("Data Visualization","Add automatic chart generation (bar charts, line graphs, pie charts) for aggregation results using Chart.js or Plotly embedded in the frontend."),
        ("Larger LLM Model","Upgrade to Qwen2.5-Coder 14B or 32B for improved SQL accuracy on complex multi-join, multi-filter queries, especially in edge cases."),
        ("Persistent GPU Deployment","Deploy Ollama on RunPod or AWS EC2 GPU instance for always-on, low-latency LLM inference without Kaggle/Colab session limitations."),
        ("Streaming Response","Implement server-sent events (SSE) to stream the LLM response tokens to the frontend in real-time — improving perceived responsiveness."),
        ("Multi-Language Support","Add support for regional Indian languages (Hindi, Marathi, Kannada) for NLP question input to make the tool accessible to more business users."),
        ("Query Scheduling","Allow users to schedule recurring queries (e.g., daily earnings report at 9 AM) with automatic email/WhatsApp delivery."),
        ("Benchmarking Dashboard","Build an internal performance dashboard showing LLM latency, validation success rates, retry rates, and most queried entities."),
        ("Integration with BI Tools","Export query results directly to Google Sheets, Power BI, or Tableau via API connector for advanced visualization and reporting."),
    ]
    for (t,d) in road:
        story.append(P(f"<b>◆  {t}</b>"))
        story.append(P(d))
        story.append(sp(4))

    # ══ 24. GLOSSARY ══════════════════════════════════════════════════════════
    sec(24, "Glossary & Definitions")
    glossary = [
        ("Agentic Analyst","The AI-powered analytics platform built for JGH Enterprises that converts natural language questions into SQL database queries and returns formatted results."),
        ("JGH Intelligence Engine","Internal branding name for the Agentic Analyst system."),
        ("NLP","Natural Language Processing — the AI capability to understand human language questions and extract structured meaning from them."),
        ("LLM","Large Language Model — the AI model (Qwen2.5-Coder 7B) used to understand natural language and generate SQL queries."),
        ("Ollama","An open-source framework for running LLMs locally on a machine (CPU or GPU) without cloud dependency. Also provides an API compatible with OpenAI format."),
        ("Qwen2.5-Coder 7B","A 7.6-billion parameter open-source AI code model by Alibaba Cloud, specialized in code generation (SQL, Python, etc.). Quantized to Q4_K_M (4.68 GB)."),
        ("AST","Abstract Syntax Tree — a structured parse tree representation of SQL code. Used by sqlglot to validate SQL structure, detect forbidden operations, and verify column existence."),
        ("RAG","Retrieval-Augmented Generation — a technique that enriches LLM prompts with relevant retrieved context (schema information, business rules, past SQL examples) to improve accuracy."),
        ("BusinessRequirement","The Pydantic data model (22 fields) that represents the structured, canonical output of the NLP Understanding phase. It captures intent, entities, specific IDs, metrics, filters, date periods, grouping, sorting, and output format."),
        ("E2E Validation","End-to-End Accuracy Validation — the 10-point post-execution check that validates the complete chain from user intent through to the actual result rows."),
        ("Self-Correction","The automatic retry mechanism where the system feeds specific validation failure reasons back to the LLM in the next prompt attempt, allowing it to correct its mistake."),
        ("Context Resolver","The component that manages multi-turn conversation continuity by merging active session memory with new query intent using inheritance, replacement, and reset rules."),
        ("FastAPI","A modern, high-performance Python web framework for building REST APIs. Used as the HTTP server and API gateway for the application."),
        ("Uvicorn","An ASGI (Asynchronous Server Gateway Interface) server implementation for Python. Runs the FastAPI application."),
        ("ChromaDB","An open-source vector database used to store and retrieve SQL history examples using semantic similarity (embeddings). Powers the RAG few-shot example retrieval."),
        ("Fernet","A symmetric encryption algorithm (AES-256 in CBC mode) from the Python cryptography library. Used to encrypt database credentials in the .env file."),
        ("Pinggy / LocalTunnel / Ngrok","Tunnel tools that expose a local port (e.g., 11434) to a public HTTPS URL. Used to connect the local application to a cloud GPU running Ollama."),
        ("jghMasterDB","The production MySQL database of JGH Enterprises containing all business data: users, transactions, inventory, withdrawals, and master data."),
        ("distributer_id","The column in the users table that stores which distributor a user (retailer, wholesaler, etc.) belongs to. Note: intentionally spelled with one 't' — legacy schema naming."),
        ("TARGET_SCOPE_TABLES","The allowlist of database tables (defined in app/database/allowed_tables.py) that the AI is permitted to query. Queries targeting other tables are rejected."),
        ("EXPLAIN","A MySQL command that returns the query execution plan for a SELECT statement without actually executing it. Used for query validation and cost estimation."),
        ("Incognito Mode","A query mode (is_private=True or incognito=True) where query logging and audit recording are suppressed. Results are returned normally."),
        ("Schema Drift","A change in the database schema (e.g., new column added, table renamed) that differs from the cached schema_metadata.json. Detected on every server startup."),
        ("BRD","Business Requirements Document — this document. A formal specification of the project's business context, requirements, architecture, and design decisions."),
    ]
    gl_data = [[Paragraph("Term",STYLES["th"]), Paragraph("Definition",STYLES["th"])]]
    gl_data += [[Paragraph(t,STYLES["tdb"]), Paragraph(d,STYLES["td"])] for t,d in glossary]
    story.append(table(gl_data, [BW*.26, BW*.74]))

    # ══ 25. SIGN-OFF ══════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(sp(20))
    story.append(Paragraph("Document Sign-Off & Approval", ParagraphStyle("so_h", fontName="Helvetica-Bold",
        fontSize=16, textColor=NAVY, alignment=TA_CENTER, spaceAfter=10)))
    story.append(div())
    story.append(sp(15))

    so_data = [
        [Paragraph(h,STYLES["th"]) for h in ["Role","Name","Organisation","Signature","Date"]],
        [P("Developer / Owner","td"), P("","td"), P("JGH Enterprises","td"), P("____________________","tdc"), P(datetime.now().strftime("%B %d, %Y"),"tdc")],
        [P("Technical Reviewer","td"), P("","td"), P("","td"), P("____________________","tdc"), P("","tdc")],
        [P("QA / Testing Lead","td"), P("","td"), P("","td"), P("____________________","tdc"), P("","tdc")],
        [P("Product / Business Owner","td"), P("","td"), P("JGH Enterprises","td"), P("____________________","tdc"), P("","tdc")],
        [P("IT / DBA Sign-Off","td"), P("","td"), P("","td"), P("____________________","tdc"), P("","tdc")],
        [P("Security & Compliance","td"), P("","td"), P("","td"), P("____________________","tdc"), P("","tdc")],
    ]
    st = Table(so_data, colWidths=[BW*.2, BW*.2, BW*.18, BW*.22, BW*.2])
    st.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),WHITE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),
        ("GRID",(0,0),(-1,-1),0.5,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,STRIPE]),
        ("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12),
        ("LEFTPADDING",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(st)
    story.append(sp(30))
    story.append(P(
        f"Auto-generated on {datetime.now().strftime('%B %d, %Y at %H:%M IST')}  •  "
        "Agentic Analyst v2.0  •  JGH Intelligence Engine  •  CONFIDENTIAL — INTERNAL USE ONLY",
        "meta"))

    # ── BUILD ──────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=draw_cover, onLaterPages=draw_header_footer)
    print(f"[SUCCESS] Complete BRD generated: {path}")
    return path


if __name__ == "__main__":
    build()
