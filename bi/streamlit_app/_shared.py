# bi/streamlit_app/_shared.py
import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_data():
    """
    Charge les données depuis le CSV fallback (Streamlit Cloud).
    """
    csv_fallback = Path(__file__).resolve().parents[1] / "data" / "processed" / "mv_month_brand_country.csv"

    if csv_fallback.exists():
        try:
            df = pd.read_csv(csv_fallback)
            # Debug : afficher colonnes lues
            st.caption(f"[DEBUG] Colonnes CSV fallback : {list(df.columns)}")
            return df
        except Exception as e:
            st.error(f"Erreur lecture CSV fallback: {e}")
            return pd.DataFrame()

    st.error(f"[DEBUG] Fichier CSV introuvable : {csv_fallback}")
    return pd.DataFrame()
