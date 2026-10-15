import pytest

from services.file_loader import FileLoader, profile_dataframe
import services.file_loader as file_loader


def test_load_csv_and_profile(tmp_path) -> None:
    path = tmp_path / "ventes.csv"
    path.write_text("region,revenue\nNorth,10\nSouth,\n", encoding="utf-8")
    frame = FileLoader().load(path)
    info = profile_dataframe(frame, filename="ventes.csv", size_bytes=path.stat().st_size)
    assert info["rows"] == 2
    assert info["nulls"]["revenue"] == 1
    assert info["nunique"]["region"] == 2
    assert "revenue" in info["numeric_stats"]


def test_load_json_records(tmp_path) -> None:
    path = tmp_path / "rows.json"
    path.write_text('[{"name": "A", "n": 1}, {"name": "B", "n": 2}]', encoding="utf-8")
    frame = FileLoader().load(path)
    assert list(frame["name"]) == ["A", "B"]


def test_load_bytes_keeps_the_first_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_loader, "MAX_UPLOAD_ROWS", 2)
    payload = "a\n1\n2\n3\n".encode()
    frame = FileLoader().load_bytes(payload, "lots.csv")
    assert list(frame["a"]) == [1, 2]
    assert frame.attrs["truncation"]["rows"] == (3, 2)
    assert file_loader.truncation_messages(frame)[0][0] == "upload_truncated_rows"


def test_load_bytes_keeps_the_first_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(file_loader, "MAX_UPLOAD_COLUMNS", 1)
    frame = FileLoader().load_bytes(b"a,b\n1,2\n", "wide.csv")
    assert list(frame.columns) == ["a"]
    assert frame.attrs["truncation"]["columns"] == (2, 1)


def test_rejects_unknown_extension(tmp_path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")
    try:
        FileLoader().load(path)
    except ValueError as exc:
        assert "non supporté" in str(exc)
    else:
        raise AssertionError("expected ValueError")
