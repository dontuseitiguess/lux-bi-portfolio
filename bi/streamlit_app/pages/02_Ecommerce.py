import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, safe_metric_number

st.title("Ecommerce")

df = load_data()
if df.empty:
    st.stop()

if not {"ca_online", "ca_offline"}.issubset(df.columns):
    st.warning("Colonnes `ca_online` / `ca_offline` absentes dans le dataset.")
    st.stop()

df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
df["year"] = df["month_key"].dt.year

tot_on = df["ca_online"].sum()
tot_off = df["ca_offline"].sum()
share_on = tot_on / (tot_on + tot_off) * 100 if (tot_on + tot_off) else None

c1, c2, c3 = st.columns(3)
c1.metric("CA online (EUR)", safe_metric_number(tot_on))
c2.metric("CA offline (EUR)", safe_metric_number(tot_off))
c3.metric("Part du online", f"{share_on:.1f} %" if share_on is not None else "-")

st.subheader("Répartition annuelle")
by_year = df.groupby("year", as_index=False)[["ca_online", "ca_offline"]].sum()
by_year_melt = by_year.melt(id_vars="year", value_vars=["ca_online", "ca_offline"], var_name="canal", value_name="ca")
fig = px.bar(by_year_melt, x="year", y="ca", color="canal", barmode="stack",
             labels={"year": "Année", "ca": "CA (EUR)", "canal": "Canal"})
st.plotly_chart(fig, use_container_width=True)
