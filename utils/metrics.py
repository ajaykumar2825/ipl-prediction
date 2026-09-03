"""Derived metrics: batting / bowling aggregates, indices, similarity."""

from __future__ import annotations

import numpy as np
import pandas as pd


def batting_table(deliveries: pd.DataFrame) -> pd.DataFrame:
    g = deliveries.groupby("batter")
    runs = g["runs_off_bat"].sum()
    balls = g.size()
    fours = (deliveries["runs_off_bat"] == 4).groupby(deliveries["batter"]).sum()
    sixes = (deliveries["runs_off_bat"] == 6).groupby(deliveries["batter"]).sum()
    # dismissals
    dism = deliveries[deliveries["is_wicket"] == 1].groupby("batter").size()
    df = pd.DataFrame({"runs": runs, "balls": balls}).fillna(0)
    df["fours"] = fours.reindex(df.index).fillna(0).astype(int)
    df["sixes"] = sixes.reindex(df.index).fillna(0).astype(int)
    df["dismissals"] = dism.reindex(df.index).fillna(0).astype(int)
    df["strike_rate"] = np.where(df["balls"] > 0, df["runs"] / df["balls"] * 100, 0.0)
    df["average"] = np.where(df["dismissals"] > 0, df["runs"] / df["dismissals"], df["runs"])
    df["boundary_pct"] = np.where(df["balls"] > 0, (df["fours"] + df["sixes"]) / df["balls"] * 100, 0.0)
    df["aggression_index"] = (df["strike_rate"] / 200 * 60 + df["boundary_pct"] * 40 / 25).clip(0, 100)
    return df.reset_index().rename(columns={"batter": "player_name"})


def bowling_table(deliveries: pd.DataFrame) -> pd.DataFrame:
    g = deliveries.groupby("bowler")
    balls = g.size()
    runs = g["total_runs"].sum()
    wkts = g["is_wicket"].sum()
    dots = (deliveries["total_runs"] == 0).groupby(deliveries["bowler"]).sum()
    df = pd.DataFrame({"balls": balls, "runs_conceded": runs, "wickets": wkts}).fillna(0)
    df["dots"] = dots.reindex(df.index).fillna(0).astype(int)
    df["overs"] = df["balls"] / 6
    df["economy"] = np.where(df["overs"] > 0, df["runs_conceded"] / df["overs"], 0.0)
    df["strike_rate"] = np.where(df["wickets"] > 0, df["balls"] / df["wickets"], df["balls"])
    df["average"] = np.where(df["wickets"] > 0, df["runs_conceded"] / df["wickets"], df["runs_conceded"])
    df["dot_pct"] = np.where(df["balls"] > 0, df["dots"] / df["balls"] * 100, 0.0)
    return df.reset_index().rename(columns={"bowler": "player_name"})


def team_record(matches: pd.DataFrame, team: str) -> dict:
    played = matches[(matches["team1"] == team) | (matches["team2"] == team)]
    n = len(played)
    wins = int((played["winner"] == team).sum())
    home_venues = {
        "Mumbai Indians": "Wankhede", "Chennai Super Kings": "Chennai",
        "Royal Challengers Bengaluru": "Bengaluru", "Kolkata Knight Riders": "Eden",
        "Delhi Capitals": "Delhi", "Punjab Kings": "Mohali",
        "Rajasthan Royals": "Jaipur", "Sunrisers Hyderabad": "Hyderabad",
        "Gujarat Titans": "Ahmedabad", "Lucknow Super Giants": "Lucknow",
    }
    key = home_venues.get(team, "")
    home = played[played["venue"].str.contains(key, na=False)] if key else played.iloc[0:0]
    hn = len(home)
    hw = int((home["winner"] == team).sum()) if hn else 0
    chase_played = played[played["team2"] == team]
    chase_won = int((chase_played["winner"] == team).sum())
    bat1 = played[played["team1"] == team]
    defend_won = int((bat1["winner"] == team).sum())
    return {
        "played": n, "wins": wins, "losses": n - wins,
        "win_pct": round(wins / n * 100, 1) if n else 0.0,
        "home_win_pct": round(hw / hn * 100, 1) if hn else 0.0,
        "away_win_pct": round((wins - hw) / max(n - hn, 1) * 100, 1) if n else 0.0,
        "chase_win_pct": round(chase_won / len(chase_played) * 100, 1) if len(chase_played) else 0.0,
        "defend_win_pct": round(defend_won / len(bat1) * 100, 1) if len(bat1) else 0.0,
    }


def phase_scores(deliveries: pd.DataFrame, matches: pd.DataFrame, team: str) -> dict:
    d = deliveries[deliveries["batting_team"] == team].copy()
    if d.empty:
        return {"powerplay": 0.0, "death": 0.0, "dot_pct": 0.0, "boundary_pct": 0.0, "overall_rr": 0.0}
    pp = d[d["over"] <= 6].groupby("match_id")["total_runs"].sum().mean()
    death = d[d["over"] >= 16].groupby("match_id")["total_runs"].sum().mean()
    return {
        "powerplay": round(float(pp or 0), 1),
        "death": round(float(death or 0), 1),
        "dot_pct": round(float((d["total_runs"] == 0).mean() * 100), 1),
        "boundary_pct": round(float(d["runs_off_bat"].isin([4, 6]).mean() * 100), 1),
        "overall_rr": round(float(d["total_runs"].sum() / max(len(d) / 6, 1)), 2),
    }


def player_similarity(bat_df: pd.DataFrame, bowl_df: pd.DataFrame, target: str, top_n: int = 5) -> pd.DataFrame:
    merged = pd.merge(bat_df, bowl_df, on="player_name", how="outer", suffixes=("_bat", "_bowl")).fillna(0)
    feats = ["runs", "strike_rate", "average", "boundary_pct", "wickets", "economy", "dot_pct"]
    for f in feats:
        if f not in merged.columns:
            merged[f] = 0.0
    X = merged[feats].to_numpy(dtype=float)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xn = (X - mu) / sd
    if target not in set(merged["player_name"]):
        return pd.DataFrame()
    t = Xn[merged["player_name"].to_numpy() == target][0]
    dist = ((Xn - t) ** 2).sum(1) ** 0.5
    merged["similarity"] = (1 / (1 + dist) * 100).round(1)
    return merged.sort_values("similarity", ascending=False).head(top_n + 1).iloc[1:][["player_name", "similarity", "runs", "strike_rate", "wickets", "economy"]]
