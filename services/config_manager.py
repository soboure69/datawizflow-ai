from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _substitute_env_vars(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return _ENV_PATTERN.sub(repl, value)


def _walk_and_substitute(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _walk_and_substitute(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_substitute(v) for v in obj]
    if isinstance(obj, str):
        return _substitute_env_vars(obj)
    return obj


@dataclass(frozen=True)
class AppConfig:
    raw: dict[str, Any]

    @property
    def database_url(self) -> str:
        db = self.raw.get("database", {})
        url = db.get("url")
        if not url or not isinstance(url, str):
            raise ValueError("Missing database.url in config")
        return url


class ConfigManager:
    def __init__(self, config_path: str = "config/config.yaml") -> None:
        self._path = Path(config_path)

    def load(self) -> AppConfig:
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")

        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        data = _walk_and_substitute(data)
        return AppConfig(raw=data)