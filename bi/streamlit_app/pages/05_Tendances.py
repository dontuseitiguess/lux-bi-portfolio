import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from _shared import load_data

st.title("Tendances (prévision simple)")

df = load_data()
if df.empty:
    st.stop()

# Série mensuelle CA
df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
ts = df.groupby(pd.Grouper(key="month_key", freq="MS"))["ca"].sum().reset_index().sort_values("month_key")
ts = ts.rename(columns={"month_key": "ds", "ca": "y"})

with st.expander("Aperçu séries (5 premières lignes)"):
    st.dataframe(ts.head())

# Tentative Prophet si dispo, sinon moyenne mobile
forecast_df = None
prophet_ok = True
try:
    from prophet import Prophet
except Exception:
    prophet_ok = False

if prophet_ok and len(ts) >= 12:
    try:
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False, changepoint_prior_scale=0.1)
        m.fit(ts)
        future = m.make_future_dataframe(periods=24, freq="MS")
        fc = m.predict(future)
        forecast_df = fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ts["ds"], y=ts["y"], mode="lines", name="Historique"))
        fig.add_trace(go.Scatter(x=forecast_df["ds"], y=forecast_df["yhat_upper"], mode="lines",
                                 name="IC sup", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=forecast_df["ds"], y=forecast_df["yhat_lower"], mode="lines",
                                 fill="tonexty", name="IC", line=dict(width=0)))
        fig.add_trace(go.Scatter(x=forecast_df["ds"], y=forecast_df["yhat"], mode="lines", name="Prévision"))
        fig.update_layout(xaxis_title="Date", yaxis_title="CA (EUR)")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Prévision Prophet impossible : {e}")
        prophet_ok = False

if not prophet_ok:
    # fallback: moyenne mobile simple
    ts2 = ts.copy()
    ts2["y_ma"] = ts2["y"].rolling(6, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts2["ds"], y=ts2["y"], mode="lines", name="Historique"))
    fig.add_trace(go.Scatter(x=ts2["ds"], y=ts2["y_ma"], mode="lines", name="Moyenne mobile (6)"))
    fig.update_layout(xaxis_title="Date", yaxis_title="CA (EUR)")
    st.plotly_chart(fig, use_container_width=True)

# Export CSV prévision si dispo
if forecast_df is not None and not forecast_df.empty:
    st.download_button(
        "Exporter la prévision (CSV)",
        data=forecast_df.to_csv(index=False).encode("utf-8"),
        file_name="forecast.csv",
        mime="text/csv",
    )
