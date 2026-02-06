import streamlit as st

st.set_page_config(page_title="DataWizflow AI", layout="wide")

st.title("DataWizflow AI")
st.write("Phase 1 : Fondations & Setup")

with st.sidebar:
    st.header("Global")
    language = st.selectbox("Language", ["FR", "EN"], index=0, key="language")

st.info("Prochaine étape : créer la page 'Connexion & Sources' et la gestion de config.")