from __future__ import annotations

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine


_DIALECT_LABELS = {
    "sqlite": "SQLite",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mssql": "MSSQL",
}


def dialect_label(database_url: str, engine: Engine | None = None) -> str:
    """Nom de dialecte lisible pour le prompt NL2SQL."""
    eng = engine or create_engine(database_url, future=True)
    name = eng.dialect.name
    return _DIALECT_LABELS.get(name, name)


def describe_schema(database_url: str) -> str:
    """Décrit tables, colonnes, clés primaires et clés étrangères."""
    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    lines: list[str] = []
    for table in inspector.get_table_names():
        pk_cols = set(inspector.get_pk_constraint(table).get("constrained_columns") or [])
        fk_by_col: dict[str, str] = {}
        for fk in inspector.get_foreign_keys(table):
            referred = fk.get("referred_table") or ""
            referred_cols = fk.get("referred_columns") or []
            for local, remote in zip(fk.get("constrained_columns") or [], referred_cols):
                fk_by_col[local] = f"{referred}.{remote}"

        lines.append(f"TABLE: {table}")
        for col in inspector.get_columns(table):
            name = str(col["name"])
            col_type = str(col.get("type") or "UNKNOWN")
            flags: list[str] = [col_type]
            if name in pk_cols:
                flags.append("PRIMARY KEY")
            if not col.get("nullable", True):
                flags.append("NOT NULL")
            if name in fk_by_col:
                flags.append(f"FOREIGN KEY → {fk_by_col[name]}")
            lines.append(f"- {name} ({', '.join(flags)})")
        lines.append("")

    return "\n".join(lines).strip()
