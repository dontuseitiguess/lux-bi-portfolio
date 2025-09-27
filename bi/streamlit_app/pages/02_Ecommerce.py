import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from _shared import load_data, sidebar_filters, safe_metric_number, yoy

st.title("Ecommerce (Digital vs Retail)")

df = load_data()
if df.empty:
    st.stop()

dff, meta = sidebar_filters(df)
if not {"ca_online", "ca_offline"}.issubset(dff.columns):
    st.warning("Colonnes `ca_online` / `ca_offline` absentes dans le dataset.")
    st.stop()

dff["total"] = dff["ca_online"].fillna(0) + dff["ca_offline"].fillna(0)

tot_on = dff["ca_online"].sum()
tot_off = dff["ca_offline"].sum()
share_on = (tot_on / (tot_on + tot_off) * 100) if (tot_on + tot_off) else None

# YoY online/offline
last_year = int(dff["year"].max())
prev_year = last_year - 1
on_yoy = yoy(dff.loc[dff["year"] == last_year, "ca_online"].sum(),
             dff.loc[dff["year"] == prev_year, "ca_online"].sum())
off_yoy = yoy(dff.loc[dff["year"] == last_year, "ca_offline"].sum(),
              dff.loc[dff["year"] == prev_year, "ca_offline"].sum())

c1, c2, c3 = st.columns(3)
c1.metric("CA online (EUR)", safe_metric_number(tot_on), f"{on_yoy:.1f}% YoY" if on_yoy is not None else None)
c2.metric("CA offline (EUR)", safe_metric_number(tot_off), f"{off_yoy:.1f}% YoY" if off_yoy is not None else None)
c3.metric("Part du online", f"{share_on:.1f} %" if share_on is not None else "-")

# Série mensuelle empilée (stacked)
st.subheader("Séries mensuelles (stacked)")
ts = dff.groupby(pd.Grouper(key="month_key", freq="MS"))[["ca_online","ca_offline"]].sum().reset_index()
tsm = ts.melt(id_vars="month_key", value_vars=["ca_online","ca_offline"], var_name="canal", value_name="ca")
fig_s = px.area(tsm, x="month_key", y="ca", color="canal", groupnorm=None,
                labels={"month_key":"Mois","ca":"CA (EUR)","canal":"Canal"})
st.plotly_chart(fig_s, use_container_width=True)

# Répartition par année
st.subheader("Répartition annuelle (stacked)")
by_year = dff.groupby("year", as_index=False)[["ca_online","ca_offline"]].sum()
by_year_m = by_year.melt(id_vars="year", value_vars=["ca_online","ca_offline"], var_name="canal", value_name="ca")
fig_b = px.bar(by_year_m, x="year", y="ca", color="canal", barmode="stack",
               labels={"year":"Année","ca":"CA (EUR)","canal":"Canal"})
st.plotly_chart(fig_b, use_container_width=True)

# Part online par année (100%)
st.subheader("Part du online par année (%)")
by_year["online_share"] = by_year["ca_online"] / (by_year["ca_online"] + by_year["ca_offline"]) * 100
fig_share = px.bar(by_year, x="year", y="online_share", labels={"year":"Année","online_share":"% Online"})
st.plotly_chart(fig_share, use_container_width=True)
