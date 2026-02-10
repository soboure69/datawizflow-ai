from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]


class SQLExecutor:
    def __init__(self, database_url: str) -> None:
        self._engine: Engine = create_engine(database_url, future=True)

    @property
    def engine(self) -> Engine:
        return self._engine

    def test_connection(self) -> None:
        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def execute(self, sql: str, params: Optional[dict[str, Any]] = None) -> QueryResult:
        with self._engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                return QueryResult(columns=columns, rows=[tuple(r) for r in rows])
            return QueryResult(columns=[], rows=[])