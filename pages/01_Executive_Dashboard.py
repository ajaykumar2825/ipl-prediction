"""Page 1 — Executive Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import download_df, footer, hero, kpi_row, section
from components.sidebar import global_filters
from components.styles import inject
from utils.charts import (line_runs_per_season, result_donut, team_wins_bar,
                          toss_donut, venue_heatmap)
from utils.data_loader import filter_matches, load_all
from utils.metrics import batting_table, bowling_table

st.set_page_config(page_title="Executive Dashboard · IPL Analytics", page_icon="📊", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Executive Dashboard", "League KPIs, trends, toss science and cap races — fully filterable.")
f = global_filters()
mf = filter_matches(matches, f["seasons"], f["teams"] or None, f["venues"] or None)
if mf.empty:
    st.warning("No matches for the current filters. Widen your selection.")
    st.stop()
mids = set(mf["match_id"])
df = deliveries[deliveries["match_id"].isin(mids)]

n = len(mf)
avg1 = mf["team1_score"].mean()
rr = df["total_runs"].sum() / max(len(df) / 6, 1)
sr = df["runs_off_bat"].sum() / max(len(df), 1) * 100
wpm = df["is_wicket"].sum() / max(n, 1)
econ = df["total_runs"].sum() / max(len(df) / 6, 1)
kpi_row([
    ("Matches", f"{n:,}", f"{mf['season'].min()}–{mf['season'].max()}"),
    ("Avg 1st innings", f"{avg1:.0f}", "runs per match"),
    ("Run rate", f"{rr:.2f}", "league tempo"),
    ("Ball strike-rate", f"{sr:.1f}", "runs per 100 balls"),
    ("Wickets / match", f"{wpm:.1f}", "bowling impact"),
    ("Economy", f"{econ:.2f}", "runs per over"),
])

c1, c2 = st.columns([1.5, 1])
with c1:
    st.plotly_chart(line_runs_per_season(mf), use_container_width=True, config={"toImageButtonOptions": {"format": "png"}})
with c2:
    st.plotly_chart(toss_donut(mf), use_container_width=True)
    st.plotly_chart(result_donut(mf), use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(team_wins_bar(mf), use_container_width=True)
with c4:
    st.plotly_chart(venue_heatmap(mf), use_container_width=True)

section("Leaderboards", "Orange & Purple Cap for the filtered sample")
bat = batting_table(df)
bowl = bowling_table(df)
l1, l2 = st.columns(2)
with l1:
    oc = bat[bat["balls"] >= 50].sort_values("runs", ascending=False).head(10)[["player_name", "runs", "balls", "strike_rate", "average", "fours", "sixes"]]
    st.dataframe(oc, use_container_width=True, hide_index=True)
    download_df(oc, "orange_cap.csv", "⬇ Orange Cap CSV")
with l2:
    pc = bowl[bowl["balls"] >= 60].sort_values("wickets", ascending=False).head(10)[["player_name", "wickets", "economy", "average", "dot_pct"]]
    st.dataframe(pc, use_container_width=True, hide_index=True)
    download_df(pc, "purple_cap.csv", "⬇ Purple Cap CSV")

section("Filtered match report", "Download the exact slice behind this dashboard")
st.dataframe(mf.sort_values("date", ascending=False).head(25), use_container_width=True, hide_index=True)
download_df(mf, "executive_report.csv", "⬇ Download full filtered report")
footer()
