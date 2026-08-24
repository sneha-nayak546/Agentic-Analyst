"""
Enterprise Export Suite API Router for JGH Intelligence Engine.
Exposes download endpoints for CSV, Excel (.xlsx), and PDF reports.
"""

import io
import json
import pandas as pd
import openpyxl
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

export_router = APIRouter(prefix="/api/export", tags=["Export"])

class ExportDataPayload(BaseModel):
    columns: Optional[List[str]] = []
    rows: Optional[List[Dict[str, Any]]] = []
    data: Optional[List[Dict[str, Any]]] = []
    title: Optional[str] = "JGH Data Export"
    filename: Optional[str] = "JGH_Data_Export"


def _extract_rows_and_cols(payload: ExportDataPayload):
    rows = payload.rows or payload.data or []
    cols = payload.columns or []
    if not cols and rows:
        cols = list(rows[0].keys())
    return cols, rows


@export_router.post("/csv")
def export_csv(payload: ExportDataPayload):
    cols, rows = _extract_rows_and_cols(payload)
    df = pd.DataFrame(rows, columns=cols if cols else None)

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    csv_bytes = stream.getvalue().encode("utf-8")

    filename = f"{payload.filename or 'JGH_Data_Export'}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@export_router.post("/excel")
def export_excel(payload: ExportDataPayload):
    cols, rows = _extract_rows_and_cols(payload)
    df = pd.DataFrame(rows, columns=cols if cols else None)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Data Export", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Data Export"]

        # Style header row
        header_fill = openpyxl.styles.PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        header_font = openpyxl.styles.Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font

        # Auto-fit columns
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    excel_bytes = output.getvalue()
    filename = f"{payload.filename or 'JGH_Data_Export'}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@export_router.post("/pdf")
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
    title_style = ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#1E3A8A'), alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('DocSub', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.HexColor('#64748B'), alignment=TA_CENTER)
    body_style = ParagraphStyle('DocBody', fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#0F172A'))
    tbl_cell = ParagraphStyle('TblCell', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.HexColor('#0F172A'))
    tbl_hdr = ParagraphStyle('TblHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white)

    story = []

    # Title Banner
    story.append(Paragraph("JGH INTELLIGENCE ENGINE", title_style))
    story.append(Paragraph("EXECUTIVE DATA REPORT & SUMMARY SPECIFICATION", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=4, spaceAfter=8))

    # Scorecard Banner
    total_records = len(rows)
    scorecard_data = [
        [Paragraph("<b>Report Name:</b>", body_style), Paragraph(payload.title or "JGH Data Export", body_style), Paragraph("<b>Total Records:</b>", body_style), Paragraph(str(total_records), body_style)],
        [Paragraph("<b>Source System:</b>", body_style), Paragraph("jghMasterDB (MySQL 8.0)", body_style), Paragraph("<b>Format:</b>", body_style), Paragraph("Executive PDF Summary", body_style)]
    ]
    sc_table = Table(scorecard_data, colWidths=[4.0*cm, 5.0*cm, 4.0*cm, 4.5*cm])
    sc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(sc_table)
    story.append(Spacer(1, 10))

    # Data Table (first 30 rows max for PDF)
    display_rows = rows[:30]
    display_cols = cols[:6] # Limit columns to fit page width cleanly

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

    doc.build(story)
    pdf_bytes = output.getvalue()

    filename = f"{payload.filename or 'JGH_Executive_Report'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
