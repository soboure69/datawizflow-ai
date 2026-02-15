import pytest

from utils.sql_safety import ensure_limit, validate_readonly_sql


def test_validate_readonly_sql_accepts_select() -> None:
    validate_readonly_sql("SELECT 1")


def test_validate_readonly_sql_accepts_with() -> None:
    validate_readonly_sql("WITH x AS (SELECT 1) SELECT * FROM x")


def test_validate_readonly_sql_rejects_non_select() -> None:
    with pytest.raises(ValueError):
        validate_readonly_sql("UPDATE sales SET revenue = 0")


def test_validate_readonly_sql_rejects_semicolon() -> None:
    with pytest.raises(ValueError):
        validate_readonly_sql("SELECT 1;")


def test_ensure_limit_adds_limit_when_missing() -> None:
    assert ensure_limit("SELECT 1", 200).endswith("LIMIT 200")


def test_ensure_limit_does_not_duplicate_limit() -> None:
    sql = "SELECT 1 LIMIT 5"
    assert ensure_limit(sql, 200) == sql
