import streamlit as st
import pandas as pd
import re

# Configuración de nivel hospitalario - SIMENP-FVL
st.set_page_config(page_title="SIMENP-FVL", layout="wide", page_icon="💊")

# --- ESTILOS Y LOGO ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("💊 SIMENP-FVL")
st.markdown("### *Sistema de Monitoreo Electrónico de Nutrición Parenteral*")
st.markdown("🔬 **Módulo de Farmacia Clínica y Nutrición**")
st.divider()

# --- BASE DE DATOS ASPEN 2019 ---
ESTANDARES = {
    "Adulto": {
        "Magnesio": (8, 20, "mEq/día"), "Calcio": (10, 15, "mEq/día"),
        "Fosforo": (20, 40, "mmol/día"), "Sodio": (1, 2, "mEq/kg/día"),
        "Potasio": (1, 2, "mEq/kg/día"), "Proteina": (0.8, 2.0, "g/kg/día")
    },
    "Neonato": {
        "Magnesio": (0.3, 0.5, "mEq/kg/día"), "Calcio": (2, 4, "mEq/kg/día"),
        "Fosforo": (1, 2, "mmol/kg/día"), "Sodio": (2, 5, "mEq/kg/día"),
        "Potasio": (2, 4, "mEq/kg/día"), "Proteina": (3.0, 4.0, "g/kg/día")
    }
}

FACTORES = {
    "MAGNESIO": 1.62, "SODIO": 2.0, "POTASIO": 2.0, "CALCIO": 0.46, 
    "FOSFORO": 1.0, "DEXTROSA": 3.4, "AMINOACIDOS": 4.0, "LIPIDOS": 9.0
}

# --- INTERFAZ SIDEBAR ---
with st.sidebar:
    st.header("👤 Datos del Paciente")
    nombre_paciente = st.text_input("Nombre y Apellido", "Fanny")
    tipo_pac = st.selectbox("Categoría Clínica", list(ESTANDARES.keys()))
    peso = st.number_input("Peso Actual (kg)", value=76.85, step=0.01)
    
    st.header("🧪 Laboratorios Críticos")
    col1, col2 = st.columns(2)
    with col1:
        lab_k = st.number_input("K+ (mEq/L)", 4.0)
        lab_p = st.number_input("P (mg/dL)", 3.5)
        lab_bun = st.number_input("BUN (mg/dL)", 15.0)
    with col2:
        lab_na = st.number_input("Na+ (mEq/L)", 140.0)
        lab_mg = st.number_input("Mg (mg/dL)", 2.0)
        lab_crea = st.number_input("Crea (mg/dL)", 0.8)

# --- MÓDULO SAP ---
st.subheader(f"📋 Formulación Médica: {nombre_paciente}")
texto_ejemplo = """MAGNESIO SULFATO 10
CALCIO GLUCONATO 10
GLICEROFOSFATO 20
GLUCOSA 50% 160
AMINOACIDOS 400
LIPIDOS 100
POTASIO CLORURO 30
SODIO CLORURO 30"""

sap_input = st.text_area("Pegue la orden de SAP aquí:", texto_ejemplo, height=200)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    res_list = []
    nutrientes = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0}
    vol_sumado = 0
    
    lineas = sap_input.strip().split('\n')
    for linea in lineas:
        linea_up = linea.upper()
        # Expresión regular robusta para capturar el último número (volumen)
        match = re.search(r"(\d+[\.,]?\d*)$", linea.strip())
        
        if match:
            try:
                vol = float(match.group(1).replace(',', '.'))
                vol_sumado += vol
                comp_id = None
                
                # Mapeo inteligente
                if "MAGNESIO" in linea_up: comp_id = "Magnesio"
                elif "SODIO" in linea_up or "NATROL" in linea_up: comp_id = "Sodio"
                elif "POTASIO" in linea_up or "KATROL" in linea_up: comp_id = "Potasio"
                elif "CALCIO" in linea_up: 
                    comp_id = "Calcio"
                    nutrientes["Ca_mEq"] += (vol * 0.46)
                elif "FOSFA" in linea_up or "GLICERO" in linea_up: 
                    comp_id = "Fosforo"
                    nutrientes["P_mmol"] +=
                    
