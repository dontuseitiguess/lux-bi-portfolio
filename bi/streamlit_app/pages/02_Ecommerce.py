import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters, safe_metric_number, yoy

st.title("Ecommerce (Digital vs Retail)")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

if not {"ca_online","ca_offline"}.issubset(dff.columns):
    st.warning("Pas de colonnes online/offline")
    st.stop()

tot_on, tot_off = dff["ca_online"].sum(), dff["ca_offline"].sum()
share_on = tot_on/(tot_on+tot_off)*100 if (tot_on+tot_off) else None

last, prev = dff["year"].max(), dff["year"].max()-1
on_yoy = yoy(dff.loc[dff["year"]==last,"ca_online"].sum(),
             dff.loc[dff["year"]==prev,"ca_online"].sum())
off_yoy = yoy(dff.loc[dff["year"]==last,"ca_offline"].sum(),
              dff.loc[dff["year"]==prev,"ca_offline"].sum())

c1,c2,c3 = st.columns(3)
c1.metric("CA online", safe_metric_number(tot_on), f"{on_yoy:.1f}%" if on_yoy else None)
c2.metric("CA offline", safe_metric_number(tot_off), f"{off_yoy:.1f}%" if off_yoy else None)
c3.metric("Part online", f"{share_on:.1f}%" if share_on else "-")

st.subheader("Séries mensuelles (stacked)")
ts = dff.groupby(pd.Grouper(key="month_key",freq="MS"))[["ca_online","ca_offline"]].sum().reset_index()
long = ts.melt(id_vars="month_key", var_name="canal", value_name="ca")
fig = px.area(long, x="month_key", y="ca", color="canal",
              labels={"month_key":"Mois","ca":"CA (EUR)","canal":"Canal"})
st.plotly_chart(fig, use_container_width=True)
st.caption("👉 Volume mensuel par canal, cumulatif pour percevoir la dynamique relative.")
