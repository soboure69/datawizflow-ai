import pandas as pd

from utils.formatters import dataframe_to_csv_bytes, dataframe_to_excel_bytes


def test_exports_csv_and_excel() -> None:
    frame = pd.DataFrame({"région": ["Nord"], "montant": [12.5]})
    csv_text = dataframe_to_csv_bytes(frame).decode("utf-8")
    assert "région" in csv_text
    assert dataframe_to_excel_bytes(frame).startswith(b"PK")


def test_pdf_report_contains_question_sql_and_value() -> None:
    from utils.formatters import dataframe_to_pdf_bytes

    frame = pd.DataFrame({"region": ["Nord"], "montant": [12.5]})
    pdf = dataframe_to_pdf_bytes(frame, question="Revenu total", sql_text="SELECT 1", language="FR")
    assert pdf.startswith(b"%PDF")
    assert b"Revenu total" in pdf
    assert b"SELECT 1" in pdf
    assert b"Nord" in pdf
