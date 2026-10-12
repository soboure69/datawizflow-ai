from __future__ import annotations


def build_nl2sql_prompt(*, question: str, schema: str, language: str = "FR", dialect: str = "SQLite") -> str:
    lang = (language or "FR").upper()
    if lang not in {"FR", "EN"}:
        lang = "EN"
    dialect_name = dialect or "SQLite"

    if lang == "FR":
        return f"""RÔLE:
Tu es un expert SQL pour {dialect_name}.

OBJECTIF:
Générer UNE SEULE requête SQL pour répondre à la question de l’utilisateur.

CONTRAINTES STRICTES:
- La requête DOIT être read-only.
- Dialecte SQL : {dialect_name}.
- Requête autorisée: uniquement SELECT (CTE WITH autorisée).
- Interdit: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, DETACH, VACUUM, REINDEX, TRUNCATE.
- N'invente jamais des tables ou des colonnes.
- Utilise uniquement les tables/colonnes présentes dans le schéma.
- Retourne uniquement le SQL, sans explication, sans commentaires, sans markdown, sans triple backticks.
- Si la question ne demande pas explicitement "tout", ajoute LIMIT 200 si aucun LIMIT n'est présent.

SCHÉMA DE LA BASE:
{schema}

EXEMPLES:
Q: Chiffre d'affaires total par catégorie
SQL:
SELECT p.category, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC
LIMIT 200;

Q: Revenu total par région
SQL:
SELECT r.region_name, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC
LIMIT 200;

QUESTION UTILISATEUR:
{question}

SQL:"""
    else:
        return f"""ROLE:
You are an expert SQL engineer for {dialect_name}.

GOAL:
Generate ONE SQL query that answers the user's question.

STRICT CONSTRAINTS:
- The query MUST be read-only.
- SQL dialect: {dialect_name}.
- Allowed: SELECT only (WITH CTE allowed).
- Forbidden: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, DETACH, VACUUM, REINDEX, TRUNCATE.
- Never invent tables or columns.
- Use only the tables/columns from the schema.
- Output ONLY the SQL. No explanation, no comments, no markdown, no triple backticks.
- If the question does not explicitly ask for "all rows", add LIMIT 200 if no LIMIT is present.

DATABASE SCHEMA:
{schema}

EXAMPLES:
Q: Total revenue by category
SQL:
SELECT p.category, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC
LIMIT 200;

Q: Total revenue by region
SQL:
SELECT r.region_name, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC
LIMIT 200;

USER QUESTION:
{question}

SQL:"""