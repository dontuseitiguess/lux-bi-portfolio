# bi/streamlit_app/_shared.py
import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_data():
    """
    Charge les données depuis Postgres (si dispo) ou fallback CSV.
    Retourne un DataFrame pandas.
    """
    # Fallback CSV
    csv_fallback = Path(__file__).resolve().parents[1] / "data" / "processed" / "mv_month_brand_country.csv"

    if csv_fallback.exists():
        try:
            df = pd.read_csv(csv_fallback)
            return df
        except Exception as e:
            st.error(f"Erreur de lecture du CSV fallback: {e}")
            return pd.DataFrame()

    st.error("Aucune source de données trouvée (Postgres non connecté et CSV fallback manquant).")
    return pd.DataFrame()


def safe_metric_number(value):
    """
    Formate un nombre pour affichage dans st.metric.
    - Valeurs nulles => "-"
    - > 1M => "X.XM"
    - > 1k => "Xk"
    """
    if value is None:
        return "-"
    try:
        v = float(value)
    except Exception:
        return "-"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"{v/1_000:.0f}k"
    else:
        return f"{v:,.0f}"
