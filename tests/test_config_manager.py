import os
from pathlib import Path

from services.config_manager import ConfigManager


def test_load_config_substitutes_env_var(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "config.yaml"
    config_path.write_text(
        "database:\n"
        "  url: ${DATABASE_URL}\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("DATABASE_URL", "sqlite:///db/test.db")

    cfg = ConfigManager(config_path=str(config_path)).load()
    assert cfg.database_url == "sqlite:///db/test.db"