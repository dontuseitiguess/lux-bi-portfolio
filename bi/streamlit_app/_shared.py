# bi/streamlit_app/_shared.py
from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def load_data() -> pd.DataFrame:
    """
    Charge la vue agrégée principale.
    Priorité :
      1) Base de données si DATABASE_URL/POSTGRES_URL dispo
      2) Fallback CSV: data/processed/mv_month_brand_country.csv
    """
    # 1) Essai DB si URL fournie en variable d'env (Cloud : souvent indispo → on tombera sur CSV)
    db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or ""
    if db_url:
        try:
            engine = create_engine(db_url)
            return pd.read_sql("select * from mv_month_brand_country", con=engine)
        except Exception as e:
            st.info("DB indisponible — fallback CSV utilisé.")
            # on continue vers CSV

    # 2) Fallback CSV (plusieurs chemins potentiels selon où est exécuté le script)
    candidates = [
        Path(__file__).resolve().parents[1] / "data" / "processed" / "mv_month_brand_country.csv",
        Path(__file__).resolve().parents[2] / "data" / "processed" / "mv_month_brand_country.csv",
        Path.cwd() / "data" / "processed" / "mv_month_brand_country.csv",
    ]
    for p in candidates:
        if p.exists():
            return pd.read_csv(p)

    raise FileNotFoundError(
        "Aucune source trouvée : ni connexion DB valide, ni CSV "
        "'data/processed/mv_month_brand_country.csv'."
    )


def safe_metric_number(x) -> str:
    try:
        return f"{float(x):,.0f}".replace(",", " ")
    except Exception:
        return "—"
