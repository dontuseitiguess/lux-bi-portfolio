import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters

st.title("Pays — Performance")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

country_col = "pays" if "pays" in dff.columns else ("pays_key" if "pays_key" in dff.columns else None)
if not country_col or "ca" not in dff:
    st.warning("Colonnes nécessaires manquantes pour l'analyse pays.")
    st.stop()

rank = dff.groupby(country_col, as_index=False)["ca"].sum().sort_values("ca", ascending=False)
st.subheader("Classement pays")
st.dataframe(rank.head(20), use_container_width=True)
st.plotly_chart(px.bar(rank.head(15), x=country_col, y="ca", labels={country_col:"Pays","ca":"CA (EUR)"}),
                use_container_width=True)

if "year" in dff:
    last, prev = dff["year"].max(), dff["year"].max()-1
    yoy_df=[]
    for pk,g in dff.groupby(country_col):
        ca_last, ca_prev = g.loc[g["year"]==last,"ca"].sum(), g.loc[g["year"]==prev,"ca"].sum()
        y=None
        if ca_prev and ca_prev!=0:
            y=(ca_last/ca_prev-1)*100
        if y is not None:
            yoy_df.append({country_col:pk, "yoy%":y})
    if yoy_df:
        yoy_df=pd.DataFrame(yoy_df).sort_values("yoy%",ascending=False)
        st.subheader("YoY par pays")
        st.plotly_chart(px.bar(yoy_df, x=country_col, y="yoy%", labels={country_col:"Pays","yoy%":"YoY %"}),
                        use_container_width=True)

# Focus pays
p_all = sorted(dff[country_col].unique())
if p_all:
    focus = st.selectbox("Pays focus", p_all)
    ts = dff[dff[country_col]==focus].groupby("month_key",as_index=False)["ca"].sum()
    st.plotly_chart(px.line(ts, x="month_key", y="ca", labels={"month_key":"Mois","ca":"CA (EUR)"}),
                    use_container_width=True)
