import pandas as pd
import streamlit as st

from services.dataviz_engine import render_viz
from services.speech_to_text import WhisperService
from utils.ui import L, init_app, ollama_from_session, remember_dataset, show_safe_error, sidebar_language


def _load_frame() -> pd.DataFrame | None:
    mode = st.session_state.get("viz_mode")
    if mode == "query":
        frame = st.session_state.get("nl2sql_df")
        return frame if isinstance(frame, pd.DataFrame) else None
    if mode == "session":
        label = st.session_state.get("viz_dataset_label")
        frames = st.session_state.get("frames") or {}
        frame = frames.get(label)
        return frame if isinstance(frame, pd.DataFrame) else None
    return st.session_state.get("viz_upload_df") if isinstance(st.session_state.get("viz_upload_df"), pd.DataFrame) else None


def _examples(frame: pd.DataFrame, language: str) -> dict[str, str]:
    numeric = [str(col) for col in frame.select_dtypes(include="number").columns]
    others = [str(col) for col in frame.columns if str(col) not in numeric]
    if language == "EN":
        examples = {"—": ""}
        if numeric:
            examples[f"Histogram of {numeric[0]}"] = f"Histogram of {numeric[0]}"
        if len(numeric) >= 2:
            examples["Scatter"] = f"Scatter plot of {numeric[0]} vs {numeric[1]}"
        if numeric and others:
            examples["Box"] = f"Box plot of {numeric[0]} by {others[0]}"
        return examples
    examples = {"—": ""}
    if numeric:
        examples[f"Histogramme de {numeric[0]}"] = f"Histogramme de {numeric[0]}"
    if len(numeric) >= 2:
        examples["Nuage de points"] = f"Nuage de points {numeric[0]} contre {numeric[1]}"
    if numeric and others:
        examples["Boîte"] = f"Boîte à moustaches de {numeric[0]} par {others[0]}"
    return examples


init_app()
language = sidebar_language()
st.title(L("dataviz_title"))

mode_labels = {
    "upload": L("viz_source_upload"),
    "session": L("viz_source_session"),
    "query": L("viz_source_query"),
}
st.session_state.setdefault("viz_mode", "query" if isinstance(st.session_state.get("nl2sql_df"), pd.DataFrame) else "upload")
mode = st.radio(L("source"), list(mode_labels.keys()), format_func=lambda key: mode_labels[key], key="viz_mode")

if mode == "upload":
    uploaded = st.file_uploader(L("upload_title"), type=["csv", "xlsx", "xls", "parquet", "json"])
    if uploaded is not None:
        from services.dataset_store import materialize_dataframe
        from services.file_loader import FileLoader, MAX_UPLOAD_BYTES

        file_id = str(getattr(uploaded, "file_id", uploaded.name))
        if st.session_state.get("viz_upload_id") != file_id:
            if int(getattr(uploaded, "size", 0)) > MAX_UPLOAD_BYTES:
                st.error("Fichier trop volumineux (maximum 25 Mo).")
                st.stop()
            frame = FileLoader().load_bytes(uploaded.getvalue(), uploaded.name)
            url, table = materialize_dataframe(frame, uploaded.name)
            remember_dataset(uploaded.name, url, table, frame)
            st.session_state["viz_upload_df"] = frame
            st.session_state["viz_upload_id"] = file_id
elif mode == "session":
    datasets = st.session_state.get("datasets") or []
    if not datasets:
        st.info(L("no_dataset"))
    else:
        labels = [item["label"] for item in datasets]
        st.selectbox(L("viz_source_session"), labels, key="viz_dataset_label")

frame = _load_frame()
if frame is None or frame.empty:
    st.info(L("no_dataset"))
    st.stop()

st.write(L("preview"))
st.dataframe(frame.head(10), use_container_width=True)
st.caption(f"{L('rows')} {len(frame)} · {L('columns')} {len(frame.columns)} · {L('nulls')} {int(frame.isna().sum().sum())}")
st.write(", ".join(f"{col} ({frame[col].dtype})" for col in frame.columns))

library_labels = {"matplotlib": L("library_static"), "plotly": L("library_interactive")}
default_library = "plotly" if st.session_state.get("viz_library") == "plotly" else "matplotlib"
st.radio(
    L("default_library"),
    ["matplotlib", "plotly"],
    index=0 if default_library == "matplotlib" else 1,
    format_func=lambda key: library_labels[key],
    key="viz_library_choice",
)

examples = _examples(frame, language)
example_name = st.selectbox(L("examples"), list(examples.keys()))
if st.button(L("load_example"), disabled=example_name == "—"):
    st.session_state["viz_question"] = examples[example_name]

audio = st.file_uploader(L("voice_upload"), type=["wav", "mp3", "m4a", "ogg"], key="viz_audio")
if audio is not None and st.button(L("transcribe"), key="viz_transcribe"):
    try:
        with st.spinner(L("transcribe_wait")):
            st.session_state["viz_question"] = WhisperService().transcribe(
                audio.getvalue(),
                "." + audio.name.rsplit(".", 1)[-1],
                language,
            )
        st.rerun()
    except (ValueError, RuntimeError) as exc:
        st.error(str(exc))
    except Exception as exc:
        show_safe_error(exc, "dataviz")

request = st.text_area(L("viz_question"), value=st.session_state.get("viz_question", ""), height=80)
st.session_state["viz_question"] = request

if st.button(L("generate_code"), disabled=not request.strip()):
    try:
        sample = frame.head(3).to_csv(index=False)
        code = ollama_from_session().generate_viz_spec(
            request=request,
            columns=[str(col) for col in frame.columns],
            column_types={str(col): str(frame[col].dtype) for col in frame.columns},
            sample=sample,
            library=str(st.session_state.get("viz_library_choice")),
            language=language,
        )
        st.session_state["viz_code"] = code
        st.success(L("code_ready"))
    except Exception as exc:
        show_safe_error(exc, "dataviz")

code = st.text_area(L("code_editable"), value=st.session_state.get("viz_code", ""), height=220)
st.session_state["viz_code"] = code

if st.button(L("run_code"), disabled=not code.strip()):
    try:
        output = render_viz(code, frame)
        st.session_state["viz_output"] = output
        st.success(L("chart_ready"))
    except Exception as exc:
        st.session_state["viz_output"] = None
        show_safe_error(exc, "dataviz")

output = st.session_state.get("viz_output")
if output is not None and getattr(output, "kind", "") == "plotly":
    if output.plotly_json:
        import plotly.io as pio

        st.plotly_chart(pio.from_json(output.plotly_json), use_container_width=True)
    if output.html:
        st.download_button(L("download_html"), data=output.html.encode("utf-8"), file_name="graphique.html", mime="text/html")
