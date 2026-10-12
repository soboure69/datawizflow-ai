from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


def sqlite_url(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def safe_table_name(name: str) -> str:
    stem = Path(name).stem.lower()
    cleaned = re.sub(r"[^a-z0-9_]", "_", stem).strip("_")
    if not cleaned:
        cleaned = "uploaded_data"
    if cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned[:60]


def materialize_dataframe(df: pd.DataFrame, filename: str, dest_dir: str | Path = "uploads") -> tuple[str, str]:
    """Écrit le DataFrame dans un SQLite local pour le réutiliser en NL2SQL."""
    table = safe_table_name(filename)
    folder = Path(dest_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{table}.db"
    engine = create_engine(sqlite_url(path), future=True)
    df.to_sql(table, engine, if_exists="replace", index=False)
    engine.dispose()
    return sqlite_url(path), table
