"""Page 8 — Records & Insights."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.cards import footer, hero, section
from components.styles import inject
from config.theme import apply_plotly_style
from utils.data_loader import load_all
from utils.metrics import batting_table, bowling_table

st.set_page_config(page_title="Records · IPL", page_icon="🏆", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Records & Insights", "Highest totals, fastest fifties, best spells and monster partnerships.")
bat = batting_table(deliveries)
bowl = bowling_table(deliveries)

t1, t2, t3 = st.columns(3)
with t1:
    section("Highest team totals")
    ht = matches.sort_values("team1_score", ascending=False).head(8)[["season", "team1", "team1_score", "team2", "venue"]]
    st.dataframe(ht, use_container_width=True, hide_index=True)
with t2:
    section("Most career runs")
    st.dataframe(bat.sort_values("runs", ascending=False).head(8)[["player_name", "runs", "strike_rate", "sixes"]],
                 use_container_width=True, hide_index=True)
with t3:
    section("Most career wickets")
    st.dataframe(bowl.sort_values("wickets", ascending=False).head(8)[["player_name", "wickets", "economy", "dot_pct"]],
                 use_container_width=True, hide_index=True)

c1, c2 = st.columns(2)
with c1:
    section("Fastest scoring (min 100 balls)", "Strike-rate monsters")
    fast = bat[bat["balls"] >= 100].sort_values("strike_rate", ascending=False).head(10)
    fig = px.scatter(fast, x="balls", y="strike_rate", size="runs", color="sixes",
                     hover_name="player_name", color_continuous_scale="Oranges")
    st.plotly_chart(apply_plotly_style(fig, "Strike-Rate vs Volume", height=380), use_container_width=True)
with c2:
    section("Most economical (min 100 balls bowled)", "Control artists")
    eco = bowl[bowl["balls"] >= 100].sort_values("economy").head(10)
    fig2 = px.bar(eco, x="economy", y="player_name", orientation="h", color="wickets",
                  color_continuous_scale="Blues", hover_data=["wickets", "dot_pct"])
    fig2.update_layout(coloraxis_showscale=False)
    st.plotly_chart(apply_plotly_style(fig2, "Best Economy Rates", height=380), use_container_width=True)

section("Milestone timeline", "League scoring evolution")
evo = matches.groupby("season").agg(avg=("team1_score", "mean"), mx=("team1_score", "max")).reset_index()
fig3 = px.line(evo, x="season", y=["avg", "mx"], markers=True, color_discrete_sequence=["#1B4FFF", "#FF6B1A"])
st.plotly_chart(apply_plotly_style(fig3, "Average vs Maximum 1st-Innings Score", height=360), use_container_width=True)
footer()
