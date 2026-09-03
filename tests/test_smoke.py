"""Smoke tests — run with:  python -m pytest tests/ -q"""

from __future__ import annotations


def test_imports():
    import app  # noqa
    import utils.data_loader, utils.metrics, utils.charts, utils.ml_models, utils.insights, utils.fantasy  # noqa
    import components.cards, components.styles, components.sidebar  # noqa


def test_datasets_build_and_validate():
    from utils.data_loader import ensure_datasets, load_all
    ensure_datasets()
    # bypass streamlit cache wrapper for pure-python test
    load_fn = getattr(load_all, "__wrapped__", load_all)
    matches, deliveries, players, venues = load_fn()
    assert len(matches) > 900, f"too few matches: {len(matches)}"
    assert len(deliveries) > 100_000
    assert len(players) >= 150
    assert len(venues) >= 10
    for col in ("winner", "venue", "season"):
        assert col in matches.columns


def test_metrics_and_fantasy():
    from utils.data_loader import load_all
    from utils.metrics import batting_table, bowling_table, team_record
    from utils.fantasy import build_fantasy_xi
    load_fn = getattr(load_all, "__wrapped__", load_all)
    matches, deliveries, players, _ = load_fn()
    bat, bowl = batting_table(deliveries), bowling_table(deliveries)
    assert len(bat) > 0 and len(bowl) > 0
    rec = team_record(matches, "Mumbai Indians")
    assert rec["played"] > 0
    xi, summary = build_fantasy_xi(bat, bowl, players)
    assert len(xi) == 11
    assert summary["remaining"] >= -0.5


def test_ml_trains_and_predicts():
    from utils.data_loader import load_all
    from utils.ml_models import predict_winner_proba, train_winner_models
    load_fn = getattr(load_all, "__wrapped__", load_all)
    matches, _, _, _ = load_fn()
    train_fn = getattr(train_winner_models, "__wrapped__", train_winner_models)
    bundle = train_fn(str(len(matches)))
    assert len(bundle["leaderboard"]) >= 4
    p, name = predict_winner_proba(bundle, "Mumbai Indians", "Chennai Super Kings",
                                   "Wankhede Stadium, Mumbai", "Mumbai Indians", "field")
    assert 0.0 < p < 1.0 and name
