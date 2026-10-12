from sqlalchemy import create_engine, text

from services.schema_service import describe_schema, dialect_label


def test_describe_schema_includes_keys(tmp_path) -> None:
    path = tmp_path / "schema.db"
    url = "sqlite:///" + path.as_posix()
    engine = create_engine(url, future=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE regions (region_id INTEGER PRIMARY KEY, region_name TEXT NOT NULL)"))
        conn.execute(
            text(
                "CREATE TABLE sales (sale_id INTEGER PRIMARY KEY, region_id INTEGER, "
                "FOREIGN KEY(region_id) REFERENCES regions(region_id))"
            )
        )
    schema = describe_schema(url)
    assert "TABLE: sales" in schema
    assert "PRIMARY KEY" in schema
    assert "FOREIGN KEY" in schema
    assert dialect_label(url) == "SQLite"
