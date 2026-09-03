"""Page 3 — Player Analytics Center."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from components.cards import footer, hero, kpi_row, section
from components.styles import inject
from config.theme import apply_plotly_style
from utils.charts import spider_player
from utils.data_loader import load_all
from utils.insights import player_insights
from utils.metrics import batting_table, bowling_table, player_similarity

st.set_page_config(page_title="Player Analytics · IPL", page_icon="⭐", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Player Analytics Center", "Profiles, consistency science, clutch flags and similarity search.")
names = sorted(players["player_name"].unique().tolist())
q = st.text_input("🔍 Search player", value="Virat Kohli", key="player_search")
cands = [n for n in names if q.lower() in n.lower()][:12] if q else names[:12]
player = st.selectbox("Player", cands or names[:12], key="player_pick")
if not player:
    st.stop()

meta = players[players["player_name"] == player].iloc[0]
c1, c2 = st.columns([1, 2])
with c1:
    st.markdown(f"""<div class="card"><b style="font-size:1.2rem">{player}</b><br>
    <span class="muted">{meta['role']} · {meta['team']}</span><br>
    <span class="muted">{meta['batting_style']} · {meta['bowling_style']}</span><br>
    <span class="muted">{meta['nationality']} · Age {meta['age']}</span></div>""", unsafe_allow_html=True)
    st.markdown("")
    st.markdown("**🤖 Analyst notes**")
    for ins in player_insights(deliveries, player):
        st.success(ins)

bat_all = batting_table(deliveries)
bowl_all = bowling_table(deliveries)
br = bat_all[bat_all["player_name"] == player]
bw = bowl_all[bowl_all["player_name"] == player]
runs = int(br["runs"].iloc[0]) if len(br) else 0
sr = float(br["strike_rate"].iloc[0]) if len(br) else 0.0
avg = float(br["average"].iloc[0]) if len(br) else 0.0
wk = int(bw["wickets"].iloc[0]) if len(bw) else 0
econ = float(bw["economy"].iloc[0]) if len(bw) else 0.0

with c2:
    kpi_row([
        ("Runs", f"{runs:,}", f"SR {sr:.1f}"),
        ("Average", f"{avg:.1f}", "per dismissal"),
        ("Wickets", f"{wk}", f"Econ {econ:.2f}" if wk else "—"),
        ("Sixes", f"{int(br['sixes'].iloc[0]) if len(br) else 0}", f"Fours {int(br['fours'].iloc[0]) if len(br) else 0}"),
    ])
    # Clutch + consistency (rule-based)
    d = deliveries[(deliveries["batter"] == player)]
    clutch = 0.0
    if len(d):
        death = d[d["over"] >= 16]
        clutch = float(death["runs_off_bat"].sum() / max(len(death), 1) * 100) if len(death) else 0.0
    st.markdown(f'<div class="card">🔥 <b>Clutch index</b> (death-over SR): <b>{clutch:.1f}</b> · '
                f"Boundary dependency: <b>{float(br['boundary_pct'].iloc[0]) if len(br) else 0:.1f}%</b> of balls</div>",
                unsafe_allow_html=True)

t1, t2 = st.columns(2)
with t1:
    section("Performance by season", "Runs & strike-rate trajectory")
    s = deliveries[deliveries["batter"] == player].groupby("season").agg(runs=("runs_off_bat", "sum"), balls=("runs_off_bat", "size")).reset_index()
    if not s.empty:
        s["sr"] = (s["runs"] / s["balls"] * 100).round(1)
        fig = px.bar(s, x="season", y="runs", color="sr", color_continuous_scale="Blues", hover_data=["balls", "sr"])
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(apply_plotly_style(fig, f"{player} — Runs by Season", height=360), use_container_width=True)
    else:
        st.info("No batting data for this player in the sample.")
with t2:
    section("Spider profile", "Percentile-style skill shape (0–100)")
    vals = {
        "Power": float(np.clip(sr / 180 * 100, 0, 100)),
        "Volume": float(np.clip(runs / max(bat_all['runs'].max(), 1) * 100 * 4, 0, 100)),
        "Wickets": float(np.clip(wk / max(bowl_all['wickets'].max(), 1) * 100 * 3, 0, 100)),
        "Control": float(np.clip((10 - econ) / 8 * 100, 0, 100)) if wk else 20.0,
        "Boundary": float(np.clip(float(br["boundary_pct"].iloc[0]) if len(br) else 0, 0, 100) / 25 * 100 / 4),
    }
    st.plotly_chart(spider_player(vals), use_container_width=True)

u1, u2 = st.columns(2)
with u1:
    section("Dismissal mix", "How they get out (league balls faced)")
    dd = deliveries[(deliveries["batter"] == player) & (deliveries["is_wicket"] == 1)]
    if not dd.empty:
        c = dd["dismissal_kind"].value_counts().reset_index()
        c.columns = ["mode", "n"]
        figd = px.pie(c, names="mode", values="n", hole=0.5, color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(apply_plotly_style(figd, "Dismissal Distribution", height=340), use_container_width=True)
    else:
        st.info("No dismissals recorded — remarkably consistent.")
with u2:
    section("Similar players", "Euclidean similarity over runs/SR/wickets/economy")
    sim = player_similarity(bat_all, bowl_all, player, top_n=5)
    if sim.empty:
        st.info("Similarity engine needs more data for this name.")
    else:
        st.dataframe(sim, use_container_width=True, hide_index=True)
footer()
