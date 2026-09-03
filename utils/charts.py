"""Plotly chart factory — every figure styled, interactive, downloadable."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.theme import CHART_COLORS, apply_plotly_style


def line_runs_per_season(matches: pd.DataFrame):
    g = matches.groupby("season").agg(avg1=("team1_score", "mean"), avg2=("team2_score", "mean"), n=("match_id", "count")).reset_index()
    g["avg_total"] = (g["avg1"] + g["avg2"]).round(1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g["season"], y=g["avg_total"], mode="lines+markers", name="Avg match total / 2",
                             line=dict(color="#1B4FFF", width=3), marker=dict(size=7, color="#FF6B1A"),
                             hovertemplate="Season %{x}<br>Avg innings: %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=g["season"], y=g["n"], mode="lines", name="Matches", yaxis="y2",
                             line=dict(color="#00C389", width=2, dash="dot")))
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", title="Matches"))
    return apply_plotly_style(fig, "Average Innings Score by Season")


def toss_donut(matches: pd.DataFrame):
    c = matches["toss_decision"].value_counts()
    fig = go.Figure(go.Pie(labels=[str(i).capitalize() for i in c.index], values=c.values, hole=0.55,
                           marker=dict(colors=["#1B4FFF", "#FF6B1A"]),
                           hovertemplate="%{label}: %{value} (%{percent})<extra></extra>"))
    return apply_plotly_style(fig, "Toss Decisions", height=340)


def result_donut(matches: pd.DataFrame):
    c = matches["result"].value_counts()
    fig = go.Figure(go.Pie(labels=[str(i).capitalize() + " wins" for i in c.index], values=c.values, hole=0.55,
                           marker=dict(colors=["#00C389", "#8B5CF6"]),
                           hovertemplate="%{label}: %{value}<extra></extra>"))
    return apply_plotly_style(fig, "Winning Method", height=340)


def team_wins_bar(matches: pd.DataFrame):
    w = matches["winner"].value_counts().reset_index()
    w.columns = ["team", "wins"]
    fig = px.bar(w, x="wins", y="team", orientation="h", color="wins", color_continuous_scale="Blues",
                 hover_data={"team": True, "wins": True})
    fig.update_layout(coloraxis_showscale=False)
    return apply_plotly_style(fig, "Wins by Franchise", height=400)


def venue_heatmap(matches: pd.DataFrame):
    pv = matches.pivot_table(index="venue", columns="season", values="team1_score", aggfunc="mean")
    short = [v.split(",")[0][:18] for v in pv.index]
    fig = go.Figure(go.Heatmap(z=pv.values, x=[str(c) for c in pv.columns], y=short, colorscale="Blues",
                               hovertemplate="Season %{x}<br>%{y}: %{z:.0f}<extra></extra>", colorbar=dict(title="Avg 1st inn")))
    return apply_plotly_style(fig, "Venue × Season Heatmap", height=420)


def radar_team(profile: dict, avg_profile: dict):
    cats = ["Win %", "Chase %", "Defend %", "Powerplay", "Death", "Boundary %"]
    v1 = [profile.get("win_pct", 0), profile.get("chase_win_pct", 0), profile.get("defend_win_pct", 0),
          min(profile.get("powerplay", 0) / 60 * 100, 100), min(profile.get("death", 0) / 60 * 100, 100),
          min(profile.get("boundary_pct", 0) * 5, 100)]
    v2 = [avg_profile.get(k, 0) for k in ["win_pct", "chase_win_pct", "defend_win_pct"]] + [50, 50, 50]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=v1 + v1[:1], theta=cats + cats[:1], fill="toself", name="Team",
                                  line=dict(color="#1B4FFF"), fillcolor="rgba(27,79,255,0.25)"))
    fig.add_trace(go.Scatterpolar(r=v2 + v2[:1], theta=cats + cats[:1], fill="toself", name="League avg",
                                  line=dict(color="#FF6B1A", dash="dot")))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
    return apply_plotly_style(fig, "Team Fingerprint Radar", height=420)


def worm_chart(ball_df: pd.DataFrame, m_row: pd.Series):
    fig = go.Figure()
    for inn, color in ((1, "#1B4FFF"), (2, "#FF6B1A")):
        d = ball_df[ball_df["inning"] == inn].copy()
        if d.empty:
            continue
        d = d.sort_values(["over", "ball"])
        d["cum"] = d["total_runs"].cumsum()
        d["ball_n"] = range(1, len(d) + 1)
        team = m_row["team1"] if inn == 1 else m_row["team2"]
        fig.add_trace(go.Scatter(x=d["ball_n"], y=d["cum"], mode="lines", name=f"Inn {inn} · {team}",
                                 line=dict(color=color, width=2.5),
                                 hovertemplate="Ball %{x}<br>Runs %{y}<extra></extra>"))
    return apply_plotly_style(fig, f"Worm Chart — {m_row['team1']} vs {m_row['team2']}")


def partnership_bars(ball_df: pd.DataFrame):
    d = ball_df.copy()
    d["pid"] = ((d["is_wicket"] == 1).cumsum())
    g = d.groupby("pid").agg(runs=("total_runs", "sum"), balls=("total_runs", "size")).reset_index()
    g = g.sort_values("runs", ascending=False).head(10)
    g["label"] = "P" + (g["pid"] + 1).astype(str)
    fig = px.bar(g, x="label", y="runs", color="runs", color_continuous_scale="Oranges",
                 hover_data=["balls"])
    fig.update_layout(coloraxis_showscale=False)
    return apply_plotly_style(fig, "Top Partnerships (runs)", height=340)


def gauge(prob: float, title: str = "Win Probability"):
    fig = go.Figure(go.Indicator(mode="gauge+number", value=prob * 100,
                                 title={"text": title, "font": {"size": 15, "color": "#0A1931"}},
                                 number={"suffix": "%", "font": {"size": 34, "color": "#0A1931"}},
                                 gauge={"axis": {"range": [0, 100]},
                                        "bar": {"color": "#1B4FFF"},
                                        "steps": [{"range": [0, 40], "color": "#FEE2E2"},
                                                  {"range": [40, 60], "color": "#FEF3C7"},
                                                  {"range": [60, 100], "color": "#D1FAE5"}]}))
    return apply_plotly_style(fig, None, height=300)


def spider_player(values: dict):
    cats = list(values.keys())
    fig = go.Figure(go.Scatterpolar(r=list(values.values()) + [list(values.values())[0]],
                                    theta=cats + cats[:1], fill="toself",
                                    line=dict(color="#FF6B1A"), fillcolor="rgba(255,107,26,0.25)"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    return apply_plotly_style(fig, "Player Skill Spider", height=380)
