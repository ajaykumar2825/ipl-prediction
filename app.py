"""IPL Sports Analytics Platform — Executive landing page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from components.cards import download_df, footer, hero, kpi_row, section
from components.sidebar import init_state
from components.styles import inject
from config.constants import APP_SUBTITLE, APP_NAME
from config.theme import apply_plotly_style
from utils.data_loader import filter_matches, load_all
from utils.metrics import batting_table, bowling_table

st.set_page_config(page_title=f"{APP_NAME} — {APP_SUBTITLE}", page_icon="🏏",
                   layout="wide", initial_sidebar_state="expanded")
inject()
init_state()

st.sidebar.title("🏏 IPL Analytics")
st.sidebar.caption("Enterprise Cricket Intelligence")
st.sidebar.markdown("---")
st.sidebar.markdown("**Navigate with the Pages menu ↑**\n\n- Executive Dashboard\n- Team Analytics\n- Player Analytics\n- Match Intelligence\n- Match Prediction AI\n- Fantasy Cricket AI\n- Venue Intelligence\n- Records & Insights\n- AI Insights")
st.sidebar.markdown("---")
season_pick = st.sidebar.selectbox("Quick season focus", [2025, 2024, 2023, 2022, 2021, 2020], index=0, key="home_season")

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero(APP_NAME, APP_SUBTITLE + " · Win probability, player intelligence, venue science & fantasy AI — IPL 2008–2025.")

m = filter_matches(matches, seasons=[season_pick]) if season_pick else matches
bat = batting_table(deliveries[deliveries["season"] == season_pick] if season_pick else deliveries)
bowl = bowling_table(deliveries[deliveries["season"] == season_pick] if season_pick else deliveries)

kpi_row([
    ("Seasons", f"{matches['season'].nunique()}", "2008 – 2025 covered"),
    ("Matches", f"{len(matches):,}", f"{len(m)} in {season_pick}"),
    ("Players", f"{players['player_name'].nunique()}", f"{len(deliveries['batter'].unique())} featured"),
    ("Deliveries", f"{len(deliveries):,}", "ball-by-ball engine"),
    ("Venues", f"{venues['venue'].nunique()}", "pitch intelligence"),
])

c1, c2 = st.columns([1.4, 1])
with c1:
    section(f"Season {season_pick} — Orange Cap race", "Most runs in the focused season")
    oc = bat.sort_values("runs", ascending=False).head(8)
    fig = px.bar(oc, x="runs", y="player_name", orientation="h", color="strike_rate",
                 color_continuous_scale="Blues", hover_data=["balls", "strike_rate", "fours", "sixes"])
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(apply_plotly_style(fig, f"Top Run-Scorers · {season_pick}", height=380),
                    use_container_width=True, config={"displayModeBar": True})
with c2:
    section(f"Season {season_pick} — Purple Cap race", "Most wickets in the focused season")
    pc = bowl.sort_values("wickets", ascending=False).head(8)
    fig2 = px.bar(pc, x="wickets", y="player_name", orientation="h", color="economy",
                  color_continuous_scale="Oranges", hover_data=["economy", "dot_pct"])
    fig2.update_layout(coloraxis_showscale=False)
    st.plotly_chart(apply_plotly_style(fig2, f"Top Wicket-Takers · {season_pick}", height=380),
                    use_container_width=True, config={"displayModeBar": True})

c3, c4 = st.columns(2)
with c3:
    section("Titles by franchise", "All-time championship share (match wins)")
    w = matches["winner"].value_counts().reset_index()
    w.columns = ["team", "wins"]
    fig3 = px.treemap(w, path=["team"], values="wins", color="wins", color_continuous_scale="Blues")
    st.plotly_chart(apply_plotly_style(fig3, "Franchise Win Treemap", height=340), use_container_width=True)
with c4:
    section("Recent results", "Latest 8 matches")
    recent = matches.sort_values("date", ascending=False).head(8)[
        ["date", "team1", "team2", "winner", "venue"]].copy()
    recent["date"] = pd.to_datetime(recent["date"]).dt.date.astype(str)
    st.dataframe(recent, use_container_width=True, hide_index=True)
    download_df(recent, "recent_results.csv", "⬇ Download recent results")

section("How to use this platform", "Built for analysts, coaches, fantasy managers and recruiters")
a, b, c = st.columns(3)
for col, t, d in zip(
    (a, b, c),
    ("📊 Analyse", "🤖 Predict", "✨ Decide"),
    ("Executive, team, player, venue and match intelligence pages with cross-filters and PNG export.",
     "Winner probability, projected totals and SHAP-style explanations from lightweight XGBoost models.",
     "Fantasy XI optimiser, rule-based AI insights and downloadable analyst reports.")):
    with col:
        st.markdown(f'<div class="card"><b>{t}</b><br><span class="muted">{d}</span></div>', unsafe_allow_html=True)

footer()
