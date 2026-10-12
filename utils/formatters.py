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
