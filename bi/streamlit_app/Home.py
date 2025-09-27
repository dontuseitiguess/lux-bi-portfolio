import streamlit as st
from _shared import load_data, safe_metric_number, sidebar_filters

st.set_page_config(page_title="Luxury BI Dashboard", layout="wide")
st.title("Luxury BI Dashboard")
st.caption("Bienvenue dans le portfolio BI — analyse du secteur luxe.")

df = load_data()
if df.empty: st.stop()

dff, meta = sidebar_filters(df)

kpi_ca = dff["ca"].sum() if "ca" in dff.columns else None
kpi_units = dff["unites"].sum() if "unites" in dff.columns else None
kpi_countries = dff["pays"].nunique() if "pays" in dff.columns else dff["pays_key"].nunique()

c1, c2, c3 = st.columns(3)
c1.metric("CA total", safe_metric_number(kpi_ca))
c2.metric("Unités", safe_metric_number(kpi_units))
c3.metric("Pays actifs", safe_metric_number(kpi_countries))

st.markdown("---")
st.markdown(
"""
### Navigation
- **Direction** : KPI clés, YoY, YTD, saisonnalité  
- **Ecommerce** : online vs offline  
- **Marques** : benchmark, comparateur  
- **Pays** : classement, focus marché  
- **Tendances** : prévisions (Prophet si dispo, fallback moyenne mobile)
"""
)
