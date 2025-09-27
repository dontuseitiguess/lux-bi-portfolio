# bi/streamlit_app/pages/02_Ecommerce.py
import streamlit as st
import pandas as pd
import plotly.express as px

from _shared import load_data, safe_metric_number

st.title("E-commerce")

# --- 1) Charger les données ---
df = load_data().copy()

# --- 2) Dates : année et mois (depuis month_key) ---
if "month_key" in df.columns:
    df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
    df["year"] = df["month_key"].dt.year
    df["month"] = df["month_key"].dt.to_period("M").astype(str)  # ex: 2024-03

# --- 3) Petite preuve de vie ---
with st.expander("Aperçu (5 premières lignes)"):
    st.dataframe(df.head())

# --- 4) Filtres ---
left, right = st.columns(2)
years = sorted(df["year"].dropna().unique()) if "year" in df.columns else []
year_sel = left.selectbox("Année", options=["Tous"] + list(years), index=0)

# (Optionnel) filtre pays si tu veux, laisse commenté si pas utile
# countries = ["Tous"] + sorted(df["pays_key"].dropna().unique().tolist()) if "pays_key" in df.columns else ["Tous"]
# country_sel = right.selectbox("Pays", options=countries, index=0)

# Appliquer les filtres
dff = df.copy()
if year_sel != "Tous" and "year" in dff.columns:
    dff = dff[dff["year"] == year_sel]
# if country_sel != "Tous" and "pays_key" in dff.columns:
#     dff = dff[dff["pays_key"] == country_sel]

# --- 5) KPIs E-commerce ---
# Sécurité : si colonnes manquantes, remets à 0
ca_on = float(dff["ca_online"].sum()) if "ca_online" in dff.columns else 0.0
ca_off = float(dff["ca_offline"].sum()) if "ca_offline" in dff.columns else 0.0
ca_total = ca_on + ca_off

# Panier moyen : priorité au calcul CA total / unités si 'unites' dispo, sinon moyenne 'aov'
if "unites" in dff.columns and dff["unites"].sum() > 0:
    aov_val = ca_total / float(dff["unites"].sum())
elif "aov" in dff.columns and len(dff) > 0:
    aov_val = float(dff["aov"].mean())
else:
    aov_val = None

digital_pct = (ca_on / ca_total * 100) if ca_total > 0 else None

k1, k2, k3, k4 = st.columns(4)
k1.metric("CA Online (EUR)", safe_metric_number(ca_on))
k2.metric("CA Offline (EUR)", safe_metric_number(ca_off))
k3.metric("Panier moyen (€)", f"{aov_val:,.0f}".replace(",", " ") if aov_val else "—")
k4.metric("% Digital", f"{digital_pct:.1f} %" if digital_pct is not None else "—")

# --- 6) Graphiques ---
st.subheader("Répartition Online vs Offline")

# A) Vue annuelle (si 'Tous') : barres empilées par année
if year_sel == "Tous" and "year" in dff.columns:
    grp = dff.groupby("year", as_index=False)[["ca_online", "ca_offline"]].sum()
    grp = grp.sort_values("year")
    grp_melt = grp.melt(id_vars="year", value_vars=["ca_online", "ca_offline"],
                        var_name="canal", value_name="ca")
    fig = px.bar(grp_melt, x="year", y="ca", color="canal", barmode="stack",
                 labels={"year": "Année", "ca": "CA (EUR)", "canal": "Canal"})
    st.plotly_chart(fig, use_container_width=True)

# B) Vue mensuelle (si une année sélectionnée) : barres empilées par mois
elif year_sel != "Tous" and "month" in dff.columns:
    grp = dff.groupby("month", as_index=False)[["ca_online", "ca_offline"]].sum()
    grp = grp.sort_values("month")
    grp_melt = grp.melt(id_vars="month", value_vars=["ca_online", "ca_offline"],
                        var_name="canal", value_name="ca")
    fig = px.bar(grp_melt, x="month", y="ca", color="canal", barmode="stack",
                 labels={"month": "Mois", "ca": "CA (EUR)", "canal": "Canal"})
    st.plotly_chart(fig, use_container_width=True)

# --- 7) Part du digital (donut) sur le filtre courant ---
st.subheader("Part du digital (période filtrée)")
donut_df = pd.DataFrame({
    "canal": ["Online", "Offline"],
    "ca": [ca_on, ca_off]
})
fig2 = px.pie(donut_df, names="canal", values="ca", hole=0.45)
st.plotly_chart(fig2, use_container_width=True)

# --- 8) Notes ---
with st.expander("Notes & définitions"):
    st.markdown(
        "- **CA Online/Offline** : colonnes `ca_online` et `ca_offline`.  \n"
        "- **Panier moyen (AOV)** : par défaut `CA total / unites` si `unites` est présent, sinon moyenne de `aov`.  \n"
        "- **% Digital** : `CA Online / (CA Online + CA Offline)` sur la période filtrée.  \n"
        "- Filtres : sélection d'année. Ajoute le filtre pays si besoin (voir code commenté)."
    )
