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


def _or_env(value: Any, env_name: str, default: str) -> str:
    if isinstance(value, str) and value and not value.startswith("${"):
        return value
    return os.environ.get(env_name, default)


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

    def ollama_settings(self) -> dict[str, Any]:
        raw = self.raw.get("ollama") or {}
        return {
            "url": _or_env(raw.get("url"), "OLLAMA_URL", "http://localhost:11434"),
            "model": _or_env(raw.get("model"), "OLLAMA_MODEL", "mistral"),
            "temperature": float(raw.get("temperature", os.environ.get("OLLAMA_TEMPERATURE", 0.3))),
            "timeout": float(raw.get("timeout", os.environ.get("OLLAMA_TIMEOUT", 60))),
        }

    def dataviz_settings(self) -> dict[str, str]:
        raw = self.raw.get("dataviz") or {}
        library = str(raw.get("default_library") or "plotly")
        theme = str(raw.get("theme") or "light")
        return {"default_library": library, "theme": theme}


class ConfigManager:
    def __init__(self, config_path: str = "config/config.yaml") -> None:
        self._path = Path(config_path)

    def load(self) -> AppConfig:
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")

        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        data = _walk_and_substitute(data)
        return AppConfig(raw=data)

    def load_raw(self) -> dict[str, Any]:
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")
        return yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}

    def save_raw(self, data: dict[str, Any]) -> None:
        self._path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )