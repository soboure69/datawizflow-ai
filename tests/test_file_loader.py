from services.file_loader import FileLoader, profile_dataframe


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


def test_rejects_unknown_extension(tmp_path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")
    try:
        FileLoader().load(path)
    except ValueError as exc:
        assert "non supporté" in str(exc)
    else:
        raise AssertionError("expected ValueError")
