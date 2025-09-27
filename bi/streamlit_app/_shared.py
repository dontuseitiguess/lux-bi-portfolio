import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from typing import Tuple, Dict, Any

# =========================
# Chargement & préparation
# =========================

@st.cache_data
def _read_csv_robuste() -> pd.DataFrame:
    """Recherche le fallback CSV à divers chemins pour Cloud / local."""
    candidates = [
        Path(__file__).resolve().parents[2] / "data" / "processed" / "mv_month_brand_country.csv",
        Path(__file__).resolve().parents[1] / "data" / "processed" / "mv_month_brand_country.csv",
        Path.cwd() / "data" / "processed" / "mv_month_brand_country.csv",
    ]
    for p in candidates:
        if p.exists():
            return pd.read_csv(p)
    return pd.DataFrame()

@st.cache_data
def load_data() -> pd.DataFrame:
    """Charge le CSV fallback et applique la préparation standard."""
    df = _read_csv_robuste()
    if df.empty:
        st.error("CSV fallback introuvable : data/processed/mv_month_brand_country.csv")
        return pd.DataFrame()

    df = df.copy()
    df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
    for col in ["ca", "unites", "aov", "marge_pct_avg", "ca_online", "ca_offline"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = df["month_key"].dt.year
    df["month"] = df["month_key"].dt.month
    df["quarter"] = df["month_key"].dt.quarter
    df = df.sort_values("month_key")
    return df

# =========================
# UI & utils
# =========================

def sidebar_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Filtres communs (années / marques / pays / période)."""
    with st.sidebar:
        st.markdown("### Filtres")
        years = sorted(df["year"].dropna().unique().tolist())
        marques = sorted(df["marque_key"].dropna().unique().tolist()) if "marque_key" in df.columns else []
        pays = sorted(df["pays_key"].dropna().unique().tolist()) if "pays_key" in df.columns else []

        sel_years = st.multiselect("Années", years, default=years)
        sel_marques = st.multiselect("Marques", marques, default=marques) if marques else []
        sel_pays = st.multiselect("Pays", pays, default=pays) if pays else []

        min_dt = pd.to_datetime(df["month_key"].min())
        max_dt = pd.to_datetime(df["month_key"].max())
        period = st.date_input("Période", value=(min_dt, max_dt), min_value=min_dt, max_value=max_dt)

        if isinstance(period, tuple) and len(period) == 2:
            from_dt, to_dt = pd.to_datetime(period[0]), pd.to_datetime(period[1])
        else:
            from_dt, to_dt = min_dt, max_dt

    mask = (df["month_key"].between(from_dt, to_dt)) & (df["year"].isin(sel_years))
    if sel_marques:
        mask &= df["marque_key"].isin(sel_marques)
    if sel_pays:
        mask &= df["pays_key"].isin(sel_pays)

    return df.loc[mask].copy(), {
        "years": sel_years, "marques": sel_marques, "pays": sel_pays,
        "from": from_dt, "to": to_dt
    }

def safe_metric_number(v):
    if v is None or pd.isna(v):
        return "-"
    v = float(v)
    if v >= 1_000_000_000: return f"{v/1_000_000_000:.1f}B"
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000: return f"{v/1_000:.0f}k"
    return f"{v:,.0f}"

def yoy(last, prev):
    if prev and prev != 0 and not pd.isna(prev):
        return (last / prev - 1) * 100
    return None

def ytd(df: pd.DataFrame, value_col="ca") -> Dict[str, float | None]:
    """Retourne YTD courant vs N-1 sur même borne mois."""
    if df.empty:
        return {"ytd": None, "ytd_prev": None, "ytd_yoy": None}
    max_month_cur = df["month_key"].max().month
    cur_year = df["year"].max()
    ytd_cur = df[(df["year"] == cur_year) & (df["month_key"].dt.month <= max_month_cur)][value_col].sum()
    ytd_prev = df[(df["year"] == cur_year - 1) & (df["month_key"].dt.month <= max_month_cur)][value_col].sum()
    return {"ytd": ytd_cur, "ytd_prev": ytd_prev, "ytd_yoy": yoy(ytd_cur, ytd_prev)}
