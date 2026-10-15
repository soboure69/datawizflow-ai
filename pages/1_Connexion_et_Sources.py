import pandas as pd
import streamlit as st

from services.config_manager import ConfigManager
from services.connection_store import ConnectionStore, mask_url
from services.dataset_store import materialize_dataframe
from services.file_loader import FileLoader, MAX_UPLOAD_BYTES, profile_dataframe, truncation_messages
from services.sql_executor import SQLExecutor
from utils.sql_safety import ensure_limit, validate_readonly_sql
from utils.ui import L, init_app, remember_dataset, show_safe_error, sidebar_language


def _default_port(db_type: str) -> int:
    return {"postgresql": 5432, "mysql": 3306, "mssql": 1433}.get(db_type, 5432)


def _ensure_demo_profile(connection_store: ConnectionStore) -> None:
    if connection_store.list_profiles():
        return
    url = ConfigManager().load().database_url
    if not url.startswith("sqlite:///"):
        return
    connection_store.save_profile(
        {"name": "demo", "db_type": "sqlite", "path": url.replace("sqlite:///", "", 1), "password": ""}
    )


def _test_url(url: str) -> None:
    try:
        SQLExecutor(url).test_connection()
        st.success(L("connection_ok"))
    except Exception as exc:
        show_safe_error(exc, "sources")


init_app()
sidebar_language()
st.title(L("connection_title"))

store = ConnectionStore()
_ensure_demo_profile(store)

st.subheader(L("profiles"))
for profile in store.list_profiles():
    name = str(profile["name"])
    kind = str(profile.get("db_type") or "sqlite")
    target = profile.get("path") or profile.get("database") or ""
    st.write(f"**{name}** · {kind} · {target}")
    use_col, test_col, delete_col = st.columns(3)
    with use_col:
        if st.button(L("use_profile"), key=f"use_{name}"):
            st.session_state["active_database_url"] = store.build_url(profile)
            st.session_state["active_source_label"] = name
            st.session_state["active_dialect"] = kind
            st.session_state.pop("schema_view", None)
            st.rerun()
    with test_col:
        if st.button(L("test_connection"), key=f"test_{name}"):
            _test_url(store.build_url(profile))
    with delete_col:
        if st.button(L("delete_profile"), key=f"del_{name}"):
            store.delete_profile(name)
            st.rerun()

name = st.text_input(L("profile_name"))
db_type = st.selectbox(L("db_type"), ["sqlite", "postgresql", "mysql", "mssql"])
path = ""
host = "localhost"
user = ""
password = ""
database = ""
port = _default_port(db_type)
if db_type == "sqlite":
    path = st.text_input(L("sqlite_path"), value="db/demo.db")
else:
    host = st.text_input(L("host"), value="localhost")
    port = int(st.number_input(L("port"), min_value=1, max_value=65535, value=_default_port(db_type)))
    user = st.text_input(L("user"))
    password = st.text_input(L("password"), type="password", help=L("password_hint"))
    database = st.text_input(L("database"))
submitted = st.button(L("save_profile"), key="save_profile_button")

if submitted:
    payload = {
        "name": name.strip(),
        "db_type": db_type,
        "path": path.strip(),
        "host": host.strip(),
        "port": port,
        "user": user.strip(),
        "database": database.strip(),
    }
    existing = store.get(name.strip()) if name.strip() else None
    if password:
        payload["password"] = password
    elif existing and existing.get("password"):
        payload["password"] = existing["password"]
    else:
        payload["password"] = ""
    try:
        store.save_profile(payload)
        st.success(L("settings_saved"))
    except Exception as exc:
        show_safe_error(exc, "sources")

st.subheader(L("schema_title"))
active_url = str(st.session_state.get("active_database_url") or "")
st.caption(mask_url(active_url))
if st.button(L("show_schema")):
    try:
        st.session_state["schema_view"] = SQLExecutor(active_url).get_schema()
    except Exception as exc:
        st.session_state["schema_view"] = ""
        show_safe_error(exc, "sources")
schema_view = st.session_state.get("schema_view")
if schema_view:
    st.code(schema_view, language="sql")

st.subheader(L("sql_examples"))
sql_text = st.text_area("SQL", value="SELECT 1 AS ok", height=120, key="connection_sql")
if st.button(L("run"), key="connection_run"):
    try:
        validate_readonly_sql(sql_text)
        result = SQLExecutor(active_url).execute(ensure_limit(sql_text, 200), timeout=30)
        frame = pd.DataFrame(result.rows, columns=result.columns) if result.columns else pd.DataFrame()
        st.dataframe(frame, use_container_width=True)
    except Exception as exc:
        show_safe_error(exc, "sources")

st.subheader(L("upload_title"))
st.caption(L("upload_help"))
uploads = st.file_uploader(
    L("upload_title"),
    type=["csv", "xlsx", "xls", "parquet", "json"],
    accept_multiple_files=True,
)
known_ids = list(st.session_state.get("loaded_file_ids") or [])
if uploads:
    loader = FileLoader()
    for uploaded in uploads:
        file_id = str(getattr(uploaded, "file_id", uploaded.name))
        if file_id not in known_ids:
            try:
                if int(getattr(uploaded, "size", 0)) > MAX_UPLOAD_BYTES:
                    raise ValueError("Fichier trop volumineux (maximum 25 Mo).")
                raw = uploaded.getvalue()
                frame = loader.load_bytes(raw, uploaded.name)
                url, table = materialize_dataframe(frame, uploaded.name)
                remember_dataset(uploaded.name, url, table, frame)
                known_ids.append(file_id)
                st.session_state["loaded_file_ids"] = known_ids
            except Exception as exc:
                st.error(f"{uploaded.name}: {exc}")
                continue
        frame = (st.session_state.get("frames") or {}).get(uploaded.name)
        if frame is None:
            continue
        info = profile_dataframe(frame, filename=uploaded.name, size_bytes=int(frame.memory_usage(deep=True).sum()))
        for key, kwargs in truncation_messages(frame):
            st.warning(L(key, **kwargs))
        st.markdown(
            f"**{uploaded.name}** · {L('rows')} {info['rows']} · {L('columns')} {len(info['columns'])}"
        )
        st.write(L("preview"))
        st.dataframe(frame.head(5), use_container_width=True)
        summary = pd.DataFrame(
            {
                "column": info["columns"],
                "dtype": [info["dtypes"][col] for col in info["columns"]],
                "nulls": [info["nulls"][col] for col in info["columns"]],
                "nunique": [info["nunique"][col] for col in info["columns"]],
            }
        )
        st.dataframe(summary, use_container_width=True)
        if info["numeric_stats"]:
            st.write(L("numeric_stats"))
            st.json(info["numeric_stats"])

if st.button(L("clear_uploads")):
    st.session_state["datasets"] = []
    st.session_state["frames"] = {}
    st.session_state["loaded_file_ids"] = []
    st.rerun()
