"""Central theme tokens consumed by CSS + Plotly."""

from config.constants import BRAND

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#1A2332", size=12),
        colorway=["#1B4FFF", "#FF6B1A", "#00C389", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899"],
        xaxis=dict(gridcolor="rgba(15,30,60,0.08)", zerolinecolor="rgba(15,30,60,0.12)"),
        yaxis=dict(gridcolor="rgba(15,30,60,0.08)", zerolinecolor="rgba(15,30,60,0.12)"),
        margin=dict(l=40, r=20, t=48, b=40),
        hoverlabel=dict(bgcolor="#0A1931", font_color="white", bordercolor="#1B4FFF"),
    )
)


def apply_plotly_style(fig, title=None, height=380):
    """Apply enterprise styling to a Plotly figure (mutates + returns)."""
    fig.update_layout(
        template=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#1A2332", size=12),
        title=dict(text=f"<b>{title}</b>" if title else "", font=dict(size=15, color="#0A1931"), x=0.01),
        margin=dict(l=40, r=16, t=52, b=40),
        height=height,
        hoverlabel=dict(bgcolor="#0A1931", font_color="white", bordercolor="#1B4FFF"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(15,30,60,0.08)")
    fig.update_yaxes(gridcolor="rgba(15,30,60,0.08)")
    return fig


CHART_COLORS = ["#1B4FFF", "#FF6B1A", "#00C389", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899", "#14B8A6"]
