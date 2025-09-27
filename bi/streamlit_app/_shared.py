import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from typing import Tuple, Dict, Any, List

# =============== Chargement & préparation ===============

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

    # conversions & colonnes calculées
    df = df.copy()
    df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
    for col in ["ca", "unites", "aov", "marge_pct_avg", "ca_online", "ca_offline"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = df["month_key"].dt.year
    df["month"] = df["month_key"].dt.month
    df["ym"] = df["month_key"].dt.to_period("M").astype(str)
    df["quarter"] = df["month_key"].dt.quarter
    df = df.sort_values("month_key")
    return df

# =============== UI & utilitaires ===============

def sidebar_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Filtre latéral commun : années / marques / pays / période."""
    with st.sidebar:
        st.markdown("### Filtres")
        years = sorted(df["year"].dropna().unique().tolist())
        marques = sorted(df["marque_key"].dropna().unique().tolist()) if "marque_key" in df.columns else []
        pays = sorted(df["pays_key"].dropna().unique().tolist()) if "pays_key" in df.columns else []

        sel_years = st.multiselect("Années", years, default=years)
        sel_marques = st.multiselect("Marques (clé)", marques, default=marques) if marques else []
        sel_pays = st.multiselect("Pays (clé)", pays, default=pays) if pays else []

        min_dt = df["month_key"].min()
        max_dt = df["month_key"].max()
        from_dt, to_dt = st.slider(
            "Période",
            value=(min_dt, max_dt),
            min_value=min_dt, max_value=max_dt, format="YYYY-MM"
        )

    mask = (df["month_key"].between(from_dt, to_dt)) & (df["year"].isin(sel_years))
    if sel_marques:
        mask &= df["marque_key"].isin(sel_marques)
    if sel_pays:
        mask &= df["pays_key"].isin(sel_pays)

    dff = df.loc[mask].copy()
    meta = {"years": sel_years, "marques": sel_marques, "pays": sel_pays, "from": from_dt, "to": to_dt}
    return dff, meta

def safe_metric_number(value):
    if value is None or pd.isna(value):
        return "-"
    try:
        v = float(value)
    except Exception:
        return "-"
    if v >= 1_000_000_000:
        return f"{v/1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}k"
    return f"{v:,.0f}"

def yoy(last: float, prev: float) -> float | None:
    if prev and prev != 0 and not pd.isna(prev):
        return (last / prev - 1) * 100
    return None

def ytd(df_m: pd.DataFrame, year_col="year", date_col="month_key", value_col="ca") -> Dict[str, float | None]:
    """Retourne YTD courant vs YTD N-1 sur même borne mois."""
    if df_m.empty:
        return {"ytd": None, "ytd_prev": None, "ytd_yoy": None}
    max_month_cur = df_m[date_col].max().month
    cur_year = df_m[year_col].max()
    ytd_cur = df_m[(df_m[year_col] == cur_year) & (df_m[date_col].dt.month <= max_month_cur)][value_col].sum()
    ytd_prev = df_m[(df_m[year_col] == cur_year - 1) & (df_m[date_col].dt.month <= max_month_cur)][value_col].sum()
    return {"ytd": ytd_cur, "ytd_prev": ytd_prev, "ytd_yoy": yoy(ytd_cur, ytd_prev)}

def percent(n, d):
    if d and d != 0 and not pd.isna(d):
        return n / d * 100
    return None
