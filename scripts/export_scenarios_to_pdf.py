"""
PDF Document Generator for Enterprise Architectural Scenarios Specification.
Parses knowledge/Enterprise_Architectural_Scenarios_Specification.md and generates
a professional, multi-page, executive PDF report titled knowledge/Enterprise_Architectural_Scenarios_Specification.pdf
with highlighted Simple Solution Callout Cards.
"""

import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

MD_PATH = PROJECT_ROOT / "knowledge" / "Enterprise_Architectural_Scenarios_Specification.md"
PDF_PATH = PROJECT_ROOT / "knowledge" / "Enterprise_Architectural_Scenarios_Specification.pdf"

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count ('Page X of Y')
    and running header/footer on all pages.
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Top Running Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(1.5 * cm, 28.3 * cm, "JGH INTELLIGENCE ENGINE — ENTERPRISE ARCHITECTURAL SPECIFICATION")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(1.5 * cm, 28.1 * cm, 19.5 * cm, 28.1 * cm)

        # Bottom Running Footer (All Pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(19.5 * cm, 1.2 * cm, page_str)
        self.drawString(1.5 * cm, 1.2 * cm, "CONFIDENTIAL — FOR ENTERPRISE ARCHITECTURE REVIEW ONLY")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(1.5 * cm, 1.5 * cm, 19.5 * cm, 1.5 * cm)

        self.restoreState()


def compile_scenarios_pdf():
    print(f"[PDF CONVERTER] Reading Markdown file from {MD_PATH} ...")
    if not MD_PATH.exists():
        print(f"❌ Error: Markdown file missing at {MD_PATH}")
        return False

    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle', fontName='Helvetica-Bold', fontSize=20, leading=24,
        textColor=colors.HexColor('#1E3A8A'), alignment=1, spaceAfter=8
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', fontName='Helvetica-Bold', fontSize=10, leading=14,
        textColor=colors.HexColor('#475569'), alignment=1, spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'H1', fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=colors.HexColor('#0F172A'), spaceBefore=14, spaceAfter=8, keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2', fontName='Helvetica-Bold', fontSize=11, leading=15,
        textColor=colors.HexColor('#1E3A8A'), spaceBefore=10, spaceAfter=6, keepWithNext=True
    )
    h3_style = ParagraphStyle(
        'H3', fontName='Helvetica-Bold', fontSize=9.5, leading=13,
        textColor=colors.HexColor('#334155'), spaceBefore=8, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=colors.HexColor('#1E293B'), spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet', fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=colors.HexColor('#1E293B'), leftIndent=12, firstLineIndent=-8, spaceAfter=4
    )
    code_style = ParagraphStyle(
        'CodeBlock', fontName='Courier', fontSize=7.5, leading=10,
        textColor=colors.HexColor('#0F172A'), backColor=colors.HexColor('#F8FAFC'),
        borderColor=colors.HexColor('#CBD5E1'), borderWidth=0.5, borderPadding=6, spaceAfter=8
    )
    callout_cell = ParagraphStyle('CalloutCell', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#1E3A8A'))
    tbl_cell = ParagraphStyle('TblCell', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#0F172A'))
    tbl_hdr = ParagraphStyle('TblHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)

    story = []

    # Title & Subtitle Banner
    story.append(Paragraph("JGH INTELLIGENCE ENGINE", title_style))
    story.append(Paragraph("ENTERPRISE ARCHITECTURAL & OPERATIONAL SCENARIOS SPECIFICATION", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1E3A8A'), spaceBefore=2, spaceAfter=12))

    # Metadata Header Table
    meta_table_data = [
        [Paragraph("<b>Document Version:</b> 2.5", body_style), Paragraph("<b>Target DB:</b> jghMasterDB (238 Tables, 6.5M+ Rows)", body_style)],
        [Paragraph("<b>Author:</b> AI Systems Architecture Team", body_style), Paragraph("<b>Status:</b> Production Approved Specification", body_style)],
        [Paragraph("<b>Scope:</b> 12 Enterprise Scenarios & Simple Solutions", body_style), Paragraph("<b>Date:</b> August 12, 2026", body_style)]
    ]
    meta_table = Table(meta_table_data, colWidths=[9.0 * cm, 9.0 * cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Parse Markdown blocks
    lines = md_content.split('\n')
    in_code_block = False
    code_lines = []

    for line in lines:
        line_s = line.strip()

        # Handle Code Blocks
        if line_s.startswith("```"):
            if in_code_block:
                code_text = "<br/>".join([c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;") for c in code_lines])
                story.append(Paragraph(code_text, code_style))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if not line_s:
            continue

        # Skip main title and metadata since we formatted top banner
        if line_s.startswith("# JGH INTELLIGENCE ENGINE") or line_s.startswith("**Document Version:**") or line_s.startswith("**Author:**") or line_s.startswith("**Scope:**"):
            continue

        # Blockquote / Simple Solution Callout Card
        if line_s.startswith(">"):
            q_text = line_s[1:].strip()
            q_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', q_text)
            q_formatted = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', q_formatted)

            callout_box = Table([[Paragraph(q_formatted, callout_cell)]], colWidths=[18.0 * cm])
            callout_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2563EB')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(Spacer(1, 4))
            story.append(callout_box)
            story.append(Spacer(1, 6))
            continue

        # Headings
        if line_s.startswith("## "):
            h_text = line_s[3:].strip()
            story.append(Paragraph(h_text, h1_style))
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#334155'), spaceBefore=2, spaceAfter=6))
        elif line_s.startswith("### "):
            h_text = line_s[4:].strip()
            story.append(Paragraph(h_text, h2_style))
        elif line_s.startswith("#### "):
            h_text = line_s[5:].strip()
            story.append(Paragraph(h_text, h3_style))

        # Bullet points
        elif line_s.startswith("- ") or line_s.startswith("* "):
            b_text = line_s[2:].strip()
            b_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', b_text)
            b_formatted = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', b_formatted)
            story.append(Paragraph(f"• {b_formatted}", bullet_style))

        # Numbered lists
        elif re.match(r'^\d+\.\s+', line_s):
            n_text = re.sub(r'^\d+\.\s+', '', line_s)
            n_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', n_text)
            n_formatted = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', n_formatted)
            story.append(Paragraph(f"{line_s.split('.')[0]}. {n_formatted}", bullet_style))

        # Standard Paragraphs
        elif not line_s.startswith("---") and not line_s.startswith("|"):
            p_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_s)
            p_formatted = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', p_formatted)
            story.append(Paragraph(p_formatted, body_style))

    # Add Architectural Component Matrix Table at the end
    story.append(Spacer(1, 10))
    story.append(Paragraph("PART III: ARCHITECTURAL COMPONENT & SOLUTION MATRIX", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#334155'), spaceBefore=2, spaceAfter=6))

    matrix_rows = [
        [Paragraph("Scenario #", tbl_hdr), Paragraph("Major Problem", tbl_hdr), Paragraph("Responsible Module", tbl_hdr), Paragraph("Simple Solution", tbl_hdr)],
        [Paragraph("Scenario 1", tbl_cell), Paragraph("Date & Time Misunderstandings", tbl_cell), Paragraph("app/agent/intent_router.py", tbl_cell), Paragraph("Converts relative phrases to fixed dates & binds column", tbl_cell)],
        [Paragraph("Scenario 2", tbl_cell), Paragraph("Multi-Step Chat Memory Loss", tbl_cell), Paragraph("app/agent/memory_manager.py", tbl_cell), Paragraph("Entity Pointer Graph tracks exact primary key IDs", tbl_cell)],
        [Paragraph("Scenario 3", tbl_cell), Paragraph("Database Code Mismatches", tbl_cell), Paragraph("app/validator/universal_validator.py", tbl_cell), Paragraph("Auto-corrects loose terms ('cash points') to DB code", tbl_cell)],
        [Paragraph("Scenario 4", tbl_cell), Paragraph("System Freezing Cross-Joins", tbl_cell), Paragraph("app/validator/query_validator.py", tbl_cell), Paragraph("Validates join paths & blocks unindexed queries >100k rows", tbl_cell)],
        [Paragraph("Scenario 5", tbl_cell), Paragraph("Database Schema Drift", tbl_cell), Paragraph("app/database/schema_drift_detector.py", tbl_cell), Paragraph("Startup detector checks live DB schema and updates metadata", tbl_cell)],
        [Paragraph("Scenario 6", tbl_cell), Paragraph("PII Data Exfiltration", tbl_cell), Paragraph("app/validator/query_validator.py", tbl_cell), Paragraph("Security Blacklist blocks 16 sensitive fields ('password')", tbl_cell)],
        [Paragraph("Scenario 7", tbl_cell), Paragraph("Ledger vs Profile Discrepancy", tbl_cell), Paragraph("knowledge/business_dictionary.json", tbl_cell), Paragraph("Routes historical reporting strictly to immutable ledger", tbl_cell)],
        [Paragraph("Scenario 8", tbl_cell), Paragraph("Dual-Role FK Ambiguity", tbl_cell), Paragraph("app/agent/query_planner.py", tbl_cell), Paragraph("Pre-checks user role to join correct FK (retailer vs wholeseller)", tbl_cell)],
        [Paragraph("Scenario 9", tbl_cell), Paragraph("Connection Pool Starvation", tbl_cell), Paragraph("app/database/config.py", tbl_cell), Paragraph("Managed connection pool + 5s query time limit hint", tbl_cell)],
        [Paragraph("Scenario 10", tbl_cell), Paragraph("Null Aggregation Bias", tbl_cell), Paragraph("app/agent/response_synthesizer.py", tbl_cell), Paragraph("Enforces explicit formulas for averages and totals", tbl_cell)],
        [Paragraph("Scenario 11", tbl_cell), Paragraph("Timezone IST/UTC Shift", tbl_cell), Paragraph("app/prompt/prompt_builder.py", tbl_cell), Paragraph("Automatically shifts local dates into exact UTC ranges", tbl_cell)],
        [Paragraph("Scenario 12", tbl_cell), Paragraph("Audit Log Privacy Leakage", tbl_cell), Paragraph("app/utils/privacy_manager.py", tbl_cell), Paragraph("Volatile RAM execution with zero disk writes when is_private: true", tbl_cell)]
    ]

    matrix_table = Table(matrix_rows, colWidths=[2.2*cm, 4.8*cm, 5.0*cm, 6.0*cm])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))

    story.append(matrix_table)

    print(f"[PDF CONVERTER] Building PDF document with Simple Solution Callout Cards ...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Success: Generated formal PDF report at {PDF_PATH} ({PDF_PATH.stat().st_size} bytes).")
    return True

if __name__ == "__main__":
    compile_scenarios_pdf()
