import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, safe_metric_number

st.title("Marques")

df = load_data()
if df.empty:
    st.stop()

# Classement par CA (par marque_key)
top = df.groupby("marque_key", as_index=False).agg(ca=("ca", "sum"), unites=("unites", "sum"))
top = top.sort_values("ca", ascending=False)

st.subheader("Top marques par CA")
fig = px.bar(top.head(10), x="marque_key", y="ca", labels={"marque_key": "Marque (clé)", "ca": "CA (EUR)"})
st.plotly_chart(fig, use_container_width=True)

with st.expander("Données (top 20)"):
    st.dataframe(top.head(20))
