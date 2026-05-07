import streamlit as st
import pandas as pd
import re

# Configuración de nivel hospitalario
st.set_page_config(page_title="Monitor Farmacoterapéutico NPT Pro", layout="wide", page_icon="⚕️")

# --- BASE DE DATOS ASPEN 2019 ---
# Formato: (Min, Max, Unidad)
ESTANDARES = {
    "Adulto": {
        "Magnesio": (8, 20, "mEq/día"), "Calcio": (10, 15, "mEq/día"),
        "Fosforo": (20, 40, "mmol/día"), "Sodio": (1, 2, "mEq/kg/día"),
        "Potasio": (1, 2, "mEq/kg/día"), "Proteina": (0.8, 2.0, "g/kg/día")
    },
    "Neonato Pretermino": {
        "Magnesio": (0.3, 0.5, "mEq/kg/día"), "Calcio": (2, 4, "mEq/kg/día"),
        "Fosforo": (1, 2, "mmol/kg/día"), "Sodio": (2, 5, "mEq/kg/día"),
        "Potasio": (2, 4, "mEq/kg/día"), "Proteina": (3.0, 4.0, "g/kg/día")
    },
    "Infante/Niño (<50kg)": {
        "Magnesio": (0.3, 0.5, "mEq/kg/día"), "Calcio": (0.5, 4, "mEq/kg/día"),
        "Fosforo": (0.5, 2, "mmol/kg/día"), "Sodio": (2, 5, "mEq/kg/día"),
        "Potasio": (2, 4, "mEq/kg/día"), "Proteina": (1.5, 3.0, "g/kg/día")
    }
}

FACTORES = {
    "MAGNESIO": 1.62, "SODIO": 2.0, "POTASIO": 2.0, "CALCIO": 0.46, 
    "FOSFORO": 1.0, "DEXTROSA": 0.5, "AMINOACIDOS": 0.1
}

# --- INTERFAZ: SIDEBAR ---
with st.sidebar:
    st.header("👤 1. Perfil del Paciente")
    tipo = st.selectbox("Grupo Etario (Guías ASPEN)", list(ESTANDARES.keys()))
    peso = st.number_input("Peso Actual (kg)", min_value=0.1, value=70.0 if "Adulto" in tipo else 1.5)
    
    st.header("🧪 2. Panel de Laboratorios")
    col1, col2 = st.columns(2)
    with col1:
        lab_k = st.number_input("K+ (mEq/L)", 4.0)
        lab_p = st.number_input("P (mg/dL)", 3.5)
        lab_bun = st.number_input("BUN (mg/dL)", 15.0)
    with col2:
        lab_na = st.number_input("Na+ (mEq/L)", 140.0)
        lab_mg = st.number_input("Mg (mg/dL)", 2.0)
        lab_crea = st.number_input("Creatinina (mg/dL)", 0.8)

# --- CUERPO PRINCIPAL ---
st.title("⚕️ Monitor de Seguimiento NPT Avanzado")
st.info("Sistema de validación clínica basado en guías ASPEN 2019.")

st.subheader("📋 3. Formulación Médica (SAP)")
sap_input = st.text_area("Pegue las líneas de SAP aquí:", "MAGNESIO 2G/10ML 20\nKATROL 10\nNATROL 15\nDEXTROSA 50% 120", height=150)

if st.button("🚀 Ejecutar Análisis Integral"):
    lineas = sap_input.strip().split('\n')
    data_analisis = []
    totales = {"Dextrosa": 0}
    
    for linea in lineas:
        linea = linea.upper()
        match = re.search(r"(\d+\.?\d*)$", linea.strip())
        if match:
            vol = float(match.group(1))
            comp = None
            if "MAGNESIO" in linea: comp = "Magnesio"
            elif "SODIO" in linea or "NATROL" in linea: comp = "Sodio"
            elif "POTASIO" in linea or "KATROL" in linea: comp = "Potasio"
            elif "CALCIO" in linea: comp = "Calcio"
            elif "FOSFA" in linea: comp = "Fosforo"
            elif "DEXTRO" in linea: comp = "Dextrosa"
            elif "AMINO" in linea: comp = "Proteina"

            if comp:
                f = FACTORES.get(comp.upper(), 1.0)
                aporte = vol * f
                if comp == "Dextrosa": totales["Dextrosa"] += aporte
                
                if comp in ESTANDARES[tipo]:
                    m_min, m_max, unit = ESTANDARES[tipo][comp]
                    r_min = m_min if "/kg" not in unit else m_min * peso
                    r_max = m_max if "/kg" not in unit else m_max * peso
                    
                    if aporte < r_min: estado = "🟡 Subdosificado"
                    elif aporte > r_max: estado = "🔴 Sobredosificado"
                    else: estado = "🟢 Óptimo"
                    
                    data_analisis.append({
                        "Componente": comp, "Aporte Total": f"{round(aporte, 2)} {unit.split('/')[0]}",
                        "Rango Recomendado": f"{round(r_min,1)} - {round(r_max,1)}", "Estado": estado
                    })

    if data_analisis:
        st.subheader("📊 Resultados vs Requerimientos ASPEN")
        st.table(pd.DataFrame(data_analisis))
        
        # --- MÓDULO DE ALERTAS DE SEGURIDAD ---
        st.subheader("🚨 Alertas de Seguridad Farmacoterapéutica")
        col_a, col_b = st.columns(2)
        
        with col_a:
            # Riesgo de Realimentación
            if lab_p < 2.5 or lab_k < 3.5 or lab_mg < 1.7:
                st.error("⚠️ RIESGO DE SÍNDROME DE REALIMENTACIÓN: Electrólitos intracelulares bajos. Iniciar NPT con precaución y monitoreo estricto.")
            
            # Relación BUN/Creatinina
            if lab_crea > 0:
                rel = lab_bun / lab_crea
                if rel > 20:
                    st.warning(f"⚠️ Relación BUN/Crea elevada ({round(rel,1)}). Evaluar deshidratación o carga proteica excesiva.")

        with col_b:
            # Cálculo de GIR
            if totales["Dextrosa"] > 0:
                gir = (totales["Dextrosa"] * 1000) / (1440 * peso)
                st.info(f"💡 Tasa de Infusión de Glucosa (GIR): {round(gir, 2)} mg/kg/min")
                if gir > 12: st.error("🚨 GIR Crítico: Riesgo de hiperglucemia y esteatosis.")
            
            # Compatibilidad Ca/P
            if any(d['Componente'] == "Calcio" for d in data_analisis) and any(d['Componente'] == "Fosforo" for d in data_analisis):
                st.warning("⚖️ COMPATIBILIDAD: Se detectó aporte conjunto de Ca y P. Verificar curvas de solubilidad para evitar precipitación.")
    else:
        st.error("No se detectaron datos válidos en el texto de SAP. Verifique el formato.")
        
