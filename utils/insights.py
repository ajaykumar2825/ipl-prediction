"""Rule-based analyst insight engine — no LLM needed."""

from __future__ import annotations

import numpy as np
import pandas as pd


def venue_insights(matches: pd.DataFrame, venues: pd.DataFrame) -> list[str]:
    out = []
    for _, v in venues.head(12).iterrows():
        chase = float(v["chase_win_pct"])
        verb = "favors chasing" if chase >= 50 else "favors defending"
        out.append(f"{v['venue'].split(',')[0]} {verb} — chasing wins {chase:.0f}% of {int(v['matches'])} matches "
                   f"(avg 1st innings {v['avg_first_innings']:.0f}, pitch: {v['pitch_class']}).")
    toss_field = float((matches["toss_decision"] == "field").mean() * 100)
    out.append(f"Captains prefer chasing league-wide — {toss_field:.0f}% choose to field first after winning the toss.")
    return out


def team_insights(matches: pd.DataFrame, deliveries: pd.DataFrame) -> list[str]:
    out = []
    w = matches["winner"].value_counts(normalize=True) * 100
    top = w.index[0]
    out.append(f"{top} own the league baseline with a {w.iloc[0]:.1f}% title-share of all matches since 2008.")
    pp = deliveries[deliveries["over"] <= 6].groupby("batting_team")["total_runs"].mean().sort_values(ascending=False)
    if len(pp):
        out.append(f"{pp.index[0]} dominate the powerplay ({pp.iloc[0]:.1f} runs/6 overs) — fastest starters in the league.")
    death = deliveries[deliveries["over"] >= 16].groupby("bowling_team")["total_runs"].mean().sort_values()
    if len(death):
        out.append(f"{death.index[0]} own the death overs, conceding only {death.iloc[0]:.1f} runs per game in overs 16–20.")
    spin = deliveries[deliveries["bowler"].str.contains("Chahal|Khan|Ashwin|Bishnoi|Patel|Chakravarthy|Kuldeep", na=False)]
    if len(spin):
        mid = spin[(spin["over"] >= 8) & (spin["over"] <= 14)]
        out.append(f"Spin controls the middle overs (8–14): economy {mid['total_runs'].mean()*6:.2f} per over across {len(mid):,} balls.")
    return out


def player_insights(deliveries: pd.DataFrame, player: str) -> list[str]:
    d = deliveries[(deliveries["batter"] == player) | (deliveries["bowler"] == player)]
    out = []
    if d.empty:
        return ["Not enough balls to generate insights for this player yet."]
    bat = d[d["batter"] == player]
    if len(bat) >= 20:
        sr = bat["runs_off_bat"].sum() / len(bat) * 100
        by_venue = bat.groupby("venue")["runs_off_bat"].agg(["sum", "count"])
        by_venue = by_venue[by_venue["count"] >= 12]
        if len(by_venue):
            best = (by_venue["sum"] / by_venue["count"] * 100).idxmax()
            best_sr = (by_venue["sum"] / by_venue["count"] * 100).max()
            lift = (best_sr - sr) / max(sr, 1) * 100
            if lift > 5:
                out.append(f"{player} performs {lift:.0f}% above career strike-rate at {str(best).split(',')[0]}.")
        out.append(f"Career T20 strike-rate {sr:.1f} across {len(bat):,} balls with {(bat['runs_off_bat'] == 6).sum()} sixes.")
    bowl = d[d["bowler"] == player]
    if len(bowl) >= 20:
        econ = bowl["total_runs"].sum() / (len(bowl) / 6)
        out.append(f"Concedes {econ:.2f} runs per over with a {(bowl['is_wicket'].sum() / max(len(bowl)/6,1)):.2f} wickets-per-over rate.")
    return out
