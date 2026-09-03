"""Page 4 — Match Intelligence."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from components.cards import footer, hero, kpi_row, section
from components.styles import inject
from config.theme import apply_plotly_style
from utils.charts import partnership_bars, worm_chart
from utils.data_loader import load_all

st.set_page_config(page_title="Match Intelligence · IPL", page_icon="🎯", layout="wide")
inject()

try:
    matches, deliveries, players, venues = load_all()
except Exception as exc:
    st.error(f"Dataset failed to load: {exc}")
    st.stop()

hero("Match Intelligence", "Timeline, worm, partnerships, phase report and impact scores for any game.")
seasons = sorted(matches["season"].unique().tolist(), reverse=True)
season = st.selectbox("Season", seasons, key="mi_season")
ms = matches[matches["season"] == season].sort_values("date")
labels = [f"{r['team1'].split()[-1]} vs {r['team2'].split()[-1]} · {r['date'].date()} · #{r['match_id']}" for _, r in ms.iterrows()]
ids = ms["match_id"].tolist()
pick = st.selectbox("Match", labels, key="mi_match") if labels else None
if pick is None:
    st.stop()
mid = ids[labels.index(pick)]
m = ms[ms["match_id"] == mid].iloc[0]
ball = deliveries[deliveries["match_id"] == mid].sort_values(["inning", "over", "ball"])

kpi_row([
    ("Fixture", f"{m['team1'].split()[-1]} v {m['team2'].split()[-1]}", str(m["venue"]).split(",")[0][:26]),
    ("Result", f"{m['winner'].split()[-1]} won", f"by {m['win_by_runs'] or m['win_by_wickets']} {m['result']}"),
    ("Scores", f"{m['team1_score']}/{m['team1_wickets']}", f"vs {m['team2_score']}/{m['team2_wickets']}"),
    ("POTM", str(m["player_of_match"])[:20], f"Toss: {str(m['toss_winner']).split()[-1]} ({m['toss_decision']})"),
])

c1, c2 = st.columns([1.5, 1])
with c1:
    st.plotly_chart(worm_chart(ball, m), use_container_width=True)
with c2:
    st.plotly_chart(partnership_bars(ball), use_container_width=True)

# Phase analysis + momentum
sec1, sec2 = st.columns(2)
with sec1:
    section("Phase report", "Powerplay / middle / death splits")
    rows = []
    for inn in (1, 2):
        d = ball[ball["inning"] == inn]
        rows.append({"innings": inn,
                     "PP (1-6)": int(d[d["over"] <= 6]["total_runs"].sum()),
                     "Middle (7-15)": int(d[(d["over"] >= 7) & (d["over"] <= 15)]["total_runs"].sum()),
                     "Death (16-20)": int(d[d["over"] >= 16]["total_runs"].sum()),
                     "Dots %": round(float((d["total_runs"] == 0).mean() * 100), 1) if len(d) else 0.0,
                     "Wickets": int(d["is_wicket"].sum())})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
with sec2:
    section("Turning points", "Biggest single-over swings")
    ov = ball.groupby(["inning", "over"]).agg(runs=("total_runs", "sum"), wkts=("is_wicket", "sum")).reset_index()
    ov = ov.sort_values("runs", ascending=False).head(6)
    st.dataframe(ov, use_container_width=True, hide_index=True)

section("Player impact scores", "Runs + 1.5×SR edge + 20×wickets − economy drag (transparent formula)")
imp_bat = ball.groupby("batter").agg(runs=("runs_off_bat", "sum"), balls=("runs_off_bat", "size")).reset_index()
imp_bat["sr"] = imp_bat["runs"] / imp_bat["balls"] * 100
imp_bat["impact"] = (imp_bat["runs"] + (imp_bat["sr"] - 130).clip(lower=-50) * 0.5).round(1)
imp_bwl = ball.groupby("bowler").agg(wkts=("is_wicket", "sum"), runs_c=("total_runs", "sum"), balls=("total_runs", "size")).reset_index()
imp_bwl["impact"] = (imp_bwl["wkts"] * 20 - (imp_bwl["runs_c"] / (imp_bwl["balls"] / 6) - 8).clip(lower=-4) * 2).round(1)
i1, i2 = st.columns(2)
with i1:
    st.dataframe(imp_bat.sort_values("impact", ascending=False).head(8), use_container_width=True, hide_index=True)
with i2:
    st.dataframe(imp_bwl.sort_values("impact", ascending=False).head(8), use_container_width=True, hide_index=True)
footer()
