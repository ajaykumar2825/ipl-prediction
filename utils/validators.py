"""Shared validators + empty-state helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def guard_empty(df: pd.DataFrame, message: str = "No results for the current filters.") -> bool:
    if df is None or len(df) == 0:
        st.warning(f"⚠️ {message} Try widening seasons, teams or venues.")
        return True
    return False


def safe_select(label: str, options: list, default=None, key: str = ""):
    if not options:
        st.warning(f"No options available for {label}.")
        return None
    idx = 0
    if default in options:
        idx = options.index(default)
    return st.selectbox(label, options, index=idx, key=key or label)
