# bi/streamlit_app/pages/03_Marques.py
import streamlit as st
import pandas as pd
import plotly.express as px

from _shared import load_data, safe_metric_number

st.title("Marques")

# --- 1) Charger & préparer ---
df = load_data().copy()

# Dates
if "month_key" in df.columns:
    df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
    df["year"] = df["month_key"].dt.year

# --- 2) Mapping optionnel marque_key -> nom lisible ---
# ⚠️ adapte ce dict si tu as la vraie dimension "marque" ailleurs
MARQUE_MAP = {
    1: "Dior",
    2: "Hermès",
    3: "Gucci",
    4: "Louis Vuitton",
    # ajoute au besoin...
}
df["marque"] = df["marque_key"].map(MARQUE_MAP).fillna(df["marque_key"].astype(str))

# --- 3) Filtres ---
left, right = st.columns(2)
years = sorted(df["year"].dropna().unique()) if "year" in df.columns else []
year_sel = left.selectbox("Année", options=["Tous"] + list(years), index=0)

# auto-sélection : Top 4 marques par CA (période filtrée)
dff_base = df if year_sel == "Tous" else df[df["year"] == year_sel]
top4 = (
    dff_base.groupby("marque", as_index=False)["ca"].sum()
    .sort_values("ca", ascending=False)
    .head(4)["marque"]
    .tolist()
)
all_brands = sorted(df["marque"].unique().tolist())
brands_sel = right.multiselect("Marques", options=all_brands, default=top4)

# appliquer filtres
dff = dff_base[dff_base["marque"].isin(brands_sel)] if brands_sel else dff_base

# --- 4) KPI comparatifs (sur la période filtrée) ---
ca_total = dff["ca"].sum() if "ca" in dff.columns else 0.0
units_total = dff["unites"].sum() if "unites" in dff.columns else 0
margin_avg = dff["marge_pct_avg"].mean() if "marge_pct_avg" in dff.columns else None
share_online = (
    dff["ca_online"].sum() / ca_total * 100
    if "ca_online" in dff.columns and ca_total > 0 else None
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("CA total (EUR)", safe_metric_number(ca_total))
k2.metric("Unités vendues", safe_metric_number(units_total))
k3.metric("Marge moyenne (%)", f"{margin_avg:.1f}" if margin_avg is not None else "—")
k4.metric("Part Online (%)", f"{share_online:.1f}" if share_online is not None else "—")

# --- 5) Classement marques (tableau) ---
st.subheader("Classement par CA")
rank = (
    dff.groupby("marque", as_index=False)
    .agg(
        ca=("ca", "sum"),
        unites=("unites", "sum"),
        marge_pct_avg=("marge_pct_avg", "mean"),
        ca_online=("ca_online", "sum"),
        ca_offline=("ca_offline", "sum"),
    )
    .sort_values("ca", ascending=False)
)
rank["% Online"] = (rank["ca_online"] / rank["ca"] * 100).round(1).fillna(0)
rank_display = rank[["marque", "ca", "unites", "marge_pct_avg", "% Online"]]
rank_display = rank_display.rename(
    columns={"marque": "Marque", "ca": "CA (EUR)", "unites": "Unités", "marge_pct_avg": "Marge (%)"}
)
st.dataframe(rank_display, use_container_width=True)

# --- 6) Graphiques ---
# A) CA par marque (barres)
st.subheader("CA par marque")
fig1 = px.bar(
    rank, x="marque", y="ca",
    labels={"marque": "Marque", "ca": "CA (EUR)"},
)
st.plotly_chart(fig1, use_container_width=True)

# B) Répartition Online/Offline par marque (stacked)
if {"ca_online", "ca_offline"}.issubset(rank.columns):
    st.subheader("Mix Online / Offline par marque")
    mix = rank[["marque", "ca_online", "ca_offline"]].copy()
    mix_melt = mix.melt(id_vars="marque", var_name="Canal", value_name="CA")
    mix_melt["Canal"] = mix_melt["Canal"].map({"ca_online": "Online", "ca_offline": "Offline"})
    fig2 = px.bar(
        mix_melt, x="marque", y="CA", color="Canal", barmode="stack",
        labels={"marque": "Marque", "CA": "CA (EUR)"}
    )
    st.plotly_chart(fig2, use_container_width=True)

# C) Tendance par marque sélectionnée (mensuelle)
if year_sel != "Tous" and "month_key" in dff.columns:
    st.subheader(f"Tendance mensuelle {year_sel}")
    trend = (
        dff.groupby(["month_key", "marque"], as_index=False)["ca"].sum()
        .sort_values("month_key")
    )
    fig3 = px.line(
        trend, x="month_key", y="ca", color="marque",
        labels={"month_key": "Mois", "ca": "CA (EUR)", "marque": "Marque"}
    )
    st.plotly_chart(fig3, use_container_width=True)

# --- 7) Notes ---
with st.expander("Notes & définitions"):
    st.markdown(
        "- **Marque** : dérivée de `marque_key` via un mapping local (à adapter si tu as une dimension).  \n"
        "- **Classement** : somme `ca` sur la période et le filtre courant.  \n"
        "- **Marge moyenne** : moyenne de `marge_pct_avg` (pondération simple).  \n"
        "- **% Online** : `ca_online / ca * 100`.  \n"
        "- **Tendance** : courbe mensuelle si une année précise est sélectionnée."
    )
