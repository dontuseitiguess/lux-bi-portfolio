import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters, yoy

st.title("Pays — Performance marchés")

df = load_data()
if df.empty:
    st.stop()

dff, meta = sidebar_filters(df)

# Classement global par CA
rank = dff.groupby("pays_key", as_index=False).agg(ca=("ca","sum"), unites=("unites","sum"))
rank = rank.sort_values("ca", ascending=False)

st.subheader("Top marchés par CA")
st.dataframe(rank.head(20), use_container_width=True)
fig = px.bar(rank.head(15), x="pays_key", y="ca",
             labels={"pays_key":"Pays (clé)","ca":"CA (EUR)"})
st.plotly_chart(fig, use_container_width=True)

# YoY par pays
st.subheader("YoY par pays (dernière année)")
last_year = int(dff["year"].max())
prev_year = last_year - 1

yoy_df = []
for pk, g in dff.groupby("pays_key"):
    ca_last = g.loc[g["year"] == last_year, "ca"].sum()
    ca_prev = g.loc[g["year"] == prev_year, "ca"].sum()
    y = yoy(ca_last, ca_prev)
    yoy_df.append({"pays_key": pk, "yoy_%": y})

yoy_df = pd.DataFrame(yoy_df).dropna().sort_values("yoy_%", ascending=False)
fig2 = px.bar(yoy_df, x="pays_key", y="yoy_%",
              labels={"pays_key":"Pays (clé)","yoy_%":"YoY %"})
st.plotly_chart(fig2, use_container_width=True)

# Focus pays
st.subheader("Focus pays (série CA)")
p_all = sorted(dff["pays_key"].unique().tolist())
p_sel = st.selectbox("Pays (clé)", p_all, index=0)
ts = dff[dff["pays_key"] == p_sel].groupby("month_key", as_index=False)["ca"].sum()
fig3 = px.line(ts, x="month_key", y="ca", labels={"month_key":"Mois","ca":"CA (EUR)"})
st.plotly_chart(fig3, use_container_width=True)
