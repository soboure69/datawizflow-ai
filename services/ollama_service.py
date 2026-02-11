from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ollama import Client


_FENCE_RE = re.compile(r"```(?:sql)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _strip_code_fences(text: str) -> str:
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _sqlite_path_from_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:///... is supported for Phase 2 demo")
    return database_url.replace("sqlite:///", "", 1)


def _describe_sqlite_schema(database_url: str) -> str:
    db_path = _sqlite_path_from_url(database_url)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        tables = [
            r[0]
            for r in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        lines: list[str] = []
        for t in tables:
            lines.append(f"TABLE {t}(")
            cols = cur.execute(f"PRAGMA table_info('{t}')").fetchall()
            for _, name, col_type, notnull, _, pk in cols:
                nn = " NOT NULL" if int(notnull) == 1 else ""
                pk_s = " PRIMARY KEY" if int(pk) == 1 else ""
                lines.append(f"  {name} {col_type}{nn}{pk_s},")
            if lines[-1].endswith(","):
                lines[-1] = lines[-1][:-1]
            lines.append(")")
            lines.append("")
        return "\n".join(lines).strip()
    finally:
        conn.close()


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str
    model: str


class OllamaService:
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        database_url: Optional[str] = None,
    ) -> None:
        self._base_url = base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        self._model = model or os.environ.get("OLLAMA_MODEL", "mistral")
        self._database_url = database_url
        self._client = Client(base_url=self._base_url)

    @property
    def settings(self) -> OllamaSettings:
        return OllamaSettings(base_url=self._base_url, model=self._model)

    def build_prompt(self, *, question: str, schema: str, language: str) -> str:
        lang = (language or "FR").upper()
        if lang not in {"FR", "EN"}:
            lang = "EN"

        if lang == "FR":
            rules = (
                "Tu es un expert SQL (SQLite).\n"
                "Génère une requête SQL STRICTEMENT en lecture seule.\n"
                "Interdits: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA.\n"
                "Retourne UNIQUEMENT le SQL, sans explication, sans markdown." 
            )
            instruction = "Question: "
        else:
            rules = (
                "You are an expert SQL engineer (SQLite).\n"
                "Generate a STRICTLY read-only SQL query.\n"
                "Forbidden: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA.\n"
                "Return ONLY the SQL, no explanation, no markdown."
            )
            instruction = "Question: "

        return (
            f"{rules}\n\n"
            "Database schema:\n"
            f"{schema}\n\n"
            f"{instruction}{question}\n"
            "SQL:"
        )

    def generate_sql(self, *, question: str, language: str = "FR", schema: Optional[str] = None) -> str:
        if not question or not question.strip():
            raise ValueError("question is required")

        schema_text = schema
        if schema_text is None:
            if not self._database_url:
                raise ValueError("schema is None and database_url was not provided")
            schema_text = _describe_sqlite_schema(self._database_url)

        prompt = self.build_prompt(question=question.strip(), schema=schema_text, language=language)

        resp = self._client.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": "You output only SQL."},
                {"role": "user", "content": prompt},
            ],
        )

        content = resp["message"]["content"]
        sql = _strip_code_fences(content)
        return sql.strip()
