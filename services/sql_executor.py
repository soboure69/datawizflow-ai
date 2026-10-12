from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from utils.sql_safety import validate_readonly_sql


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]


class SQLExecutor:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._engine: Engine = create_engine(database_url, future=True, pool_pre_ping=True)

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def database_url(self) -> str:
        return self._database_url

    def test_connection(self) -> None:
        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def get_schema(self) -> str:
        from services.schema_service import describe_schema
        return describe_schema(self._database_url)

    def get_dialect(self) -> str:
        from services.schema_service import dialect_label
        return dialect_label(self._database_url, engine=self._engine)

    def explain(self, sql: str) -> None:
        validate_readonly_sql(sql)
        with self._engine.connect() as conn:
            self._configure_readonly_connection(conn, 30)
            conn.execute(text(f"EXPLAIN {sql}"))

    def execute(
        self, sql: str, params: Optional[dict[str, Any]] = None, *, timeout: Optional[float] = None,
        max_rows: Optional[int] = None,
    ) -> QueryResult:
        validate_readonly_sql(sql)
        with self._engine.connect() as conn:
            self._configure_readonly_connection(conn, timeout)
            result = conn.execute(text(sql), params or {})
            if result.returns_rows:
                rows = result.fetchmany(max_rows) if max_rows else result.fetchall()
                return QueryResult(columns=list(result.keys()), rows=[tuple(row) for row in rows])
            return QueryResult(columns=[], rows=[])

    def _configure_readonly_connection(self, conn: Any, timeout: Optional[float]) -> None:
        """Use server-side limits; a least-privilege database role is still mandatory."""
        seconds = max(1, int(timeout or 30))
        dialect = self._engine.dialect.name
        if dialect == "sqlite":
            conn.exec_driver_sql("PRAGMA query_only = ON")
        elif dialect == "postgresql":
            conn.exec_driver_sql("SET TRANSACTION READ ONLY")
            conn.exec_driver_sql(f"SET LOCAL statement_timeout = {seconds * 1000}")
        elif dialect == "mysql":
            conn.exec_driver_sql("SET SESSION TRANSACTION READ ONLY")
            conn.exec_driver_sql(f"SET SESSION MAX_EXECUTION_TIME = {seconds * 1000}")
