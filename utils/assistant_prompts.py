from __future__ import annotations


def advice_system_prompt(*, language: str, context: str) -> str:
    if (language or "FR").upper() == "FR":
        return f"""Tu es un assistant data science pédagogue.
Tu conseilles sur les modèles, le feature engineering, les anomalies et l'interprétation.
Tu restes concret et tu n'inventes pas de colonnes absentes du contexte.
Réponds en français.

CONTEXTE:
{context}"""
    return f"""You are a practical data science assistant.
Advise on models, feature engineering, anomalies, and how to interpret results.
Do not invent columns that are not in the context.
Answer in English.

CONTEXT:
{context}"""


def notebook_prompt(*, language: str, context: str) -> str:
    if (language or "FR").upper() == "FR":
        return f"""Produis un squelette de notebook Jupyter en Markdown.
Inclure : préparation, exploration, feature engineering, un modèle simple, évaluation, visualisation.
Le code doit être réaliste par rapport au contexte. Pas d'appel réseau.

CONTEXTE:
{context}"""
    return f"""Produce a Jupyter notebook skeleton in Markdown.
Include: preparation, exploration, feature engineering, a simple model, evaluation, and a chart.
Keep the code realistic for the context. No network calls.

CONTEXT:
{context}"""


def explain_prompt(*, language: str, context: str) -> str:
    if (language or "FR").upper() == "FR":
        return f"""Explique le résultat suivant à un décideur, puis ajoute une note plus technique.
Reste fidèle aux chiffres du contexte.

CONTEXTE:
{context}"""
    return f"""Explain the following result for a decision maker, then add a short technical note.
Stay faithful to the numbers in the context.

CONTEXT:
{context}"""
