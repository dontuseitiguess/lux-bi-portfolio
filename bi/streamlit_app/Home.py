# bi/streamlit_app/Home.py
import streamlit as st
from _shared import load_data, safe_metric_number

st.set_page_config(page_title="Luxury BI Dashboard", layout="wide")

st.title("Luxury BI Dashboard")
st.markdown("Bienvenue dans le portfolio BI — analyse du secteur luxe.")

# Charger données
df = load_data()

if df.empty:
    st.warning("⚠️ Aucune donnée trouvée.")
    st.stop()
else:
    st.success(f"✅ Dataset chargé : {len(df)} lignes, {len(df.columns)} colonnes")
    st.write("Colonnes disponibles :", list(df.columns))

    with st.expander("Aperçu des données (5 premières lignes)"):
        st.dataframe(df.head())

    # Aperçu rapide
    kpi1 = df["ca"].sum() if "ca" in df.columns else None
    kpi2 = df["unites"].sum() if "unites" in df.columns else None
    kpi3 = df["pays_key"].nunique() if "pays_key" in df.columns else None

    c1, c2, c3 = st.columns(3)
    c1.metric("CA total", safe_metric_number(kpi1))
    c2.metric("Unités vendues", safe_metric_number(kpi2))
    c3.metric("Pays actifs", safe_metric_number(kpi3))

st.markdown("---")
st.markdown(
    """
    ### Navigation
    Utilise le menu à gauche pour accéder aux pages :
    - **Direction** : KPI exécutifs
    - **Ecommerce** : focus digital
    - **Marques** : benchmark marques
    - **Pays** : marchés géographiques
    - **Tendances** : prévisions et Google Trends
    """
)
