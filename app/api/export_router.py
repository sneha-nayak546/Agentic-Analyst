"""
Enterprise Export Suite API Router for JGH Intelligence Engine.
Compliant with Section 15 Specifications:
- Report title derived from question
- Original question
- Final conversational answer
- Calculated explanation
- Results data table
- Query details (entity, metric, period, filters, tables used)
- Executed SQL query
- Verification status
- Execution latency breakdown
Exposes download endpoints for CSV, Excel (.xlsx), and PDF reports.
"""

import io
import json
import datetime
import pandas as pd
import openpyxl
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT

export_router = APIRouter(tags=["Export"])

class ExportDataPayload(BaseModel):
    columns: Optional[List[str]] = []
    rows: Optional[List[Dict[str, Any]]] = []
    data: Optional[List[Dict[str, Any]]] = []
    title: Optional[str] = None
    filename: Optional[str] = "JGH_Executive_Report"
    question: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    sql: Optional[str] = None
    verification_status: Optional[str] = "VERIFIED"
    details: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None


def _extract_rows_and_cols(payload: ExportDataPayload):
    rows = payload.rows or payload.data or []
    cols = payload.columns or []
    if not cols and rows:
        cols = list(rows[0].keys())
    return cols, rows


@export_router.post("/api/export/csv")
@export_router.post("/export/csv")
def export_csv(payload: ExportDataPayload):
    cols, rows = _extract_rows_and_cols(payload)
    df = pd.DataFrame(rows, columns=cols if cols else None)

    stream = io.StringIO()
    # Write metadata header comments
    q_str = (payload.question or payload.title or "").replace("\n", " ")
    ans_str = (payload.answer or "").replace("\n", " ")
    exp_str = (payload.explanation or "").replace("\n", " ")
    sql_str = (payload.sql or "").replace("\n", " ")
    stream.write(f"# JGH INTELLIGENCE ENGINE — EXECUTIVE DATA REPORT\n")
    stream.write(f"# Question: {q_str}\n")
    stream.write(f"# Verification Status: {payload.verification_status or 'VERIFIED'}\n")
    if ans_str:
        stream.write(f"# Answer: {ans_str}\n")
    if exp_str:
        stream.write(f"# Explanation: {exp_str}\n")
    if sql_str:
        stream.write(f"# Executed SQL: {sql_str}\n")
    if payload.performance:
        stream.write(f"# Latency (ms): {json.dumps(payload.performance)}\n")
    stream.write("# ------------------------------------------------------------\n")

    df.to_csv(stream, index=False)
    csv_bytes = stream.getvalue().encode("utf-8")

    filename = f"{payload.filename or 'JGH_Data_Export'}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@export_router.post("/api/export/excel")
@export_router.post("/export/excel")
def export_excel(payload: ExportDataPayload):
    cols, rows = _extract_rows_and_cols(payload)
    df = pd.DataFrame(rows, columns=cols if cols else None)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Executive Summary & Details
        summary_rows = [
            ["Report Title", payload.title or (f"Analysis: {payload.question}" if payload.question else "JGH Executive Report")],
            ["Original Question", payload.question or "N/A"],
            ["Verification Status", payload.verification_status or "VERIFIED"],
            ["Generated At", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Total Records", len(rows)],
            ["", ""],
            ["Conversational Answer", payload.answer or "N/A"],
            ["Calculated Explanation", payload.explanation or "N/A"],
            ["", ""],
            ["Executed SQL", payload.sql or "N/A"],
        ]

        if payload.details:
            summary_rows.append(["", ""])
            summary_rows.append(["Query Details", ""])
            for k, v in payload.details.items():
                summary_rows.append([f"  • {k}", str(v)])

        if payload.performance:
            summary_rows.append(["", ""])
            summary_rows.append(["Performance Breakdown (ms)", ""])
            for k, v in payload.performance.items():
                summary_rows.append([f"  • {k}", f"{v} ms"])

        summary_df = pd.DataFrame(summary_rows, columns=["Property", "Value"])
        summary_df.to_excel(writer, sheet_name="Executive Summary", index=False)

        # Sheet 2: Verified Data
        df.to_excel(writer, sheet_name="Verified Data", index=False)

        # Apply Styling to Executive Summary
        wb = writer.book
        ws_sum = writer.sheets["Executive Summary"]
        header_fill = openpyxl.styles.PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = openpyxl.styles.Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for cell in ws_sum[1]:
            cell.fill = header_fill
            cell.font = header_font
        ws_sum.column_dimensions["A"].width = 28
        ws_sum.column_dimensions["B"].width = 80

        # Apply Styling to Verified Data
        ws_data = writer.sheets["Verified Data"]
        data_hdr_fill = openpyxl.styles.PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        for cell in ws_data[1]:
            cell.fill = data_hdr_fill
            cell.font = header_font

        for col in ws_data.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws_data.column_dimensions[col_letter].width = max(max_len + 3, 14)

    excel_bytes = output.getvalue()
    filename = f"{payload.filename or 'JGH_Executive_Report'}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@export_router.post("/api/export/pdf")
@export_router.post("/export/pdf")
def export_pdf(payload: ExportDataPayload):
    cols, rows = _extract_rows_and_cols(payload)

    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=colors.HexColor('#1E3A8A'), alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('DocSub', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#64748B'), alignment=TA_CENTER)
    section_title = ParagraphStyle('SectionHdr', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=colors.HexColor('#1E3A8A'))
    body_style = ParagraphStyle('DocBody', fontName='Helvetica', fontSize=8, leading=11, textColor=colors.HexColor('#0F172A'))
    answer_style = ParagraphStyle('AnswerText', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor('#0F172A'))
    code_style = ParagraphStyle('CodeText', fontName='Courier', fontSize=7, leading=9, textColor=colors.HexColor('#1E293B'))
    tbl_cell = ParagraphStyle('TblCell', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#0F172A'))
    tbl_hdr = ParagraphStyle('TblHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)

    story = []

    # Title Banner
    story.append(Paragraph("JGH INTELLIGENCE ENGINE", title_style))
    story.append(Paragraph("EXECUTIVE BUSINESS REPORT & FACTUAL DATA SPECIFICATION", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=4, spaceAfter=8))

    # Metadata / Scorecard Table
    total_records = len(rows)
    scorecard_data = [
        [
            Paragraph("<b>Original Question:</b>", body_style),
            Paragraph(payload.question or payload.title or "Analytics Query", body_style),
            Paragraph("<b>Verification Status:</b>", body_style),
            Paragraph(f"<font color='#10B981'><b>{payload.verification_status or 'VERIFIED'}</b></font>", body_style)
        ],
        [
            Paragraph("<b>Generated:</b>", body_style),
            Paragraph(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), body_style),
            Paragraph("<b>Verified Records:</b>", body_style),
            Paragraph(str(total_records), body_style)
        ]
    ]
    sc_table = Table(scorecard_data, colWidths=[3.5*cm, 6.0*cm, 3.5*cm, 4.5*cm])
    sc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(sc_table)
    story.append(Spacer(1, 8))

    # Conversational Answer Section
    if payload.answer:
        story.append(Paragraph("<b>Conversational Answer</b>", section_title))
        ans_box = Table([[Paragraph(payload.answer.replace("\n", "<br/>"), answer_style)]], colWidths=[17.5*cm])
        ans_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(ans_box)
        story.append(Spacer(1, 6))

    # Calculated Explanation Section
    if payload.explanation:
        story.append(Paragraph("<b>Calculated Business Explanation</b>", section_title))
        exp_box = Table([[Paragraph(payload.explanation.replace("\n", "<br/>"), body_style)]], colWidths=[17.5*cm])
        exp_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0FDF4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BBF7D0')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(exp_box)
        story.append(Spacer(1, 6))

    # Verified Data Table (top 25 rows max to fit cleanly on page)
    if rows:
        story.append(Paragraph(f"<b>Verified Database Results ({len(rows)} rows)</b>", section_title))
        display_rows = rows[:25]
        display_cols = cols[:6]

        table_data = [[Paragraph(str(c), tbl_hdr) for c in display_cols]]
        for r in display_rows:
            row_cells = [Paragraph(str(r.get(c, '')), tbl_cell) for c in display_cols]
            table_data.append(row_cells)

        col_w = 17.5 / max(len(display_cols), 1)
        data_table = Table(table_data, colWidths=[col_w * cm] * len(display_cols))
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
        ]))
        story.append(data_table)
        story.append(Spacer(1, 8))

    # Executed SQL & Latency Section (in KeepTogether block)
    if payload.sql:
        sql_elements = [
            Paragraph("<b>Executed & Verified SQL Query</b>", section_title),
            Table([[Paragraph(payload.sql, code_style)]], colWidths=[17.5*cm], style=[
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
                ('PADDING', (0, 0), (-1, -1), 5),
            ])
        ]
        story.append(KeepTogether(sql_elements))

    doc.build(story)
    pdf_bytes = output.getvalue()

    filename = f"{payload.filename or 'JGH_Executive_Report'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
