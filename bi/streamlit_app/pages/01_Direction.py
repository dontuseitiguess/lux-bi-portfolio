import streamlit as st
from _shared import load_data, safe_metric_number

st.title("Direction")

df = load_data()

# Affiche la forme + 5 premières lignes pour preuve de vie
st.caption(f"Dataset : {df.shape[0]} lignes × {df.shape[1]} colonnes")
with st.expander("Aperçu (5 premières lignes)"):
    st.dataframe(df.head())

# KPIs (robustes aux colonnes manquantes)
cols = st.columns(3)
if "revenue" in df.columns:
    cols[0].metric("CA total (EUR)", safe_metric_number(df["revenue"].sum()))
else:
    cols[0].metric("CA total (EUR)", "—")

if "orders" in df.columns:
    cols[1].metric("Commandes", safe_metric_number(df["orders"].sum()))
else:
    cols[1].metric("Commandes", "—")

if "country" in df.columns:
    cols[2].metric("Pays actifs", str(df["country"].nunique()))
else:
    cols[2].metric("Pays actifs", "—")

# YoY si 'year' dispo
if "year" in df.columns and "revenue" in df.columns:
    try:
        y_max = int(df["year"].max())
        rev_cur = df.loc[df["year"] == y_max, "revenue"].sum()
        rev_prev = df.loc[df["year"] == (y_max - 1), "revenue"].sum()
        yoy = (rev_cur / rev_prev - 1) * 100 if rev_prev else None
        st.write(
            f"**YoY {y_max-1}→{y_max}** : "
            + (f"{yoy:.1f} %" if yoy is not None else "n/a (année N-1 absente)")
        )
    except Exception:
        st.write("YoY : n/a")
