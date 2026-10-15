import time

import pandas as pd
import streamlit as st

from services.history_store import HistoryStore
from services.connection_store import mask_url
from services.speech_to_text import WhisperService
from services.text_to_speech import summarize_dataframe, synthesize_speech
from services.sql_executor import SQLExecutor
from utils.logger import get_logger
from utils.sql_safety import ensure_limit, validate_readonly_sql
from utils.ui import L, apply_source, init_app, ollama_from_session, render_exports, render_profile_table, show_safe_error, sidebar_language, source_options

_LOGGER = get_logger("nl2sql")


def _question_examples(language: str, schema: str) -> dict[str, str]:
    if "sales" in schema.lower():
        if language == "EN":
            return {
                "—": "",
                "Top products": "Show the top 5 products by revenue",
                "Revenue by region": "Total revenue by region",
                "Revenue by month": "Total revenue by month in 2024",
            }
        return {
            "—": "",
            "Top produits": "Top 5 produits par revenu total",
            "Revenu par région": "Revenu total par région",
            "Revenu par mois": "Revenu total par mois en 2024",
        }
    if language == "EN":
        return {"—": "", "Preview": "Show 20 rows"}
    return {"—": "", "Aperçu": "Montre 20 lignes"}


def _sql_examples() -> dict[str, str]:
    return {
        "—": "",
        "Top 5 produits": """SELECT p.product_name, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.product_name
ORDER BY revenue_total DESC
LIMIT 5""",
        "Revenu par région": """SELECT r.region_name, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC""",
    }


def _schema_text(executor: SQLExecutor) -> str:
    url = executor.database_url
    if st.session_state.get("schema_url") != url:
        st.session_state["schema_text"] = executor.get_schema()
        st.session_state["schema_url"] = url
        st.session_state["active_dialect"] = executor.get_dialect()
    return str(st.session_state.get("schema_text") or "")


def run_sql(*, question: str, sql_text: str, executor: SQLExecutor, history: HistoryStore, language: str, model: str) -> None:
    try:
        validate_readonly_sql(sql_text)
        sql_to_run = ensure_limit(sql_text, limit=int(st.session_state.get("nl2sql_limit") or 200))
        started = time.perf_counter()
        result = executor.execute(sql_to_run, timeout=30)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        frame = pd.DataFrame(result.rows, columns=result.columns) if result.columns else pd.DataFrame()
        st.session_state["nl2sql_df"] = frame
        st.session_state["nl2sql_sql_executed"] = sql_to_run
        st.session_state["nl2sql_elapsed_ms"] = elapsed_ms
        history.add_history(
            question=question,
            sql_text=sql_text,
            executed_sql=sql_to_run,
            row_count=len(frame),
            status="success",
            model=model,
            language=language,
            database_url=mask_url(executor.database_url),
        )
        _LOGGER.info("query ok rows=%s ms=%s", len(frame), elapsed_ms)
        st.success(L("run_ok"))
    except Exception as exc:
        history.add_history(
            question=question,
            sql_text=sql_text,
            executed_sql=sql_text,
            row_count=0,
            status="error",
            error_message=str(exc),
            model=model,
            language=language,
            database_url=mask_url(executor.database_url),
        )
        _LOGGER.info("query error %s", exc)
        show_safe_error(exc, "nl2sql")


init_app()
language = sidebar_language()
st.title(L("nl2sql_title"))

database_url = str(st.session_state.get("active_database_url"))
executor = SQLExecutor(database_url)
ollama = ollama_from_session(database_url)
history = HistoryStore()
history.ensure_schema()

try:
    schema = _schema_text(executor)
except Exception as exc:
    schema = ""
    show_safe_error(exc, "nl2sql")

with st.sidebar:
    st.caption(f"Ollama : {ollama.settings.model}")
    st.selectbox(L("limit"), [50, 200, 1000], index=1, key="nl2sql_limit")
    options = source_options()
    labels = {key: label for key, label in options}
    current_label = str(st.session_state.get("active_source_label") or "")
    keys = [key for key, _ in options]
    default_index = 0
    for i, key in enumerate(keys):
        if labels[key] == current_label:
            default_index = i
    choice = st.selectbox(L("source"), keys, index=default_index, format_func=lambda key: labels[key])
    if st.button(L("use_profile"), key="nl2sql_use_source"):
        apply_source(choice)
        st.session_state.pop("schema_url", None)
        st.rerun()

    examples = _question_examples(language, schema)
    example_name = st.selectbox(L("examples"), list(examples.keys()))
    if st.button(L("load_example"), disabled=example_name == "—"):
        st.session_state["nl2sql_question"] = examples[example_name]

    sql_examples = _sql_examples()
    sql_example_name = st.selectbox(L("sql_examples"), list(sql_examples.keys()))
    if st.button(L("load_example"), key="load_sql_example", disabled=sql_example_name == "—"):
        st.session_state["nl2sql_sql"] = sql_examples[sql_example_name]

audio = st.file_uploader(L("voice_upload"), type=["wav", "mp3", "m4a", "ogg"])
if audio is not None and st.button(L("transcribe")):
    try:
        with st.spinner(L("transcribe_wait")):
            text = WhisperService().transcribe(audio.getvalue(), "." + audio.name.rsplit(".", 1)[-1], language)
        st.session_state["nl2sql_question"] = text
        st.rerun()
    except (ValueError, RuntimeError) as exc:
        st.error(str(exc))
    except Exception as exc:
        show_safe_error(exc, "nl2sql")

question = st.text_area(
    L("question"),
    value=st.session_state.get("nl2sql_question", ""),
    height=100,
    placeholder=L("question_placeholder"),
)
st.session_state["nl2sql_question"] = question

generate_col, clear_col = st.columns(2)
with generate_col:
    if st.button(L("generate_sql"), disabled=not question.strip()):
        try:
            st.session_state["nl2sql_sql"] = ollama.generate_sql(
                question=question,
                language=language,
                schema=schema,
                dialect=str(st.session_state.get("active_dialect") or "SQLite"),
            )
            st.success(L("sql_ready"))
        except Exception as exc:
            show_safe_error(exc, "nl2sql")
with clear_col:
    if st.button(L("clear")):
        st.session_state["nl2sql_question"] = ""
        st.session_state["nl2sql_sql"] = ""
        st.session_state["nl2sql_df"] = None
        st.rerun()

sql_text = st.text_area(
    L("sql_editable"),
    value=st.session_state.get("nl2sql_sql", ""),
    height=180,
)
st.session_state["nl2sql_sql"] = sql_text

check_col, run_col = st.columns(2)
with check_col:
    if st.button(L("check_syntax"), disabled=not sql_text.strip()):
        try:
            validate_readonly_sql(sql_text)
            executor.explain(ensure_limit(sql_text, int(st.session_state.get("nl2sql_limit") or 200)))
            st.success(L("syntax_ok"))
        except Exception as exc:
            show_safe_error(exc, "nl2sql")
with run_col:
    if st.button(L("run"), disabled=not sql_text.strip()):
        run_sql(
            question=question,
            sql_text=sql_text,
            executor=executor,
            history=history,
            language=language,
            model=ollama.settings.model,
        )

frame = st.session_state.get("nl2sql_df")
executed = st.session_state.get("nl2sql_sql_executed")
if executed:
    st.caption(L("executed_sql"))
    st.code(executed, language="sql")
if isinstance(frame, pd.DataFrame):
    st.subheader(L("results"))
    elapsed = st.session_state.get("nl2sql_elapsed_ms")
    if elapsed is not None:
        st.caption(f"{L('elapsed')} : {elapsed} ms · {L('row_count', n=len(frame))}")
    if not frame.empty:
        st.caption(L("result_schema"))
        st.write(", ".join(f"{col} ({frame[col].dtype})" for col in frame.columns))
        filtered = render_profile_table(frame)
    else:
        filtered = frame
        st.info(L("row_count", n=0))
    shown = filtered if isinstance(filtered, pd.DataFrame) else frame
    render_exports(shown, question=question, sql_text=str(executed or ""))
    if st.button(L("read_aloud")):
        try:
            spoken = summarize_dataframe(shown, language)
            with st.spinner(L("read_aloud_wait")):
                st.session_state["nl2sql_speech"] = synthesize_speech(spoken, language)
            st.session_state["nl2sql_speech_text"] = spoken
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
        except Exception as exc:
            show_safe_error(exc, "nl2sql")
    if st.session_state.get("nl2sql_speech"):
        st.caption(str(st.session_state.get("nl2sql_speech_text") or ""))
        st.audio(st.session_state["nl2sql_speech"], format="audio/wav")

    st.subheader(L("save_view"))
    title = st.text_input(L("view_name"))
    description = st.text_input(L("view_description"))
    if st.button(L("save_view")):
        if not title.strip():
            st.error(L("need_title"))
        elif not sql_text.strip():
            st.error(L("empty_sql"))
        else:
            history.save_view(
                title=title.strip(),
                question=question.strip(),
                sql_text=sql_text.strip(),
                description=description.strip() or None,
                model=ollama.settings.model,
                language=language,
                database_url=mask_url(database_url),
            )
            st.success(L("saved"))

st.subheader(L("history"))
hist_search = st.text_input(L("search"), key="nl2sql_hist_search")
hist_status = st.selectbox(L("status"), ["ALL", "success", "error"], key="nl2sql_hist_status")
hist_page = int(st.number_input(L("page"), min_value=1, value=1, step=1, key="nl2sql_hist_page"))
items = history.list_history(
    limit=10,
    offset=(hist_page - 1) * 10,
    search_text=hist_search,
    status=None if hist_status == "ALL" else hist_status,
)
if not items:
    st.caption(L("no_history"))
for item in items:
    st.write(f"#{item.id} · {item.created_at} · {item.status} · {item.row_count} · {item.model} · {item.language}")
    with st.expander(f"#{item.id}"):
        st.code(item.question)
        st.code(item.executed_sql, language="sql")
        load_col, run_col, delete_col = st.columns(3)
        with load_col:
            if st.button(L("load"), key=f"history_load_{item.id}"):
                st.session_state["nl2sql_sql"] = item.sql_text
                st.session_state["nl2sql_question"] = item.question
                st.rerun()
        with run_col:
            if st.button(L("load_run"), key=f"history_run_{item.id}"):
                st.session_state["nl2sql_sql"] = item.sql_text
                st.session_state["nl2sql_question"] = item.question
                run_sql(
                    question=item.question,
                    sql_text=item.sql_text,
                    executor=executor,
                    history=history,
                    language=language,
                    model=ollama.settings.model,
                )
        with delete_col:
            if st.button(L("delete"), key=f"history_delete_{item.id}"):
                history.delete_history(item.id)
                st.rerun()

st.subheader(L("saved_views"))
views_search = st.text_input(L("search"), key="nl2sql_views_search")
views_page = int(st.number_input(L("page"), min_value=1, value=1, step=1, key="nl2sql_views_page"))
views = history.list_saved_views(limit=10, offset=(views_page - 1) * 10, search_text=views_search)
if not views:
    st.caption(L("no_views"))
for view in views:
    st.write(f"#{view.id} · {view.created_at} · {view.title} · {view.model} · {view.language}")
    with st.expander(view.title):
        if view.description:
            st.write(view.description)
        st.code(view.question)
        st.code(view.sql_text, language="sql")
        load_col, delete_col = st.columns(2)
        with load_col:
            if st.button(L("load"), key=f"view_load_{view.id}"):
                st.session_state["nl2sql_sql"] = view.sql_text
                st.session_state["nl2sql_question"] = view.question
                st.rerun()
        with delete_col:
            if st.button(L("delete"), key=f"view_delete_{view.id}"):
                history.delete_saved_view(view.id)
                st.rerun()
