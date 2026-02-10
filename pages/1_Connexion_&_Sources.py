import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.config_manager import ConfigManager
from services.sql_executor import SQLExecutor

load_dotenv()

st.title("Connexion & Sources")

cfg = ConfigManager().load()
st.write("Database URL:")
st.code(cfg.database_url)

executor = SQLExecutor(cfg.database_url)

col1, col2 = st.columns([1, 2])
with col1:
    if st.button("Tester la connexion"):
        try:
            executor.test_connection()
            st.success("Connexion OK")
        except Exception as e:
            st.error(str(e))

with col2:
    st.caption("Test simple : SELECT 1, ou création table de démo ensuite (Phase 1 / tâche 4).")

st.subheader("Exécuter une requête SQL (lecture)")
sql = st.text_area("SQL", value="SELECT 1 AS ok", height=120)

if st.button("Exécuter"):
    try:
        res = executor.execute(sql)
        if res.rows and res.columns:
            df = pd.DataFrame(res.rows, columns=res.columns)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Requête exécutée (aucun résultat à afficher).")
    except Exception as e:
        st.error(str(e))