import streamlit as st
import pandas as pd
import re

# Configuración Nivel Hospitalario v4.1
st.set_page_config(page_title="NPT Pharma Monitor Pro", layout="wide", page_icon="⚕️")
st.title("⚕️ Monitor Farmacoterapéutico Integral - NPT")

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
    st.header("👤 1. Identificación y Clínica")
    nombre = st.text_input("Nombre del Paciente", "Paciente Ejemplo")
    tipo = st.selectbox("Grupo Etario", list(ESTANDARES.keys()))
    peso = st.number_input("Peso (kg)", value=76.85, step=0.01, min_value=0.1)
    
    st.header("🧪 2. Laboratorios")
    col1, col2 = st.columns(2)
    with col1:
        lab_k = st.number_input("K+ (mEq/L)", value=4.0, min_value=0.0)
        lab_p = st.number_input("P (mg/dL)", value=3.5, min_value=0.0)
        lab_bun = st.number_input("BUN (mg/dL)", value=15.0, min_value=0.0)
    with col2:
        lab_na = st.number_input("Na+ (mEq/L)", value=140.0, min_value=0.0)
        lab_mg = st.number_input("Mg (mg/dL)", value=2.0, min_value=0.0)
        lab_crea = st.number_input("Crea (mg/dL)", value=0.8, min_value=0.0)

# --- MÓDULO SAP ---
st.subheader(f"📋 Formulación: {nombre}")
st.info("💡 El Volumen Total se calculará automáticamente sumando los componentes.")
sap_input = st.text_area("Pegue líneas de SAP:", 
                         "MAGNESIO 10\nKATROL 30\nNATROL 30\nCALCIO 10\nGLICEROFOSFATO 20\nGLUCOSA 50% 160\nAMINOACIDOS 400\nLIPIDOS 100", height=200)

if st.button("🚀 EJECUTAR ANÁLISIS INTEGRAL", type="primary"):
    res_list = []
    nutrientes = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0}
    vol_calculado = 0
    
    lineas = sap_input.strip().split('\n')
    for linea in lineas:
        linea_up = linea.upper()
        # Captura el volumen (último número)
        match = re.search(r"(\d+[\.,]?\d*)$", linea.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_calculado += vol # Suma automática al volumen total
            
            comp = None
            if "MAGNESIO" in linea_up: comp = "Magnesio"
            elif "SODIO" in linea_up or "NATROL" in linea_up: comp = "Sodio"
            elif "POTASIO" in linea_up or "KATROL" in linea_up: comp = "Potasio"
            elif "CALCIO" in linea_up: 
                comp = "Calcio"
                nutrientes["Ca_mEq"] += (vol * 0.46)
            elif "FOSFA" in linea_up or "GLICERO" in linea_up: 
                comp = "Fosforo"
                nutrientes["P_mmol"] += vol
            elif "DEXTRO" in linea_up or "GLUCOSA" in linea_up: 
                comp = "Dextrosa"
                nutrientes["Dex_g"] += (vol * 0.5)
            elif "AMINO" in linea_up: 
                comp = "Proteina"
                nutrientes["Prot_g"] += (vol * 0.1)
            elif "LIPID" in linea_up or "SMOF" in linea_up:
                comp = "Lipidos"
                nutrientes["Lip_g"] += (vol * 0.2)
            
            if comp:
                # Factor de conversión para la tabla (mEq o mmol según tipo)
                f_conv = 1.62 if comp=="Magnesio" else 2.0 if (comp=="Sodio" or comp=="Potasio") else 0.46 if comp=="Calcio" else 1.0
                aporte = vol * f_conv
                
                if comp in ESTANDARES[tipo]:
                    m_min, m_max, unit = ESTANDARES[tipo][comp]
                    r_min = m_min if "/kg" not in unit else m_min * peso
                    r_max = m_max if "/kg" not in unit else m_max * peso
                    estado = "🟢 Óptimo" if r_min <= aporte <= r_max else "🔴 Sobre" if aporte > r_max else "🟡 Sub"
                    res_list.append({"Componente": comp, "Aporte": round(aporte,2), "Meta": f"{round(r_min,1)}-{round(r_max,1)}", "Estado": estado})

    if res_list:
        st.success(f"📦 Volumen Total Detectado: {round(vol_calculado, 1)} mL")
        st.table(pd.DataFrame(res_list))
        
        # --- CÁLCULOS METABÓLICOS ---
        st.subheader("⚙️ Balance y Estabilidad")
        c_dex = nutrientes["Dex_g"] * 3.4
        c_lip = nutrientes["Lip_g"] * 9.0
        c_np = c_dex + c_lip
        nitrogeno = nutrientes["Prot_g"] / 6.25
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            gir = (nutrientes["Dex_g"] * 1000) / (1440 * peso)
            st.metric("GIR (
            
