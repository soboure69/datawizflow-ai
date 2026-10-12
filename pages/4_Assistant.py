import pandas as pd
import streamlit as st

from services.sql_executor import SQLExecutor
from utils.assistant_prompts import advice_system_prompt, explain_prompt, notebook_prompt
from utils.ui import L, init_app, ollama_from_session, show_safe_error, sidebar_language


def _context() -> str:
    parts: list[str] = []
    url = str(st.session_state.get("active_database_url") or "")
    if url:
        try:
            parts.append(SQLExecutor(url).get_schema())
        except Exception as exc:
            parts.append(str(exc))
    frame = st.session_state.get("nl2sql_df")
    if isinstance(frame, pd.DataFrame) and not frame.empty:
        parts.append(frame.head(8).to_csv(index=False))
    question = st.session_state.get("nl2sql_question")
    if question:
        parts.append(str(question))
    return "\n".join(parts)[:6000]


def _ask(system: str, user: str) -> None:
    messages = st.session_state["assistant_messages"]
    messages.append({"role": "user", "content": user})
    answer = ollama_from_session().ask(system_prompt=system, user_prompt=user)
    messages.append({"role": "assistant", "content": answer})


init_app()
language = sidebar_language()
st.title(L("assistant_title"))
st.session_state.setdefault("assistant_messages", [])

context = _context()
with st.expander(L("active_source")):
    st.code(context or L("no_dataset"))

for message in st.session_state["assistant_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

explain_col, notebook_col = st.columns(2)
with explain_col:
    if st.button(L("explain_result")):
        try:
            _ask(explain_prompt(language=language, context=context), L("explain_result"))
            st.rerun()
        except Exception as exc:
            show_safe_error(exc, "assistant")
with notebook_col:
    if st.button(L("notebook")):
        try:
            _ask(notebook_prompt(language=language, context=context), L("notebook"))
            st.rerun()
        except Exception as exc:
            show_safe_error(exc, "assistant")

prompt = st.chat_input(L("assistant_placeholder"))
if prompt:
    try:
        _ask(advice_system_prompt(language=language, context=context), prompt)
        st.rerun()
    except Exception as exc:
        show_safe_error(exc, "assistant")
