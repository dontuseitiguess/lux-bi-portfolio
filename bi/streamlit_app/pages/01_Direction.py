import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, safe_metric_number

st.title("Direction")

df = load_data()
if df.empty:
    st.stop()

# dates
df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
df["year"] = df["month_key"].dt.year

# KPI
ca_total = df["ca"].sum()
units_total = df["unites"].sum()
pays_actifs = df["pays_key"].nunique()

c1, c2, c3 = st.columns(3)
c1.metric("CA total (EUR)", safe_metric_number(ca_total))
c2.metric("Unités vendues", safe_metric_number(units_total))
c3.metric("Pays actifs", safe_metric_number(pays_actifs))

# YoY
ymax = df["year"].max()
ymin = df["year"].min()
ca_cur = df.loc[df["year"] == ymax, "ca"].sum()
ca_prev = df.loc[df["year"] == ymax - 1, "ca"].sum()
yoy = (ca_cur / ca_prev - 1) * 100 if ca_prev else None
st.subheader("Croissance annuelle (YoY)")
st.success(f"YoY {ymax-1}→{ymax} : {yoy:.1f} %") if yoy is not None else st.info("YoY indisponible")

# CA par année
st.subheader("CA par année")
by_year = df.groupby("year", as_index=False)["ca"].sum()
fig = px.bar(by_year, x="year", y="ca", labels={"year": "Année", "ca": "CA (EUR)"})
st.plotly_chart(fig, use_container_width=True)

with st.expander("Notes & définitions"):
    st.markdown(
        "- **CA** : somme de la colonne `ca` (EUR).  \n"
        "- **Unités** : somme de `unites`.  \n"
        "- **Pays actifs** : nombre de valeurs distinctes de `pays_key`.  \n"
        "- **YoY** : croissance du CA entre N-1 et N, basée sur `month_key`."
    )
