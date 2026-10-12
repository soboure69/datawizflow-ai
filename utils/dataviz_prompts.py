from __future__ import annotations


def build_dataviz_prompt(
    *, request: str, columns: list[str], column_types: dict[str, str], sample: str,
    library: str, language: str = "FR",
) -> str:
    columns_text = ", ".join(columns)
    types_text = "\n".join(f"- {name}: {dtype}" for name, dtype in column_types.items())
    schema = ('{"chart":"bar|line|scatter|histogram|box", "x":"column", '
              '"y":"column or empty string", "color":"column or empty string", '
              '"aggregation":"sum|mean|count|min|max or empty string", "title":"text"}')
    if (language or "FR").upper() == "FR":
        return f"""Tu es un expert en dataviz.

COLONNES : {columns_text}
TYPES :
{types_text}
EXEMPLES :
{sample}

TÂCHE : génère une spécification JSON pour : "{request}"
CONTRAINTES : réponds uniquement par un JSON valide, sans markdown. Schéma strict : {schema}.
Utilise seulement les colonnes fournies. histogram n'exige pas y.
JSON :"""
    return f"""You are a data visualization expert.

COLUMNS: {columns_text}
TYPES:
{types_text}
SAMPLE:
{sample}

TASK: create a JSON specification for: "{request}"
CONSTRAINTS: output only valid JSON, without markdown. Strict schema: {schema}.
Use only supplied columns. histogram does not require y.
JSON:"""
