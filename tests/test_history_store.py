from pathlib import Path

from services.history_store import HistoryStore


def test_history_store_roundtrip(tmp_path: Path) -> None:
    internal_db = tmp_path / "internal.db"
    store = HistoryStore(internal_db_url=f"sqlite:///{internal_db.as_posix()}")

    store.add_history(
        question="q",
        sql_text="SELECT 1",
        executed_sql="SELECT 1 LIMIT 50",
        row_count=1,
        status="success",
        error_message=None,
        model="mistral",
        language="FR",
        database_url="sqlite:///db/demo.db",
    )

    items = store.list_history(limit=10)
    assert len(items) == 1
    assert items[0].model == "mistral"
    assert items[0].language == "FR"
    assert items[0].database_url == "sqlite:///db/demo.db"

    assert len(store.list_history(limit=10, search_text="q")) == 1
    assert len(store.list_history(limit=10, search_text="does-not-exist")) == 0
    assert len(store.list_history(limit=10, status="success")) == 1
    assert len(store.list_history(limit=10, status="error")) == 0

    store.save_view(
        title="v1",
        question="q",
        sql_text="SELECT 1",
        model="mistral",
        language="FR",
        database_url="sqlite:///db/demo.db",
    )

    views = store.list_saved_views(limit=10)
    assert len(views) == 1
    assert views[0].title == "v1"
    assert views[0].model == "mistral"

    assert len(store.list_saved_views(limit=10, search_text="v1")) == 1
    assert len(store.list_saved_views(limit=10, search_text="does-not-exist")) == 0

    store.delete_history(items[0].id)
    assert store.list_history(limit=10) == []

    store.delete_saved_view(views[0].id)
    assert store.list_saved_views(limit=10) == []
