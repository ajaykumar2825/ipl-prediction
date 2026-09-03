"""Reusable UI components."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def hero(title: str, subtitle: str, badge: str = "● LIVE · IPL 2008 – 2025"):
    st.markdown(
        f"""<div class="hero"><div class="badge">{badge}</div>
        <h1>{title}</h1><p>{subtitle}</p></div>""",
        unsafe_allow_html=True,
    )


def kpi_row(items: list[tuple[str, str, str]]):
    cols = st.columns(len(items))
    for c, (lbl, val, sub) in zip(cols, items):
        with c:
            st.markdown(f'<div class="kpi"><div class="lbl">{lbl}</div><div class="val">{val}</div><div class="sub">{sub}</div></div>',
                        unsafe_allow_html=True)


def section(title: str, blurb: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if blurb:
        st.markdown(f'<div class="muted">{blurb}</div>', unsafe_allow_html=True)


def download_df(df: pd.DataFrame, name: str, label: str = "⬇ Download CSV"):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"), file_name=name, mime="text/csv", key=f"dl_{name}")


def footer():
    st.markdown(
        '<div class="footer">IPL Sports Analytics Platform · Enterprise Cricket Intelligence · '
        'Data: IPL 2008–2025 · Built with Streamlit + Plotly + scikit-learn · v2.1.0</div>',
        unsafe_allow_html=True,
    )


def empty_state(msg: str):
    st.info(f"ℹ️ {msg}")
