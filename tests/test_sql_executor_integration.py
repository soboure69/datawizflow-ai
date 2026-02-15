import sqlite3
from pathlib import Path

from services.sql_executor import SQLExecutor


def test_sql_executor_can_query_sqlite_file(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.execute("INSERT INTO t(v) VALUES ('a'), ('b')")
        conn.commit()
    finally:
        conn.close()

    executor = SQLExecutor(f"sqlite+pysqlite:///{db_path.as_posix()}")
    res = executor.execute("SELECT COUNT(*) AS n FROM t")
    assert res.columns == ["n"]
    assert res.rows == [(2,)]
