"""Global sidebar: navigation aid + global filters persisted in session state."""

from __future__ import annotations

import streamlit as st

from config.constants import SEASONS, TEAMS, VENUES


def init_state():
    ss = st.session_state
    ss.setdefault("g_seasons", [2023, 2024, 2025])
    ss.setdefault("g_teams", [])
    ss.setdefault("g_venues", [])


def global_filters(location: str = "sidebar"):
    init_state()
    ctx = st.sidebar if location == "sidebar" else st
    ctx.markdown("### 🎛 Global Filters")
    seasons = ctx.multiselect("Seasons", SEASONS, default=st.session_state["g_seasons"], key="f_seasons")
    teams = ctx.multiselect("Teams", TEAMS, default=st.session_state["g_teams"], key="f_teams")
    venues = ctx.multiselect("Venues", VENUES, default=st.session_state["g_venues"], key="f_venues")
    st.session_state["g_seasons"] = seasons or SEASONS
    st.session_state["g_teams"] = teams
    st.session_state["g_venues"] = venues
    return {"seasons": seasons or SEASONS, "teams": teams, "venues": venues}
