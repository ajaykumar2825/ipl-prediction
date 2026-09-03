"""Global CSS — glassmorphism, premium sports theme, responsive."""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
.stApp { background: radial-gradient(1200px 500px at 15% -5%, rgba(27,79,255,.10), transparent),
                     radial-gradient(1000px 480px at 90% 0%, rgba(255,107,26,.10), transparent),
                     linear-gradient(180deg, #F7F9FF 0%, #F4F6FB 100%); }
.hero {
  background: linear-gradient(120deg, #0A1931 0%, #12295E 45%, #1B4FFF 75%, #FF6B1A 130%);
  border-radius: 20px; padding: 34px 30px; color: white; position: relative; overflow: hidden;
  box-shadow: 0 18px 50px rgba(10,25,49,.28);
}
.hero h1 { font-size: 2.1rem; font-weight: 800; margin: 0 0 6px 0; letter-spacing: -.5px; }
.hero p { opacity: .92; font-size: 1.02rem; margin: 0; }
.hero .badge { display:inline-block; background: rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.25);
  padding: 4px 12px; border-radius: 999px; font-size: .75rem; font-weight: 700; letter-spacing: 1.2px; margin-bottom: 10px; }
.kpi { background: rgba(255,255,255,.86); backdrop-filter: blur(10px); border: 1px solid rgba(27,79,255,.12);
  border-radius: 16px; padding: 16px 16px; box-shadow: 0 8px 24px rgba(10,25,49,.07); transition: transform .15s ease, box-shadow .15s ease; }
.kpi:hover { transform: translateY(-2px); box-shadow: 0 14px 32px rgba(10,25,49,.12); }
.kpi .lbl { font-size: .72rem; font-weight: 700; letter-spacing: 1px; color: #8A94A6; text-transform: uppercase; }
.kpi .val { font-size: 1.6rem; font-weight: 800; color: #0A1931; }
.kpi .sub { font-size: .8rem; color: #4B5563; }
.card { background: white; border: 1px solid rgba(27,79,255,.10); border-radius: 16px; padding: 18px;
  box-shadow: 0 8px 24px rgba(10,25,49,.06); }
.section-title { font-weight: 800; color: #0A1931; font-size: 1.15rem; margin: 6px 0 2px 0; }
.muted { color: #6B7280; font-size: .88rem; }
.footer { text-align:center; color:#8A94A6; font-size:.8rem; padding: 22px 0 6px 0; }
div.stButton > button { border-radius: 12px; font-weight: 700; }
.stDownloadButton > button { border-radius: 12px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0A1931 0%, #10234F 100%); }
[data-testid="stSidebar"] * { color: #E6EBF7 !important; }
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] { color: #0A1931; }
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)
