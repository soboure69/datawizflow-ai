from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import yaml
from cryptography.fernet import Fernet


class ConnectionStore:
    """Profils de connexion YAML, mots de passe chiffrés avec Fernet."""

    def __init__(self, path: str | Path = "config/connections.yaml", fernet_key: str | None = None) -> None:
        self._path = Path(path)
        self._fernet = Fernet(_resolve_key(fernet_key))

    def list_profiles(self) -> list[dict[str, Any]]:
        data = self._load()
        profiles = data.get("profiles") or {}
        return [dict(value) for value in profiles.values()]

    def get(self, name: str) -> dict[str, Any] | None:
        profiles = self._load().get("profiles") or {}
        raw = profiles.get(name)
        return dict(raw) if raw else None

    def save_profile(self, profile: dict[str, Any]) -> None:
        name = str(profile.get("name") or "").strip()
        if not name:
            raise ValueError("Le profil doit avoir un nom.")
        stored = dict(profile)
        stored["name"] = name
        password = stored.get("password") or ""
        if password and not str(password).startswith("enc:"):
            stored["password"] = self.encrypt(str(password))
        data = self._load()
        profiles = data.setdefault("profiles", {})
        profiles[name] = stored
        self._dump(data)

    def delete_profile(self, name: str) -> None:
        data = self._load()
        profiles = data.get("profiles") or {}
        profiles.pop(name, None)
        data["profiles"] = profiles
        self._dump(data)

    def encrypt(self, value: str) -> str:
        if not value:
            return ""
        token = self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return f"enc:{token}"

    def decrypt(self, value: str) -> str:
        if not value:
            return ""
        if value.startswith("enc:"):
            return self._fernet.decrypt(value[4:].encode("utf-8")).decode("utf-8")
        return value

    def build_url(self, profile: dict[str, Any]) -> str:
        db_type = str(profile.get("db_type") or "sqlite").lower()
        if db_type == "sqlite":
            path = str(profile.get("path") or "").strip()
            if not path:
                raise ValueError("Chemin SQLite manquant.")
            return "sqlite:///" + Path(path).as_posix()

        driver = {
            "postgresql": "postgresql+psycopg2",
            "mysql": "mysql+pymysql",
            "mssql": "mssql+pyodbc",
        }.get(db_type)
        if not driver:
            raise ValueError(f"Type de base non supporté : {db_type}")

        user = quote_plus(str(profile.get("user") or ""))
        password = quote_plus(self.decrypt(str(profile.get("password") or "")))
        host = str(profile.get("host") or "localhost")
        port = int(profile.get("port") or _default_port(db_type))
        database = quote_plus(str(profile.get("database") or ""))
        url = f"{driver}://{user}:{password}@{host}:{port}/{database}"
        if db_type == "mssql":
            url += "?driver=ODBC+Driver+17+for+SQL+Server"
        return url

    def public_view(self, profile: dict[str, Any]) -> dict[str, Any]:
        view = dict(profile)
        if view.get("password"):
            view["password"] = "***"
        return view

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"profiles": {}}
        return yaml.safe_load(self._path.read_text(encoding="utf-8")) or {"profiles": {}}

    def _dump(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def mask_url(url: str) -> str:
    """Masque le mot de passe dans une URL SQLAlchemy."""
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds, tail = rest.split("@", 1)
    if ":" not in creds:
        return url
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{tail}"


def _default_port(db_type: str) -> int:
    return {"postgresql": 5432, "mysql": 3306, "mssql": 1433}.get(db_type, 5432)


def _resolve_key(explicit: str | None) -> bytes:
    if explicit:
        return explicit.encode("utf-8")
    env_key = os.environ.get("FERNET_KEY", "").strip()
    if env_key:
        return env_key.encode("utf-8")
    if os.environ.get("APP_ENV", "development").lower() == "production":
        raise RuntimeError("FERNET_KEY is required in production.")
    key_path = Path("config/.fernet_key")
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip().encode("utf-8")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    key_path.write_text(key.decode("utf-8"), encoding="utf-8")
    return key
