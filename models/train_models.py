"""Pre-train + persist models to ./models/winner_model.joblib (optional; app trains lazily)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib

BASE = Path(__file__).resolve().parent.parent


def main() -> None:
    from utils.ml_models import train_winner_models
    from utils.data_loader import ensure_datasets, load_all
    ensure_datasets()
    matches, _, _, _ = load_all()
    bundle = train_winner_models(str(len(matches)))
    out = BASE / "models" / "winner_bundle.joblib"
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"best": bundle["best_name"], "leaderboard": bundle["leaderboard"]}, out)
    print(f"Saved {out} · best={bundle['best_name']}")


if __name__ == "__main__":
    main()
