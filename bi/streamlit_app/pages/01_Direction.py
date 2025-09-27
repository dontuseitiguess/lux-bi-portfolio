# bi/streamlit_app/pages/01_Direction.py
import streamlit as st
import pandas as pd

from _shared import load_data, safe_metric_number

st.title("Direction")

# --- 1) Charger les données ---
df = load_data()

# --- 2) Préparer les dates (à partir de month_key) ---
# month_key est de type "YYYY-MM-DD" -> on en tire l'année pour le YoY
if "month_key" in df.columns:
    # robustesse : on parse même si déjà au bon format
    df["month_key"] = pd.to_datetime(df["month_key"], errors="coerce")
    df["year"] = df["month_key"].dt.year

# --- 3) Aperçu rapide pour contrôle ---
st.caption(f"Dataset : {df.shape[0]} lignes × {df.shape[1]} colonnes")
with st.expander("Aperçu (5 premières lignes)"):
    st.dataframe(df.head())

# --- 4) KPIs clés ---
c1, c2, c3 = st.columns(3)

# CA total
if "ca" in df.columns:
    c1.metric("CA total (EUR)", safe_metric_number(df["ca"].sum()))
else:
    c1.metric("CA total (EUR)", "—")

# Unités vendues
if "unites" in df.columns:
    c2.metric("Unités vendues", safe_metric_number(df["unites"].sum()))
else:
    c2.metric("Unités vendues", "—")

# Pays actifs
if "pays_key" in df.columns:
    c3.metric("Pays actifs", str(df["pays_key"].nunique()))
else:
    c3.metric("Pays actifs", "—")

# --- 5) Croissance YoY ---
st.subheader("Croissance annuelle (YoY)")
if "year" in df.columns and "ca" in df.columns:
    try:
        y_max = int(df["year"].max())
        rev_cur = df.loc[df["year"] == y_max, "ca"].sum()
        rev_prev = df.loc[df["year"] == (y_max - 1), "ca"].sum()
        yoy = (rev_cur / rev_prev - 1) * 100 if rev_prev else None

        if yoy is not None:
            st.success(f"YoY {y_max-1}→{y_max} : **{yoy:.1f} %**")
        else:
            st.info("YoY : n/a (pas de CA l'année N-1).")
    except Exception as e:
        st.warning(f"YoY : n/a ({e})")
else:
    st.info("Impossible de calculer le YoY (colonnes manquantes : year et/ou ca).")

# --- 6) CA par année (vue rapide) ---
try:
    if "year" in df.columns and "ca" in df.columns:
        ca_by_year = (
            df.groupby("year", as_index=False)["ca"]
            .sum()
            .sort_values("year")
        )
        st.subheader("CA par année")
        st.bar_chart(ca_by_year.set_index("year"))  # simple et robuste
except Exception:
    pass

# --- 7) Notes ---
with st.expander("Notes & définitions"):
    st.markdown(
        "- **CA** : somme de la colonne `ca` (EUR).  \n"
        "- **Unités vendues** : somme de `unites`.  \n"
        "- **Pays actifs** : nombre de valeurs distinctes de `pays_key`.  \n"
        "- **YoY** : croissance du CA entre l'année N-1 et l'année N, calculée depuis `month_key`."
    )
