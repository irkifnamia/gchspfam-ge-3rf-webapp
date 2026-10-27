"""Consistent interactive chart styling."""

from __future__ import annotations

import plotly.graph_objects as go


def apply_academic_layout(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top",
            "font": {"size": 17},
            "pad": {"b": 12},
        },
        template="plotly_white",
        font={"family": "Arial, sans-serif", "size": 13, "color": "#17212B"},
        legend={
            "title_text": "",
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0,
            "xanchor": "left",
            "font": {"size": 12},
            "itemsizing": "constant",
        },
        margin={"l": 55, "r": 25, "t": 150, "b": 55},
        hoverlabel={"namelength": -1},
    )
    figure.update_xaxes(showgrid=False, zeroline=False, automargin=True)
    figure.update_yaxes(gridcolor="#E5E9EF", zeroline=False, automargin=True)
    return figure
