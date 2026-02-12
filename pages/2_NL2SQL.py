import io

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.config_manager import ConfigManager
from services.ollama_service import OllamaService
from services.sql_executor import SQLExecutor
from utils.sql_safety import ensure_limit, validate_readonly_sql

load_dotenv()

st.title("NL2SQL")

cfg = ConfigManager().load()

executor = SQLExecutor(cfg.database_url)
ollama = OllamaService(database_url=cfg.database_url)

with st.sidebar:
    st.header("NL2SQL Settings")
    language = st.selectbox("Language", ["FR", "EN"], index=0, key="nl2sql_language")
    model_info = f"{ollama.settings.model} @ {ollama.settings.base_url}"
    st.caption(f"Ollama: {model_info}")

    limit = st.selectbox("LIMIT", [50, 200, 1000], index=1, key="nl2sql_limit")

examples = {
    "—": "",
    "Top 5 produits par revenu": """SELECT p.product_name, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.product_name
ORDER BY revenue_total DESC
LIMIT 5""",
    "Revenu total par catégorie": """SELECT p.category, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC""",
    "Revenu total par région": """SELECT r.region_name, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC""",
    "Revenu total par mois (2024)": """SELECT d.year, d.month, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN dates d ON d.date = s.sale_date
GROUP BY d.year, d.month
ORDER BY d.year, d.month""",
}

with st.sidebar:
    st.subheader("Exemples")
    example_name = st.selectbox("Charger un exemple", list(examples.keys()), index=0)
    if st.button("Charger l'exemple", disabled=(example_name == "—")):
        st.session_state["nl2sql_sql"] = examples[example_name]

st.subheader("Question (langage naturel)")
question = st.text_area(
    "Question",
    value=st.session_state.get("nl2sql_question", ""),
    height=100,
    placeholder="Ex: Donne le chiffre d'affaires total par catégorie",
)
st.session_state["nl2sql_question"] = question

col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("Générer SQL", disabled=not bool(question.strip())):
        try:
            sql_generated = ollama.generate_sql(question=question, language=language)
            st.session_state["nl2sql_sql"] = sql_generated
            st.success("SQL généré")
        except Exception as e:
            st.error(str(e))

with col_b:
    if st.button("Effacer"):
        st.session_state["nl2sql_question"] = ""
        st.session_state["nl2sql_sql"] = ""
        st.session_state["nl2sql_df"] = None


st.subheader("SQL (éditable)")
sql_text = st.text_area(
    "SQL",
    value=st.session_state.get("nl2sql_sql", ""),
    height=180,
    placeholder="Le SQL généré apparaîtra ici…",
)
st.session_state["nl2sql_sql"] = sql_text


st.subheader("Exécution")
if st.button("Valider + Exécuter", disabled=not bool(sql_text.strip())):
    try:
        validate_readonly_sql(sql_text)
        sql_to_run = ensure_limit(sql_text, limit=int(limit))
        res = executor.execute(sql_to_run)

        df = pd.DataFrame(res.rows, columns=res.columns) if res.columns else pd.DataFrame()
        st.session_state["nl2sql_df"] = df
        st.session_state["nl2sql_sql_executed"] = sql_to_run
        st.success("Exécution OK")
    except Exception as e:
        st.error(str(e))


df = st.session_state.get("nl2sql_df")
sql_executed = st.session_state.get("nl2sql_sql_executed")

if sql_executed:
    st.caption("SQL exécuté :")
    st.code(sql_executed, language="sql")

if df is not None:
    st.subheader("Résultats")
    st.caption(f"Lignes: {len(df)}")
    st.dataframe(df, use_container_width=True)

    st.subheader("Export")
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Télécharger CSV", data=csv_bytes, file_name="nl2sql_result.csv", mime="text/csv")
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")

    st.download_button(
        "Télécharger Excel",
        data=excel_buffer.getvalue(),
    file_name="nl2sql_result.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)