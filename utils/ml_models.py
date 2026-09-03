"""Lightweight ML: winner classification + score regression. No SHAP dep."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.ensemble import ExtraTreesClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

try:
    from xgboost import XGBClassifier
    _HAS_XGB = True
except Exception:
    _HAS_XGB = False


def build_match_features(matches: pd.DataFrame):
    df = matches.copy()
    le_team = LabelEncoder().fit(pd.concat([df["team1"], df["team2"]]).astype(str))
    le_venue = LabelEncoder().fit(df["venue"].astype(str))
    X = pd.DataFrame({
        "team1_enc": le_team.transform(df["team1"].astype(str)),
        "team2_enc": le_team.transform(df["team2"].astype(str)),
        "venue_enc": le_venue.transform(df["venue"].astype(str)),
        "toss_team1": (df["toss_winner"] == df["team1"]).astype(int),
        "toss_bat": (df["toss_decision"] == "bat").astype(int),
        "season_norm": (df["season"] - 2008) / 17.0,
        "h2h_proxy": ((df["team1"] > df["team2"]).astype(int)),
    })
    y = (df["winner"] == df["team1"]).astype(int)
    meta = {"le_team": le_team, "le_venue": le_venue}
    return X, y, meta


@st.cache_resource(show_spinner="Training prediction models…")
def train_winner_models(_matches_hash: str = "") -> dict:
    """Train small models on the current snapshot. Hash arg busts cache on data change."""
    import utils.data_loader as dl
    matches, _, _, _ = dl.load_all()
    X, y, meta = build_match_features(matches)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    cands: dict = {
        "Logistic Regression": LogisticRegression(max_iter=500),
        "Random Forest": RandomForestClassifier(n_estimators=120, max_depth=10, n_jobs=1, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
        "Extra Trees": ExtraTreesClassifier(n_estimators=120, max_depth=None, n_jobs=1, random_state=42),
    }
    if _HAS_XGB:
        cands["XGBoost"] = XGBClassifier(n_estimators=120, max_depth=5, learning_rate=0.08,
                                         subsample=0.9, colsample_bytree=0.9, n_jobs=1,
                                         eval_metric="logloss", random_state=42)
    rows, fitted = [], {}
    for name, clf in cands.items():
        clf.fit(Xtr, ytr)
        p = clf.predict(Xte)
        try:
            auc = roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])
        except Exception:
            auc = float("nan")
        rows.append({"model": name,
                     "accuracy": round(accuracy_score(yte, p), 4),
                     "precision": round(precision_score(yte, p, zero_division=0), 4),
                     "recall": round(recall_score(yte, p, zero_division=0), 4),
                     "f1": round(f1_score(yte, p, zero_division=0), 4),
                     "roc_auc": round(float(auc), 4) if auc == auc else None})
        fitted[name] = clf
    lb = pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)
    best_name = str(lb.iloc[0]["model"])
    cm = confusion_matrix(yte, fitted[best_name].predict(Xte))
    # feature importance (model-agnostic fallback to coefficients)
    best = fitted[best_name]
    try:
        imp = np.asarray(best.feature_importances_, dtype=float)
    except AttributeError:
        try:
            imp = np.abs(np.asarray(best.coef_).ravel())
        except Exception:
            imp = np.ones(X.shape[1])
    imp = imp / (imp.sum() + 1e-12)
    feat_imp = pd.DataFrame({"feature": list(X.columns), "importance": (imp * 100).round(1)}).sort_values("importance", ascending=False)
    return {"leaderboard": lb, "models": fitted, "best_name": best_name,
            "confusion_matrix": cm, "feature_importance": feat_imp, "meta": meta,
            "columns": list(X.columns)}


def predict_winner_proba(bundle: dict, team_a: str, team_b: str, venue: str,
                         toss_winner: str, toss_decision: str, season: int = 2025) -> tuple[float, str]:
    """Return (P(team_a wins), best_model_name). Handles unseen labels gracefully."""
    meta, model = bundle["meta"], bundle["models"][bundle["best_name"]]
    le_team, le_venue = meta["le_team"], meta["le_venue"]

    def enc_team(t):
        t = str(t)
        if t in set(le_team.classes_):
            return int(le_team.transform([t])[0])
        return int(np.median(le_team.transform(le_team.classes_)))

    def enc_venue(v):
        v = str(v)
        if v in set(le_venue.classes_):
            return int(le_venue.transform([v])[0])
        return int(np.median(le_venue.transform(le_venue.classes_)))

    X = pd.DataFrame([{
        "team1_enc": enc_team(team_a), "team2_enc": enc_team(team_b),
        "venue_enc": enc_venue(venue),
        "toss_team1": 1 if toss_winner == team_a else 0,
        "toss_bat": 1 if str(toss_decision).lower() == "bat" else 0,
        "season_norm": (int(season) - 2008) / 17.0,
        "h2h_proxy": 1 if str(team_a) > str(team_b) else 0,
    }], columns=bundle["columns"])
    p = float(model.predict_proba(X)[0][1])
    # Blend with in-play context is done by the page; here pure pre-match
    return float(np.clip(p, 0.02, 0.98)), str(bundle["best_name"])


def inplay_adjust(p_pre: float, current_score: int, overs: float, wickets: int,
                  team_a: str, team_b: str, venue_avg: float = 165.0) -> float:
    """Transparent rule-based in-play adjustment (no black box)."""
    overs = max(float(overs), 0.5)
    rr = current_score / overs
    par_rr = venue_avg / 20.0
    rr_edge = np.clip((rr - par_rr) / 4.0, -0.25, 0.25)
    wkt_pen = wickets * 0.028
    overs_left_factor = (20 - overs) / 20.0  # early game → regress to pre-match
    adj = p_pre + (rr_edge - wkt_pen) * (1 - overs_left_factor * 0.55)
    return float(np.clip(adj, 0.02, 0.98))


@st.cache_resource(show_spinner="Training score model…")
def train_score_model(_hash: str = ""):
    import utils.data_loader as dl
    matches, _, _, _ = dl.load_all()
    df = matches.copy()
    X = pd.DataFrame({
        "season_norm": (df["season"] - 2008) / 17.0,
        "is_final": ((df["season"] % 2) == 0).astype(int),
        "venue bat-first bias": (df["toss_decision"] == "bat").astype(int),
    })
    y = df["team1_score"].astype(float)
    reg = LinearRegression().fit(X, y)
    resid = float(np.abs(y - reg.predict(X)).mean())
    return {"model": reg, "mae": round(resid, 1)}
