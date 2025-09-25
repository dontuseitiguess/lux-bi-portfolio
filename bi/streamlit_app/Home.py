import os
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Luxe BI – Home", page_icon="💎", layout="wide")

st.title("💎 Digitalisation du Luxe – BI Portfolio")
st.caption("Mode démo : se connecte à Postgres si disponible, sinon bascule sur CSV versionné.")

# --- Try DB first, else CSV ---
DB_URL = os.environ.get("DB_URL")
USE_CSV = os.environ.get("USE_CSV", "0") == "1"

engine = None
if DB_URL and not USE_CSV:
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DB_URL, future=True)
        with engine.connect() as con:
            con.exec_driver_sql("SELECT 1")
        st.success("Connexion base OK")
    except Exception as e:
        st.warning(f"DB indisponible, fallback CSV. Détail: {e}")
        engine = None
else:
    st.info("Mode CSV forcé (pas de DB_URL ou USE_CSV=1).")

# --- Load data (MV) ---
@st.cache_data(ttl=300)
def load_mv():
    if engine:
        from sqlalchemy import text
        sql = """
        SELECT
          month_key, m.marque_nom, p.pays_lib,
          ca, unites, aov, marge_pct_avg, ca_online, ca_offline
        FROM mv_month_brand_country x
        JOIN dim_marque m ON m.marque_key=x.marque_key
        JOIN dim_pays   p ON p.pays_key=x.pays_key
        ORDER BY month_key
        """
        with engine.begin() as con:
            return pd.read_sql(text(sql), con)
    else:
        csv_path = "data/processed/mv_month_brand_country.csv"
        df = pd.read_csv(csv_path, parse_dates=["month_key"])
        # enrichis noms si tu veux (ici on garde keys -> labels pas dispos en CSV)
        # pour une démo lisible, on peut garder keys, ou préparer un CSV déjà joint
        df["marque_nom"] = df.get("marque_nom", "Marque")
        df["pays_lib"] = df.get("pays_lib", "Pays")
        return df

df = load_mv()
if df.empty:
    st.error("Aucune donnée à afficher. Vérifie l’export CSV ou la DB.")
    st.stop()

# Filtres
months = sorted(df["month_key"].unique())
col1, col2 = st.columns(2)
with col1:
    m_from = st.selectbox("Période – début (mois)", months, index=0)
with col2:
    m_to = st.selectbox("Période – fin (mois)", months, index=len(months)-1)

marques = sorted(df["marque_nom"].unique())
pays = sorted(df["pays_lib"].unique())
colA, colB = st.columns(2)
with colA:
    sel_marques = st.multiselect("Marques", options=marques, default=marques[:2])
with colB:
    sel_pays = st.multiselect("Pays", options=pays, default=pays[:2])

# Filtrage
df_f = df[(df["month_key"] >= pd.to_datetime(m_from)) & (df["month_key"] <= pd.to_datetime(m_to))]
if sel_marques:
    df_f = df_f[df_f["marque_nom"].isin(sel_marques)]
if sel_pays:
    df_f = df_f[df_f["pays_lib"].isin(sel_pays)]

# KPIs
def kpis(d):
    ca = float(d["ca"].sum())
    unites = int(d["unites"].sum())
    aov = (ca / unites) if unites else 0
    marge = float(d["marge_pct_avg"].mean()) if not d.empty else 0
    ca_online = float(d["ca_online"].sum())
    ca_offline = float(d["ca_offline"].sum())
    mix_online = (ca_online / (ca_online + ca_offline) * 100) if (ca_online + ca_offline) else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CA total (€)", f"{ca:,.0f}".replace(",", " "))
    c2.metric("Unités", f"{unites:,}".replace(",", " "))
    c3.metric("AOV (€)", f"{aov:,.0f}".replace(",", " "))
    c4.metric("Marge % (moy.)", f"{marge:.1f}%")
    st.caption(f"Mix Online: **{mix_online:.1f}%** | Offline: **{100-mix_online:.1f}%**")

kpis(df_f)

# Graphes
st.subheader("Évolution mensuelle du CA")
ts = df_f.groupby("month_key", as_index=False)["ca"].sum()
fig1 = px.line(ts, x="month_key", y="ca")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Top CA par marque")
top_brand = df_f.groupby("marque_nom", as_index=False)["ca"].sum().sort_values("ca", ascending=False).head(10)
fig2 = px.bar(top_brand, x="marque_nom", y="ca")
st.plotly_chart(fig2, use_container_width=True)

st.caption("Astuce : si la DB n’est pas accessible sur le cloud, l’app bascule automatiquement sur le CSV exporté.")
