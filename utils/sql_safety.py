from __future__ import annotations

import re


_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|pragma|attach|detach|vacuum|reindex|truncate|copy|grant|revoke|call|exec(?:ute)?|load_extension|into|pg_read_file|pg_read_binary_file|pg_ls_dir|dblink)\b",
    re.IGNORECASE,
)
_COMMENTS_AND_STRINGS = re.compile(r"(?:--[^\r\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\")")


def _tokens_only(sql: str) -> str:
    return _COMMENTS_AND_STRINGS.sub(" ", sql)


def validate_readonly_sql(sql: str) -> None:
    if not sql or not sql.strip():
        raise ValueError("SQL vide")
    normalized = _tokens_only(sql).strip().lstrip("(").strip()
    if ";" in normalized:
        raise ValueError("Les requêtes multi-statements sont interdites.")
    if not re.match(r"^(select|with)\b", normalized, re.IGNORECASE):
        raise ValueError("Seules les requêtes SELECT/WITH sont autorisées (read-only).")
    forbidden = _FORBIDDEN.search(normalized)
    if forbidden:
        raise ValueError(f"Mot-clé interdit détecté: {forbidden.group(1)}")


def ensure_limit(sql: str, limit: int) -> str:
    """Always cap the outer result, even if LIMIT occurs in a comment or CTE."""
    validate_readonly_sql(sql)
    return f"SELECT * FROM ({sql.strip()}) AS _datawizflow_result LIMIT {int(limit)}"
