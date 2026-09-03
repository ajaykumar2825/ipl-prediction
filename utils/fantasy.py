"""Fantasy XI optimiser — value-based greedy selection under credit cap."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _fantasy_value(bat: pd.DataFrame, bowl: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    b = bat.set_index("player_name") if not bat.empty else pd.DataFrame()
    w = bowl.set_index("player_name") if not bowl.empty else pd.DataFrame()
    df = players.copy()
    runs = df["player_name"].map(b["runs"] if "runs" in getattr(b, "columns", []) else pd.Series(dtype=float)).fillna(0)
    sr = df["player_name"].map(b["strike_rate"] if "strike_rate" in getattr(b, "columns", []) else pd.Series(dtype=float)).fillna(0)
    wk = df["player_name"].map(w["wickets"] if "wickets" in getattr(w, "columns", []) else pd.Series(dtype=float)).fillna(0)
    econ = df["player_name"].map(w["economy"] if "economy" in getattr(w, "columns", []) else pd.Series(dtype=float)).fillna(9.0)
    df["exp_points"] = (runs * 1.0 + (sr - 120).clip(lower=-40) * 0.4 + wk * 25.0 + (9.0 - econ).clip(lower=-3) * 4.0 + 10).round(1)
    # credits 7.0–10.5 scaled from exp_points + noise-free deterministic hash
    r = df["exp_points"].rank(pct=True)
    df["credits"] = (7.0 + r * 3.5).round(1)
    df["confidence"] = (55 + r * 43).round(1)
    return df


def build_fantasy_xi(bat: pd.DataFrame, bowl: pd.DataFrame, players: pd.DataFrame,
                     budget: float = 100.0, wk: int = 1, bat_n: int = 4,
                     ar: int = 2, bowl_n: int = 4) -> tuple[pd.DataFrame, dict]:
    pool = _fantasy_value(bat, bowl, players)
    need = {"Wicket-Keeper": wk, "Batter": bat_n, "All-Rounder": ar, "Bowler": bowl_n}
    # value density greedy per role
    pool["density"] = pool["exp_points"] / pool["credits"]
    picks = []
    for role, n in need.items():
        cand = pool[pool["role"] == role].sort_values("density", ascending=False).head(max(n * 3, n + 2))
        picks.append(cand.head(n))
    xi = pd.concat(picks).sort_values("exp_points", ascending=False).reset_index(drop=True)
    total = float(xi["credits"].sum())
    # repair over-budget: swap most-expensive members for cheapest same-role alts
    guard = 0
    while total > budget and guard < 200:
        guard += 1
        cand_xi = xi.sort_values(["credits", "density"], ascending=[False, True]).iloc[0]
        alt = pool[(pool["role"] == cand_xi["role"]) & (~pool["player_name"].isin(xi["player_name"]))].sort_values("credits").head(1)
        if alt.empty or float(alt["credits"].iloc[0]) >= float(cand_xi["credits"]):
            swapped = False
            for _, row in xi.sort_values(["credits", "density"], ascending=[False, True]).iloc[1:].iterrows():
                alt2 = pool[(pool["role"] == row["role"]) & (~pool["player_name"].isin(xi["player_name"]))].sort_values("credits").head(1)
                if not alt2.empty and float(alt2["credits"].iloc[0]) < float(row["credits"]):
                    xi = pd.concat([xi[xi["player_name"] != row["player_name"]], alt2], ignore_index=True)
                    swapped = True
                    break
            if not swapped:
                break
        else:
            xi = xi[xi["player_name"] != cand_xi["player_name"]]
            xi = pd.concat([xi, alt], ignore_index=True)
        total = float(xi["credits"].sum())
    xi = xi.sort_values("exp_points", ascending=False).reset_index(drop=True)
    xi["is_captain"] = False
    xi["is_vice"] = False
    if len(xi):
        xi.loc[xi.index[0], "is_captain"] = True
    if len(xi) > 1:
        xi.loc[xi.index[1], "is_vice"] = True
    summary = {"total_credits": round(total, 1), "remaining": round(budget - total, 1),
               "expected_points": round(float(xi["exp_points"].sum()), 1)}
    return xi[["player_name", "role", "team", "credits", "exp_points", "confidence", "is_captain", "is_vice"]], summary
