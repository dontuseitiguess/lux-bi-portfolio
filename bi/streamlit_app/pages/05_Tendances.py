# bi/streamlit_app/pages/05_Tendances.py
import streamlit as st
import pandas as pd
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go

from _shared import load_data, safe_metric_number

st.title("Tendances & Prévisions")

# =========================
# 1) Charger & préparer
# =========================
df = load_data().copy()

if "month_key" not in df.columns or "ca" not in df.columns:
    st.error("Colonnes requises manquantes : 'month_key' et/ou 'ca'.")
    st.stop()

# Parse date + CA mensuel
df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
ts = (
    df.groupby(pd.Grouper(key="month_key", freq="MS"))["ca"]
    .sum()
    .reset_index()
    .sort_values("month_key")
    .rename(columns={"month_key": "ds", "ca": "y"})
)

with st.expander("Aperçu séries (5 premières lignes)"):
    st.dataframe(ts.head())

st.caption(f"Série mensuelle : {len(ts)} points | de {ts['ds'].min().date()} à {ts['ds'].max().date()}")

# =========================
# 2) Contrôles
# =========================
c1, c2, c3 = st.columns(3)
option_hzn = c1.selectbox("Horizon de prévision", ["Jusqu'à 2030", "Années (custom)"], index=0)
years_ahead = 5
if option_hzn == "Années (custom)":
    years_ahead = c2.slider("Nombre d'années à prévoir", 1, 8, 5, 1)
cp_scale = float(c3.slider("Changepoint prior scale (sensibilité)", 0.01, 0.50, 0.10, 0.01))

# =========================
# 3) Graphique Historique simple
# =========================
st.subheader("Historique du CA (mensuel)")
fig_hist = px.line(ts, x="ds", y="y", labels={"ds": "Mois", "y": "CA (EUR)"})
st.plotly_chart(fig_hist, use_container_width=True)

# =========================
# 4) Prévision (Prophet si dispo)
# =========================
st.subheader("Prévision")

prophet_ok = True
forecast_df = None
try:
    from prophet import Prophet
except Exception as e:
    prophet_ok = False
    st.info(
        "Prophet n'est pas disponible dans l'environnement. "
        "Le graphique ci-dessous pourrait utiliser un modèle alternatif si activé."
    )

if prophet_ok and len(ts) >= 12:
    # Horizon en mois
    if option_hzn == "Jusqu'à 2030":
        last = ts["ds"].max()
        months_to_2030 = (2030 - last.year) * 12 - (last.month - 1)
        periods = max(1, months_to_2030)
    else:
        periods = years_ahead * 12

    try:
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=cp_scale,
        )
        m.fit(ts)  # ts avec colonnes ds (datetime) et y (numérique)

        future = m.make_future_dataframe(periods=periods, freq="MS")
        forecast = m.predict(future)

        forecast_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

        # Plot custom Plotly (historique + forecast + IC)
        hist = ts.rename(columns={"y": "value"}).assign(type="Historique")
        fc = forecast_df.rename(columns={"yhat": "value"}).assign(type="Prévision")
        fc_ci = forecast_df.copy()

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=hist["ds"], y=hist["value"], mode="lines", name="Historique"))
        fig_fc.add_trace(go.Scatter(x=fc_ci["ds"], y=fc_ci["yhat_upper"], mode="lines", name="IC supérieur", line=dict(width=0), showlegend=False))
        fig_fc.add_trace(go.Scatter(x=fc_ci["ds"], y=fc_ci["yhat_lower"], fill="tonexty", mode="lines", name="Intervalle de confiance", line=dict(width=0)))
        fig_fc.add_trace(go.Scatter(x=fc["ds"], y=fc["value"], mode="lines", name="Prévision"))
        fig_fc.update_layout(xaxis_title="Date", yaxis_title="CA (EUR)")
        st.plotly_chart(fig_fc, use_container_width=True)
    except Exception as e:
        st.warning(f"Prévision Prophet impossible : {e}")

elif len(ts) < 12:
    st.warning("Pas assez d'historique (< 12 points) pour une prévision fiable.")

# =========================
# 5) Bouton Export CSV (prévision)
# =========================
if forecast_df is not None and not forecast_df.empty:
    st.download_button(
        "📥 Exporter la prévision (CSV)",
        data=forecast_df.to_csv(index=False).encode("utf-8"),
        file_name="forecast_2030.csv",
        mime="text/csv",
    )

# =========================
# 6) Insights (YoY & CAGR) + section REPORT.md
# =========================
with st.expander("Insights automatiques"):
    yoy_val = None
    cagr_hist_val = None
    cagr_fc_val = None
    report_md = ""

    try:
        s = ts.copy()
        s["year"] = s["ds"].dt.year
        last_year = int(s["year"].max())
        ca_cur = float(s.loc[s["year"] == last_year, "y"].sum())
        ca_prev = float(s.loc[s["year"] == (last_year - 1), "y"].sum())
        yoy_val = (ca_cur / ca_prev - 1) * 100 if ca_prev else None

        # CAGR historique (première année complète -> dernière année complète)
        y_first = int(s["year"].min())
        ca_first = float(s.loc[s["year"] == y_first, "y"].sum())
        if ca_first and last_year > y_first:
            n = last_year - y_first
            cagr_hist_val = ((ca_cur / ca_first) ** (1 / n) - 1) * 100

        # CAGR prévu vers fin forecast
        if forecast_df is not None and not forecast_df.empty:
            last_actual_date = ts["ds"].max()
            ca_base = float(ts.loc[ts["ds"] == last_actual_date, "y"].sum())
            last_forecast_date = forecast_df["ds"].max()
            ca_target = float(forecast_df.loc[forecast_df["ds"] == last_forecast_date, "yhat"].mean())
            if ca_base > 0 and last_forecast_date > last_actual_date:
                years_span = (last_forecast_date.year - last_actual_date.year) + \
                             (last_forecast_date.month - last_actual_date.month) / 12.0
                cagr_fc_val = ((ca_target / ca_base) ** (1 / years_span) - 1) * 100

        bullets = []
        bullets.append(f"• **YoY {last_year-1}→{last_year}** : {yoy_val:.1f} %" if yoy_val is not None else "• **YoY** : n/a")
        if cagr_hist_val is not None:
            bullets.append(f"• **CAGR historique** {y_first}→{last_year} : {cagr_hist_val:.1f} %/an")
        if cagr_fc_val is not None:
            bullets.append(f"• **CAGR prévu** : {cagr_fc_val:.1f} %/an (jusqu'à l'horizon de prévision)")

        st.markdown("\n".join(bullets))

        # Section REPORT.md prête à copier
        report_md = f"""
## Tendances & Prévisions — Résumé exécutif

- **Historique :** série mensuelle du CA de {s['ds'].min().date()} à {s['ds'].max().date()} ({len(s)} points).
- **YoY** {last_year-1}→{last_year} : {f"{yoy_val:.1f} %" if yoy_val is not None else "n/a"}.
- **CAGR historique** {y_first}→{last_year} : {f"{cagr_hist_val:.1f} %/an" if cagr_hist_val is not None else "n/a"}.
- **Prévision :** modèle Prophet avec saisonnalité annuelle et sensibilité {cp_scale}.
- **CAGR prévu** (vers la fin d'horizon) : {f"{cagr_fc_val:.1f} %/an" if cagr_fc_val is not None else "n/a"}.
- **Remarques :** les écarts peuvent provenir de promotions, lancements produits et mix online/offline. À valider avec le métier.

"""
        st.subheader("Section REPORT.md (à copier)")
        st.code(report_md.strip(), language="markdown")

        st.download_button(
            "📝 Télécharger la section REPORT.md",
            data=report_md.strip().encode("utf-8"),
            file_name="REPORT_section_tendances.md",
            mime="text/markdown",
        )

    except Exception:
        st.write("Insights indisponibles (données insuffisantes).")

# =========================
# 7) Google Trends (fallback CSV)
# =========================
st.subheader("Google Trends (fallback CSV)")

def load_trends_csv():
    candidates = [
        Path(__file__).resolve().parents[1] / "data" / "processed" / "google_trends.csv",
        Path(__file__).resolve().parents[2] / "data" / "processed" / "google_trends.csv",
        Path.cwd() / "data" / "processed" / "google_trends.csv",
        Path(__file__).resolve().parents[1] / "data" / "raw" / "google_trends.csv",
        Path(__file__).resolve().parents[2] / "data" / "raw" / "google_trends.csv",
        Path.cwd() / "data" / "raw" / "google_trends.csv",
    ]
    for p in candidates:
        if p.exists():
            try:
                return pd.read_csv(p)
            except Exception:
                pass
    return None

gt = load_trends_csv()
if gt is None:
    st.info(
        "Aucun CSV Google Trends trouvé. Place un fichier `google_trends.csv` dans "
        "`data/processed/` ou `data/raw/` (colonnes attendues : `date`, `topic`, `score`)."
    )
else:
    date_col = next((c for c in gt.columns if c.lower() in ("date", "ds")), None)
    topic_col = next((c for c in gt.columns if c.lower() in ("topic", "keyword", "marque")), None)
    score_col = next((c for c in gt.columns if c.lower() in ("score", "value", "index")), None)

    if not (date_col and topic_col and score_col):
        st.warning("Colonnes Trends non reconnues. Attendu: `date`, `topic`, `score`.")
    else:
        gt[date_col] = pd.to_datetime(gt[date_col], errors="coerce")
        topics = ["Tous"] + sorted(gt[topic_col].dropna().unique().tolist())
        sel = st.selectbox("Sujet", topics, index=0)
        gff = gt if sel == "Tous" else gt[gt[topic_col] == sel]
        gff = gff.sort_values(date_col)

        st.caption(f"Tendances — {sel}")
        fig_gt = px.line(gff, x=date_col, y=score_col, color=topic_col if sel == "Tous" else None,
                         labels={date_col: "Date", score_col: "Score", topic_col: "Sujet"})
        st.plotly_chart(fig_gt, use_container_width=True)

# =========================
# 8) Notes
# =========================
with st.expander("Notes & hypothèses"):
    st.markdown(
        "- **Prévision Prophet** : saisonnalité annuelle, sensibilité ajustable via `changepoint_prior_scale`.  \n"
        "- **Horizon** : jusqu'à 2030 ou custom (années).  \n"
        "- **IC** : ruban entre `yhat_lower` et `yhat_upper`.  \n"
        "- **Google Trends** : lecture d'un CSV fallback.  \n"
        "- **Caveat** : prévisions illustratives, à consolider avec l’équipe métier."
    )
