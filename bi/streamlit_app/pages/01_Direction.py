import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from _shared import load_data, sidebar_filters, safe_metric_number, yoy, ytd

st.title("Direction")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

# KPI globaux
ca_total = dff["ca"].sum()
units_total = dff["unites"].sum()
pays_actifs = dff["pays"].nunique() if "pays" in dff.columns else dff["pays_key"].nunique()
marge_avg = dff["marge_pct_avg"].mean() if "marge_pct_avg" in dff.columns else None

last_year, prev_year = dff["year"].max(), dff["year"].max()-1
ca_last = dff.loc[dff["year"]==last_year,"ca"].sum()
ca_prev = dff.loc[dff["year"]==prev_year,"ca"].sum()
yoy_global = yoy(ca_last, ca_prev)

ytd_info = ytd(dff)

c1, c2, c3, c4 = st.columns(4)
c1.metric("CA total", safe_metric_number(ca_total), f"{yoy_global:.1f}% YoY" if yoy_global else None)
c2.metric("Unités", safe_metric_number(units_total))
c3.metric("Pays actifs", safe_metric_number(pays_actifs))
c4.metric("Marge moyenne", f"{marge_avg:.1f}%" if marge_avg is not None else "-")

# YTD
st.subheader("YTD vs N-1")
c5, c6, c7 = st.columns(3)
c5.metric("YTD CA", safe_metric_number(ytd_info["ytd"]))
c6.metric("YTD N-1", safe_metric_number(ytd_info["ytd_prev"]))
c7.metric("YTD YoY", f"{ytd_info['ytd_yoy']:.1f}%" if ytd_info["ytd_yoy"] else "-")

# Série mensuelle
st.subheader("Série mensuelle du CA")
ts = dff.groupby(pd.Grouper(key="month_key", freq="MS"))["ca"].sum().reset_index()
ts["MA6"] = ts["ca"].rolling(6, min_periods=1).mean()
fig = go.Figure()
fig.add_trace(go.Scatter(x=ts["month_key"], y=ts["ca"], mode="lines", name="CA"))
fig.add_trace(go.Scatter(x=ts["month_key"], y=ts["MA6"], mode="lines", name="MA(6)"))
st.plotly_chart(fig, use_container_width=True)

# Heatmap saisonnalité
st.subheader("Saisonnalité année × mois")
season = dff.pivot_table(index="year", columns="month", values="ca", aggfunc="sum").fillna(0)
fig_h = px.imshow(season, aspect="auto", labels=dict(x="Mois", y="Année", color="CA"))
st.plotly_chart(fig_h, use_container_width=True)

# Top listes avec noms
c8, c9 = st.columns(2)
c8.subheader("Top 5 marques")
c8.dataframe(dff.groupby("marque")["ca"].sum().sort_values(ascending=False).head(5))
c9.subheader("Top 5 pays")
c9.dataframe(dff.groupby("pays")["ca"].sum().sort_values(ascending=False).head(5))
