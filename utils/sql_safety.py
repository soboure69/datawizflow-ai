from __future__ import annotations

import re


_FORBIDDEN = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "pragma",
    "attach",
    "detach",
    "vacuum",
    "reindex",
    "truncate",
]

_FORBIDDEN_RE = re.compile(r"\b(" + "|".join(_FORBIDDEN) + r")\b", re.IGNORECASE)
_LIMIT_RE = re.compile(r"\blimit\b", re.IGNORECASE)


def validate_readonly_sql(sql: str) -> None:
    if not sql or not sql.strip():
        raise ValueError("SQL vide")

    s = sql.strip().lstrip("(").strip()

    # Only SELECT / WITH allowed
    if not (s.lower().startswith("select") or s.lower().startswith("with")):
        raise ValueError("Seules les requêtes SELECT/WITH sont autorisées (read-only).")

    # Simple multi-statement protection
    # (au début on reste strict : refuse tout ';' pour éviter 'SELECT...; DROP ...')
    if ";" in s:
        raise ValueError("Les requêtes multi-statements sont interdites (retire le ';').")

    # Forbidden keywords
    m = _FORBIDDEN_RE.search(s)
    if m:
        raise ValueError(f"Mot-clé interdit détecté: {m.group(1)}")


def ensure_limit(sql: str, limit: int) -> str:
    s = sql.strip()
    if _LIMIT_RE.search(s):
        return s
    return f"{s}\nLIMIT {int(limit)}"