import streamlit as st
from _shared import load_data, safe_metric_number

st.set_page_config(page_title="Luxury BI Dashboard", layout="wide")
st.title("Luxury BI Dashboard")
st.caption("Bienvenue dans le portfolio BI — analyse du secteur luxe.")

df = load_data()
if df.empty:
    st.stop()

with st.expander("Aperçu des données (5 premières lignes)"):
    st.dataframe(df.head())

kpi_ca = df["ca"].sum() if "ca" in df.columns else None
kpi_units = df["unites"].sum() if "unites" in df.columns else None
kpi_countries = df["pays_key"].nunique() if "pays_key" in df.columns else None

c1, c2, c3 = st.columns(3)
c1.metric("CA total (EUR)", safe_metric_number(kpi_ca))
c2.metric("Unités vendues", safe_metric_number(kpi_units))
c3.metric("Pays actifs", safe_metric_number(kpi_countries))

st.markdown("---")
st.markdown(
    """
    ### Navigation
    - **Direction** : KPI clés & tendances annuelles  
    - **Ecommerce** : online vs offline  
    - **Marques** : classement par CA  
    - **Pays** : classement par CA  
    - **Tendances** : prévision simple (sans Google Trends)
    """
)
