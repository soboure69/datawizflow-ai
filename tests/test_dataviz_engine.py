import pandas as pd
import pytest

from services.dataviz_engine import VizError, parse_viz_spec, render_viz


def test_render_viz_returns_plotly_chart() -> None:
    frame = pd.DataFrame({"month": ["Jan", "Feb"], "revenue": [1, 3]})
    output = render_viz({"chart": "bar", "x": "month", "y": "revenue", "title": "Revenue"}, frame)
    assert output.kind == "plotly"
    assert output.plotly_json


def test_rejects_python_instead_of_spec() -> None:
    with pytest.raises(VizError):
        parse_viz_spec("import os", ["n"])


def test_rejects_unknown_columns_and_chart() -> None:
    with pytest.raises(VizError):
        parse_viz_spec('{"chart":"bar","x":"missing","y":"n"}', ["n"])
    with pytest.raises(VizError):
        parse_viz_spec('{"chart":"pie","x":"n","y":""}', ["n"])
