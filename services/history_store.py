from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _sqlite_path_from_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:///... is supported for internal history DB")
    return database_url.replace("sqlite:///", "", 1)


@dataclass(frozen=True)
class HistoryItem:
    id: int
    created_at: str
    question: str
    sql_text: str
    executed_sql: str
    row_count: int
    status: str
    error_message: Optional[str]
    model: Optional[str]
    language: Optional[str]
    database_url: Optional[str]


@dataclass(frozen=True)
class SavedView:
    id: int
    created_at: str
    title: str
    question: str
    sql_text: str
    model: Optional[str]
    language: Optional[str]
    database_url: Optional[str]
    description: Optional[str] = None


class HistoryStore:
    def __init__(self, internal_db_url: Optional[str] = None) -> None:
        self._db_url = internal_db_url or os.environ.get("INTERNAL_DB_URL", "sqlite:///db/internal.db")
        self._db_path = _sqlite_path_from_url(self._db_url)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    
    def _column_exists(self, cur: sqlite3.Cursor, table: str, column: str) -> bool:
        cols = cur.execute(f"PRAGMA table_info('{table}')").fetchall()
        names = {c[1] for c in cols}
        return column in names


    def _add_column_if_missing(self, cur: sqlite3.Cursor, table: str, column: str, col_type: str) -> None:
        if not self._column_exists(cur, table, column):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def ensure_schema(self) -> None:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    question TEXT NOT NULL,
                    sql_text TEXT NOT NULL,
                    executed_sql TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_query_history_created_at
                ON query_history(created_at);

                CREATE TABLE IF NOT EXISTS saved_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    question TEXT NOT NULL,
                    sql_text TEXT NOT NULL,
                    description TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_saved_views_created_at
                ON saved_views(created_at);
                """
            )
            
        
            self._add_column_if_missing(cur, "query_history", "model", "TEXT")
            self._add_column_if_missing(cur, "query_history", "language", "TEXT")
            self._add_column_if_missing(cur, "query_history", "database_url", "TEXT")

            self._add_column_if_missing(cur, "saved_views", "model", "TEXT")
            self._add_column_if_missing(cur, "saved_views", "language", "TEXT")
            self._add_column_if_missing(cur, "saved_views", "database_url", "TEXT")
            self._add_column_if_missing(cur, "saved_views", "description", "TEXT")
            
            conn.commit()
        finally:
            conn.close()

    def add_history(
        self,
        *,
        question: str,
        sql_text: str,
        executed_sql: str,
        row_count: int,
        status: str,
        error_message: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        database_url: Optional[str] = None,
    ) -> None:
        self.ensure_schema()
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO query_history(created_at, question, sql_text, executed_sql, row_count, status, error_message, model, language, database_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(timespec="seconds"),
                    question,
                    sql_text,
                    executed_sql,
                    int(row_count),
                    status,
                    error_message,
                    model,
                    language,
                    database_url,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_history(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        search_text: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[HistoryItem]:
        self.ensure_schema()
        conn = self._connect()
        try:
            sql = (
                "SELECT id, created_at, question, sql_text, executed_sql, row_count, status, error_message, model, language, database_url "
                "FROM query_history"
            )
            params: list[Any] = []
            where: list[str] = []

            if status:
                where.append("status = ?")
                params.append(status)

            if search_text and search_text.strip():
                where.append("(question LIKE ? OR sql_text LIKE ? OR executed_sql LIKE ?)")
                like = f"%{search_text.strip()}%"
                params.extend([like, like, like])

            if where:
                sql += " WHERE " + " AND ".join(where)

            sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([int(limit), int(offset)])

            rows = conn.execute(sql, tuple(params)).fetchall()
            return [HistoryItem(*r) for r in rows]
        finally:
            conn.close()

    def delete_history(self, history_id: int) -> None:
        self.ensure_schema()
        conn = self._connect()
        try:
            conn.execute("DELETE FROM query_history WHERE id = ?", (int(history_id),))
            conn.commit()
        finally:
            conn.close()

    def save_view(self, *, title: str, question: str, sql_text: str,
                  model: Optional[str] = None,
                  language: Optional[str] = None,
                  database_url: Optional[str] = None,
                  description: Optional[str] = None) -> None:
        self.ensure_schema()
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO saved_views(created_at, title, question, sql_text, model, language, database_url, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (datetime.utcnow().isoformat(timespec="seconds"), title, question, sql_text, model, language, database_url, description),
            )
            conn.commit()
        finally:
            conn.close()
    def list_saved_views(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        search_text: Optional[str] = None,
    ) -> list[SavedView]:
        self.ensure_schema()
        conn = self._connect()
        try:
            sql = (
                "SELECT id, created_at, title, question, sql_text, model, language, database_url, description "
                "FROM saved_views"
            )
            params: list[Any] = []
            where: list[str] = []

            if search_text and search_text.strip():
                where.append("(title LIKE ? OR question LIKE ? OR sql_text LIKE ?)")
                like = f"%{search_text.strip()}%"
                params.extend([like, like, like])

            if where:
                sql += " WHERE " + " AND ".join(where)

            sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([int(limit), int(offset)])

            rows = conn.execute(sql, tuple(params)).fetchall()
            return [SavedView(*r) for r in rows]
        finally:
            conn.close()

    def delete_saved_view(self, view_id: int) -> None:
        self.ensure_schema()
        conn = self._connect()
        try:
            conn.execute("DELETE FROM saved_views WHERE id = ?", (int(view_id),))
            conn.commit()
        finally:
            conn.close()
