from __future__ import annotations

import io

import pandas as pd
from openpyxl.styles import Font


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Excel avec en-têtes en gras et largeur de colonnes ajustée."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")
        sheet = writer.sheets["results"]
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for column in sheet.columns:
            length = 0
            for cell in column:
                value = "" if cell.value is None else str(cell.value)
                length = max(length, len(value))
            sheet.column_dimensions[column[0].column_letter].width = min(length + 2, 40)
    return buffer.getvalue()


def dataframe_to_parquet_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    return buffer.getvalue()


def dataframe_to_pdf_bytes(
    df: pd.DataFrame,
    question: str = "",
    sql_text: str = "",
    language: str = "FR",
) -> bytes:
    """Rapport PDF : question, SQL exécuté et un extrait du tableau."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font = _pdf_font()
    english = (language or "FR").upper() == "EN"
    labels = {
        "title": "DataWizflow report" if english else "Rapport DataWizflow",
        "question": "Question" if english else "Question",
        "sql": "Executed SQL" if english else "SQL exécuté",
        "rows": "Rows" if english else "Lignes",
        "excerpt": "First rows of the filtered table." if english else "Premières lignes du tableau filtré.",
    }
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("pdf_title", parent=styles["Heading1"], fontName=font, fontSize=16, leading=20)
    body = ParagraphStyle("pdf_body", parent=styles["Normal"], fontName=font, fontSize=9, leading=12)
    cell = ParagraphStyle("pdf_cell", parent=styles["Normal"], fontName=font, fontSize=8, leading=10)

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=labels["title"],
        leftMargin=36,
        rightMargin=36,
        pageCompression=0,
    )
    story: list[object] = [Paragraph(_xml(labels["title"]), title_style), Spacer(1, 12)]
    if question.strip():
        story.append(Paragraph(f"<b>{labels['question']}</b>", body))
        story.append(Paragraph(_xml(question.strip()).replace("\n", "<br/>"), body))
        story.append(Spacer(1, 8))
    if sql_text.strip():
        story.append(Paragraph(f"<b>{labels['sql']}</b>", body))
        story.append(Paragraph(_xml(sql_text.strip()).replace("\n", "<br/>"), body))
        story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>{labels['rows']}</b> : {len(df)}", body))
    story.append(Paragraph(labels["excerpt"], body))
    story.append(Spacer(1, 8))
    story.append(_pdf_table(df, cell))
    document.build(story)
    return buffer.getvalue()


def _pdf_table(df: pd.DataFrame, cell_style: object) -> object:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Table, TableStyle

    columns = [str(column) for column in list(df.columns)[:6]]
    preview = df.iloc[:25, : len(columns)] if columns else df.iloc[:0]
    header_style = ParagraphStyle("pdf_header", parent=cell_style, textColor=colors.white)
    header = [Paragraph(f"<b>{_xml(column)}</b>", header_style) for column in columns]
    rows = [header]
    for _, row in preview.iterrows():
        rows.append([Paragraph(_xml(_cell_text(row[column])), cell_style) for column in columns])
    if not columns:
        rows = [[Paragraph("—", cell_style)]]
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d0d7de")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _pdf_font() -> str:
    from pathlib import Path

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if "ReportSans" in pdfmetrics.getRegisteredFontNames():
        return "ReportSans"
    for candidate in (
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ):
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("ReportSans", str(candidate)))
            pdfmetrics.registerFontFamily(
                "ReportSans",
                normal="ReportSans",
                bold="ReportSans",
                italic="ReportSans",
                boldItalic="ReportSans",
            )
            return "ReportSans"
    return "Helvetica"


def _cell_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    text = str(value)
    return text if len(text) <= 80 else text[:77] + "..."


def _xml(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
