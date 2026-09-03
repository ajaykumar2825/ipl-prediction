"""Page 5 — Match Prediction AI."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from components.cards import footer, hero, section
from components.styles import inject
from config.constants import SEASONS, TEAMS, VENUES, VENUE_AVG
from config.theme import apply_plotly_style
from utils.charts import gauge
from utils.data_loader import load_all
from utils.ml_models import inplay_adjust, predict_winner_proba, train_score_model, train_winner_models

st.set_page_config(page_title="Match Prediction AI · IPL", page_icon="🤖", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Match Prediction AI", "Pre-match odds + live in-play adjustment with transparent explanations.")
bundle = train_winner_models(str(len(matches)))
score_m = train_score_model(str(len(matches)))

c1, c2, c3 = st.columns(3)
with c1:
    team_a = st.selectbox("Team A", TEAMS, index=0, key="pa_a")
    team_b = st.selectbox("Team B", [t for t in TEAMS if t != team_a], index=1, key="pa_b")
    venue = st.selectbox("Venue", VENUES, key="pa_venue")
with c2:
    toss_w = st.selectbox("Toss winner", [team_a, team_b], key="pa_toss")
    toss_d = st.selectbox("Toss decision", ["bat", "field"], index=1, key="pa_dec")
    season = st.selectbox("Season context", SEASONS, index=len(SEASONS) - 1, key="pa_season")
with c3:
    st.markdown("**📡 In-play state (optional)**")
    cur = st.number_input("Current score", 0, 300, 85, key="pa_cur")
    ov = st.number_input("Overs completed", 0.0, 20.0, 8.0, step=0.5, key="pa_ov")
    wk = st.number_input("Wickets lost", 0, 10, 2, key="pa_wk")

p_pre, model_name = predict_winner_proba(bundle, team_a, team_b, venue, toss_w, toss_d, season)
p_live = inplay_adjust(p_pre, int(cur), float(ov), int(wk), team_a, team_b, float(VENUE_AVG.get(venue, 165)))
conf = abs(p_live - 0.5) * 2
proj_total = int(round(float(VENUE_AVG.get(venue, 165)) + (cur / max(ov, 0.5) - 8.25) * 6)) if ov else int(VENUE_AVG.get(venue, 165))

g1, g2 = st.columns([1, 1.4])
with g1:
    st.plotly_chart(gauge(p_live, f"{team_a.split()[-1]} win probability"), use_container_width=True)
    st.markdown(f'<div class="card">🏆 <b>Projected winner: {team_a if p_live >= 0.5 else team_b}</b><br>'
                f'<span class="muted">Confidence {conf*100:.0f}% · Model: {model_name} · Expected total ≈ {proj_total}</span></div>',
                unsafe_allow_html=True)
with g2:
    section("Why this prediction?", "SHAP-style attribution without the SHAP dependency")
    fi = bundle["feature_importance"]
    fig = px.bar(fi, x="importance", y="feature", orientation="h", color="importance",
                 color_continuous_scale="Blues")
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(apply_plotly_style(fig, "Feature Importance (%)", height=300), use_container_width=True)
    lb = bundle["leaderboard"]
    st.dataframe(lb, use_container_width=True, hide_index=True)

section("Probability timeline (illustrative)", "How the live edge evolves as overs progress")
tl = pd.DataFrame({"over": list(range(0, 21)),
                   team_a.split()[-1]: [inplay_adjust(p_pre, int(cur * o / max(ov, 0.5)), float(o), int(wk * o / max(ov, 0.5)), team_a, team_b) * 100 for o in range(0, 21)]})
fig2 = px.line(tl, x="over", y=tl.columns[1], markers=True, color_discrete_sequence=["#1B4FFF"])
st.plotly_chart(apply_plotly_style(fig2, "Win % vs Overs", height=320), use_container_width=True)
st.caption(f"Pre-match P({team_a.split()[-1]})={p_pre*100:.1f}% → Live {p_live*100:.1f}% · Score model MAE ±{score_m['mae']} runs · Confusion matrix (best model): {bundle['confusion_matrix'].tolist()}")
footer()
