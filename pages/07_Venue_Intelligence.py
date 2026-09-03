"""Page 7 — Venue Intelligence."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from components.cards import footer, hero, kpi_row, section
from components.styles import inject
from config.theme import apply_plotly_style
from utils.data_loader import load_all

st.set_page_config(page_title="Venue Intelligence · IPL", page_icon="🏟", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Venue Intelligence", "Pitch science: par scores, chase bias, phase tables and leaderboards.")
v = st.selectbox("Venue", venues["venue"].tolist(), key="vi_venue")
row = venues[venues["venue"] == v].iloc[0]
vm = matches[matches["venue"] == v]

kpi_row([
    ("Matches", f"{int(row['matches'])}", str(row["pitch_class"])),
    ("Avg 1st innings", f"{row['avg_first_innings']:.0f}", f"2nd: {row['avg_second_innings']:.0f}"),
    ("Chase win %", f"{row['chase_win_pct']:.0f}%", f"Bat-first {row['bat_first_win_pct']:.0f}%"),
    ("Highest chase", f"{int(row['highest_chase'])}", f"Lowest defended {int(row['lowest_defended'])}"),
    ("Toss bat %", f"{row['toss_bat_pct']:.0f}%", "captains choosing bat"),
])

c1, c2 = st.columns(2)
with c1:
    section("First-innings distribution", "What a good score looks like here")
    fig = px.histogram(vm, x="team1_score", nbins=18, color_discrete_sequence=["#1B4FFF"])
    st.plotly_chart(apply_plotly_style(fig, f"1st Innings Scores — {v.split(',')[0]}", height=360), use_container_width=True)
with c2:
    section("Phase averages at this venue", "Runs per match by phase")
    d = deliveries[deliveries["venue"] == v]
    phases = {
        "Powerplay (1–6)": float(d[d["over"] <= 6].groupby("match_id")["total_runs"].sum().mean() or 0),
        "Middle (7–15)": float(d[(d["over"] >= 7) & (d["over"] <= 15)].groupby("match_id")["total_runs"].sum().mean() or 0),
        "Death (16–20)": float(d[d["over"] >= 16].groupby("match_id")["total_runs"].sum().mean() or 0),
    }
    fig2 = px.bar(x=list(phases.keys()), y=list(phases.values()), color=list(phases.values()),
                  color_continuous_scale="Oranges")
    fig2.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Avg runs")
    st.plotly_chart(apply_plotly_style(fig2, "Phase Par Scores", height=360), use_container_width=True)

section("Venue leaderboard", "All grounds ranked by batting friendliness")
st.dataframe(venues.sort_values("avg_first_innings", ascending=False), use_container_width=True, hide_index=True)
footer()
