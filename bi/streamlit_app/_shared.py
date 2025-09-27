# bi/streamlit_app/_shared.py
import pandas as pd
import streamlit as st
from pathlib import Path

@st.cache_data
def load_data():
    """
    Charge les données depuis le CSV fallback (Streamlit Cloud ou local).
    Teste plusieurs chemins possibles pour éviter les erreurs.
    """
    candidates = [
        Path(__file__).resolve().parents[2] / "data" / "processed" / "mv_month_brand_country.csv",
        Path(__file__).resolve().parents[1] / "data" / "processed" / "mv_month_brand_country.csv",
        Path.cwd() / "data" / "processed" / "mv_month_brand_country.csv",
        Path.cwd() / "data" / "raw" / "mv_month_brand_country.csv",
    ]

    for csv_path in candidates:
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                st.caption(f"[DEBUG] Chargé depuis : {csv_path}")
                st.caption(f"[DEBUG] Colonnes : {list(df.columns)}")

                if df.empty:
                    st.error("⚠️ Le CSV fallback a été trouvé mais il est vide.")
                    st.stop()

                return df
            except Exception as e:
                st.error(f"Erreur lecture {csv_path}: {e}")
                st.stop()

    st.error("[DEBUG] Aucun CSV trouvé dans les chemins testés.")
    st.stop()


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
