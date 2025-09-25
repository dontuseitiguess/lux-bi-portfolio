# --- bootstrap sys.path pour trouver _shared.py depuis /pages ---
import os, sys
APP_DIR = os.path.dirname(os.path.dirname(__file__))  # .../bi/streamlit_app
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
# ----------------------------------------------------------------
from _shared import load_data


import streamlit as st
st.set_page_config(page_title="Direction", layout="wide")
st.title("Direction – Vue exécutive")
st.write("✅ Page minimale OK (test)")
