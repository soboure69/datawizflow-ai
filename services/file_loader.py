from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Union

import pandas as pd

Source = Union[str, Path, bytes, io.BytesIO]
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_UPLOAD_ROWS = 200_000
MAX_UPLOAD_COLUMNS = 200


class FileLoader:
    """Charge un fichier tabulaire (CSV, Excel, Parquet, JSON) en DataFrame."""

    def load(self, source: Source, filename: str | None = None) -> pd.DataFrame:
        name = filename or (str(source) if isinstance(source, (str, Path)) else "upload")
        ext = Path(name).suffix.lower()
        if ext == ".csv":
            return pd.read_csv(source)
        if ext in {".xlsx", ".xls"}:
            return pd.read_excel(source)
        if ext == ".parquet":
            return pd.read_parquet(source)
        if ext == ".json":
            return pd.read_json(source)
        raise ValueError(f"Format non supporté : {ext or name}")

    def load_bytes(self, data: bytes, filename: str) -> pd.DataFrame:
        if len(data) > MAX_UPLOAD_BYTES:
            raise ValueError("Fichier trop volumineux (maximum 25 Mo).")
        frame = self.load(io.BytesIO(data), filename=filename)
        if len(frame) > MAX_UPLOAD_ROWS or len(frame.columns) > MAX_UPLOAD_COLUMNS:
            raise ValueError("Jeu de données trop volumineux (200 000 lignes ou 200 colonnes maximum).")
        return frame


def profile_dataframe(df: pd.DataFrame, *, filename: str = "", size_bytes: int = 0) -> dict[str, Any]:
    """Résumé utile à l'écran Connexion et au prompt DataViz."""
    numeric = df.select_dtypes(include="number")
    stats: dict[str, dict[str, float]] = {}
    if not numeric.empty:
        described = numeric.describe().to_dict()
        for col, values in described.items():
            stats[str(col)] = {str(k): float(v) for k, v in values.items() if pd.notna(v)}

    samples: dict[str, list[str]] = {}
    for col in df.columns:
        values = df[col].dropna().astype(str).head(3).tolist()
        samples[str(col)] = values

    return {
        "filename": filename,
        "rows": int(len(df)),
        "columns": [str(c) for c in df.columns],
        "dtypes": {str(c): str(df[c].dtype) for c in df.columns},
        "nulls": {str(c): int(v) for c, v in df.isna().sum().items()},
        "nunique": {str(c): int(v) for c, v in df.nunique(dropna=True).items()},
        "size_bytes": int(size_bytes),
        "numeric_stats": stats,
        "samples": samples,
    }
