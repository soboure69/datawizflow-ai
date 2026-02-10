from services.sql_executor import SQLExecutor


def test_sql_executor_can_connect_and_select_one() -> None:
    executor = SQLExecutor("sqlite+pysqlite:///:memory:")
    executor.test_connection()

    res = executor.execute("SELECT 1 AS ok")
    assert res.columns == ["ok"]
    assert res.rows == [(1,)]