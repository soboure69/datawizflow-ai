from pathlib import Path

import streamlit as st

from services.config_manager import ConfigManager
from services.connection_store import ConnectionStore
from services.speech_to_text import whisper_status
from services.sql_executor import SQLExecutor
from utils.ui import L, init_app, ollama_from_session, show_safe_error, sidebar_language, tail_logs


def _write_theme(theme: str) -> None:
    folder = Path(".streamlit")
    folder.mkdir(parents=True, exist_ok=True)
    base = "dark" if theme == "dark" else "light"
    (folder / "config.toml").write_text(f"[theme]\nbase = \"{base}\"\n", encoding="utf-8")


init_app()
sidebar_language()
st.title(L("config_title"))

ollama = ollama_from_session()
with st.form("ollama_form"):
    url = st.text_input(L("ollama_url"), value=str(st.session_state.get("ollama_url")))
    models: list[str] = []
    try:
        if ollama.ping():
            models = ollama.list_models()
    except Exception:
        models = []
    current_model = str(st.session_state.get("ollama_model") or "mistral")
    if models:
        index = models.index(current_model) if current_model in models else 0
        model = st.selectbox(L("model"), models, index=index)
    else:
        model = st.text_input(L("model"), value=current_model)
    current_temperature = float(st.session_state.get("ollama_temperature") or 0.3)
    current_temperature = min(1.0, max(0.1, round(current_temperature, 1)))
    temperature = st.slider(L("temperature"), min_value=0.1, max_value=1.0, value=current_temperature, step=0.1)
    timeout = st.number_input(L("timeout"), min_value=5, max_value=300, value=int(st.session_state.get("ollama_timeout") or 60))
    library = st.selectbox(L("default_library"), ["plotly", "matplotlib"], index=0 if st.session_state.get("viz_library") == "plotly" else 1)
    theme = st.selectbox(L("theme"), ["light", "dark"], index=0 if st.session_state.get("viz_theme") != "dark" else 1)
    saved = st.form_submit_button(L("save_settings"))

if saved:
    st.session_state["ollama_url"] = url.strip()
    st.session_state["ollama_model"] = str(model).strip()
    st.session_state["ollama_temperature"] = float(temperature)
    st.session_state["ollama_timeout"] = float(timeout)
    st.session_state["viz_library"] = library
    st.session_state["viz_theme"] = theme
    manager = ConfigManager()
    raw = manager.load_raw()
    raw.setdefault("ollama", {})
    raw["ollama"]["url"] = url.strip()
    raw["ollama"]["model"] = str(model).strip()
    raw["ollama"]["temperature"] = float(temperature)
    raw["ollama"]["timeout"] = float(timeout)
    raw.setdefault("dataviz", {})
    raw["dataviz"]["default_library"] = library
    raw["dataviz"]["theme"] = theme
    manager.save_raw(raw)
    _write_theme(theme)
    st.success(L("settings_saved"))
    st.caption(L("theme_hint"))

st.subheader(L("diagnostics"))
fresh = ollama_from_session()
if fresh.ping():
    st.success(L("ollama_up"))
else:
    st.error(L("ollama_down"))

try:
    SQLExecutor(str(st.session_state.get("active_database_url"))).test_connection()
    st.success(L("db_up"))
except Exception as exc:
    show_safe_error(exc, "configuration")

whisper_ok, whisper_detail = whisper_status()
if whisper_ok:
    st.success(L("whisper_up"))
else:
    st.warning(f"{L('whisper_down')} ({whisper_detail})")

st.subheader(L("profiles"))
store = ConnectionStore()
for profile in store.list_profiles():
    name = str(profile["name"])
    cols = st.columns([3, 1])
    cols[0].write(f"{name} · {profile.get('db_type')}")
    if cols[1].button(L("test_connection"), key=f"cfg_test_{name}"):
        try:
            SQLExecutor(store.build_url(profile)).test_connection()
            st.success(L("connection_ok"))
        except Exception as exc:
            show_safe_error(exc, "configuration")

st.subheader(L("logs"))
lines = tail_logs(50)
if not lines:
    st.caption(L("no_logs"))
else:
    st.code("\n".join(lines))
