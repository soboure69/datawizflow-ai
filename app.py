import streamlit as st

from utils.ui import L, init_app, sidebar_language

st.set_page_config(page_title="DataWizflow AI", layout="wide")
init_app()
sidebar_language()

st.title(L("app_title"))
st.write(L("app_subtitle"))
st.info(L("home_steps"))

left, right = st.columns(2)
with left:
    st.subheader(L("card_connect_title"))
    st.write(L("card_connect_body"))
    st.subheader(L("card_nl2sql_title"))
    st.write(L("card_nl2sql_body"))
with right:
    st.subheader(L("card_viz_title"))
    st.write(L("card_viz_body"))
    st.subheader(L("card_assistant_title"))
    st.write(L("card_assistant_body"))
