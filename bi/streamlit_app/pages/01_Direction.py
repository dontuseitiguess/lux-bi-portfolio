import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from _shared import load_data, sidebar_filters, safe_metric_number, yoy, ytd

st.title("Direction")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

brand_col = "marque" if "marque" in dff.columns else ("marque_key" if "marque_key" in dff.columns else None)
country_col = "pays" if "pays" in dff.columns else ("pays_key" if "pays_key" in dff.columns else None)

# KPI
ca_total = dff["ca"].sum() if "ca" in dff.columns else None
units_total = dff["unites"].sum() if "unites" in dff.columns else None
pays_actifs = dff[country_col].nunique() if country_col else None
marge_avg = dff["marge_pct_avg"].mean() if "marge_pct_avg" in dff.columns else None

last_year = dff["year"].max() if "year" in dff.columns else None
prev_year = last_year - 1 if last_year else None
ca_last = dff.loc[dff["year"] == last_year, "ca"].sum() if last_year else None
ca_prev = dff.loc[dff["year"] == prev_year, "ca"].sum() if prev_year else None
yoy_global = yoy(ca_last, ca_prev) if ca_last is not None and ca_prev is not None else None

ytd_info = ytd(dff)

c1, c2, c3, c4 = st.columns(4)
c1.metric("CA total", safe_metric_number(ca_total), f"{yoy_global:.1f}% YoY" if yoy_global else None)
c2.metric("Unités", safe_metric_number(units_total))
c3.metric("Pays actifs", safe_metric_number(pays_actifs))
c4.metric("Marge moyenne", f"{marge_avg:.1f}%" if marge_avg is not None else "-")

# Série mensuelle
st.subheader("Série mensuelle du CA")
if "month_key" in dff and "ca" in dff:
    ts = dff.groupby(pd.Grouper(key="month_key", freq="MS"))["ca"].sum().reset_index()
    ts["MA6"] = ts["ca"].rolling(6, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts["month_key"], y=ts["ca"], mode="lines", name="CA"))
    fig.add_trace(go.Scatter(x=ts["month_key"], y=ts["MA6"], mode="lines", name="MA(6)"))
    st.plotly_chart(fig, use_container_width=True)

# Saisonnalité
if "year" in dff and "month" in dff and "ca" in dff:
    st.subheader("Saisonnalité année × mois")
    season = dff.pivot_table(index="year", columns="month", values="ca", aggfunc="sum").fillna(0)
    st.plotly_chart(px.imshow(season, aspect="auto", labels=dict(x="Mois", y="Année", color="CA")),
                    use_container_width=True)

# Top listes (robuste même sans dims)
c8, c9 = st.columns(2)
if brand_col:
    c8.subheader("Top 5 marques")
    c8.dataframe(dff.groupby(brand_col)["ca"].sum().sort_values(ascending=False).head(5))
if country_col:
    c9.subheader("Top 5 pays")
    c9.dataframe(dff.groupby(country_col)["ca"].sum().sort_values(ascending=False).head(5))
