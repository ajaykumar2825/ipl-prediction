# Architecture

```
streamlit run app.py
app.py ── landing + KPIs
pages/01..09 ── lazy-loaded, each calls load_all() (st.cache_data)
utils/data_loader.py ── Parquet or deterministic synthesis (seed 42)
utils/ml_models.py ── sklearn/XGBoost, st.cache_resource
utils/metrics|charts|insights|fantasy ── pure functions
config/ ── constants + Plotly theme
components/ ── hero, KPI cards, CSS, sidebar filters
data/*.parquet ── generated on first run (also data/build_datasets.py)
```

Memory: Parquet + categoricals, one cached dataset copy, small models
(n_estimators≤120, n_jobs=1), no TF/torch/LLM. Cold start < 15 s.
