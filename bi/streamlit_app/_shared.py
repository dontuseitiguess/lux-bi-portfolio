import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Charge le fallback CSV exporté depuis Postgres pour tourner sur Streamlit Cloud.
    On teste quelques chemins usuels pour éviter les soucis d'arborescence.
    """
    candidates = [
        Path(__file__).resolve().parents[2] / "data" / "processed" / "mv_month_brand_country.csv",
        Path(__file__).resolve().parents[1] / "data" / "processed" / "mv_month_brand_country.csv",
        Path.cwd() / "data" / "processed" / "mv_month_brand_country.csv",
    ]
    for p in candidates:
        if p.exists():
            try:
                df = pd.read_csv(p)
                return df
            except Exception:
                pass
    st.error("CSV fallback introuvable : data/processed/mv_month_brand_country.csv")
    return pd.DataFrame()

def safe_metric_number(value):
    if value is None:
        return "-"
    try:
        v = float(value)
    except Exception:
        return "-"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}k"
    return f"{v:,.0f}"
