import os
import pandas as pd
import streamlit as st

# Page config (no markdown components)
st.set_page_config(page_title="Luxe BI - Home", layout="wide", initial_sidebar_state="expanded")

# ---------------- helpers
def _secrets():
    try:
        return dict(st.secrets)
    except Exception:
        return {}
SECRETS = _secrets()

def get_cfg(key: str, default=None):
    return SECRETS.get(key, os.getenv(key, default))

# ---------------- loaders
def load_from_postgres(query: str) -> pd.DataFrame:
    db_url = get_cfg("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL not set")
    from sqlalchemy import create_engine
    eng = create_engine(db_url, pool_pre_ping=True)
    df = pd.read_sql(query, eng)
    df = df.rename(columns={"month_key": "month", "ca": "ca_total", "marge_pct_avg": "marge_pct"})
    df["__source__"] = "postgres"
    return df

def load_from_csv(path_mv: str) -> pd.DataFrame:
    if not os.path.exists(path_mv):
        raise FileNotFoundError(f"CSV not found: {path_mv}")
    mv = pd.read_csv(path_mv)

    dm_path = get_cfg("CSV_DIM_MARQUE_PATH", "data/processed/dim_marque.csv")
    dp_path = get_cfg("CSV_DIM_PAYS_PATH",   "data/processed/dim_pays.csv")

    dm = pd.read_csv(dm_path)  # marque_key, marque
    dp = pd.read_csv(dp_path)  # pays_key, pays

    if "marque_key" in mv.columns:
        mv = mv.merge(dm, on="marque_key", how="left")
    if "pays_key" in mv.columns:
        mv = mv.merge(dp, on="pays_key",   how="left")

    mv = mv.rename(columns={"month_key": "month", "ca": "ca_total", "marge_pct_avg": "marge_pct"})
    keep = ["month","marque","pays","ca_total","unites","aov","marge_pct","ca_online","ca_offline"]
    mv = mv[[c for c in keep if c in mv.columns]].copy()
    mv["__source__"] = "csv"
    return mv

@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    query = "SELECT * FROM mv_month_brand_country"
    csv_path = get_cfg("CSV_FALLBACK_PATH", "data/processed/mv_month_brand_country.csv")
    db_url = get_cfg("DB_URL")
    if db_url:
        try:
            return load_from_postgres(query)
        except Exception:
            pass
    return load_from_csv(csv_path)

# ---------------- data
st.text("Digitalisation du Luxe - BI Dashboard")
df = load_data()

# dates
date_cols = [c for c in df.columns if c.lower() in ("mois","month","period","date")]
if not date_cols:
    st.text("Missing date column (expected: mois/month/period/date).")
    st.dataframe(df.head(20))
    st.stop()
DATE_COL = date_cols[0]
df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
df = df.dropna(subset=[DATE_COL])

# columns
BRAND_COL = "marque" if "marque" in df.columns else None
COUNTRY_COL = "pays"   if "pays"   in df.columns else None
CA_COL     = "ca_total" if "ca_total" in df.columns else None
UNITS_COL  = "unites"   if "unites" in df.columns else None
MARGIN_COL = "marge_pct" if "marge_pct" in df.columns else None

if any(x is None for x in [BRAND_COL, COUNTRY_COL, CA_COL]):
    st.text("Required columns missing: [date, marque, pays, ca_total].")
    st.dataframe(df.head(20))
    st.stop()

# ---------------- filters (labels are plain strings)
st.sidebar.text("Filtres")
min_date, max_date = df[DATE_COL].min(), df[DATE_COL].max()
date_range = st.sidebar.slider(
    "Periode",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
)
brand_opts = sorted(df[BRAND_COL].dropna().unique().tolist())
country_opts = sorted(df[COUNTRY_COL].dropna().unique().tolist())
sel_brands = st.sidebar.multiselect("Marques", brand_opts, default=brand_opts[:5])
sel_countries = st.sidebar.multiselect("Pays", country_opts, default=country_opts[:10])

mask = df[DATE_COL].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))
if sel_brands:
    mask &= df[BRAND_COL].isin(sel_brands)
if sel_countries:
    mask &= df[COUNTRY_COL].isin(sel_countries)
dff = df.loc[mask].copy()

# ---------------- KPIs (numbers only, no currency sign)
total_ca = int(dff[CA_COL].sum()) if CA_COL in dff else 0
total_units = int(dff[UNITS_COL].sum()) if UNITS_COL and UNITS_COL in dff else 0
aov = int(total_ca / total_units) if total_units > 0 else 0
src = dff["__source__"].iloc[0].upper() if "__source__" in dff.columns and len(dff) else "NA"

k1, k2, k3, k4 = st.columns(4)
k1.metric("CA total", f"{total_ca:,}".replace(",", " "))
k2.metric("Unites", f"{total_units:,}".replace(",", " "))
k3.metric("AOV", f"{aov:,}".replace(",", " "))
k4.metric("Source", src)

# ---------------- charts + table
st.text("Evolution mensuelle du CA")
ts = dff.groupby(DATE_COL)[CA_COL].sum().sort_index().reset_index()
st.line_chart(ts.set_index(DATE_COL))

st.text("Top marques (CA)")
top_brands = dff.groupby(BRAND_COL)[CA_COL].sum().sort_values(ascending=False).head(10).reset_index()
st.bar_chart(top_brands.set_index(BRAND_COL))

st.text("Apercu des donnees filtrees (top 50)")
st.dataframe(dff.head(50))

# Optional: download filtered data (safe, plain label)
csv_bytes = dff.to_csv(index=False).encode("utf-8")
st.download_button("Telecharger CSV (filtres appliques)", data=csv_bytes, file_name="lux_bi_filtered.csv", mime="text/csv")
