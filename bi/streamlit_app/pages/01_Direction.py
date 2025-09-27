import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from _shared import load_data, sidebar_filters, safe_metric_number, yoy, ytd

st.title("Direction")

df = load_data()
if df.empty:
    st.stop()

dff, meta = sidebar_filters(df)

# Sécurité colonnes
required = {"month_key", "ca", "unites", "pays_key"}
if not required.issubset(dff.columns):
    st.error(f"Colonnes manquantes: {required - set(dff.columns)}")
    st.stop()

# KPI globaux
ca_total = dff["ca"].sum()
units_total = dff["unites"].sum()
pays_actifs = dff["pays_key"].nunique()
marge_avg = dff["marge_pct_avg"].mean() if "marge_pct_avg" in dff.columns else None

# YoY global (année pleine)
last_year = int(dff["year"].max())
prev_year = last_year - 1
ca_last = dff.loc[dff["year"] == last_year, "ca"].sum()
ca_prev = dff.loc[dff["year"] == prev_year, "ca"].sum()
yoy_global = yoy(ca_last, ca_prev)

# YTD
ytd_info = ytd(dff, value_col="ca")

c1, c2, c3, c4 = st.columns(4)
c1.metric("CA total (EUR)", safe_metric_number(ca_total), 
          delta=(f"{yoy_global:.1f}% YoY" if yoy_global is not None else None))
c2.metric("Unités vendues", safe_metric_number(units_total))
c3.metric("Pays actifs", safe_metric_number(pays_actifs))
c4.metric("Marge moyenne", f"{marge_avg:.1f} %" if marge_avg is not None else "-")

# YTD card
st.markdown("#### YTD vs YTD N-1")
c5, c6, c7 = st.columns(3)
c5.metric("YTD CA", safe_metric_number(ytd_info["ytd"]))
c6.metric("YTD N-1", safe_metric_number(ytd_info["ytd_prev"]))
c7.metric("YTD YoY", f"{ytd_info['ytd_yoy']:.1f} %" if ytd_info["ytd_yoy"] is not None else "-")

# Séries mensuelles (avec moyenne mobile)
st.subheader("Série mensuelle du CA")
ts = dff.groupby(pd.Grouper(key="month_key", freq="MS"))["ca"].sum().reset_index()
ts["MA6"] = ts["ca"].rolling(6, min_periods=1).mean()
fig_ts = go.Figure()
fig_ts.add_trace(go.Scatter(x=ts["month_key"], y=ts["ca"], mode="lines", name="CA"))
fig_ts.add_trace(go.Scatter(x=ts["month_key"], y=ts["MA6"], mode="lines", name="MA(6)"))
fig_ts.update_layout(xaxis_title="Mois", yaxis_title="CA (EUR)")
st.plotly_chart(fig_ts, use_container_width=True)

# CA par année + delta
st.subheader("CA par année (avec delta vs N-1)")
by_year = dff.groupby("year", as_index=False)["ca"].sum().sort_values("year")
by_year["delta"] = by_year["ca"].diff()
fig_y = px.bar(by_year, x="year", y="ca", text="delta",
               labels={"year":"Année","ca":"CA (EUR)"},
               title=None)
fig_y.update_traces(texttemplate="+%{text:,.0f}", selector=dict(type='bar'))
st.plotly_chart(fig_y, use_container_width=True)

# Heatmap saisonnalité (année x mois)
st.subheader("Saisonnalité (année × mois)")
season = dff.pivot_table(index="year", columns="month", values="ca", aggfunc="sum").fillna(0.0)
fig_h = px.imshow(season, aspect="auto", labels=dict(x="Mois", y="Année", color="CA (EUR)"),
                  x=[str(m) for m in season.columns], y=[str(y) for y in season.index])
st.plotly_chart(fig_h, use_container_width=True)

# Top listes
c8, c9 = st.columns(2)
top_brand = dff.groupby("marque_key", as_index=False)["ca"].sum().sort_values("ca", ascending=False).head(5)
top_country = dff.groupby("pays_key", as_index=False)["ca"].sum().sort_values("ca", ascending=False).head(5)

c8.subheader("Top 5 marques")
c8.dataframe(top_brand, use_container_width=True)
c9.subheader("Top 5 pays")
c9.dataframe(top_country, use_container_width=True)
