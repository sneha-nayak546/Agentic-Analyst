"""
BRD Generator for Agentic Analyst - JGH Intelligence Engine
Generates a professional, beautiful PDF Business Requirements Document
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon, Path
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.platypus import Image
from datetime import datetime
import os

# ─── BRAND COLORS ──────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0D1B3E")   # Deep navy
COBALT     = colors.HexColor("#1A56DB")   # Primary blue
SKY        = colors.HexColor("#60A5FA")   # Light blue accent
TEAL       = colors.HexColor("#0EA5E9")   # Teal
GOLD       = colors.HexColor("#F59E0B")   # Gold
SILVER     = colors.HexColor("#94A3B8")   # Silver
LIGHT_BG   = colors.HexColor("#F0F6FF")   # Light blue bg
DARK_BG    = colors.HexColor("#1E293B")   # Dark section bg
SUCCESS    = colors.HexColor("#10B981")   # Green
WHITE      = colors.white
BLACK      = colors.HexColor("#0F172A")   # Almost black text
SUBTLE_LINE= colors.HexColor("#CBD5E1")   # Subtle border
SECTION_BG = colors.HexColor("#EFF6FF")   # Section background

W, H = A4

def build_styles():
    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=30,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=38,
        spaceAfter=8,
    )
    styles["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle",
        fontName="Helvetica",
        fontSize=13,
        textColor=colors.HexColor("#93C5FD"),
        alignment=TA_CENTER,
        leading=18,
    )
    styles["cover_tag"] = ParagraphStyle(
        "cover_tag",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=GOLD,
        alignment=TA_CENTER,
        leading=14,
        spaceBefore=4,
    )
    styles["h1"] = ParagraphStyle(
        "h1",
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=WHITE,
        leading=24,
        spaceBefore=0,
        spaceAfter=4,
    )
    styles["h2"] = ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=COBALT,
        leading=18,
        spaceBefore=10,
        spaceAfter=4,
    )
    styles["h3"] = ParagraphStyle(
        "h3",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        textColor=NAVY,
        leading=14,
        spaceBefore=6,
        spaceAfter=3,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=BLACK,
        leading=14,
        spaceAfter=4,
        alignment=TA_JUSTIFY,
    )
    styles["body_bold"] = ParagraphStyle(
        "body_bold",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        textColor=BLACK,
        leading=14,
        spaceAfter=2,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=BLACK,
        leading=14,
        leftIndent=16,
        bulletIndent=4,
        spaceAfter=2,
    )
    styles["sub_bullet"] = ParagraphStyle(
        "sub_bullet",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        leading=13,
        leftIndent=30,
        bulletIndent=16,
        spaceAfter=1,
    )
    styles["table_header"] = ParagraphStyle(
        "table_header",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=12,
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=BLACK,
        leading=12,
    )
    styles["caption"] = ParagraphStyle(
        "caption",
        fontName="Helvetica",
        fontSize=8,
        textColor=SILVER,
        alignment=TA_CENTER,
        leading=12,
        spaceBefore=2,
    )
    styles["toc_item"] = ParagraphStyle(
        "toc_item",
        fontName="Helvetica",
        fontSize=10,
        textColor=COBALT,
        leading=18,
        leftIndent=20,
    )
    styles["toc_number"] = ParagraphStyle(
        "toc_number",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=NAVY,
        leading=18,
    )
    styles["meta"] = ParagraphStyle(
        "meta",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        leading=14,
        alignment=TA_CENTER,
    )
    styles["code"] = ParagraphStyle(
        "code",
        fontName="Courier",
        fontSize=8.5,
        textColor=colors.HexColor("#1E40AF"),
        leading=13,
        leftIndent=12,
        backColor=LIGHT_BG,
    )
    return styles


# ─── CUSTOM FLOWABLES ──────────────────────────────────────────────────────────
class SectionHeader(Flowable):
    """Dark navy section header banner"""
    def __init__(self, number, title, width=None):
        Flowable.__init__(self)
        self.number = number
        self.title = title
        self.bw = width or (W - 2.4 * inch)
        self.height = 32

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(NAVY)
        c.roundRect(0, 0, self.bw, self.height, 6, fill=1, stroke=0)
        # Gold accent bar
        c.setFillColor(GOLD)
        c.rect(0, 0, 5, self.height, fill=1, stroke=0)
        # Number badge
        c.setFillColor(COBALT)
        c.circle(22, self.height / 2, 10, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(22, self.height / 2 - 3.5, str(self.number))
        # Title
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, self.height / 2 - 4.5, self.title.upper())

    def wrap(self, avW, avH):
        return self.bw, self.height


class SubSectionHeader(Flowable):
    """Cobalt left-border subsection header"""
    def __init__(self, title, width=None):
        Flowable.__init__(self)
        self.title = title
        self.bw = width or (W - 2.4 * inch)
        self.height = 22

    def draw(self):
        c = self.canv
        c.setFillColor(SECTION_BG)
        c.roundRect(0, 0, self.bw, self.height, 4, fill=1, stroke=0)
        c.setFillColor(COBALT)
        c.rect(0, 0, 4, self.height, fill=1, stroke=0)
        c.setFillColor(COBALT)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(14, 6, self.title)

    def wrap(self, avW, avH):
        return self.bw, self.height


class HorizontalDivider(Flowable):
    def __init__(self, width=None, color=SUBTLE_LINE):
        Flowable.__init__(self)
        self.bw = width or (W - 2.4 * inch)
        self.color = color
        self.height = 1

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 0, self.bw, 0)

    def wrap(self, avW, avH):
        return self.bw, 4


def draw_cover_page(canvas, doc):
    """Draw the full-page cover — called as onFirstPage callback"""
    c = canvas
    c.saveState()

    # Dark navy background
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Gradient overlay
    for i in range(40):
        alpha = i / 40.0
        col = colors.HexColor(
            "#{:02x}{:02x}{:02x}".format(
                int(13 + (26 - 13) * alpha),
                int(27 + (86 - 27) * alpha),
                int(62 + (219 - 62) * alpha)
            )
        )
        c.setFillColor(col)
        c.rect(0, H * (i / 40.0), W, H / 40.0 + 1, fill=1, stroke=0)

    # Decorative circles
    for (cx2, cy2, r, a) in [
        (W * 0.9, H * 0.85, 160, 0.06),
        (W * 0.85, H * 0.80, 100, 0.1),
        (W * 0.05, H * 0.2, 120, 0.07),
        (W * 0.15, H * 0.15, 60, 0.1),
    ]:
        c.setFillColorRGB(0.1, 0.33, 0.86, alpha=a)
        c.circle(cx2, cy2, r, fill=1, stroke=0)

    # Gold top bar
    c.setFillColor(GOLD)
    c.rect(0, H - 8, W, 8, fill=1, stroke=0)

    # Bottom accent bar
    c.setFillColor(COBALT)
    c.rect(0, 0, W, 5, fill=1, stroke=0)

    # Logo monogram
    lx, ly = W / 2, H * 0.72
    c.setFillColor(COBALT)
    c.circle(lx, ly, 45, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#2563EB"))
    c.setLineWidth(2)
    c.circle(lx, ly, 40, fill=0, stroke=1)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(lx, ly - 8, "JGH")
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#93C5FD"))
    c.drawCentredString(lx, ly + 26, "INTELLIGENCE ENGINE")

    # Main title
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(WHITE)
    c.drawCentredString(W / 2, H * 0.56, "AGENTIC ANALYST")
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#93C5FD"))
    c.drawCentredString(W / 2, H * 0.52, "Business Requirements Document")

    # Gold divider
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(W / 2 - 80, H * 0.49, W / 2 + 80, H * 0.49)

    # Tagline
    c.setFont("Helvetica", 10)
    c.setFillColor(GOLD)
    c.drawCentredString(W / 2, H * 0.46, "Enterprise AI-Powered Natural Language SQL Agent")

    # Meta block
    meta_y = H * 0.30
    meta_items = [
        ("DOCUMENT TYPE", "BRD – Business Requirements Document"),
        ("PROJECT", "Agentic Analyst / JGH Intelligence Engine"),
        ("VERSION", "v2.0 – Production Release"),
        ("DATE", datetime.now().strftime("%B %d, %Y")),
        ("STATUS", "Approved for Production"),
        ("CLASSIFICATION", "CONFIDENTIAL – Internal Use Only"),
    ]
    box_w = 340
    box_h = len(meta_items) * 20 + 20
    bx = (W - box_w) / 2
    by = meta_y - box_h + 10
    c.setFillColor(colors.HexColor("#0F2050"))
    c.roundRect(bx, by, box_w, box_h, 6, fill=1, stroke=0)
    c.setStrokeColor(COBALT)
    c.setLineWidth(0.8)
    c.roundRect(bx, by, box_w, box_h, 6, fill=0, stroke=1)

    y = meta_y
    for label, value in meta_items:
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(GOLD)
        c.drawString(bx + 16, y - 4, label + ":")
        c.setFont("Helvetica", 7.5)
        c.setFillColor(WHITE)
        c.drawString(bx + 130, y - 4, value)
        y -= 20

    # Footer
    c.setFont("Helvetica", 7)
    c.setFillColor(SILVER)
    c.drawCentredString(W / 2, 20, "CONFIDENTIAL  •  JGH Enterprise Analytics  •  © 2026  •  All Rights Reserved")

    c.restoreState()


class SystemArchDiagram(Flowable):
    """Horizontal system architecture flowchart"""
    def __init__(self, width=None):
        Flowable.__init__(self)
        self.bw = width or (W - 2.4 * inch)
        self.height = 260

    def _box(self, c, x, y, w, h, bg, label, sublabel="", radius=6, text_col=WHITE):
        c.setFillColor(bg)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=0)
        c.setFillColor(text_col)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(x + w / 2, y + h / 2 + (5 if sublabel else 0), label)
        if sublabel:
            c.setFont("Helvetica", 6.5)
            c.setFillColor(colors.HexColor("#CBD5E1") if text_col == WHITE else SILVER)
            c.drawCentredString(x + w / 2, y + h / 2 - 7, sublabel)

    def _arrow(self, c, x1, y1, x2, y2, color=COBALT):
        c.setStrokeColor(color)
        c.setLineWidth(1.5)
        c.line(x1, y1, x2, y2)
        # Arrowhead
        import math
        angle = math.atan2(y2 - y1, x2 - x1)
        size = 6
        c.setFillColor(color)
        p = c.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(x2 - size * math.cos(angle - 0.4), y2 - size * math.sin(angle - 0.4))
        p.lineTo(x2 - size * math.cos(angle + 0.4), y2 - size * math.sin(angle + 0.4))
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    def draw(self):
        c = self.canv
        bw = self.bw
        bh = self.height

        # Background
        c.setFillColor(colors.HexColor("#F8FAFF"))
        c.roundRect(0, 0, bw, bh, 8, fill=1, stroke=0)
        c.setStrokeColor(SUBTLE_LINE)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, bw, bh, 8, fill=0, stroke=1)

        # Title
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(NAVY)
        c.drawCentredString(bw / 2, bh - 16, "SYSTEM ARCHITECTURE — AGENTIC ANALYST PIPELINE")

        # ── Layer 1: Frontend ─────────────────────────────────────────────
        self._box(c, 5, bh - 70, 60, 40, COBALT, "FRONTEND", "React UI")

        # ── Layer 2: FastAPI Gateway ──────────────────────────────────────
        self._box(c, 75, bh - 70, 65, 40, NAVY, "FASTAPI", "API Gateway")
        self._arrow(c, 65, bh - 50, 75, bh - 50)

        # ── Layer 3: Agent Pipeline (tall) ────────────────────────────────
        agent_x = 150
        c.setFillColor(colors.HexColor("#EFF6FF"))
        c.roundRect(agent_x - 5, bh - 195, 140, 165, 6, fill=1, stroke=0)
        c.setStrokeColor(COBALT)
        c.setLineWidth(0.8)
        c.roundRect(agent_x - 5, bh - 195, 140, 165, 6, fill=0, stroke=1)
        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(COBALT)
        c.drawCentredString(agent_x + 65, bh - 45, "AI AGENT PIPELINE")

        self._arrow(c, 140, bh - 50, agent_x, bh - 50)

        # Agent blocks (stacked vertically)
        sub_boxes = [
            (agent_x, bh - 80,  colors.HexColor("#1D4ED8"), "NLP Understanding", "Qwen 2.5 7B"),
            (agent_x, bh - 110, colors.HexColor("#2563EB"), "Context Resolver", "Memory"),
            (agent_x, bh - 140, colors.HexColor("#3B82F6"), "SQL Generator", "LLM + Det"),
            (agent_x, bh - 170, colors.HexColor("#60A5FA"), "Validator Layer", "AST + E2E"),
        ]
        for (bx, by, bg, lbl, sub) in sub_boxes:
            self._box(c, bx, by, 130, 24, bg, lbl, sub)

        # down arrows between stacked boxes
        for by in [bh - 86, bh - 116, bh - 146]:
            c.setStrokeColor(SKY)
            c.setLineWidth(1)
            c.line(agent_x + 65, by, agent_x + 65, by - 6)

        # ── Layer 4: LLM / Knowledge ──────────────────────────────────────
        self._arrow(c, agent_x + 140, bh - 130, agent_x + 150, bh - 130)

        llm_x = agent_x + 150
        self._box(c, llm_x, bh - 100, 65, 35, colors.HexColor("#7C3AED"), "OLLAMA", "qwen2.5:7b")
        self._box(c, llm_x, bh - 155, 65, 35, colors.HexColor("#0891B2"), "KNOWLEDGE", "Schema")
        self._box(c, llm_x, bh - 210, 65, 35, colors.HexColor("#065F46"), "HISTORY", "RAG")

        # arrows to LLM/knowledge
        for by in [bh - 82, bh - 137, bh - 192]:
            self._arrow(c, llm_x - 0, bh - 130, llm_x, by + 17)

        # ── Layer 5: MySQL DB ─────────────────────────────────────────────
        db_x = llm_x + 75
        self._arrow(c, agent_x + 140, bh - 158, db_x, bh - 158)
        self._box(c, db_x, bh - 175, 60, 40, colors.HexColor("#B45309"), "MySQL DB", "MasterDB")

        # ── Layer 6: Outputs ──────────────────────────────────────────────
        out_x = db_x + 70
        self._arrow(c, db_x + 60, bh - 155, out_x, bh - 155)

        out_items = [
            (bh - 90, SUCCESS, "JSON API"),
            (bh - 125, GOLD, "CSV / Excel"),
            (bh - 160, colors.HexColor("#DB2777"), "PDF Report"),
            (bh - 195, colors.HexColor("#7C3AED"), "Dashboard"),
        ]
        for (oy, oc, ol) in out_items:
            self._box(c, out_x, oy, 50, 22, oc, ol)
            if oy != bh - 90:
                c.setStrokeColor(SUBTLE_LINE)
                c.setLineWidth(0.5)
                c.line(out_x + 35, oy + 22, out_x + 35, oy + 26)

        # Legend
        legend_y = 14
        items = [("User Layer", COBALT), ("Agent Pipeline", colors.HexColor("#3B82F6")),
                 ("LLM / Knowledge", colors.HexColor("#7C3AED")),
                 ("Data Store", colors.HexColor("#B45309")), ("Output", SUCCESS)]
        lx = 10
        for (lbl, lc) in items:
            c.setFillColor(lc)
            c.rect(lx, legend_y, 10, 10, fill=1, stroke=0)
            c.setFillColor(BLACK)
            c.setFont("Helvetica", 6.5)
            c.drawString(lx + 13, legend_y + 1, lbl)
            lx += 80

    def wrap(self, avW, avH):
        return self.bw, self.height


class InfographicBar(Flowable):
    """A horizontal progress/stat bar"""
    def __init__(self, label, value, max_val, color, width=None):
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.max_val = max_val
        self.color = color
        self.bw = width or (W - 2.4 * inch)
        self.height = 22

    def draw(self):
        c = self.canv
        c.setFont("Helvetica", 8.5)
        c.setFillColor(BLACK)
        c.drawString(0, 6, self.label)
        bar_x = 150
        bar_w = self.bw - 150 - 50
        pct = min(self.value / self.max_val, 1.0)
        c.setFillColor(SUBTLE_LINE)
        c.roundRect(bar_x, 4, bar_w, 12, 4, fill=1, stroke=0)
        c.setFillColor(self.color)
        c.roundRect(bar_x, 4, bar_w * pct, 12, 4, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(self.color)
        c.drawRightString(self.bw, 6, str(self.value))

    def wrap(self, avW, avH):
        return self.bw, self.height


# ─── MAIN BUILDER ─────────────────────────────────────────────────────────────
def build_brd():
    out_path = "reports/Agentic_Analyst_BRD.pdf"
    os.makedirs("reports", exist_ok=True)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=1.2 * inch,
        rightMargin=1.2 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title="Agentic Analyst – Business Requirements Document",
        author="JGH Intelligence Engine",
        subject="BRD v2.0",
    )

    S = build_styles()
    story = []
    bw = W - 2.4 * inch

    def sp(n=6): return Spacer(1, n)
    def h1(t): return Paragraph(t, S["h1"])
    def h2(t): return Paragraph(t, S["h2"])
    def h3(t): return Paragraph(t, S["h3"])
    def body(t): return Paragraph(t, S["body"])
    def bbold(t): return Paragraph(t, S["body_bold"])
    def bullet(t): return Paragraph(f"• {t}", S["bullet"])
    def sbullet(t): return Paragraph(f"◦  {t}", S["sub_bullet"])
    def caption(t): return Paragraph(t, S["caption"])
    def divider(): return HorizontalDivider(bw)

    def section(num, title):
        story.append(sp(14))
        story.append(SectionHeader(num, title, bw))
        story.append(sp(10))

    def subsection(title):
        story.append(sp(8))
        story.append(SubSectionHeader(title, bw))
        story.append(sp(5))

    def meta_table(data):
        """Small two-column info table"""
        tdata = [[Paragraph(k, S["body_bold"]), Paragraph(v, S["body"])] for k, v in data]
        t = Table(tdata, colWidths=[bw * 0.3, bw * 0.7])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
            ("BACKGROUND", (1, 0), (1, -1), WHITE),
            ("TEXTCOLOR", (0, 0), (-1, -1), BLACK),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, WHITE]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    def req_table(rows):
        """Requirements table"""
        header = [Paragraph(h, S["table_header"]) for h in ["REQ ID", "Requirement", "Priority", "Status"]]
        tdata = [header]
        for r in rows:
            tdata.append([
                Paragraph(r[0], S["table_cell"]),
                Paragraph(r[1], S["table_cell"]),
                Paragraph(r[2], S["table_cell"]),
                Paragraph(r[3], S["table_cell"]),
            ])
        t = Table(tdata, colWidths=[bw * 0.12, bw * 0.58, bw * 0.15, bw * 0.15])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return t

    def priority_badge(p):
        c = {"HIGH": SUCCESS, "MEDIUM": GOLD, "LOW": SILVER, "CRITICAL": colors.HexColor("#DC2626")}.get(p, COBALT)
        return f'<font color="{c.hexval() if hasattr(c, "hexval") else "#1A56DB"}">{p}</font>'

    # ─── COVER PAGE: drawn via onFirstPage callback ───────────────────────────
    # First page is a blank spacer; cover is drawn by draw_cover_page()
    story.append(PageBreak())

    # ─── TABLE OF CONTENTS ───────────────────────────────────────────────────
    story.append(sp(10))
    story.append(Paragraph("TABLE OF CONTENTS", ParagraphStyle("toc_title",
        fontName="Helvetica-Bold", fontSize=16, textColor=NAVY, alignment=TA_CENTER, spaceAfter=14)))
    story.append(divider())
    story.append(sp(8))

    toc_entries = [
        ("1", "Executive Summary"),
        ("2", "Project Overview"),
        ("3", "Business Objectives & Goals"),
        ("4", "System Architecture"),
        ("5", "Functional Requirements"),
        ("6", "Technical Components"),
        ("7", "Data Architecture & Database Schema"),
        ("8", "Security & Compliance"),
        ("9", "Validation & Quality Assurance"),
        ("10", "API Endpoints & Integration"),
        ("11", "Non-Functional Requirements"),
        ("12", "Known Issues & Resolutions"),
        ("13", "Deployment Architecture"),
        ("14", "Glossary & Definitions"),
    ]
    toc_data = []
    for (num, title) in toc_entries:
        toc_data.append([
            Paragraph(f"{num}.", S["toc_number"]),
            Paragraph(title, S["toc_item"]),
            Paragraph("· · · · · · · · · · · · · · · · · · ·", ParagraphStyle("dots",
                fontName="Helvetica", fontSize=9, textColor=SUBTLE_LINE, alignment=TA_RIGHT)),
        ])
    t = Table(toc_data, colWidths=[bw * 0.06, bw * 0.6, bw * 0.34])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ─── SECTION 1: EXECUTIVE SUMMARY ────────────────────────────────────────
    section(1, "Executive Summary")
    story.append(body(
        "The <b>Agentic Analyst</b> — internally branded as the <b>JGH Intelligence Engine</b> — is a "
        "production-grade, enterprise AI-powered natural language analytics platform built for JGH Enterprises. "
        "The system enables business users, analysts, and operations teams to query live MySQL business data "
        "using plain English, without writing a single line of SQL code."
    ))
    story.append(sp(6))
    story.append(body(
        "The platform operates as a fully automated, multi-step AI pipeline: it understands user intent, "
        "constructs accurate SQL queries, validates them through multiple layers of safety and accuracy "
        "checking, executes them against the live production database, and returns beautifully formatted "
        "tabular results, charts, and downloadable reports — all within seconds."
    ))
    story.append(sp(8))

    ks_data = [
        ["Key Statistic", "Value"],
        ["Technology Stack", "Python 3.13 + FastAPI + Ollama + MySQL"],
        ["AI Model", "Qwen2.5-Coder 7B (Local + Cloud GPU support)"],
        ["Database", "jghMasterDB — Production MySQL"],
        ["Tables in Scope", "50+ enterprise business tables"],
        ["API Version", "v2.0 — Production Release"],
        ["Validation Layers", "10-Point E2E Accuracy Validation"],
        ["Export Formats", "JSON, CSV, Excel, PDF"],
        ["Session Memory", "Conversational Context Resolver"],
    ]
    kt = Table(ks_data, colWidths=[bw * 0.45, bw * 0.55])
    kt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(kt)

    # ─── SECTION 2: PROJECT OVERVIEW ─────────────────────────────────────────
    section(2, "Project Overview")
    story.append(meta_table([
        ("Project Name", "Agentic Analyst — JGH Intelligence Engine"),
        ("Owner", "JGH Enterprises — Analytics & Technology Division"),
        ("Developer", "[Confidential]"),
        ("Document Version", "v2.0"),
        ("Date", datetime.now().strftime("%B %d, %Y")),
        ("Status", "Production Active"),
        ("Server URL", "http://localhost:8000"),
        ("LLM Model", "Qwen2.5-Coder 7B (via Ollama)"),
        ("Database", "jghMasterDB — MySQL Production"),
        ("LLM Endpoint", "http://localhost:11434 (Local) / Pinggy Tunnel (Cloud GPU)"),
    ]))

    # ─── SECTION 3: BUSINESS OBJECTIVES ──────────────────────────────────────
    section(3, "Business Objectives & Goals")
    story.append(body(
        "The primary goal of this project is to democratise data access within JGH Enterprises by "
        "eliminating the technical barrier of SQL knowledge. Business users should be able to obtain "
        "real-time insights from production data using conversational English."
    ))
    story.append(sp(6))

    obj_rows = [
        ("OBJ-01", "Enable non-technical users to query live business data in plain English", "HIGH", "Achieved"),
        ("OBJ-02", "Generate read-only, validated, safe SQL queries from NLP with zero data mutation risk", "CRITICAL", "Achieved"),
        ("OBJ-03", "Provide conversational multi-turn context (follow-up queries)", "HIGH", "Achieved"),
        ("OBJ-04", "Export results as CSV, Excel, and PDF reports", "MEDIUM", "Achieved"),
        ("OBJ-05", "Enforce enterprise security — no credentials or sensitive data leakage", "CRITICAL", "Achieved"),
        ("OBJ-06", "Support cloud GPU inference for performance scalability", "HIGH", "Achieved"),
        ("OBJ-07", "Self-correct SQL generation errors automatically via retry loop", "HIGH", "Achieved"),
        ("OBJ-08", "Maintain full query audit history and knowledge graph", "MEDIUM", "Achieved"),
    ]
    story.append(req_table(obj_rows))

    # ─── SECTION 4: SYSTEM ARCHITECTURE ──────────────────────────────────────
    section(4, "System Architecture")
    story.append(body(
        "The system follows a strict layered, multi-agent pipeline architecture. Each user query passes "
        "sequentially through 7 processing stages before results are delivered. This ensures accuracy, "
        "security, and auditability at every step."
    ))
    story.append(sp(8))
    story.append(SystemArchDiagram(bw))
    story.append(sp(4))
    story.append(caption("Figure 1 — End-to-End System Architecture of the Agentic Analyst Platform"))
    story.append(sp(10))

    subsection("Pipeline Stages")
    stages = [
        ("Stage 1 — Ambiguity Check", "The query passes through the Ambiguity Checker which detects underspecified requests (e.g., 'show data') and prompts the user for clarification before proceeding."),
        ("Stage 2 — Security Firewall", "A pattern-matching firewall blocks any requests attempting to retrieve passwords, encryption keys, auth tokens, or other restricted security credentials."),
        ("Stage 3 — NLP Understanding (LLM)", "The NLP Understanding Agent uses the Qwen2.5-Coder 7B model via Ollama to parse the natural language question into a structured BusinessRequirement JSON schema capturing intent, entities, IDs, metrics, date ranges, filters, and output format."),
        ("Stage 4 — Context Resolver", "The Context Resolver merges the parsed request with the active session context (previous questions, entity filters, date ranges) to support multi-turn conversational queries."),
        ("Stage 5 — SQL Generation (LLM)", "The SQL Generator uses the structured execution plan and a rich schema-aware prompt (built by the Prompt Builder with RAG context from the Knowledge Graph) to invoke the LLM and produce a valid MySQL SELECT query."),
        ("Stage 6 — Validation Layer (3-pass)", "The generated SQL passes through: (a) AST Validator (syntax, security, column existence), (b) Semantic Validator (alignment with execution plan), and (c) EXPLAIN Validator (query plan cost check). Any failure triggers an automatic self-correction retry (up to 3 attempts)."),
        ("Stage 7 — E2E Accuracy Validator", "Post-execution, a 10-point end-to-end accuracy check validates: user intent → entity → ID/identifier → relationship → filters → date range → metric → aggregation → SQL completeness → actual result rows."),
    ]
    for (title, desc) in stages:
        story.append(bbold(f"► {title}"))
        story.append(body(desc))
        story.append(sp(4))

    # ─── SECTION 5: FUNCTIONAL REQUIREMENTS ──────────────────────────────────
    section(5, "Functional Requirements")

    subsection("Core NLP & Query Engine")
    fr_core = [
        ("FR-01", "Accept natural language questions via REST API POST /query endpoint", "HIGH", "Implemented"),
        ("FR-02", "Parse user questions into structured BusinessRequirement via LLM (Qwen2.5-Coder 7B)", "CRITICAL", "Implemented"),
        ("FR-03", "Generate valid MySQL SELECT queries from structured execution plans", "CRITICAL", "Implemented"),
        ("FR-04", "Auto-detect query intent: list, count, aggregate, earnings, balance, SKU, withdrawal, etc.", "HIGH", "Implemented"),
        ("FR-05", "Self-correct SQL generation errors in up to 3 retry attempts", "HIGH", "Implemented"),
        ("FR-06", "Support specific ID-based queries (distributor_id, retailer_id, user_id)", "HIGH", "Implemented"),
        ("FR-07", "Support temporal queries: current month, specific month, date ranges, year", "HIGH", "Implemented"),
        ("FR-08", "Support geographic/region filters (state, city, district, pincode)", "MEDIUM", "Implemented"),
    ]
    story.append(req_table(fr_core))
    story.append(sp(8))

    subsection("Context & Session Management")
    fr_ctx = [
        ("FR-09", "Maintain session-level conversational memory across follow-up queries", "HIGH", "Implemented"),
        ("FR-10", "Resolve anaphoric references ('their', 'them', 'that person', 'in that region')", "HIGH", "Implemented"),
        ("FR-11", "Support explicit context reset commands ('start new analysis', 'reset context')", "MEDIUM", "Implemented"),
        ("FR-12", "Detect and handle follow-up vs. standalone query intent", "HIGH", "Implemented"),
    ]
    story.append(req_table(fr_ctx))
    story.append(sp(8))

    subsection("Reporting & Export")
    fr_export = [
        ("FR-13", "Export query results as CSV file", "MEDIUM", "Implemented"),
        ("FR-14", "Export query results as Excel (.xlsx) file", "MEDIUM", "Implemented"),
        ("FR-15", "Export query results as PDF report", "MEDIUM", "Implemented"),
        ("FR-16", "Stream large CSV exports via chunked HTTP streaming", "LOW", "Implemented"),
        ("FR-17", "Save reports to disk under /reports/ directory", "LOW", "Implemented"),
    ]
    story.append(req_table(fr_export))
    story.append(sp(8))

    subsection("Security & Privacy")
    fr_sec = [
        ("FR-18", "Block all requests for passwords, encryption keys, private tokens", "CRITICAL", "Implemented"),
        ("FR-19", "Restrict SQL to SELECT-only; block INSERT/UPDATE/DELETE/DROP", "CRITICAL", "Implemented"),
        ("FR-20", "Prevent access to sensitive database columns (password, secret, token)", "CRITICAL", "Implemented"),
        ("FR-21", "Support Incognito / Private mode (suppress query logging)", "MEDIUM", "Implemented"),
        ("FR-22", "Maintain query audit history in knowledge/sql_history/ directory", "MEDIUM", "Implemented"),
    ]
    story.append(req_table(fr_sec))

    # ─── SECTION 6: TECHNICAL COMPONENTS ─────────────────────────────────────
    section(6, "Technical Components")
    comp_data = [
        ["Component", "File / Module", "Responsibility"],
        ["NLP Understanding Agent", "app/agent/nlp_understanding.py", "Converts natural language to BusinessRequirement JSON via LLM"],
        ["SQL Agent (Orchestrator)", "app/agent/sql_agent.py", "Orchestrates the full 7-stage pipeline with retry logic"],
        ["Context Resolver", "app/agent/context_resolver.py", "Merges session context with new query; supports follow-up"],
        ["Memory Manager", "app/agent/memory_manager.py", "Manages session-level conversational memory and history"],
        ["Intent Router", "app/agent/intent_router.py", "Routes queries to correct handler (SQL, collaboration, ID search)"],
        ["Ambiguity Checker", "app/agent/ambiguity_checker.py", "Detects underspecified or vague queries before processing"],
        ["Prompt Builder", "app/prompt/prompt_builder.py", "Builds schema-aware LLM prompts with RAG context"],
        ["SQL Generator (LLM)", "app/llm/sql_generator.py", "Invokes Ollama LLM to generate MySQL SELECT queries"],
        ["SQL Cleaner", "app/utils/sql_cleaner.py", "Post-processes raw LLM output into clean, valid SQL"],
        ["AST Validator", "app/validator/sql_ast_validator.py", "Validates SQL syntax, security, and column existence"],
        ["Semantic SQL Validator", "app/validator/semantic_sql_validator.py", "Validates SQL semantic alignment with execution plan"],
        ["E2E Accuracy Validator", "app/validator/e2e_accuracy_validator.py", "10-point end-to-end accuracy check post-execution"],
        ["SQL Optimizer", "app/validator/sql_optimizer.py", "AST-level SQL optimization (alias normalization, etc.)"],
        ["Read Executor", "app/database/read_executor.py", "Executes validated SELECT queries against MySQL"],
        ["Schema Drift Detector", "app/database/schema_drift_detector.py", "Detects schema changes on startup"],
        ["Knowledge Graph", "app/knowledge/knowledge_graph.py", "Enterprise knowledge graph for schema relationships"],
        ["DB Profiler", "app/knowledge/db_profiler.py", "Profiles live database for schema metadata"],
        ["Report Generator", "app/utils/report_generator.py", "Generates CSV, Excel, and PDF exports"],
        ["Response Generator", "app/agent/response_generator.py", "Generates natural language summaries of query results"],
        ["FastAPI Gateway", "app/api/main.py", "REST API gateway with 30+ endpoints"],
    ]
    comp_t = Table(comp_data, colWidths=[bw * 0.22, bw * 0.3, bw * 0.48])
    comp_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(comp_t)

    # ─── SECTION 7: DATA ARCHITECTURE ────────────────────────────────────────
    section(7, "Data Architecture & Database Schema")
    story.append(body(
        "The system operates against the <b>jghMasterDB</b> production MySQL database. The database "
        "contains the complete JGH enterprise business data spanning users, distributors, retailers, "
        "wholesalers, wallet transactions, SKU inventories, withdrawal requests, and scheme management."
    ))
    story.append(sp(8))

    subsection("Key Business Tables")
    table_data = [
        ["Table Name", "Description", "Key Columns"],
        ["users", "All platform users (retailers, distributors, wholesalers, etc.)", "id, name, mobile_number, user_role, wallet_balance, state_id, distributer_id"],
        ["retailer_distributor_mappings", "Maps retailers to their assigned distributor", "id, retailer_id, distributor_id, created_at"],
        ["wallet_transaction", "All wallet credit/debit transactions", "id, user_id, amount, transaction_type, reference_type, created_at"],
        ["withdrawal_request", "Payout/withdrawal requests by users", "id, user_id, amount, status, tds_amount, created_at"],
        ["sku_inventories", "Product box scanning inventory", "id, sku_code, distributer_id, retailer_scanned_at, wholesaler_scanned_at"],
        ["distributor_targets", "Monthly sales targets for distributors", "id, distributor_id, target_amount, month, year"],
        ["executive_distributor_mappings", "Maps sales executives to distributors", "id, executive_id, distributor_id"],
        ["scheme_wallet_transactions", "Scheme-based wallet credits", "id, user_id, amount, scheme_id, created_at"],
        ["state", "Indian states master data", "id, sname (state name)"],
        ["companies", "JGH partner company details", "id, name, phone, email, sap_code, business_unit"],
    ]
    dt = Table(table_data, colWidths=[bw * 0.22, bw * 0.28, bw * 0.5])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(dt)
    story.append(sp(8))

    subsection("User Roles")
    role_data = [
        ["Role ID", "Role Name", "Description"],
        ["1", "Admin", "Full system administrator access"],
        ["2", "Retailer", "Shop/retail business owners; earn via QR scan"],
        ["3", "Mechanic", "Service center / garage owners"],
        ["4", "Distributor", "Regional product distributors; manage retailers"],
        ["5", "Wholesaler", "Bulk product distributors; supply to distributors"],
        ["6", "Executive", "JGH field sales executives"],
        ["7", "National Executive", "National-level sales management"],
    ]
    rt = Table(role_data, colWidths=[bw * 0.12, bw * 0.25, bw * 0.63])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COBALT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (0, -1), COBALT),
    ]))
    story.append(rt)

    # ─── SECTION 8: SECURITY & COMPLIANCE ────────────────────────────────────
    section(8, "Security & Compliance")

    sec_items = [
        ("Read-Only Database Access", "The system is strictly limited to READ operations. The database connection uses a read-only MySQL user account. The AST Validator programmatically blocks any INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or COMMIT statement before execution."),
        ("Credential Protection Firewall", "A keyword-matching firewall at both the API layer (app/api/main.py) and the agent layer (app/agent/sql_agent.py) blocks all queries containing terms like 'password', 'encryption key', 'master key', 'private key', 'auth token'. This prevents sensitive credential exposure regardless of how the question is phrased."),
        ("Sensitive Column Blacklist", "The AST Validator maintains a blacklist of column names (password, secret, token, master_key, auth_token, private_key, password_hash). Any generated SQL attempting to SELECT these columns is blocked before database execution."),
        ("Table Scope Enforcement", "SQL queries are validated against an allowed table list (TARGET_SCOPE_TABLES in app/database/allowed_tables.py). Queries referencing tables outside this scope are rejected."),
        ("Column Validation", "Generated SQL is validated against schema metadata to ensure all referenced columns exist in the referenced tables. Hallucinated column names are caught before execution."),
        ("Query Audit Logging", "All queries (question + generated SQL + execution result + validation status) are logged to knowledge/sql_history/query_audit_history.json for full auditability. Private/Incognito mode suppresses this logging."),
        ("CORS Policy", "The FastAPI server has CORS configured. Origins are currently set to allow all (*) for development; to be restricted to specific frontend domains in production."),
        ("Encrypted Database Config", "Database connection credentials are AES-256 Fernet-encrypted in the .env file. The decryption master key is stored separately in .master.key and referenced via environment variable."),
    ]
    for (title, desc) in sec_items:
        story.append(bbold(f"🔒  {title}"))
        story.append(body(desc))
        story.append(sp(5))

    # ─── SECTION 9: VALIDATION & QA ──────────────────────────────────────────
    section(9, "Validation & Quality Assurance")
    story.append(body(
        "The system implements a rigorous 5-layer validation architecture ensuring every SQL query is "
        "syntactically correct, semantically aligned with user intent, safe to execute, and accurate in result."
    ))
    story.append(sp(8))

    val_data = [
        ["Layer", "Validator", "Checks Performed"],
        ["Layer 1", "AST Validator", "SQL syntax, SELECT-only enforcement, forbidden operations, sensitive columns, table allowlist, column existence"],
        ["Layer 2", "Semantic SQL Validator", "Verifies SQL aligns with NLP execution plan (correct table, intent, presence of expected filters)"],
        ["Layer 3", "EXPLAIN Validator", "Runs MySQL EXPLAIN to verify the query execution plan is valid and not catastrophically expensive"],
        ["Layer 4", "Database Execution", "Actual execution against MySQL with error capture and retry routing on database-level failures"],
        ["Layer 5 (E2E)", "10-Point E2E Accuracy Validator", "Validates: User Intent → Entity → ID/Identifier → Relationship → Filters → Date Range → Metric → Aggregation → SQL Completeness → Actual Result"],
    ]
    vt = Table(val_data, colWidths=[bw * 0.12, bw * 0.25, bw * 0.63])
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (0, -1), COBALT),
    ]))
    story.append(vt)
    story.append(sp(10))

    subsection("Self-Correction Retry Mechanism")
    story.append(body(
        "When any validation layer (Layers 1–5) fails, the system does NOT immediately return an error "
        "to the user. Instead, it captures the specific failure reason and feeds it back to the LLM as "
        "additional context for a corrected retry attempt. The system attempts up to <b>3 retries</b> "
        "before returning a final blocked status. This self-correction loop significantly improves success "
        "rate on complex, ambiguous, or first-attempt-incorrect queries."
    ))

    # ─── SECTION 10: API ENDPOINTS ────────────────────────────────────────────
    section(10, "API Endpoints & Integration")
    api_data = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/", "Serves the frontend React/Vue single-page application"],
        ["GET", "/health", "System health check — DB connectivity, table count, model"],
        ["GET", "/api/llm/health", "LLM health check — Ollama online status and model info"],
        ["GET", "/schema", "Returns database schema map {table: [columns]}"],
        ["POST", "/query", "Main NLP query endpoint — accepts natural language question, returns SQL + results"],
        ["POST", "/agent/collaborate", "Collaborative multi-step query mode"],
        ["GET", "/api/query-history", "Retrieves query audit history"],
        ["POST", "/export/csv", "Export result set as CSV file"],
        ["POST", "/export/excel", "Export result set as Excel file"],
        ["POST", "/export/pdf", "Export result set as PDF report"],
        ["POST", "/export/sql-csv", "Execute SQL query directly and export as CSV"],
        ["GET", "/api/settings", "Get current AI model and system settings"],
        ["POST", "/api/settings", "Update AI model, temperature, and system settings"],
        ["GET", "/api/erd", "Generate Entity-Relationship Diagram from schema"],
        ["GET", "/api/knowledge/profile", "Returns full live database profile and stats"],
    ]
    at = Table(api_data, colWidths=[bw * 0.1, bw * 0.32, bw * 0.58])
    at.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (0, -1), COBALT),
    ]))
    story.append(at)

    # ─── SECTION 11: NON-FUNCTIONAL REQUIREMENTS ──────────────────────────────
    section(11, "Non-Functional Requirements")
    nfr_rows = [
        ("NFR-01", "Response time for simple queries should be under 10 seconds (local LLM)", "HIGH", "Monitored"),
        ("NFR-02", "System must not expose or mutate production data (read-only)", "CRITICAL", "Enforced"),
        ("NFR-03", "All query failures must be logged with full pipeline trace for debugging", "HIGH", "Implemented"),
        ("NFR-04", "Application must start up with diagnostic checks and report failures clearly", "MEDIUM", "Implemented"),
        ("NFR-05", "System must support hot-reload for development (WatchFiles integration)", "LOW", "Implemented"),
        ("NFR-06", "LLM endpoint must be configurable via environment variable (OLLAMA_BASE_URL)", "HIGH", "Implemented"),
        ("NFR-07", "Database credentials must never appear in plaintext in source code or logs", "CRITICAL", "Enforced"),
        ("NFR-08", "System must gracefully handle LLM unavailability with informative error messages", "HIGH", "Implemented"),
        ("NFR-09", "Export files must be auto-named with timestamp to avoid overwriting", "LOW", "Implemented"),
        ("NFR-10", "System schema must auto-update if database schema changes are detected", "MEDIUM", "Implemented"),
    ]
    story.append(req_table(nfr_rows))

    # ─── SECTION 12: KNOWN ISSUES & RESOLUTIONS ───────────────────────────────
    section(12, "Known Issues & Bug Resolutions")
    story.append(body(
        "The following bugs were identified during development and testing, and have been resolved "
        "as part of the ongoing production stabilisation effort."
    ))
    story.append(sp(6))

    issue_data = [
        ["Issue ID", "Description", "Root Cause", "Resolution", "Status"],
        ["BUG-01", "LLM Offline error despite Ollama running", "OLLAMA_BASE_URL pointed to expired Pinggy tunnel in .env", "Updated OLLAMA_BASE_URL to http://localhost:11434", "Resolved"],
        ["BUG-02", "Empty SQL query error on valid questions", "Stop token '```' was set in LLM options, causing LLM to halt before writing SQL code block", "Removed '```' from stop tokens list in sql_generator.py", "Resolved"],
        ["BUG-03", "E2E Validation ID check failing", "Validator received specific_id as dict {'value': '5997', 'type': 'distributor_id'} but str() converted the whole dict instead of extracting value", "Added isinstance dict check to extract 'value' key before validation", "Resolved"],
        ["BUG-04", "Slow query response time on local hardware", "7B parameter LLM inference on CPU/integrated GPU is slower than cloud GPU", "Documented; option to re-connect to Kaggle/Colab cloud GPU via OLLAMA_BASE_URL", "Documented"],
    ]
    it = Table(issue_data, colWidths=[bw * 0.1, bw * 0.24, bw * 0.24, bw * 0.28, bw * 0.14])
    it.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, SUBTLE_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.HexColor("#7C3AED")),
    ]))
    story.append(it)

    # ─── SECTION 13: DEPLOYMENT ARCHITECTURE ──────────────────────────────────
    section(13, "Deployment Architecture")

    subsection("Local Development Setup")
    local_steps = [
        "Install Python 3.13 and create virtual environment (venv/)",
        "Install dependencies: pip install -r requirements.txt",
        "Install Ollama from https://ollama.ai and pull model: ollama run qwen2.5-coder:7b",
        "Configure .env with ENCRYPTED_DB_CONFIG and OLLAMA_BASE_URL=http://localhost:11434",
        "Place .master.key decryption key file in project root",
        "Start server: python start_server.py",
        "Access application at http://localhost:8000",
    ]
    for i, step in enumerate(local_steps, 1):
        story.append(bullet(f"Step {i}: {step}"))
    story.append(sp(8))

    subsection("Cloud GPU Configuration (Performance Mode)")
    cloud_steps = [
        "Start a Kaggle or Google Colab notebook with GPU accelerator (T4 / P100)",
        "Install Ollama in notebook: !curl -fsSL https://ollama.com/install.sh | sh",
        "Pull model: !ollama run qwen2.5-coder:7b",
        "Expose Ollama via Pinggy or LocalTunnel: !lt --port 11434",
        "Copy the generated tunnel URL (e.g., https://xyz.pinggy.io)",
        "Update .env: OLLAMA_BASE_URL=\"https://xyz.pinggy.io\"",
        "Restart server: python start_server.py — now routes to cloud GPU",
    ]
    for i, step in enumerate(cloud_steps, 1):
        story.append(bullet(f"Step {i}: {step}"))
    story.append(sp(8))

    subsection("Production Deployment Considerations")
    story.append(bullet("Replace Pinggy/LocalTunnel with RunPod, AWS EC2 (g4dn), or Vultr GPU for 24/7 uptime"))
    story.append(bullet("Secure Ollama endpoint with Nginx reverse proxy + HTTPS + Basic Auth or VPN (Tailscale)"))
    story.append(bullet("Restrict FastAPI CORS origins to specific frontend domain"))
    story.append(bullet("Deploy FastAPI with Gunicorn + Uvicorn workers for multi-threaded production serving"))
    story.append(bullet("Use Docker / docker-compose for containerised deployment (Dockerfile and docker-compose.yml included)"))
    story.append(bullet("Set up database read-replica for analytics queries to avoid impacting production write performance"))

    # ─── SECTION 14: GLOSSARY ────────────────────────────────────────────────
    section(14, "Glossary & Definitions")
    glossary = [
        ("Agentic Analyst", "The AI-powered analytics platform built for JGH Enterprises that converts natural language into SQL."),
        ("JGH Intelligence Engine", "Internal branding name for the Agentic Analyst system."),
        ("NLP", "Natural Language Processing — the AI capability to understand human language questions."),
        ("LLM", "Large Language Model — the AI model (Qwen2.5-Coder 7B) used to generate SQL from natural language."),
        ("Ollama", "An open-source tool to run LLMs locally on a machine without cloud dependency."),
        ("AST", "Abstract Syntax Tree — a structured parse tree of SQL code used for validation."),
        ("RAG", "Retrieval-Augmented Generation — technique to inject relevant schema/history context into LLM prompts."),
        ("FastAPI", "A modern, high-performance Python web framework used as the REST API server."),
        ("E2E Validation", "End-to-End Accuracy Validation — a 10-point post-execution check ensuring query correctness."),
        ("Context Resolver", "The component that merges active session memory with new query intent to support follow-up questions."),
        ("Self-Correction", "Automatic retry mechanism where the system feeds validation failure reasons back to the LLM for correction."),
        ("Pinggy / LocalTunnel / Ngrok", "Tools that expose a local or remote port to a public HTTPS URL, used to access cloud GPU Ollama."),
        ("jghMasterDB", "The production MySQL database containing all JGH business data."),
        ("BRD", "Business Requirements Document — this document. A formal specification of system requirements and design."),
        ("Qwen2.5-Coder 7B", "A 7.6 billion parameter open-source AI code model by Alibaba Cloud, specialised in code generation."),
    ]
    for term, defn in glossary:
        story.append(bbold(f"{term}"))
        story.append(body(defn))
        story.append(sp(3))

    # ─── FINAL PAGE: SIGN-OFF ─────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(sp(30))
    story.append(Paragraph("Document Sign-Off", ParagraphStyle("signoff_title",
        fontName="Helvetica-Bold", fontSize=16, textColor=NAVY, alignment=TA_CENTER)))
    story.append(sp(10))
    story.append(divider())
    story.append(sp(20))

    sign_data = [
        ["Role", "Name", "Signature", "Date"],
        ["Developer / Owner", "[Confidential]", "_______________________", datetime.now().strftime("%B %d, %Y")],
        ["Technical Reviewer", "", "_______________________", ""],
        ["Business Owner", "", "_______________________", ""],
        ["QA Sign-Off", "", "_______________________", ""],
    ]
    st = Table(sign_data, colWidths=[bw * 0.25, bw * 0.25, bw * 0.3, bw * 0.2])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, SUBTLE_LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
    ]))
    story.append(st)
    story.append(sp(30))
    story.append(Paragraph(
        f"This document was auto-generated on {datetime.now().strftime('%B %d, %Y at %H:%M IST')}  •  "
        "Agentic Analyst v2.0  •  JGH Intelligence Engine  •  CONFIDENTIAL",
        ParagraphStyle("footer_note", fontName="Helvetica", fontSize=8, textColor=SILVER, alignment=TA_CENTER)
    ))

    # ─── PAGE TEMPLATE ────────────────────────────────────────────────────────
    def on_page(canvas, doc):
        canvas.saveState()
        # Header bar
        canvas.setFillColor(NAVY)
        canvas.rect(0, H - 28, W, 28, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, H - 28, W, 3, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(1.2 * inch, H - 18, "AGENTIC ANALYST")
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SKY)
        canvas.drawString(1.2 * inch + 100, H - 18, "JGH Intelligence Engine — BRD v2.0")
        canvas.setFillColor(GOLD)
        canvas.drawRightString(W - 1.2 * inch, H - 18, "CONFIDENTIAL")
        # Footer
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, W, 22, fill=1, stroke=0)
        canvas.setFillColor(COBALT)
        canvas.rect(0, 22, W, 1.5, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(1.2 * inch, 7, f"© 2026 JGH Enterprises  |  Generated: {datetime.now().strftime('%B %d, %Y')}")
        canvas.setFillColor(GOLD)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(W - 1.2 * inch, 7, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_cover_page, onLaterPages=on_page)
    print(f"[SUCCESS] BRD generated: {out_path}")
    return out_path


if __name__ == "__main__":
    build_brd()
