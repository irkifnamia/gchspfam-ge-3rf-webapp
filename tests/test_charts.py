from __future__ import annotations

import plotly.graph_objects as go

from src.charts import apply_academic_layout


def test_academic_layout_reserves_separate_title_and_legend_space():
    figure = go.Figure(
        data=[
            go.Bar(name="A long legend entry", x=[1], y=[1]),
            go.Bar(name="Another long legend entry", x=[1], y=[2]),
        ]
    )

    result = apply_academic_layout(figure, "A chart title")

    assert result.layout.title.y == 0.98
    assert result.layout.title.yanchor == "top"
    assert result.layout.legend.y == 1.02
    assert result.layout.legend.yanchor == "bottom"
    assert result.layout.margin.t == 150
    assert result.layout.xaxis.automargin is True
    assert result.layout.yaxis.automargin is True
