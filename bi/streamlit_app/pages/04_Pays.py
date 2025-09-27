import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters, yoy

st.title("Pays — Performance")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

rank=dff.groupby("pays_key",as_index=False)["ca"].sum().sort_values("ca",ascending=False)
st.subheader("Classement pays")
st.dataframe(rank.head(20))
st.plotly_chart(px.bar(rank.head(15),x="pays_key",y="ca"),use_container_width=True)

last, prev = dff["year"].max(), dff["year"].max()-1
yoy_df=[]
for pk,g in dff.groupby("pays_key"):
    ca_last,ca_prev=g.loc[g["year"]==last,"ca"].sum(), g.loc[g["year"]==prev,"ca"].sum()
    y=yoy(ca_last,ca_prev)
    if y is not None: yoy_df.append({"pays_key":pk,"yoy%":y})
yoy_df=pd.DataFrame(yoy_df).sort_values("yoy%",ascending=False)
st.subheader("YoY par pays")
st.plotly_chart(px.bar(yoy_df,x="pays_key",y="yoy%"),use_container_width=True)

focus=st.selectbox("Pays focus",sorted(dff["pays_key"].unique()))
ts=dff[dff["pays_key"]==focus].groupby("month_key",as_index=False)["ca"].sum()
st.plotly_chart(px.line(ts,x="month_key",y="ca"),use_container_width=True)
