cat > bi/streamlit_app/_shared.py << 'PY'
import os
import pandas as pd
import streamlit as st

def _secrets():
    try:
        return dict(st.secrets)
    except Exception:
        return {}
SECRETS = _secrets()

def get_cfg(key, default=None):
    return SECRETS.get(key, os.getenv(key, default))

@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    # Fichiers CSV (fallback)
    csv_path = get_cfg("CSV_FALLBACK_PATH", "data/processed/mv_month_brand_country.csv")
    dm_path  = get_cfg("CSV_DIM_MARQUE_PATH", "data/processed/dim_marque.csv")
    dp_path  = get_cfg("CSV_DIM_PAYS_PATH",   "data/processed/dim_pays.csv")

    mv = pd.read_csv(csv_path)

    # Harmonisation des colonnes
    rename_map = {
        "month_key": "month",
        "ca": "ca_total",
        "marge_pct_avg": "marge_pct",
    }
    mv = mv.rename(columns=rename_map)
    mv["month"] = pd.to_datetime(mv["month"], errors="coerce")

    # Enrichissement libellés
    if os.path.exists(dm_path):
        dm = pd.read_csv(dm_path)  # marque_key, marque
        if "marque_key" in mv.columns:
            mv = mv.merge(dm, on="marque_key", how="left")
    if os.path.exists(dp_path):
        dp = pd.read_csv(dp_path)  # pays_key, pays
        if "pays_key" in mv.columns:
            mv = mv.merge(dp, on="pays_key", how="left")

    # Valeurs par défaut si colonnes manquent
    for col, default in [("ca_online", 0.0), ("ca_offline", 0.0), ("unites", 0.0), ("aov", None), ("marge_pct", None)]:
        if col not in mv.columns:
            mv[col] = default
    if "ca_total" not in mv.columns:
        mv["ca_total"] = mv["ca_online"].fillna(0) + mv["ca_offline"].fillna(0)

    mv["__source__"] = "csv"
    return mv
PY
