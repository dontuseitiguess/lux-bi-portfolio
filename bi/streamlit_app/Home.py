import streamlit as st
from _shared import load_data, safe_metric_number, sidebar_filters

st.set_page_config(page_title="Luxury BI Dashboard", layout="wide")

st.title("Luxury BI Dashboard")
st.caption("Bienvenue dans le portfolio BI — analyse du secteur luxe.")

df = load_data()
if df.empty:
    st.stop()

# filtres communs
dff, meta = sidebar_filters(df)

with st.expander("Aperçu des données (5 premières lignes)"):
    st.dataframe(dff.head())

kpi_ca = dff["ca"].sum() if "ca" in dff.columns else None
kpi_units = dff["unites"].sum() if "unites" in dff.columns else None
kpi_countries = dff["pays_key"].nunique() if "pays_key" in dff.columns else None

c1, c2, c3 = st.columns(3)
c1.metric("CA total (EUR)", safe_metric_number(kpi_ca))
c2.metric("Unités vendues", safe_metric_number(kpi_units))
c3.metric("Pays actifs", safe_metric_number(kpi_countries))

st.markdown("---")
st.markdown(
    """
    ### Navigation
    - **Direction** : KPI clés, YoY, YTD, saisonnalité  
    - **Ecommerce** : online vs offline, part digitale, séries  
    - **Marques** : benchmark, part de marché, comparateur  
    - **Pays** : classement, YoY par pays, focus marché  
    - **Tendances** : prévision simple (Prophet si dispo, sinon moyenne mobile)
    """
)

