from utils.i18n import translate
from utils.nl2sql_prompts import build_nl2sql_prompt


def test_translate_switches_language() -> None:
    assert translate("run", "FR") == "Valider et exécuter"
    assert translate("run", "EN") == "Validate and run"
    assert translate("row_count", "EN", n=3) == "3 rows"


def test_prompt_mentions_dialect() -> None:
    prompt = build_nl2sql_prompt(question="revenue", schema="TABLE sales", language="EN", dialect="PostgreSQL")
    assert "PostgreSQL" in prompt
    assert "revenue" in prompt
