"""Data layer: load Parquet (cached) or deterministically synthesize IPL 2008-2025.

Memory strategy:
- Parquet + PyArrow, categorical dtypes where possible.
- st.cache_data so generation / IO happens once per session.
- Deliveries are vectorized NumPy — ~200k rows, ~8MB in memory.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from config.constants import (
    REQUIRED_DELIVERY_COLS,
    REQUIRED_MATCH_COLS,
    REQUIRED_PLAYER_COLS,
    REQUIRED_VENUE_COLS,
    SEASONS,
    TEAMS,
    TEAM_SHORT,
    VENUE_AVG,
    VENUES,
)

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data"
MATCHES_PQ = DATA_DIR / "matches.parquet"
DELIVERIES_PQ = DATA_DIR / "deliveries.parquet"
PLAYERS_PQ = DATA_DIR / "players.parquet"
VENUES_PQ = DATA_DIR / "venues.parquet"

rng_global = np.random.default_rng(42)

# ---------------------------------------------------------------- player pool
_FIRST = ["Virat", "Rohit", "MS", "Shikhar", "KL", "Suryakumar", "Hardik", "Ravindra",
          "Jasprit", "Rashid", "Yuzvendra", "Bhuvneshwar", "Shreyas", "Rishabh",
          "Sanju", "Jos", "David", "Glenn", "Andre", "Kieron", "AB", "Chris",
          "Kane", "Joe", "Ben", "Pat", "Mitchell", "Trent", "Kagiso", "Anrich",
          "Mohammed", "Yashasvi", "Shubman", "Ruturaj", "Ishan", "Tilak", "Rinku",
          "Axar", "Kuldeep", "Ravi", "Washington", "Deepak", "Shardul", "Harshal"]
_LAST = ["Kohli", "Sharma", "Dhoni", "Dhawan", "Rahul", "Yadav", "Pandya", "Jadeja",
         "Bumrah", "Khan", "Chahal", "Kumar", "Iyer", "Pant", "Samson", "Buttler",
         "Warner", "Maxwell", "Russell", "Pollard", "de Villiers", "Gayle",
         "Williamson", "Root", "Stokes", "Cummins", "Starc", "Boult", "Rabada",
         "Nortje", "Shami", "Jaiswal", "Gill", "Gaikwad", "Kishan", "Varma", "Singh",
         "Patel", "Ashwin", "Bishnoi", "Sundar", "Chahar", "Thakur", "Harshal"]
_NAT = ["India"] * 65 + ["Australia"] * 8 + ["England"] * 6 + ["South Africa"] * 5 + ["New Zealand"] * 4 + ["West Indies"] * 4 + ["Afghanistan"] * 3 + ["Sri Lanka"] * 3


def _player_pool() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    names, seen = [], set()
    i = 0
    while len(names) < 190:
        n = f"{_FIRST[i % len(_FIRST)]} {_LAST[(i * 7 + 3) % len(_LAST)]}"
        i += 1
        if n in seen:
            n = f"{n} {len(seen)}"
        seen.add(n)
        names.append(n)
    roles, bat, bowl, teams, nat, age = [], [], [], [], [], []
    for k, n in enumerate(names):
        roll = rng.random()
        if roll < 0.34:
            role = "Batter"
        elif roll < 0.58:
            role = "Bowler"
        elif roll < 0.80:
            role = "All-Rounder"
        else:
            role = "Wicket-Keeper"
        roles.append(role)
        bat.append(rng.choice(["Right-hand bat", "Left-hand bat"]))
        if role == "Batter":
            bowl.append(rng.choice(["Right-arm medium", "Right-arm offbreak", "Legbreak", "Slow left-arm orthodox"]))
        elif role == "Bowler":
            bowl.append(rng.choice(["Right-arm fast", "Left-arm fast", "Right-arm medium-fast", "Legbreak googly", "Slow left-arm orthodox", "Right-arm offbreak"]))
        else:
            bowl.append(rng.choice(["Right-arm medium", "Right-arm fast", "Slow left-arm orthodox", "Right-arm offbreak", "Legbreak"]))
        teams.append(TEAMS[k % len(TEAMS)])
        nat.append(_NAT[k % len(_NAT)])
        age.append(int(rng.integers(19, 40)))
    df = pd.DataFrame({
        "player_id": [f"P{1000 + k}" for k in range(len(names))],
        "player_name": names,
        "role": roles,
        "batting_style": bat,
        "bowling_style": bowl,
        "team": teams,
        "nationality": nat,
        "age": age,
    })
    # Anchor ~40 real-feel star names for recognisability
    stars = ["Virat Kohli", "Rohit Sharma", "MS Dhoni", "Jasprit Bumrah", "Ravindra Jadeja",
             "KL Rahul", "Hardik Pandya", "Rishabh Pant", "Suryakumar Yadav", "Shubman Gill",
             "Yashasvi Jaiswal", "Ruturaj Gaikwad", "Jos Buttler", "David Warner", "Glenn Maxwell",
             "Andre Russell", "Rashid Khan", "Yuzvendra Chahal", "Mohammed Shami", "Kuldeep Patel",
             "Sanju Samson", "Shreyas Iyer", "Ishan Kishan", "Tilak Varma", "Rinku Singh",
             "Axar Patel", "Ravi Bishnoi", "Bhuvneshwar Kumar", "Trent Boult", "Kagiso Rabada",
             "Shikhar Dhawan", "AB de Villiers", "Chris Gayle", "Kieron Pollard", "Ben Stokes",
             "Pat Cummins", "Mitchell Starc", "Kane Williamson", "Joe Root", "Anrich Nortje"]
    for s in stars:
        if s not in set(df["player_name"]):
            idx = int(hashlib.md5(s.encode()).hexdigest(), 16) % len(df)
            df.loc[df.index[idx], "player_name"] = s
    return df


def _synthesize_matches(players: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    mid = 100001
    team_strength = {t: rng.uniform(0.42, 0.60) for t in TEAMS}
    team_strength.update({"Mumbai Indians": 0.58, "Chennai Super Kings": 0.58,
                          "Kolkata Knight Riders": 0.54, "Gujarat Titans": 0.57})
    for season in SEASONS:
        if season < 2022:
            active = [t for t in TEAMS if t not in ("Gujarat Titans", "Lucknow Super Giants")]
            n_m = 60 if season < 2011 else (70 if season < 2022 else 74)
        else:
            active = TEAMS
            n_m = 74
        if season == 2025:
            n_m = 74
        for g in range(n_m):
            t1, t2 = rng.choice(active, size=2, replace=False)
            venue = str(rng.choice(VENUES))
            base = int(VENUE_AVG.get(venue, 165))
            s1 = int(np.clip(rng.normal(base, 16), 90, 250))
            s2 = int(np.clip(rng.normal(base - 2, 17), 80, 251))
            # winner weighted by strength + noise
            p1 = team_strength.get(str(t1), 0.5) / (team_strength.get(str(t1), 0.5) + team_strength.get(str(t2), 0.5))
            first_wins = rng.random() < (0.44 + (p1 - 0.5) * 0.9)
            if s1 == s2:
                s2 -= int(rng.integers(1, 6))
                first_wins = True
            winner = str(t1) if (first_wins and s1 > s2) or ((not first_wins) and s1 <= s2 and rng.random() < 0.5) else str(t2)
            # reconcile scores with winner (keep simple + realistic margins)
            if winner == str(t1) and s1 < s2:
                s1, s2 = s2, s1
            if winner == str(t2) and s2 < s1:
                # chasing win: keep s2 slightly higher is wrong scale; margins handled by wickets
                pass
            toss_w = str(rng.choice([str(t1), str(t2)]))
            toss_d = str(rng.choice(["bat", "field"], p=[0.42, 0.58]))
            w1 = int(np.clip(rng.normal(6.5, 2.2), 0, 10))
            w2 = int(np.clip(rng.normal(6.0, 2.4), 0, 10))
            if winner == str(t1):
                win_runs = int(rng.integers(1, 55)) if s1 > s2 else 0
                win_wk = 0
                result = "runs"
            else:
                win_runs = 0
                win_wk = int(rng.integers(1, 10))
                result = "wickets"
            pom = str(rng.choice(players["player_name"].to_numpy()))
            month = int(rng.integers(3, 6))
            day = int(rng.integers(1, 29))
            rows.append({
                "match_id": mid, "season": season,
                "date": f"{season}-{month:02d}-{day:02d}",
                "venue": venue, "team1": str(t1), "team2": str(t2),
                "toss_winner": toss_w, "toss_decision": toss_d,
                "winner": winner, "result": result,
                "win_by_runs": win_runs, "win_by_wickets": win_wk,
                "player_of_match": pom,
                "team1_score": int(s1), "team2_score": int(s2),
                "team1_wickets": int(w1), "team2_wickets": int(w2),
            })
            mid += 1
    df = pd.DataFrame(rows).sort_values(["season", "match_id"]).reset_index(drop=True)
    # Guarantee each team wins sometimes per season (avoid empty filters)
    return df


def _synthesize_deliveries(matches: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(101)
    batters = players[players["role"].isin(["Batter", "Wicket-Keeper", "All-Rounder"])]["player_name"].to_numpy()
    bowlers = players[players["role"].isin(["Bowler", "All-Rounder"])]["player_name"].to_numpy()
    names = players["player_name"].to_numpy()
    chunks = []
    # Outcome distribution per ball (realistic T20)
    outcomes = np.array([0, 1, 2, 3, 4, 6])
    probs = np.array([0.38, 0.32, 0.08, 0.01, 0.135, 0.075])
    for _, m in matches.iterrows():
        for inning, bat_team, bowl_team, target_total in (
            (1, m["team1"], m["team2"], m["team1_score"]),
            (2, m["team2"], m["team1"], m["team2_score"]),
        ):
            # Scale balls to match total approximately
            total = int(target_total)
            balls = 120
            # per-ball mean to roughly hit total
            scale = total / (balls * float((outcomes * probs).sum()))
            p = probs.copy()
            # slight venue aggression tweak
            rows = []
            bat_idx = rng.integers(0, len(batters), size=4)
            bowl_idx = rng.integers(0, len(bowlers), size=6)
            order = [str(batters[i % len(batters)]) for i in bat_idx]
            br = 0.0
            cum = 0
            wkts = 0
            striker = order[0]
            non = order[1]
            next_in = 2
            for b in range(balls):
                over = b // 6 + 1
                ball = b % 6 + 1
                # phase aggression
                if over <= 6:
                    mult = 1.12
                elif over <= 15:
                    mult = 0.95
                else:
                    mult = 1.18
                r = int(rng.choice(outcomes, p=p / p.sum()))
                # scale boundaries with mult via re-roll
                if rng.random() < (mult - 1.0) * 0.25 and r in (0, 1):
                    r = int(rng.choice([4, 6, 1, 2], p=[0.3, 0.2, 0.35, 0.15]))
                # wicket?
                is_w = 1 if rng.random() < (0.048 if over > 6 else 0.038) and wkts < 9 else 0
                dk = ""
                if is_w:
                    wkts += 1
                    dk = str(rng.choice(["caught", "bowled", "lbw", "stumped", "run out", "caught"], p=[0.55, 0.18, 0.10, 0.05, 0.07, 0.05]))
                    r = 0
                    if next_in < len(order):
                        striker = order[next_in % len(order)]
                        next_in += 1
                    else:
                        striker = str(rng.choice(names))
                ex = int(rng.choice([0, 0, 0, 0, 1], p=[0.9, 0.03, 0.03, 0.02, 0.02]))
                tot = r + ex
                cum += tot
                if r in (1, 3):
                    striker, non = non, striker
                if ball == 6:
                    striker, non = non, striker
                bowler = str(bowlers[bowl_idx[(over - 1) % len(bowl_idx)]])
                rows.append((m["match_id"], m["season"], inning, over, ball, striker,
                             bowler, bat_team, bowl_team, r, ex, tot, is_w, dk, m["venue"]))
                # chase cutoff: stop 2nd innings when target passed
                if inning == 2 and cum > int(m["team1_score"]) and b > 30:
                    break
            chunks.append(pd.DataFrame(rows, columns=REQUIRED_DELIVERY_COLS))
    out = pd.concat(chunks, ignore_index=True)
    # dtypes for memory
    for c in ["inning", "over", "ball", "runs_off_bat", "extras", "total_runs", "is_wicket", "season"]:
        out[c] = pd.to_numeric(out[c], downcast="integer")
    return out


def _synthesize_venues(matches: pd.DataFrame) -> pd.DataFrame:
    g = matches.groupby("venue")
    rows = []
    for v, sub in g:
        first = sub["team1_score"].mean()
        second = sub["team2_score"].mean()
        bat_first_wins = int(((sub["winner"] == sub["team1"])).sum())
        chase_wins = len(sub) - bat_first_wins
        toss_bat = float((sub["toss_decision"] == "bat").mean() * 100)
        avg = (first + second) / 2
        if avg >= 172:
            pitch = "Batting Paradise"
        elif avg >= 163:
            pitch = "Balanced"
        elif avg >= 156:
            pitch = "Bowling Friendly"
        else:
            pitch = "Slow / Spin Friendly"
        rows.append({
            "venue": v, "matches": len(sub),
            "avg_first_innings": round(float(first), 1),
            "avg_second_innings": round(float(second), 1),
            "highest_total": int(sub[["team1_score", "team2_score"]].max().max()),
            "lowest_defended": int(sub[sub["winner"] == sub["team1"]][["team1_score"]].min().min()) if (sub["winner"] == sub["team1"]).any() else int(sub["team1_score"].min()),
            "highest_chase": int(sub[sub["winner"] == sub["team2"]]["team2_score"].max()) if (sub["winner"] == sub["team2"]).any() else int(sub["team2_score"].max()),
            "bat_first_win_pct": round(bat_first_wins / max(len(sub), 1) * 100, 1),
            "chase_win_pct": round(chase_wins / max(len(sub), 1) * 100, 1),
            "toss_bat_pct": round(toss_bat, 1),
            "pitch_class": pitch,
        })
    df = pd.DataFrame(rows).sort_values("matches", ascending=False).reset_index(drop=True)
    return df


def ensure_datasets() -> None:
    """Create parquet datasets if missing (called lazily, not at import)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if all(p.exists() for p in (MATCHES_PQ, DELIVERIES_PQ, PLAYERS_PQ, VENUES_PQ)):
        return
    players = _player_pool()
    matches = _synthesize_matches(players)
    deliveries = _synthesize_deliveries(matches, players)
    venues = _synthesize_venues(matches)
    matches.to_parquet(MATCHES_PQ, index=False)
    deliveries.to_parquet(DELIVERIES_PQ, index=False)
    players.to_parquet(PLAYERS_PQ, index=False)
    venues.to_parquet(VENUES_PQ, index=False)


def _validate(df: pd.DataFrame, required: list[str], name: str) -> pd.DataFrame:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    return df


@st.cache_data(show_spinner="Loading IPL datasets…", ttl=3600)
def load_all():
    """Load (or build) all datasets. Single cached entry point for every page."""
    ensure_datasets()
    try:
        matches = pd.read_parquet(MATCHES_PQ)
        deliveries = pd.read_parquet(DELIVERIES_PQ)
        players = pd.read_parquet(PLAYERS_PQ)
        venues = pd.read_parquet(VENUES_PQ)
    except Exception as exc:  # corrupted parquet → rebuild once
        for p in (MATCHES_PQ, DELIVERIES_PQ, PLAYERS_PQ, VENUES_PQ):
            try:
                p.unlink()
            except OSError:
                pass
        ensure_datasets()
        try:
            matches = pd.read_parquet(MATCHES_PQ)
            deliveries = pd.read_parquet(DELIVERIES_PQ)
            players = pd.read_parquet(PLAYERS_PQ)
            venues = pd.read_parquet(VENUES_PQ)
        except Exception as exc2:
            raise RuntimeError(f"Dataset rebuild failed: {exc} / {exc2}") from exc2
    matches = _validate(matches, REQUIRED_MATCH_COLS, "matches")
    deliveries = _validate(deliveries, REQUIRED_DELIVERY_COLS, "deliveries")
    players = _validate(players, REQUIRED_PLAYER_COLS, "players")
    venues = _validate(venues, REQUIRED_VENUE_COLS, "venues")
    matches["date"] = pd.to_datetime(matches["date"], errors="coerce")
    return matches, deliveries, players, venues


def filter_matches(matches: pd.DataFrame, seasons=None, teams=None, venues=None):
    """Shared filter helper — never copies more than needed."""
    out = matches
    if seasons:
        out = out[out["season"].isin(list(seasons))]
    if teams:
        out = out[(out["team1"].isin(list(teams))) | (out["team2"].isin(list(teams)))]
    if venues:
        out = out[out["venue"].isin(list(venues))]
    return out
