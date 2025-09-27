import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data

st.title("Pays")

df = load_data()
if df.empty:
    st.stop()

# Classement par CA (par pays_key)
rank = df.groupby("pays_key", as_index=False).agg(ca=("ca", "sum"), unites=("unites", "sum"))
rank = rank.sort_values("ca", ascending=False)

st.subheader("Classement par CA (pays)")
fig = px.bar(rank.head(10), x="pays_key", y="ca", labels={"pays_key": "Pays (clé)", "ca": "CA (EUR)"})
st.plotly_chart(fig, use_container_width=True)

with st.expander("Données (top 20)"):
    st.dataframe(rank.head(20))
