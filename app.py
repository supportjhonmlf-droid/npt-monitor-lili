import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v10.3 - Soporte de Decisión Clínica Robusto
# =========================================================

st.set_page_config(page_title="SIMENP Professional", layout="wide", page_icon="🧪")

# --- GUÍAS TÉCNICAS (ASPEN / ESPEN / ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir_max": 5.0, "lip": 1.5, "aaf": 100},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir_max": 4.0, "lip": 1.0, "aaf": 100},
    "Obesidad (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir_max": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir_max": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir_max": 10.0, "lip": 2.5, "aaf": 150}
}

# Factores de conversión SAP (v8.1 base + robustez) - CORREGIDO
SAP_CONV = {
    "Magnesio": {"f": 1.62, "u": "mEq", "kw": ["MAGNESIO", "MG"]},
    "Sodio": {"f": 2.0, "u": "mEq", "kw": ["SODIO", "NA"]},
    "Potasio": {"f": 2.0, "u": "mEq", "kw": ["POTASIO", "K"]},
    "Calcio": {"f": 0.46, "u": "mEq", "kw": ["CALCIO", "CA"]},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw": ["FOSFORO", "FÓSFORO", "P"]},
    "Dextrosa": {"f": 0.5, "u": "g", "kw": ["DEXTROSA", "GLUCOSA"]},
    "Proteína": {"f": 0.1, "u": "g", "kw": ["AMINOACIDO", "AMINOÁCIDO", "PROTEINA", "PROTEÍNA"]},
    "Lípidos": {"f": 0.2, "u": "g", "kw": ["LIPIDO", "LÍPIDO", "SMOF", "INTRALIPID"]}
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("Nombre / ID", "Paciente 01")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    horas_inf = st.number_input("Horas de goteo", value=24, min_value=1)
    
    st.header("🔬 Monitorización")
    v_p = st.number_input("P sérico (mg/dL)", value=3.5)
    v_tg = st.number_input("TG séricos (mg/dL)", value=150.0)
    v_glu = st.number_input("Gl
    
