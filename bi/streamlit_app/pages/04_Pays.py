# bi/streamlit_app/pages/04_Pays.py
import streamlit as st
import pandas as pd
import plotly.express as px

from _shared import load_data, safe_metric_number

st.title("Pays")

# --- 1) Charger & préparer ---
df = load_data().copy()

# Dates -> année & mois
if "month_key" in df.columns:
    df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
    df["year"] = df["month_key"].dt.year
    df["month"] = df["month_key"].dt.to_period("M").astype(str)

# --- 2) Mapping optionnel pays_key -> nom lisible ---
# ⚠️ Adapte ce dict selon ta dimension pays (si tu en as une, remplace par un merge).
PAYS_MAP = {
    1: "France",
    2: "États-Unis",
    3: "Royaume-Uni",
    4: "Chine",
    5: "Japon",
    6: "Allemagne",
    7: "Italie",
    8: "Émirats",
    # ...
}
if "pays_key" in df.columns:
    df["pays"] = df["pays_key"].map(PAYS_MAP).fillna(df["pays_key"].astype(str))
else:
    df["pays"] = "N/A"

# --- 3) Filtres ---
left, right = st.columns(2)
years = sorted(df["year"].dropna().unique()) if "year" in df.columns else []
year_sel = left.selectbox("Année", options=["Tous"] + list(years), index=0)

# Calculer base filtrée
dff = df if year_sel == "Tous" else df[df["year"] == year_sel]

# Liste des pays (tri par CA)
top_countries = (
    dff.groupby("pays", as_index=False)["ca"].sum()
    .sort_values("ca", ascending=False)["pays"]
    .tolist()
)
default_selection = top_countries[:1] if top_countries else []
country_sel = right.multiselect("Focus pays (optionnel)", options=top_countries, default=default_selection)

# --- 4) KPIs globaux ---
ca_total = float(dff["ca"].sum()) if "ca" in dff.columns else 0.0
nb_pays = dff["pays"].nunique()
top_row = (
    dff.groupby("pays", as_index=False)["ca"].sum().sort_values("ca", ascending=False).head(1)
    if ca_total > 0 else pd.DataFrame(columns=["pays", "ca"])
)
top_label = f"{top_row.iloc[0]['pays']} ({safe_metric_number(top_row.iloc[0]['ca'])})" if len(top_row) else "—"

c1, c2, c3 = st.columns(3)
c1.metric("CA total (EUR)", safe_metric_number(ca_total))
c2.metric("Pays actifs", str(nb_pays))
c3.metric("Top pays (CA)", top_label)

# --- 5) Classement par CA ---
st.subheader("Classement par CA")

# Colonnes cibles + fonction d'agg et libellé lisible
rank_cols = {
    "ca": ("CA (EUR)", "sum"),
    "unites": ("Unités", "sum"),
    "marge_pct_avg": ("Marge (%)", "mean"),
    "ca_online": ("CA Online", "sum"),
    "ca_offline": ("CA Offline", "sum"),
}

present_cols = [c for c in rank_cols if c in dff.columns]

# Cast en numérique (sécurisé) pour éviter les plantages d'agg
for c in present_cols:
    dff[c] = pd.to_numeric(dff[c], errors="coerce")

agg_dict = {c: rank_cols[c][1] for c in present_cols}

if not agg_dict:
    st.info("Colonnes d'agrégation absentes (aucune parmi ca, unites, marge_pct_avg, ca_online, ca_offline).")
else:
    rank = dff.groupby("pays", as_index=False).agg(agg_dict)

    if "ca" in rank.columns:
        rank = rank.sort_values("ca", ascending=False)

    rank_display = rank.copy()
    if {"ca_online", "ca"}.issubset(rank_display.columns):
        rank_display["% Online"] = (rank_display["ca_online"] / rank_display["ca"] * 100).round(1)

    rename_map = {"pays": "Pays"}
    rename_map.update({c: rank_cols[c][0] for c in present_cols})
    rank_display = rank_display.rename(columns=rename_map)

    prefer = ["Pays", "CA (EUR)", "Unités", "Marge (%)", "CA Online", "CA Offline", "% Online"]
    order = [c for c in prefer if c in rank_display.columns]
    st.dataframe(rank_display[order], use_container_width=True)

# --- 6) Graphique Top 10 pays (CA) ---
st.subheader("Top 10 pays par CA")
top10 = rank.head(10) if not rank.empty else rank
fig1 = px.bar(
    top10.sort_values("ca", ascending=True),
    x="ca", y="pays", orientation="h",
    labels={"pays": "Pays", "ca": "CA (EUR)"},
)
st.plotly_chart(fig1, use_container_width=True)

# --- 7) Croissance YoY par pays (si une année sélectionnée) ---
if year_sel != "Tous" and "year" in df.columns:
    st.subheader(f"Croissance YoY par pays ( {year_sel-1} → {year_sel} )")

    prev = df[df["year"] == (year_sel - 1)]
    cur = df[df["year"] == year_sel]

    ca_prev = prev.groupby("pays", as_index=False)["ca"].sum().rename(columns={"ca": "ca_prev"})
    ca_cur = cur.groupby("pays", as_index=False)["ca"].sum().rename(columns={"ca": "ca_cur"})
    yoy = pd.merge(ca_cur, ca_prev, on="pays", how="left")
    yoy["YoY %"] = ((yoy["ca_cur"] / yoy["ca_prev"] - 1) * 100).replace([pd.NA, pd.NaT], None)
    yoy = yoy.sort_values("YoY %", ascending=False)

    st.dataframe(yoy[["pays", "ca_prev", "ca_cur", "YoY %"]], use_container_width=True)
    fig2 = px.bar(
        yoy.dropna(subset=["YoY %"]).head(15),
        x="pays", y="YoY %",
        labels={"pays": "Pays", "YoY %": "Croissance %"},
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- 8) Tendance mensuelle (si un pays est sélectionné) ---
if country_sel:
    for p in country_sel:
        st.subheader(f"Tendance mensuelle — {p}")
        tf = dff[dff["pays"] == p]
        trend = tf.groupby("month", as_index=False)["ca"].sum().sort_values("month")
        if not trend.empty:
            fig3 = px.line(trend, x="month", y="ca", labels={"month": "Mois", "ca": "CA (EUR)"})
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Pas de données pour ce pays dans le filtre courant.")

# --- 9) Notes ---
with st.expander("Notes & définitions"):
    st.markdown(
        "- **Pays** : dérivé de `pays_key` via un mapping local (à remplacer par une vraie dimension si dispo).  \n"
        "- **Classement** : agrégation sur la période filtrée (CA, Unités, etc.).  \n"
        "- **Top pays** : premier pays par CA sur la période filtrée.  \n"
        "- **YoY par pays** : comparaison entre l'année sélectionnée et l'année N-1.  \n"
        "- **Tendance** : courbe mensuelle du CA pour les pays sélectionnés."
    )
