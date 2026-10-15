from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.config_manager import ConfigManager
from services.connection_store import ConnectionStore, mask_url
from services.ollama_service import OllamaService
from utils.formatters import (
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    dataframe_to_parquet_bytes,
    dataframe_to_pdf_bytes,
)
from utils.i18n import translate
from utils.logger import get_logger
from utils.auth import require_authentication


def init_app() -> None:
    """Charge .env et prépare l'état de session partagé entre les pages."""
    load_dotenv()
    cfg = ConfigManager().load()
    ollama = cfg.ollama_settings()
    viz = cfg.dataviz_settings()
    app_cfg = cfg.raw.get("app") or {}
    st.session_state.setdefault("language", str(app_cfg.get("default_language") or "FR"))
    st.session_state.setdefault("active_database_url", cfg.database_url)
    st.session_state.setdefault("active_source_label", "config")
    st.session_state.setdefault("active_dialect", "SQLite")
    st.session_state.setdefault("ollama_url", ollama["url"])
    st.session_state.setdefault("ollama_model", ollama["model"])
    st.session_state.setdefault("ollama_temperature", float(ollama["temperature"]))
    st.session_state.setdefault("ollama_timeout", float(ollama["timeout"]))
    st.session_state.setdefault("viz_library", viz["default_library"])
    st.session_state.setdefault("viz_theme", viz["theme"])
    st.session_state.setdefault("datasets", [])
    require_authentication()


def L(key: str, **kwargs: object) -> str:
    return translate(key, str(st.session_state.get("language") or "FR"), **kwargs)


def show_safe_error(exc: Exception, context: str) -> None:
    """Keep technical details in server logs, not in the browser."""
    get_logger(context).exception("request failed: %s", exc)
    st.error("Operation impossible. Consultez les journaux du serveur ou contactez un administrateur.")


def sidebar_language() -> str:
    with st.sidebar:
        st.header("DataWizflow")
        current = "EN" if st.session_state.get("language") == "EN" else "FR"
        st.selectbox(L("language_label"), ["FR", "EN"], index=0 if current == "FR" else 1, key="language")
        label = st.session_state.get("active_source_label") or "config"
        url = mask_url(str(st.session_state.get("active_database_url") or ""))
        st.caption(f"{L('active_source')} : {label}")
        st.caption(url)
    return str(st.session_state.get("language") or "FR")


def ollama_from_session(database_url: str | None = None) -> OllamaService:
    return OllamaService(
        base_url=str(st.session_state.get("ollama_url") or "http://localhost:11434"),
        model=str(st.session_state.get("ollama_model") or "mistral"),
        database_url=database_url,
        temperature=float(st.session_state.get("ollama_temperature") or 0.3),
        timeout=float(st.session_state.get("ollama_timeout") or 60),
    )


def source_options() -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    try:
        for profile in ConnectionStore().list_profiles():
            name = str(profile.get("name"))
            options.append((f"profile:{name}", name))
    except Exception:
        get_logger("ui").exception("profiles")
    for dataset in st.session_state.get("datasets") or []:
        options.append((f"file:{dataset['label']}", str(dataset["label"])))
    if not options:
        options.append(("config", "config"))
    return options


def apply_source(choice: str) -> None:
    if choice == "config":
        cfg = ConfigManager().load()
        st.session_state["active_database_url"] = cfg.database_url
        st.session_state["active_source_label"] = "config"
        st.session_state["active_dialect"] = "SQLite"
        return
    if choice.startswith("profile:"):
        name = choice.split(":", 1)[1]
        profile = ConnectionStore().get(name)
        if not profile:
            return
        store = ConnectionStore()
        st.session_state["active_database_url"] = store.build_url(profile)
        st.session_state["active_source_label"] = name
        st.session_state["active_dialect"] = str(profile.get("db_type") or "sqlite")
        return
    if choice.startswith("file:"):
        label = choice.split(":", 1)[1]
        for dataset in st.session_state.get("datasets") or []:
            if dataset["label"] == label:
                st.session_state["active_database_url"] = dataset["url"]
                st.session_state["active_source_label"] = label
                st.session_state["active_dialect"] = "SQLite"
                return


def remember_dataset(label: str, url: str, table: str, frame: pd.DataFrame) -> None:
    datasets = [item for item in st.session_state.get("datasets") or [] if item["label"] != label]
    datasets.append({"label": label, "url": url, "table": table})
    st.session_state["datasets"] = datasets
    st.session_state["frames"] = st.session_state.get("frames") or {}
    st.session_state["frames"][label] = frame
    st.session_state["active_database_url"] = url
    st.session_state["active_source_label"] = label
    st.session_state["active_dialect"] = "SQLite"


def render_profile_table(df: pd.DataFrame) -> pd.DataFrame:
    """Filtre, tri et pages de 50 lignes. Retourne le jeu filtré complet pour l'export."""
    query = st.text_input(L("filter_results"), key="result_filter")
    view = df
    if query.strip():
        mask = view.astype(str).apply(lambda col: col.str.contains(query.strip(), case=False, na=False)).any(axis=1)
        view = view.loc[mask]
    sort_options = [L("none")] + [str(col) for col in view.columns]
    sort_col = st.selectbox(L("sort_by"), sort_options, key="result_sort")
    if sort_col != L("none") and sort_col in view.columns:
        try:
            view = view.sort_values(sort_col, kind="mergesort")
        except TypeError:
            view = view.astype(str).sort_values(sort_col, kind="mergesort")
    page_size = 50
    pages = max(1, (len(view) + page_size - 1) // page_size)
    page = int(st.number_input(L("page"), min_value=1, max_value=pages, value=1, step=1, key="result_page"))
    start = (page - 1) * page_size
    st.caption(L("page_of", page=page, pages=pages) + " · " + L("row_count", n=len(view)))
    st.dataframe(view.iloc[start : start + page_size], use_container_width=True)
    return view


def render_exports(df: pd.DataFrame, stem: str = "resultat", question: str = "", sql_text: str = "") -> None:
    st.download_button(L("export_csv"), data=dataframe_to_csv_bytes(df), file_name=f"{stem}.csv", mime="text/csv")
    st.download_button(
        L("export_excel"),
        data=dataframe_to_excel_bytes(df),
        file_name=f"{stem}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.download_button(
        L("export_pdf"),
        data=dataframe_to_pdf_bytes(df, question=question, sql_text=sql_text, language=str(st.session_state.get("language") or "FR")),
        file_name=f"{stem}.pdf",
        mime="application/pdf",
    )
    try:
        parquet = dataframe_to_parquet_bytes(df)
    except Exception as exc:
        st.caption(str(exc))
        return
    st.download_button(L("export_parquet"), data=parquet, file_name=f"{stem}.parquet", mime="application/octet-stream")


def tail_logs(limit: int = 50) -> list[str]:
    path = Path("logs/app.log")
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-limit:]
