# bi/streamlit_app/pages/05_Tendances.py
import streamlit as st
import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.express as px

from _shared import load_data

st.title("Tendances & Prévisions")

# Charger données
df = load_data()

# Vérifications colonnes
if df.empty:
    st.error("⚠️ Données introuvables.")
    st.stop()

required = {"month_key", "ca"}
missing = required - set(df.columns)
if missing:
    st.error(f"⚠️ Colonnes manquantes : {missing}")
    st.stop()

# ================================
# 1) Préparation des données
# ================================
series = df.copy()
series["ds"] = pd.to_datetime(series["month_key"], errors="coerce")
series["y"] = series["ca"]

series = series.dropna(subset=["ds", "y"]).sort_values("ds")

with st.expander("Aperçu séries (5 premières lignes)"):
    st.dataframe(series[["ds", "y"]].head())

st.caption(f"Série mensuelle : {len(series)} points | de {series['ds'].min().date()} à {series['ds'].max().date()}")

# ================================
# 2) Paramètres utilisateur
# ================================
horizon_map = {
    "6 mois": 6,
    "12 mois": 12,
    "Jusqu'à 2030": (2030 - series["ds"].dt.year.max()) * 12,
}
horizon_choice = st.selectbox("Horizon de prévision", list(horizon_map.keys()), index=2)
horizon_months = horizon_map[horizon_choice]

changepoint_prior = st.slider("Changepoint prior scale (sensibilité)", 0.01, 0.5, 0.1, 0.01)

# ================================
# 3) Modèle Prophet
# ================================
try:
    m = Prophet(changepoint_prior_scale=changepoint_prior)
    m.fit(series[["ds", "y"]])

    future = m.make_future_dataframe(periods=horizon_months, freq="M")
    forecast = m.predict(future)

    st.subheader("Historique du CA (mensuel)")
    fig = plot_plotly(m, forecast)
    st.plotly_chart(fig, use_container_width=True)

    # Export prévisions
    st.download_button(
        "📥 Exporter la prévision (CSV)",
        data=forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(index=False).encode("utf-8"),
        file_name="forecast_2030.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error(f"Erreur Prophet : {e}")
    st.stop()

# ================================
# 4) Google Trends (si dispo)
# ================================
import os
from pathlib import Path

candidates = [
    Path(__file__).resolve().parents[2] / "data" / "processed" / "google_trends.csv",
    Path(__file__).resolve().parents[2] / "data" / "raw" / "google_trends.csv",
]

gt_path = next((p for p in candidates if p.exists()), None)
gt = pd.read_csv(gt_path) if gt_path else None

if gt is None:
    st.warning("Aucun CSV Google Trends trouvé. Place un fichier google_trends.csv dans data/processed/ ou data/raw/")
else:
    st.subheader("Google Trends (fallback CSV)")
    st.dataframe(gt.head())

# ================================
# 5) Corrélation CA ↔ Google Trends
# ================================
st.subheader("Corrélation CA ↔ Google Trends")

if gt is not None:
    date_col = next((c for c in gt.columns if c.lower() in ("date", "ds")), None)
    topic_col = next((c for c in gt.columns if c.lower() in ("topic", "keyword", "marque")), None)
    score_col = next((c for c in gt.columns if c.lower() in ("score", "value", "index")), None)

    if date_col and topic_col and score_col:
        gt_corr = gt.copy()
        gt_corr[date_col] = pd.to_datetime(gt_corr[date_col], errors="coerce")
        gt_corr["ds"] = gt_corr[date_col].dt.to_period("M").dt.to_timestamp()

        # Agrégat mensuel par sujet
        gt_corr = gt_corr.groupby(["ds", topic_col], as_index=False)[score_col].mean()
        pivot = gt_corr.pivot(index="ds", columns=topic_col, values=score_col)

        # Join avec série CA
        series_ca = series.set_index("ds")[["y"]]
        df_corr = series_ca.join(pivot, how="inner")

        corr = df_corr.corr()["y"].drop("y")

        fig_corr = px.bar(
            corr,
            orientation="h",
            title="Corrélation entre CA et Google Trends",
            labels={"value": "Corrélation (Pearson)", "index": "Sujet"},
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        best_topic = corr.abs().idxmax()
        best_value = corr[best_topic]

        # Rapport pour REPORT.md
        report_md = f"""
### Corrélation CA et Google Trends

- **Période analysée** : {df_corr.index.min().date()} → {df_corr.index.max().date()}.
- **Sujet le plus corrélé au CA** : **{best_topic}** (*r* = {best_value:.2f}, n = {len(df_corr)}).
- **Interprétation** : un r proche de 1 indique une co-variation forte entre l'intérêt de recherche et le CA.
  À consolider avec le contexte (campagnes, lancements, mix online/offline).
"""
        st.markdown("### Section REPORT.md — Corrélation (à copier)")
        st.code(report_md, language="markdown")

        st.download_button(
            "📥 Télécharger la section Corrélation (REPORT.md)",
            data=report_md.encode("utf-8"),
            file_name="report_correlation.md",
            mime="text/markdown",
        )
