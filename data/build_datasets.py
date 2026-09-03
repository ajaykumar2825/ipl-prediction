"""Regenerate Parquet datasets deterministically:  python data/build_datasets.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.data_loader import ensure_datasets

if __name__ == "__main__":
    ensure_datasets()
    print("Datasets built in ./data/*.parquet")
