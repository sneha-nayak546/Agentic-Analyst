"""
PDF Document Generator for Business Executive Scenarios Specification.
Parses knowledge/Business_Executive_Scenarios_Specification.md and generates
a professional, multi-page, executive PDF report titled knowledge/Business_Executive_Scenarios_Specification.pdf.
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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas

MD_PATH = PROJECT_ROOT / "knowledge" / "Business_Executive_Scenarios_Specification.md"
PDF_PATH = PROJECT_ROOT / "knowledge" / "Business_Executive_Scenarios_Specification.pdf"

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
            self.drawString(1.5 * cm, 28.3 * cm, "JGH INTELLIGENCE ENGINE — BUSINESS EXECUTIVE SCENARIOS")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(1.5 * cm, 28.1 * cm, 19.5 * cm, 28.1 * cm)

        # Bottom Running Footer (All Pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(19.5 * cm, 1.2 * cm, page_str)
        self.drawString(1.5 * cm, 1.2 * cm, "CONFIDENTIAL — FOR EXECUTIVE MANAGEMENT REVIEW ONLY")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(1.5 * cm, 1.5 * cm, 19.5 * cm, 1.5 * cm)

        self.restoreState()


def compile_business_scenarios_pdf():
    print(f"[PDF CONVERTER] Reading Business Markdown from {MD_PATH} ...")
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
    callout_cell = ParagraphStyle('CalloutCell', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#1E3A8A'))
    tbl_cell = ParagraphStyle('TblCell', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#0F172A'))
    tbl_hdr = ParagraphStyle('TblHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)

    story = []

    # Title & Subtitle Banner
    story.append(Paragraph("JGH INTELLIGENCE ENGINE", title_style))
    story.append(Paragraph("BUSINESS EXECUTIVE SCENARIOS SPECIFICATION", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1E3A8A'), spaceBefore=2, spaceAfter=12))

    # Metadata Header Table
    meta_table_data = [
        [Paragraph("<b>Document Version:</b> 3.0", body_style), Paragraph("<b>Target System:</b> JGH Enterprise Analytics Platform", body_style)],
        [Paragraph("<b>Author:</b> Business Strategy & AI Architecture Team", body_style), Paragraph("<b>Audience:</b> C-Suite & Operations Leadership", body_style)],
        [Paragraph("<b>Scope:</b> 10 Executive Business Scenarios", body_style), Paragraph("<b>Date:</b> August 12, 2026", body_style)]
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

    for line in lines:
        line_s = line.strip()

        if not line_s:
            continue

        # Skip main title and metadata since we formatted top banner
        if line_s.startswith("# JGH INTELLIGENCE ENGINE") or line_s.startswith("**Document Version:**") or line_s.startswith("**Target Audience:**") or line_s.startswith("**Scope:**"):
            continue

        # Blockquote / Business Solution Callout Card
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

        # Standard Paragraphs
        elif not line_s.startswith("---") and not line_s.startswith("|"):
            p_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_s)
            p_formatted = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', p_formatted)
            story.append(Paragraph(p_formatted, body_style))

    # Add Business Value & Impact Matrix Table at the end
    story.append(Spacer(1, 10))
    story.append(Paragraph("BUSINESS VALUE & IMPACT MATRIX", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#334155'), spaceBefore=2, spaceAfter=6))

    matrix_rows = [
        [Paragraph("Scenario #", tbl_hdr), Paragraph("Business Focus Area", tbl_hdr), Paragraph("Target Executive", tbl_hdr), Paragraph("Key Business Impact Delivered", tbl_hdr)],
        [Paragraph("Scenario 1", tbl_cell), Paragraph("Sales Incentives", tbl_cell), Paragraph("VP of Sales", tbl_cell), Paragraph("Prevents overpayment of unearned loyalty bonuses", tbl_cell)],
        [Paragraph("Scenario 2", tbl_cell), Paragraph("Fraud Prevention", tbl_cell), Paragraph("Head of Internal Audit", tbl_cell), Paragraph("Protects reward reserves from fake/recycled QR scans", tbl_cell)],
        [Paragraph("Scenario 3", tbl_cell), Paragraph("Supply Chain Velocity", tbl_cell), Paragraph("Director of Supply Chain", tbl_cell), Paragraph("Eliminates regional bottlenecks & wholesaler hoarding", tbl_cell)],
        [Paragraph("Scenario 4", tbl_cell), Paragraph("Treasury & Liquidity", tbl_cell), Paragraph("CFO & Treasury", tbl_cell), Paragraph("Forecasts weekly bank payout liabilities to avoid failures", tbl_cell)],
        [Paragraph("Scenario 5", tbl_cell), Paragraph("Mechanic Retention", tbl_cell), Paragraph("Customer Success Lead", tbl_cell), Paragraph("Identifies churning mechanics for targeted re-engagement", tbl_cell)],
        [Paragraph("Scenario 6", tbl_cell), Paragraph("Territory Governance", tbl_cell), Paragraph("Regional Sales Directors", tbl_cell), Paragraph("Ensures conflict-free commission attribution & single truth", tbl_cell)],
        [Paragraph("Scenario 7", tbl_cell), Paragraph("SKU Margin Optimization", tbl_cell), Paragraph("Product Managers", tbl_cell), Paragraph("Restructures point values to boost high-margin sales", tbl_cell)],
        [Paragraph("Scenario 8", tbl_cell), Paragraph("Operational Governance", tbl_cell), Paragraph("HR & IT Operations", tbl_cell), Paragraph("Audits Roles 1-14 to enforce administrative accountability", tbl_cell)],
        [Paragraph("Scenario 9", tbl_cell), Paragraph("Inventory Planning", tbl_cell), Paragraph("Kolkata Warehouse Lead", tbl_cell), Paragraph("Predicts seasonal stock buffer needs across 5 states", tbl_cell)],
        [Paragraph("Scenario 10", tbl_cell), Paragraph("Executive Privacy", tbl_cell), Paragraph("Board of Directors / CEO", tbl_cell), Paragraph("Zero-disk trace execution for confidential board reviews", tbl_cell)]
    ]

    matrix_table = Table(matrix_rows, colWidths=[2.2*cm, 4.0*cm, 4.8*cm, 7.0*cm])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))

    story.append(matrix_table)

    print(f"[PDF CONVERTER] Building Business Executive PDF document ...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ Success: Generated formal PDF report at {PDF_PATH} ({PDF_PATH.stat().st_size} bytes).")
    return True

if __name__ == "__main__":
    compile_business_scenarios_pdf()
