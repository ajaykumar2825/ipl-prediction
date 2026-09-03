"""Page 9 — AI Insights (rule-based analyst engine)."""

from __future__ import annotations

import streamlit as st

from components.cards import footer, hero, section
from components.styles import inject
from utils.data_loader import load_all
from utils.insights import player_insights, team_insights, venue_insights

st.set_page_config(page_title="AI Insights · IPL", page_icon="💡", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("AI Insights", "Auto-generated analyst briefings — deterministic rules, zero LLM cost.")
tab1, tab2, tab3 = st.tabs(["🏟 Venue brief", "🛡 Team brief", "⭐ Player brief"])
with tab1:
    section("Venue intelligence feed", f"{len(venues)} grounds analysed")
    for i, ins in enumerate(venue_insights(matches, venues), 1):
        st.info(f"**{i:02d}.** {ins}")
with tab2:
    section("Team intelligence feed", "League structure findings")
    for i, ins in enumerate(team_insights(matches, deliveries), 1):
        st.success(f"**{i:02d}.** {ins}")
with tab3:
    section("Player deep-dive", "Pick any player for a generated dossier")
    p = st.selectbox("Player", sorted(players["player_name"].unique().tolist()),
                     index=0, key="ai_player")
    for ins in player_insights(deliveries, p):
        st.warning(f"◆ {ins}")
footer()
