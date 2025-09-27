# bi/streamlit_app/pages/05_Tendances.py
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go

from _shared import load_data, safe_metric_number

st.title("Tendances & Prévisions")

# ============ 1) Charger & préparer ============
df = load_data().copy()

if "month_key" not in df.columns or "ca" not in df.columns:
    st.error("Colonnes requises manquantes : 'month_key' et/ou 'ca'.")
    st.stop()

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
st.caption(f"Serie mensuelle : {len(ts)} points | de {ts['ds'].min().date()} à {ts['ds'].max().date()}")

# ============ 2) Contrôles ============
c1, c2, c3 = st.columns(3)
option_hzn = c1.selectbox("Horizon de prévision", ["Jusqu'a 2030", "Annees (custom)"], index=0)
years_ahead = 5
if option_hzn == "Annees (custom)":
    years_ahead = c2.slider("Nombre d'annees a prevoir", 1, 8, 5, 1)
cp_scale = float(c3.slider("Changepoint prior scale (sensibilite)", 0.01, 0.50, 0.10, 0.01))

# ============ 3) Historique ============
st.subheader("Historique du CA (mensuel)")
fig_hist = px.line(ts, x="ds", y="y", labels={"ds": "Mois", "y": "CA (EUR)"})
st.plotly_chart(fig_hist, use_container_width=True)

# ============ 4) Prévision (Prophet si dispo) ============
st.subheader("Prévision")
prophet_ok = True
forecast_df = None
try:
    from prophet import Prophet
except Exception:
    prophet_ok = False
    st.info("Prophet indisponible sur cet environnement (la page reste fonctionnelle).")

if prophet_ok and len(ts) >= 12:
    if option_hzn == "Jusqu'a 2030":
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
        m.fit(ts)

        future = m.make_future_dataframe(periods=periods, freq="MS")
        forecast = m.predict(future)

        forecast_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

        hist = ts.rename(columns={"y": "value"}).assign(type="Historique")
        fc = forecast_df.rename(columns={"yhat": "value"}).assign(type="Prévision")
        ci = forecast_df.copy()

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(x=hist["ds"], y=hist["value"], mode="lines", name="Historique"))
        fig_fc.add_trace(go.Scatter(x=ci["ds"], y=ci["yhat_upper"], mode="lines", name="IC sup", line=dict(width=0), showlegend=False))
        fig_fc.add_trace(go.Scatter(x=ci["ds"], y=ci["yhat_lower"], fill="tonexty", mode="lines", name="IC", line=dict(width=0)))
        fig_fc.add_trace(go.Scatter(x=fc["ds"], y=fc["value"], mode="lines", name="Prévision"))
        fig_fc.update_layout(xaxis_title="Date", yaxis_title="CA (EUR)")
        st.plotly_chart(fig_fc, use_container_width=True)
    except Exception as e:
        st.warning(f"Prévision Prophet impossible : {e}")
elif len(ts) < 12:
    st.warning("Pas assez d'historique (< 12 points) pour une prévision fiable.")

# ============ 5) Export CSV (prévision) ============
if forecast_df is not None and not forecast_df.empty:
    st.download_button(
        "Exporter la prevision (CSV)",
        data=forecast_df.to_csv(index=False).encode("utf-8"),
        file_name="forecast_2030.csv",
        mime="text/csv",
    )

# ============ 6) Insights (YoY & CAGR) + section REPORT.md ============
def fmt_pct(x):
    try:
        return f"{x:.1f} %"
    except Exception:
        return "n/a"

with st.expander("Insights automatiques"):
    yoy_val = None
    cagr_hist_val = None
    cagr_fc_val = None

    try:
        s = ts.copy()
        s["year"] = s["ds"].dt.year
        last_year = int(s["year"].max())
        ca_cur = float(s.loc[s["year"] == last_year, "y"].sum())
        ca_prev = float(s.loc[s["year"] == (last_year - 1), "y"].sum())
        yoy_val = (ca_cur / ca_prev - 1) * 100 if ca_prev else None

        y_first = int(s["year"].min())
        ca_first = float(s.loc[s["year"] == y_first, "y"].sum())
        if ca_first and last_year > y_first:
            n_years = last_year - y_first
            cagr_hist_val = ((ca_cur / ca_first) ** (1 / n_years) - 1) * 100

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
        bullets.append(f"- YoY {last_year-1} -> {last_year} : {fmt_pct(yoy_val)}" if yoy_val is not None else "- YoY : n/a")
        if cagr_hist_val is not None:
            bullets.append(f"- CAGR historique {y_first} -> {last_year} : {fmt_pct(cagr_hist_val)}/an")
        if cagr_fc_val is not None:
            bullets.append(f"- CAGR prevu : {fmt_pct(cagr_fc_val)}/an (jusqu'a l'horizon)")
        st.markdown("\n".join(bullets))

        yoy_str = fmt_pct(yoy_val) if yoy_val is not None else "n/a"
        cagr_hist_str = fmt_pct(cagr_hist_val) + "/an" if cagr_hist_val is not None else "n/a"
        cagr_fc_str = fmt_pct(cagr_fc_val) + "/an" if cagr_fc_val is not None else "n/a"

        report_md = (
            "## Tendances & Prévisions — Résumé executif\n\n"
            f"- Historique : serie mensuelle du CA de {s['ds'].min().date()} a {s['ds'].max().date()} ({len(s)} points).\n"
            f"- YoY {last_year-1}->{last_year} : {yoy_str}.\n"
            f"- CAGR historique {y_first}->{last_year} : {cagr_hist_str}.\n"
            f"- Prévision : Prophet (saisonnalite annuelle), sensibilite {cp_scale}.\n"
            f"- CAGR prevu (fin d'horizon) : {cagr_fc_str}.\n"
            "- Remarques : a confronter aux promotions, lancements, mix online/offline.\n"
        )
        st.subheader("Section REPORT.md (a copier)")
        st.code(report_md, language="markdown")
        st.download_button(
            "Telecharger la section REPORT.md",
            data=report_md.encode("utf-8"),
            file_name="REPORT_section_tendances.md",
            mime="text/markdown",
        )
    except Exception:
        st.write("Insights indisponibles (donnees insuffisantes).")

# ============ 7) Google Trends (fallback CSV) ============
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
        "Aucun CSV Google Trends trouve. Place un fichier 'google_trends.csv' dans "
        "data/processed/ ou data/raw/ (colonnes attendues : date, topic, score)."
    )
else:
    date_col = next((c for c in gt.columns if c.lower() in ("date", "ds")), None)
    topic_col = next((c for c in gt.columns if c.lower() in ("topic", "keyword", "marque")), None)
    score_col = next((c for c in gt.columns if c.lower() in ("score", "value", "index")), None)

    if not (date_col and topic_col and score_col):
        st.warning("Colonnes Trends non reconnues. Attendu : date, topic, score.")
    else:
        gt[date_col] = pd.to_datetime(gt[date_col], errors="coerce")
        topics = ["Tous"] + sorted(gt[topic_col].dropna().unique().tolist())
        sel = st.selectbox("Sujet", topics, index=0)
        gff = gt if sel == "Tous" else gt[gt[topic_col] == sel]
        gff = gff.sort_values(date_col)

        st.caption(f"Tendances — {sel}")
        fig_gt = px.line(
            gff, x=date_col, y=score_col,
            color=topic_col if sel == "Tous" else None,
            labels={date_col: "Date", score_col: "Score", topic_col: "Sujet"}
        )
        st.plotly_chart(fig_gt, use_container_width=True)

        # ============ 7bis) Corrélation CA <-> Trends ============
        st.subheader("Correlation CA et Google Trends")
        try:
            gt_corr = gt.copy()
            gt_corr[date_col] = pd.to_datetime(gt_corr[date_col], errors="coerce")
            gt_corr["ds"] = gt_corr[date_col].dt.to_period("M").dt.to_timestamp()

            gt_corr = gt_corr.groupby(["ds", topic_col], as_index=False)[score_col].mean()
            pivot = gt_corr.pivot(index="ds", columns=topic_col, values=score_col)

            series = ts.set_index("ds").copy()
            df_corr = series.join(pivot, how="inner")  # periode commune

            def z(x):
                std = x.std(ddof=0)
                if std is None or std == 0 or np.isnan(std):
                    return x
                return (x - x.mean()) / std

            zdf = df_corr.apply(z)

            corr_series = zdf.corr(numeric_only=True)["y"].dropna()
            corr_series = corr_series.drop(labels=["y"], errors="ignore")
            corrs = corr_series.sort_values(ascending=False).to_frame(name="corr_Pearson").reset_index().rename(columns={"index": "topic"})

            n_per_topic = df_corr.drop(columns=["y"]).notna().sum(axis=0).to_dict()
            corrs["n_obs"] = corrs["topic"].map(n_per_topic)

            if corrs.empty:
                st.info("Pas assez de recouvrement temporel entre CA et Trends pour calculer la correlation.")
            else:
                corrs_sorted = corrs.sort_values("corr_Pearson", ascending=True).tail(15)
                corrs_sorted["signe"] = np.where(corrs_sorted["corr_Pearson"] >= 0, "Positif", "Negatif")
                corrs_sorted["text"] = corrs_sorted["corr_Pearson"].map(lambda v: f"{v:.2f}")

                fig_corr = px.bar(
                    corrs_sorted,
                    x="corr_Pearson",
                    y="topic",
                    orientation="h",
                    color="signe",
                    hover_data={"n_obs": True, "corr_Pearson": ":.3f", "signe": False},
                    labels={"topic": "Sujet", "corr_Pearson": "Correlation (Pearson)", "n_obs": "n obs"},
                )
                fig_corr.update_layout(xaxis=dict(range=[-1, 1]))
                fig_corr.update_traces(text=corrs_sorted["text"], textposition="outside", cliponaxis=False)
                st.caption(f"Periode commune analysee : {df_corr.index.min().date()} -> {df_corr.index.max().date()} (voir n obs dans le hover)")
                st.plotly_chart(fig_corr, use_container_width=True)

                st.download_button(
                    "Exporter les correlations (CSV)",
                    data=corrs.sort_values("corr_Pearson", ascending=False).to_csv(index=False).encode("utf-8"),
                    file_name="correlations_ca_trends.csv",
                    mime="text/csv",
                )

                top_row = corrs.sort_values("corr_Pearson", ascending=False).iloc[0]
                topic_best = str(top_row["topic"])
                corr_best = float(top_row["corr_Pearson"])
                n_best = int(top_row.get("n_obs", 0))

                report_corr_md = (
                    "### Correlation CA et Google Trends\n\n"
                    f"- Periode analysee : {df_corr.index.min().date()} -> {df_corr.index.max().date()}.\n"
                    f"- Sujet le plus correle au CA : {topic_best} (r = {corr_best:.2f}, n = {n_best}).\n"
                    "- Interpretation : un r proche de 1 indique une co-variation forte entre l'interet de recherche et le CA. "
                    "A consolider avec le contexte (campagnes, lancements, mix online/offline).\n"
                )
                st.subheader("Section REPORT.md — Correlation (a copier)")
                st.code(report_corr_md, language="markdown")
                st.download_button(
                    "Telecharger la section Correlation (REPORT.md)",
                    data=report_corr_md.encode("utf-8"),
                    file_name="REPORT_section_correlation.md",
                    mime="text/markdown",
                )
        except Exception as e:
            st.warning(f"Correlation non calculee : {e}")

# ============ 8) Notes ============
with st.expander("Notes & hypotheses"):
    st.markdown(
        "- Prophet : saisonnalite annuelle, sensibilite ajustable via changepoint_prior_scale.\n"
        "- Horizon : jusqu'a 2030 ou custom (annees).\n"
        "- IC : ruban entre yhat_lower et yhat_upper.\n"
        "- Google Trends : lecture d'un CSV fallback.\n"
        "- Correlation : Pearson sur periode commune (serie CA jointe aux Trends).\n"
        "- Caveat : resultats illustratifs — a consolider avec les equipes metier.\n"
    )
