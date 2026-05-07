import streamlit as st
import pandas as pd
import re

# Configuración SIMENP-FVL v5.1
st.set_page_config(page_title="SIMENP-FVL", layout="wide", page_icon="💊")

st.title("💊 SIMENP-FVL")
st.markdown("### *Sistema de Monitoreo Electrónico de Nutrición Parenteral*")
st.markdown("🔬 **Módulo de Farmacia Clínica - Fundación Valle del Lili**")
st.divider()

# --- BASE DE DATOS ASPEN 2019 ---
ESTANDARES = {
    "Adulto": {
        "Magnesio": (8, 20, "mEq/día"), "Calcio": (10, 15, "mEq/día"),
        "Fósforo": (20, 40, "mmol/día"), "Sodio": (1, 2, "mEq/kg/día"),
        "Potasio": (1, 2, "mEq/kg/día"), "Proteína": (0.8, 2.0, "g/kg/día")
    },
    "Neonato": {
        "Magnesio": (0.3, 0.5, "mEq/kg/día"), "Calcio": (2, 4, "mEq/kg/día"),
        "Fósforo": (1, 2, "mmol/kg/día"), "Sodio": (2, 5, "mEq/kg/día"),
        "Potasio": (2, 4, "mEq/kg/día"), "Proteína": (3.0, 4.0, "g/kg/día")
    }
}

# --- INTERFAZ SIDEBAR (SIN BLOQUEOS) ---
with st.sidebar:
    st.header("👤 Datos del Paciente")
    nombre = st.text_input("Nombre y Apellido", "Fanny")
    tipo_pac = st.selectbox("Categoría Clínica", list(ESTANDARES.keys()))
    peso = st.number_input("Peso Actual (kg)", value=76.85, step=0.01, min_value=0.1)
    
    st.header("🧪 Laboratorios")
    # Se eliminaron restricciones de min_value para evitar bloqueos en paraclínicos bajos
    col1, col2 = st.columns(2)
    with col1:
        lab_k = st.number_input("K+ (mEq/L)", value=4.0, step=0.1, min_value=0.0)
        lab_p = st.number_input("P (mg/dL)", value=3.5, step=0.1, min_value=0.0)
        lab_bun = st.number_input("BUN (mg/dL)", value=15.0, step=0.1, min_value=0.0)
    with col2:
        lab_na = st.number_input("Na+ (mEq/L)", value=140.0, step=0.1, min_value=0.0)
        lab_mg = st.number_input("Mg (mg/dL)", value=2.0, step=0.1, min_value=0.0)
        lab_crea = st.number_input("Creatinina (mg/dL)", value=0.8, step=0.1, min_value=0.0)

# --- MÓDULO DE PROCESAMIENTO SAP ---
st.subheader(f"📋 Formulación: {nombre}")
sap_input = st.text_area("Pegue la orden de SAP aquí:", height=200)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    res_list = []
    nutri = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0}
    vol_total = 0
    
    lineas = sap_input.strip().split('\n')
    for linea in lineas:
        linea_up = linea.upper()
        match = re.search(r"(\d+[\.,]?\d*)$", linea.strip())
        
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_total += vol
            comp_id = None
            
            # Identificación y Factores de Conversión
            if "MAGNESIO" in linea_up: comp_id = "Magnesio"
            elif "SODIO" in linea_up or "NATROL" in linea_up: comp_id = "Sodio"
            elif "POTASIO" in linea_up or "KATROL" in linea_up: comp_id = "Potasio"
            elif "CALCIO" in linea_up: 
                comp_id = "Calcio"
                nutri["Ca_mEq"] += (vol * 0.46)
            elif "FOSFA" in linea_up or "GLICERO" in linea_up: 
                comp_id = "Fósforo"
                nutri["P_mmol"] += vol
            elif "DEXTRO" in linea_up or "GLUCOSA" in linea_up: 
                comp_id = "Dextrosa"
                nutri["Dex_g"] += (vol * 0
                
