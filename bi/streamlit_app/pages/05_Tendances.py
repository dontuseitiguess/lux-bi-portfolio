import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from _shared import load_data, sidebar_filters

st.title("Tendances & Prévisions")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

ts=dff.groupby(pd.Grouper(key="month_key",freq="MS"))["ca"].sum().reset_index().rename(columns={"month_key":"ds","ca":"y"})
forecast_df=None

use_prophet=st.toggle("Essayer Prophet",True)
if use_prophet and len(ts)>=12:
    try:
        from prophet import Prophet
        m=Prophet(yearly_seasonality=True)
        m.fit(ts)
        fc=m.predict(m.make_future_dataframe(periods=24,freq="MS"))
        forecast_df=fc[["ds","yhat","yhat_lower","yhat_upper"]]
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=ts["ds"],y=ts["y"],mode="lines",name="Historique"))
        fig.add_trace(go.Scatter(x=forecast_df["ds"],y=forecast_df["yhat"],mode="lines",name="Prévision"))
        st.plotly_chart(fig,use_container_width=True)
    except Exception as e:
        st.warning(f"Prophet erreur : {e}")
        use_prophet=False
if not use_prophet:
    ts["MA6"]=ts["y"].rolling(6,min_periods=1).mean()
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=ts["ds"],y=ts["y"],mode="lines",name="Historique"))
    fig.add_trace(go.Scatter(x=ts["ds"],y=ts["MA6"],mode="lines",name="MA6"))
    st.plotly_chart(fig,use_container_width=True)
