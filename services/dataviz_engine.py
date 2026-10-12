from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd


_ALLOWED_CHARTS = {"bar", "line", "scatter", "histogram", "box"}
_ALLOWED_AGGREGATIONS = {"sum", "mean", "count", "min", "max"}


class VizError(ValueError):
    pass


@dataclass
class VizOutput:
    kind: str
    plotly_json: str
    html: str


def parse_viz_spec(raw: str | dict[str, Any], columns: list[str]) -> dict[str, str]:
    """Validate a small declarative chart schema; no user Python is executed."""
    try:
        spec = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise VizError("La spécification doit être un objet JSON valide.") from exc
    chart = str(spec.get("chart") or "").lower()
    x = str(spec.get("x") or "")
    y = str(spec.get("y") or "")
    color = str(spec.get("color") or "")
    aggregation = str(spec.get("aggregation") or "").lower()
    title = str(spec.get("title") or "")[:200]
    if chart not in _ALLOWED_CHARTS:
        raise VizError("Type de graphique non autorisé.")
    if x not in columns:
        raise VizError("La colonne x est requise et doit exister.")
    if chart not in {"histogram", "box"} and y not in columns:
        raise VizError("La colonne y est requise pour ce graphique.")
    if y and y not in columns:
        raise VizError("La colonne y doit exister.")
    if color and color not in columns:
        raise VizError("La colonne color doit exister.")
    if aggregation and aggregation not in _ALLOWED_AGGREGATIONS:
        raise VizError("Agrégation non autorisée.")
    return {"chart": chart, "x": x, "y": y, "color": color, "aggregation": aggregation, "title": title}


def render_viz(spec: str | dict[str, Any], df: pd.DataFrame) -> VizOutput:
    """Render a Plotly chart from a validated spec, without eval/exec/imports."""
    if len(df) > 200_000:
        raise VizError("Jeu de données trop volumineux pour la visualisation (200 000 lignes max).")
    parsed = parse_viz_spec(spec, [str(col) for col in df.columns])
    try:
        import plotly.express as px

        data = df.copy()
        x, y, color = parsed["x"], parsed["y"] or None, parsed["color"] or None
        if parsed["aggregation"] and y:
            agg = parsed["aggregation"]
            if agg == "count":
                grouped = data.groupby([x] + ([color] if color else []), dropna=False).size().reset_index(name="count")
                data, y = grouped, "count"
            else:
                data = data.groupby([x] + ([color] if color else []), dropna=False)[y].agg(agg).reset_index()
        chart = parsed["chart"]
        if chart == "bar":
            fig = px.bar(data, x=x, y=y, color=color, title=parsed["title"])
        elif chart == "line":
            fig = px.line(data, x=x, y=y, color=color, title=parsed["title"])
        elif chart == "scatter":
            fig = px.scatter(data, x=x, y=y, color=color, title=parsed["title"])
        elif chart == "histogram":
            fig = px.histogram(data, x=x, color=color, title=parsed["title"])
        else:
            fig = px.box(data, x=x, y=y, color=color, title=parsed["title"])
        return VizOutput(kind="plotly", plotly_json=fig.to_json(), html=fig.to_html(include_plotlyjs="cdn", full_html=True))
    except Exception as exc:
        raise VizError("Impossible de générer le graphique demandé.") from exc
