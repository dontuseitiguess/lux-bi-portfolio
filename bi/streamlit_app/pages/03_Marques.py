import streamlit as st
import pandas as pd
import plotly.express as px
from _shared import load_data, sidebar_filters, yoy

st.title("Marques — Benchmark")

df = load_data()
if df.empty: st.stop()
dff, meta = sidebar_filters(df)

brand_col = "marque" if "marque" in dff.columns else ("marque_key" if "marque_key" in dff.columns else None)
if not brand_col or "ca" not in dff:
    st.warning("Colonnes nécessaires manquantes pour l'analyse marques.")
    st.stop()

st.subheader("Classement Marques")
rank = dff.groupby(brand_col, as_index=False)["ca"].sum().sort_values("ca", ascending=False)
st.dataframe(rank.head(20), use_container_width=True)
st.download_button("💾 Exporter (CSV) — Classement Marques",
                   data=rank.to_csv(index=False).encode("utf-8"),
                   file_name="classement_marques.csv", mime="text/csv")

st.plotly_chart(px.bar(rank.head(15), x=brand_col, y="ca",
                       labels={brand_col:"Marque","ca":"CA (EUR)"}),
                use_container_width=True)
st.caption("👉 Les 15 premières marques sur la période filtrée.")

# YoY
if "year" in dff:
    last, prev = dff["year"].max(), dff["year"].max()-1
    yoy_df=[]
    for mk,g in dff.groupby(brand_col):
        ca_last, ca_prev = g.loc[g["year"]==last,"ca"].sum(), g.loc[g["year"]==prev,"ca"].sum()
        if ca_prev and ca_prev!=0:
            yoy_df.append({brand_col:mk, "yoy%": (ca_last/ca_prev-1)*100})
    yoy_df=pd.DataFrame(yoy_df).sort_values("yoy%",ascending=False)
    st.subheader("YoY par marque")
    st.plotly_chart(px.bar(yoy_df.head(15), x=brand_col, y="yoy%",
                           labels={brand_col:"Marque","yoy%":"YoY %"}),
                    use_container_width=True)
    st.caption("👉 Accélération (YoY) des marques les plus dynamiques.")

# Comparateur
mk_all = sorted(dff[brand_col].unique())
if mk_all:
    m1 = st.selectbox("Marque A", mk_all, 0)
    m2 = st.selectbox("Marque B", mk_all, 1 if len(mk_all)>1 else 0)
    ts = dff.groupby(["month_key", brand_col], as_index=False)["ca"].sum()
    st.plotly_chart(px.line(ts[ts[brand_col].isin([m1,m2])], x="month_key", y="ca", color=brand_col,
                            labels={"month_key":"Mois","ca":"CA (EUR)",brand_col:"Marque"}),
                    use_container_width=True)
    st.caption("👉 Comparaison temporelle de deux marques au choix.")
