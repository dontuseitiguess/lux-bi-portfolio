# bi/streamlit_app/pages/05_Tendances.py (STUB TEMPORAIRE)
import streamlit as st
import pandas as pd
from pathlib import Path

st.title("Tendances (diagnostic)")
st.success("Le fichier 05_Tendances.py est chargé sans erreur de syntaxe.")

# Montre la présence d'un CSV Trends si dispo (pour confirmer le chemin)
candidates = [
    Path(__file__).resolve().parents[1] / "data" / "processed" / "google_trends.csv",
    Path(__file__).resolve().parents[2] / "data" / "processed" / "google_trends.csv",
    Path.cwd() / "data" / "processed" / "google_trends.csv",
    Path(__file__).resolve().parents[1] / "data" / "raw" / "google_trends.csv",
    Path(__file__).resolve().parents[2] / "data" / "raw" / "google_trends.csv",
    Path.cwd() / "data" / "raw" / "google_trends.csv",
]
paths = [str(p) for p in candidates if p.exists()]
st.write("CSV Trends détectés :", paths if paths else "(aucun)")

