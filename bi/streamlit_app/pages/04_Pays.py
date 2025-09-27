import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters, yoy

st.title("Pays — Performance")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

rank=dff.groupby("pays", as_index=False)["ca"].sum().sort_values("ca",ascending=False)
st.subheader("Classement pays")
st.dataframe(rank.head(20), use_container_width=True)
st.plotly_chart(px.bar(rank.head(15), x="pays", y="ca", labels={"pays":"Pays","ca":"CA (EUR)"}),
                use_container_width=True)

last, prev = dff["year"].max(), dff["year"].max()-1
yoy_df=[]
for pk,g in dff.groupby("pays"):
    ca_last,ca_prev=g.loc[g["year"]==last,"ca"].sum(), g.loc[g["year"]==prev,"ca"].sum()
    y=yoy(ca_last,ca_prev)
    if y is not None: yoy_df.append({"pays":pk,"yoy%":y})
yoy_df=pd.DataFrame(yoy_df).sort_values("yoy%",ascending=False)

st.subheader("YoY par pays")
st.plotly_chart(px.bar(yoy_df, x="pays", y="yoy%", labels={"pays":"Pays","yoy%":"YoY %"}),
                use_container_width=True)

focus=st.selectbox("Pays focus",sorted(dff["pays"].unique()))
ts=dff[dff["pays"]==focus].groupby("month_key",as_index=False)["ca"].sum()
st.plotly_chart(px.line(ts, x="month_key", y="ca", labels={"month_key":"Mois","ca":"CA (EUR)"}),
                use_container_width=True)
