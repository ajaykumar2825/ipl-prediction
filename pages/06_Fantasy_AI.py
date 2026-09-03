"""Page 6 — Fantasy Cricket AI."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from components.cards import download_df, footer, hero, kpi_row, section
from components.styles import inject
from config.constants import TEAMS, VENUES
from config.theme import apply_plotly_style
from utils.data_loader import load_all
from utils.fantasy import build_fantasy_xi
from utils.metrics import batting_table, bowling_table

st.set_page_config(page_title="Fantasy AI · IPL", page_icon="✨", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Fantasy Cricket AI", "Credit-optimised Dream XI with captain science and role balance.")
c1, c2, c3 = st.columns(3)
with c1:
    venue = st.selectbox("Venue", VENUES, key="fx_venue")
    opp = st.selectbox("Opponent focus", TEAMS, key="fx_opp")
with c2:
    budget = st.slider("Budget (credits)", 80.0, 110.0, 100.0, 0.5, key="fx_budget")
    wk = st.number_input("Wicket-keepers", 1, 3, 1, key="fx_wk")
with c3:
    bat_n = st.number_input("Batters", 3, 6, 4, key="fx_bat")
    ar = st.number_input("All-rounders", 1, 4, 2, key="fx_ar")
    bowl_n = st.number_input("Bowlers", 3, 6, 4, key="fx_bowl")

bat = batting_table(deliveries)
bowl = bowling_table(deliveries)
xi, summary = build_fantasy_xi(bat, bowl, players, budget=float(budget),
                               wk=int(wk), bat_n=int(bat_n), ar=int(ar), bowl_n=int(bowl_n))
if len(xi) != int(wk + bat_n + ar + bowl_n):
    st.warning("Role mix adjusted to available pool — showing best feasible XI.")

kpi_row([
    ("Expected points", f"{summary['expected_points']:.0f}", "model-projected total"),
    ("Credits used", f"{summary['total_credits']:.1f}", f"{summary['remaining']:.1f} remaining"),
    ("Captain", str(xi[xi['is_captain']]['player_name'].iloc[0])[:18] if len(xi) else "—", "2× points"),
    ("Vice-captain", str(xi[xi['is_vice']]['player_name'].iloc[0])[:18] if len(xi) > 1 else "—", "1.5× points"),
])

d1, d2 = st.columns([1.5, 1])
with d1:
    show = xi.copy()
    show["role_tag"] = show.apply(lambda r: f"{'© ' if r['is_captain'] else ('ⓥ ' if r['is_vice'] else '')}{r['player_name']}", axis=1)
    st.dataframe(show[["role_tag", "role", "team", "credits", "exp_points", "confidence"]],
                 use_container_width=True, hide_index=True)
    download_df(xi, "dream_xi.csv", "⬇ Download Dream XI")
with d2:
    section("Role balance", "Formation shape")
    rc = xi["role"].value_counts().reset_index()
    rc.columns = ["role", "n"]
    fig = px.pie(rc, names="role", values="n", hole=0.55, color_discrete_sequence=px.colors.sequential.Blues)
    st.plotly_chart(apply_plotly_style(fig, "XI Composition", height=320), use_container_width=True)
    section("Confidence", "Per-player model confidence")
    fig2 = px.bar(xi.sort_values("confidence"), x="confidence", y="player_name", orientation="h",
                  color="confidence", color_continuous_scale="Greens")
    fig2.update_layout(coloraxis_showscale=False)
    st.plotly_chart(apply_plotly_style(fig2, "Confidence %", height=360), use_container_width=True)
footer()
