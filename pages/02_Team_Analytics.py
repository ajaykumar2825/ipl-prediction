"""Page 2 — Team Analytics Center."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.cards import download_df, footer, hero, kpi_row, section
from components.styles import inject
from config.constants import SEASONS, TEAMS
from config.theme import apply_plotly_style
from utils.charts import radar_team
from utils.data_loader import load_all
from utils.metrics import phase_scores, team_record
from utils.validators import safe_select

st.set_page_config(page_title="Team Analytics · IPL", page_icon="🛡", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Team Analytics Center", "Win curves, fingerprints, momentum and venue splits per franchise.")
team = safe_select("Franchise", TEAMS, "Mumbai Indians", key="team_pick") or TEAMS[0]
seasons = st.multiselect("Seasons", SEASONS, default=[2023, 2024, 2025], key="team_seasons") or SEASONS

mf = matches[matches["season"].isin(seasons)]
rec = team_record(mf, team)
ph = phase_scores(deliveries[deliveries["match_id"].isin(set(mf["match_id"]))], mf, team)

kpi_row([
    ("Win %", f"{rec['win_pct']}%", f"{rec['wins']}/{rec['played']} matches"),
    ("Home win %", f"{rec['home_win_pct']}%", "fortress factor"),
    ("Away win %", f"{rec['away_win_pct']}%", "travel form"),
    ("Chase %", f"{rec['chase_win_pct']}%", "2nd innings nerve"),
    ("Defend %", f"{rec['defend_win_pct']}%", "1st innings grip"),
    ("Powerplay", f"{ph['powerplay']}", "avg runs / 6 overs"),
])

# league-average fingerprint baseline
all_rec = {t: team_record(mf, t) for t in TEAMS}
avg_prof = {k: round(sum(r[k] for r in all_rec.values()) / len(all_rec), 1) for k in ("win_pct", "chase_win_pct", "defend_win_pct")}
prof = {"win_pct": rec["win_pct"], "chase_win_pct": rec["chase_win_pct"], "defend_win_pct": rec["defend_win_pct"],
        "powerplay": ph["powerplay"], "death": ph["death"], "boundary_pct": ph["boundary_pct"]}

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(radar_team(prof, avg_prof), use_container_width=True)
with c2:
    section("Season win trend", "Rolling form curve")
    tm = mf[(mf["team1"] == team) | (mf["team2"] == team)].copy()
    tm["won"] = (tm["winner"] == team).astype(int)
    trend = tm.groupby("season")["won"].mean().reset_index()
    trend["win_pct"] = (trend["won"] * 100).round(1)
    fig = px.area(trend, x="season", y="win_pct", markers=True, color_discrete_sequence=["#1B4FFF"])
    st.plotly_chart(apply_plotly_style(fig, f"{team} — Win % by Season", height=420), use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    section("Runs by over", "Batting tempo shape (league vs team)")
    d = deliveries[(deliveries["batting_team"] == team) & (deliveries["match_id"].isin(set(mf["match_id"])))]
    by_over = d.groupby("over")["total_runs"].mean().reset_index()
    lg = deliveries[deliveries["match_id"].isin(set(mf["match_id"]))].groupby("over")["total_runs"].mean().reset_index()
    import plotly.graph_objects as go
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=lg["over"], y=lg["total_runs"], name="League", line=dict(color="#8A94A6", dash="dot")))
    fig2.add_trace(go.Scatter(x=by_over["over"], y=by_over["total_runs"], name=team, line=dict(color="#FF6B1A", width=3)))
    st.plotly_chart(apply_plotly_style(fig2, "Average Runs per Over", height=380), use_container_width=True)
with c4:
    section("Venue splits", "Top grounds for this franchise")
    tm2 = mf[(mf["team1"] == team) | (mf["team2"] == team)]
    vs = tm2.groupby("venue").agg(played=("match_id", "count"),
                                  wins=("winner", lambda s: int((s == team).sum()))).reset_index()
    vs["win_pct"] = (vs["wins"] / vs["played"] * 100).round(1)
    vs = vs.sort_values("played", ascending=False).head(10)
    fig3 = px.bar(vs, x="win_pct", y=vs["venue"].str.slice(0, 22), orientation="h",
                  color="win_pct", color_continuous_scale="Blues", hover_data=["played", "wins"])
    fig3.update_layout(coloraxis_showscale=False)
    st.plotly_chart(apply_plotly_style(fig3, "Win % by Venue (min. sample)", height=380), use_container_width=True)

section("Match log", f"Every {team} game in scope")
log = tm.sort_values("date", ascending=False)
st.dataframe(log, use_container_width=True, hide_index=True)
download_df(log, f"{team.replace(' ', '_')}_matchlog.csv")
footer()
