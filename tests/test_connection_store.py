from cryptography.fernet import Fernet

from services.connection_store import ConnectionStore, mask_url


def test_password_is_encrypted_and_url_is_built(tmp_path) -> None:
    store = ConnectionStore(path=tmp_path / "connections.yaml", fernet_key=Fernet.generate_key().decode())
    store.save_profile(
        {
            "name": "pg",
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "user": "analyst",
            "password": "secret",
            "database": "app",
        }
    )
    stored = store.get("pg")
    assert stored is not None
    assert str(stored["password"]).startswith("enc:")
    assert store.decrypt(stored["password"]) == "secret"
    assert store.public_view(stored)["password"] == "***"
    url = store.build_url(stored)
    assert url.startswith("postgresql+psycopg2://analyst:secret@localhost:5432/app")
    assert mask_url(url) == "postgresql+psycopg2://analyst:***@localhost:5432/app"


def test_sqlite_profile_url(tmp_path) -> None:
    store = ConnectionStore(path=tmp_path / "connections.yaml", fernet_key=Fernet.generate_key().decode())
    store.save_profile({"name": "demo", "db_type": "sqlite", "path": "db/demo.db", "password": ""})
    assert store.build_url(store.get("demo")) == "sqlite:///db/demo.db"
