import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters, safe_metric_number, yoy

st.title("Marques — Benchmark")

df = load_data()
if df.empty:
    st.stop()

dff, meta = sidebar_filters(df)

# Classement global
rank = dff.groupby("marque_key", as_index=False).agg(ca=("ca","sum"), unites=("unites","sum"))
total_ca = rank["ca"].sum()
rank["part_%"] = (rank["ca"] / total_ca * 100).round(1) if total_ca else 0
rank = rank.sort_values("ca", ascending=False)

st.subheader("Classement par CA")
st.dataframe(rank.head(20), use_container_width=True)

fig = px.bar(rank.head(15), x="marque_key", y="ca",
             labels={"marque_key":"Marque (clé)","ca":"CA (EUR)"})
st.plotly_chart(fig, use_container_width=True)

# YoY par marque (dernière année vs N-1)
st.subheader("YoY par marque (dernière année)")
last_year = int(dff["year"].max())
prev_year = last_year - 1

yoy_df = []
for mk, g in dff.groupby("marque_key"):
    ca_last = g.loc[g["year"] == last_year, "ca"].sum()
    ca_prev = g.loc[g["year"] == prev_year, "ca"].sum()
    y = yoy(ca_last, ca_prev)
    yoy_df.append({"marque_key": mk, "yoy_%": y})

yoy_df = pd.DataFrame(yoy_df).dropna().sort_values("yoy_%", ascending=False)
fig2 = px.bar(yoy_df.head(15), x="marque_key", y="yoy_%",
              labels={"marque_key":"Marque (clé)","yoy_%":"YoY %"})
st.plotly_chart(fig2, use_container_width=True)

# Comparateur 2 marques
st.subheader("Comparateur 2 marques (série CA)")
mk_all = sorted(dff["marque_key"].unique().tolist())
colA, colB = st.columns(2)
m1 = colA.selectbox("Marque A", mk_all, index=0)
m2 = colB.selectbox("Marque B", mk_all, index=1 if len(mk_all)>1 else 0)

ts = dff.groupby(["month_key","marque_key"], as_index=False)["ca"].sum()
ts_m = ts[ts["marque_key"].isin([m1,m2])]
fig3 = px.line(ts_m, x="month_key", y="ca", color="marque_key",
               labels={"month_key":"Mois","ca":"CA (EUR)","marque_key":"Marque"})
st.plotly_chart(fig3, use_container_width=True)
