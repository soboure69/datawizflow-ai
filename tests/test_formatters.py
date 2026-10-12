import pandas as pd

from utils.formatters import dataframe_to_csv_bytes, dataframe_to_excel_bytes


def test_exports_csv_and_excel() -> None:
    frame = pd.DataFrame({"région": ["Nord"], "montant": [12.5]})
    csv_text = dataframe_to_csv_bytes(frame).decode("utf-8")
    assert "région" in csv_text
    assert dataframe_to_excel_bytes(frame).startswith(b"PK")
