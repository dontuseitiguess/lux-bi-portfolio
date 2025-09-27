import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters, yoy

st.title("Marques — Benchmark")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

rank = dff.groupby("marque", as_index=False)["ca"].sum().sort_values("ca", ascending=False)
st.subheader("Classement marques")
st.dataframe(rank.head(20), use_container_width=True)
st.plotly_chart(px.bar(rank.head(15), x="marque", y="ca", labels={"marque":"Marque","ca":"CA (EUR)"}),
                use_container_width=True)

last, prev = dff["year"].max(), dff["year"].max()-1
yoy_df=[]
for mk,g in dff.groupby("marque"):
    ca_last, ca_prev = g.loc[g["year"]==last,"ca"].sum(), g.loc[g["year"]==prev,"ca"].sum()
    y=yoy(ca_last,ca_prev)
    if y is not None: yoy_df.append({"marque":mk,"yoy%":y})
yoy_df=pd.DataFrame(yoy_df).sort_values("yoy%",ascending=False)

st.subheader("YoY par marque")
st.plotly_chart(px.bar(yoy_df.head(15), x="marque", y="yoy%", labels={"marque":"Marque","yoy%":"YoY %"}),
                use_container_width=True)

# comparateur
mk_all=sorted(dff["marque"].unique())
m1=st.selectbox("Marque A",mk_all,0)
m2=st.selectbox("Marque B",mk_all,1 if len(mk_all)>1 else 0)
ts=dff.groupby(["month_key","marque"], as_index=False)["ca"].sum()
st.plotly_chart(px.line(ts[ts["marque"].isin([m1,m2])], x="month_key", y="ca", color="marque",
                        labels={"month_key":"Mois","ca":"CA (EUR)","marque":"Marque"}),
                use_container_width=True)
