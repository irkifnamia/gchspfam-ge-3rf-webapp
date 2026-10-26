"""Consistent interactive chart styling."""

from __future__ import annotations

import plotly.graph_objects as go


def apply_academic_layout(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left"},
        template="plotly_white",
        font={"family": "Arial, sans-serif", "size": 13, "color": "#17212B"},
        legend={"title_text": "", "orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        margin={"l": 45, "r": 20, "t": 75, "b": 45},
        hoverlabel={"namelength": -1},
    )
    figure.update_xaxes(showgrid=False, zeroline=False)
    figure.update_yaxes(gridcolor="#E5E9EF", zeroline=False)
    return figure
