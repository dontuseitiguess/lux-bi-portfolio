import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# =========================
# Chargement & préparation
# =========================

@st.cache_data
def _read_csv_first(*rel_paths: str) -> pd.DataFrame:
    """Cherche le premier CSV existant parmi plusieurs chemins relatifs."""
    bases = [
        Path(__file__).resolve().parents[2],
        Path(__file__).resolve().parents[1],
        Path.cwd(),
    ]
    for base in bases:
        for rel in rel_paths:
            p = base / rel
            if p.exists():
                return pd.read_csv(p)
    return pd.DataFrame()

def _find_name_column(df_dim: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in df_dim.columns:
            return c
    # tente versions case-insensitive
    lower = {c.lower(): c for c in df_dim.columns}
    for c in candidates:
        if c in lower:
            return lower[c]
    return None

@st.cache_data
def _load_dimensions() -> dict:
    """Charge dim_marque et dim_pays et renvoie des maps clé->nom."""
    maps: dict = {"brand_map": None, "country_map": None}

    # --- Marques ---
    dim_brand = _read_csv_first("data/processed/dim_marque.csv", "data/raw/dim_marque.csv")
    if not dim_brand.empty:
        key_col = "marque_key" if "marque_key" in dim_brand.columns else None
        name_col = _find_name_column(dim_brand, ["marque", "brand", "brand_name", "name", "label"])
        if key_col and name_col:
            maps["brand_map"] = dict(zip(dim_brand[key_col], dim_brand[name_col]))

    # --- Pays ---
    dim_country = _read_csv_first("data/processed/dim_pays.csv", "data/raw/dim_pays.csv")
    if not dim_country.empty:
        key_col = "pays_key" if "pays_key" in dim_country.columns else None
        name_col = _find_name_column(dim_country, ["pays", "country", "country_name", "name", "label"])
        if key_col and name_col:
            maps["country_map"] = dict(zip(dim_country[key_col], dim_country[name_col]))

    return maps

@st.cache_data
def load_data() -> pd.DataFrame:
    """Charge le fact + enrichit avec noms de marques/pays si disponibles."""
    fact = _read_csv_first("data/processed/mv_month_brand_country.csv")
    if fact.empty:
        st.error("CSV fallback introuvable : data/processed/mv_month_brand_country.csv")
        return pd.DataFrame()

    df = fact.copy()
    # types de base
    df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
    for col in ["ca", "unites", "aov", "marge_pct_avg", "ca_online", "ca_offline"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = df["month_key"].dt.year
    df["month"] = df["month_key"].dt.month
    df["quarter"] = df["month_key"].dt.quarter
    df = df.sort_values("month_key")

    # enrichissement avec dimensions
    maps = _load_dimensions()
    if "marque_key" in df.columns and maps.get("brand_map"):
        df["marque"] = df["marque_key"].map(maps["brand_map"]).fillna(df["marque_key"].astype(str))
    elif "marque_key" in df.columns:
        df["marque"] = df["marque_key"].astype(str)

    if "pays_key" in df.columns and maps.get("country_map"):
        df["pays"] = df["pays_key"].map(maps["country_map"]).fillna(df["pays_key"].astype(str))
    elif "pays_key" in df.columns:
        df["pays"] = df["pays_key"].astype(str)

    return df

# =========================
# UI & utils
# =========================

def sidebar_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Filtres communs (années / marques / pays / période) — robustes."""
    with st.sidebar:
        st.markdown("### Filtres")

        years = sorted(df["year"].dropna().unique().tolist())
        marques = sorted(df["marque"].dropna().unique().tolist()) if "marque" in df.columns else []
        pays = sorted(df["pays"].dropna().unique().tolist()) if "pays" in df.columns else []

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
        mask &= df["marque"].isin(sel_marques)
    if sel_pays:
        mask &= df["pays"].isin(sel_pays)

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
    if df.empty:
        return {"ytd": None, "ytd_prev": None, "ytd_yoy": None}
    max_month_cur = df["month_key"].max().month
    cur_year = df["year"].max()
    ytd_cur = df[(df["year"] == cur_year) & (df["month_key"].dt.month <= max_month_cur)][value_col].sum()
    ytd_prev = df[(df["year"] == cur_year - 1) & (df["month_key"].dt.month <= max_month_cur)][value_col].sum()
    return {"ytd": ytd_cur, "ytd_prev": ytd_prev, "ytd_yoy": yoy(ytd_cur, ytd_prev)}
