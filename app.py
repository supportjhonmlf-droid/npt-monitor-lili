import streamlit as st
import pandas as pd
import re

# Configuración de nivel hospitalario - SIMENP-FVL
st.set_page_config(page_title="SIMENP-FVL Pro", layout="wide", page_icon="💊")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stAlert { border-radius: 10px; }
    .stMetric { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💊 SIMENP-FVL v6.0")
st.markdown("### *Sistema Integral de Monitoreo Electrónico de Nutrición Parenteral*")
st.caption("Fundación Valle del Lili - Basado en Guías ASPEN 2019")
st.divider()

# --- DATOS TÉCNICOS ASPEN 2019 ---
# Fuente:
ESTANDARES = {
    "Adulto": {
        "Magnesio": (8, 20, "mEq/d"), "Calcio": (10, 15, "mEq/d"),
        "Fósforo": (20, 40, "mmol/d"), "Sodio": (1, 2, "mEq/kg/d"),
        "Potasio": (1, 2, "mEq/kg/d"), "Proteína": (0.8, 2.0, "g/kg/d")
    },
    "Neonato Pretérmino": {
        "Magnesio": (0.3, 0.5, "mEq/kg/d"), "Calcio": (2, 4, "mEq/kg/d"),
        "Fósforo": (1, 2, "mmol/kg/d"), "Sodio": (2, 5, "mEq/kg/d"),
        "Potasio": (2, 4, "mEq/kg/d"), "Proteína": (3.0, 4.0, "g/kg/d")
    },
    "Infante/Niño (<50kg)": {
        "Magnesio": (0.3, 0.5, "mEq/kg/d"), "Calcio": (0.5, 4, "mEq/kg/d"),
        "Fósforo": (0.5, 2, "mmol/kg/d"), "Sodio": (2, 5, "mEq/kg/d"),
        "Potasio": (2, 4, "mEq/kg/d"), "Proteína": (1.5, 3.0, "g/kg/d")
    }
}

FACTORES = {
    "MAGNESIO": 1.62, "SODIO": 2.0, "POTASIO": 2.0, "CALCIO": 0.46, 
    "FOSFORO": 1.0, "DEXTROSA": 3.4, "AMINOACIDOS": 4.0, "LIPIDOS": 9.0
}

# --- INTERFAZ: ENTRADA DE DATOS ---
with st.sidebar:
    st.header("👤 1. Información del Paciente")
    nombre = st.text_input("Nombre Completo", "Fanny")
    tipo_pac = st.selectbox("Grupo Etario (ASPEN)", list(ESTANDARES.keys()))
    peso = st.number_input("Peso Actual (kg)", value=76.85, step=0.01, min_value=0.1)
    
    st.header("🧪 2. Panel de Laboratorios")
    col1, col2 = st.columns(2)
    with col1:
        lab_k = st.number_input("K+ (mEq/L)", value=4.0, min_value=0.0)
        lab_p = st.number_input("P (mg/dL)", value=3.5, min_value=0.0)
        lab_bun = st.number_input("BUN (mg/dL)", value=15.0, min_value=0.0)
    with col2:
        lab_na = st.number_input("Na+ (mEq/L)", value=140.0, min_value=0.0)
        lab_mg = st.number_input("Mg (mg/dL)", value=2.0, min_value=0.0)
        lab_crea = st.number_input("Crea (mg/dL)", value=0.8, min_value=0.0)

# --- CUERPO PRINCIPAL ---
st.subheader(f"📋 Formulación SAP: {nombre}")
sap_input = st.text_area("Pegue la orden de SAP aquí:", height=180, 
                         placeholder="Ejemplo:\nMAGNESIO SULFATO 10\nKATROL 30\nNATROL 30\n...")

if st.button("🚀 EJECUTAR SEGUIMIENTO INTEGRAL", type="primary"):
    res_data = []
    nutri = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0}
    vol_calc = 0
    
    lineas = sap_input.strip().split('\n')
    for linea in lineas:
        linea_up = linea.upper()
        match = re.search(r"(\d+[\.,]?\d*)$", linea.strip())
        
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_calc += vol
            c_id = None
            
            # Identificación de Componentes
            if "MAGNESIO" in linea_up: c_id = "Magnesio"
            elif "SODIO" in linea_up or "NATROL" in linea_up: c_id = "Sodio"
            elif "POTASIO" in linea_up or "KATROL" in linea_up: c_id = "Potasio"
            elif "CALCIO" in linea_up: 
                c_id = "Calcio"
                nutri["Ca_mEq"] += (vol * 0.46)
            elif "FOSFA" in linea_up or "GLICERO" in linea_up: 
                c_id = "Fósforo"
                nutri["P_mmol"] += vol
            elif "DEXTRO" in linea_up or "GLUCOSA" in linea_up: 
                c_id = "Dextrosa"
                nutri["Dex_g"] += (vol * 0.5) # Asumiendo DAD 50%
            elif "AMINO" in linea_up: 
                c_id = "Proteína"
                nutri["Prot_g"] += (vol * 0.1) # Asumiendo Solución 10%
            elif "LIPID" in linea_up or "SMOF" in linea_up:
                c_id = "Lípidos"
                nutri["Lip_g"] += (vol * 0.2) # Asumiendo Emulsión 20%
            
            if c_id:
                f = 1.62 if c_id=="Magnesio" else 2.0 if c_id in ["Sodio", "Potasio"] else 0.46 if c_id=="Calcio" else 1.0
                total = vol * f
                
                if c_id in ESTANDARES[tipo_pac]:
                    mi, ma, un = ESTANDARES[tipo_pac][c_id]
                    r_min = mi if "/kg" not in un else mi * peso
                    r_max = ma if "/kg" not in un else ma * peso
                    status = "🟢 Óptimo" if r_min <= total <= r_max else "🔴 Sobre" if total > r_max else "🟡 Sub"
                    res_data.append({"Componente": c_id, "Aporte": round(total, 2), "Meta ASPEN": f"{round(r_min,1)}-{round(r_max,1)}", "Estado": status})

    if res_data:
        st.success(f"📦 Volumen Total Detectado: {round(vol_calc, 1)} mL")
        st.table(pd.DataFrame(res_data))
        
        # --- CÁLCULOS METABÓLICOS Y ESTABILIDAD ---
        st.subheader("🍏 Perfil Nutricional y Seguridad Físico-Química")
        c_dex, c_lip, c_prot = nutri["Dex_g"]*3.4, nutri["Lip_g"]*9, nutri["Prot_g"]*4
        total_kcal = c_dex + c_lip + c_prot
        n_g = nutri["Prot_g"] / 6.25
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            gir = (nutri["Dex_g"] * 1000) / (1440 * peso)
            st.metric("GIR", f"{round(gir,2)}", help="Tasa de Oxidación de Glucosa (mg/kg/min)")
        with col_m2:
            rel_cnp_n = (c_dex + c_lip) / n_g if n_g > 0 else 0
            st.metric("Rel. Cal NP / N", f"{round(rel_cnp_n,1)}:1")
        with col_m3:
            idx_precip = ((nutri["Ca_mEq"] + nutri["P_mmol"]) / vol_calc) * 1000 if vol_calc > 0 else 0
            st.metric("Índice Precipitación", f"{round(idx_precip,1)}", help="Suma de Ca + P por litro")
        with col_m4:
            st.metric("Total Kcal", f"{round(total_kcal,0)}")

        # --- ALERTAS DE SEGURIDAD (CRUCE DE DATOS) ---
        st.divider()
        st.subheader("🚨 Diagnóstico Farmacoterapéutico")
        
        # 1. Alertas de Realimentación (Refeeding)
        if lab_p < 2.5 or lab_k < 3.5 or lab_mg < 1.7:
            st.error(f"⚠️ RIESGO DE REALIMENTACIÓN: Electrólitos intracelulares bajos (P: {lab_p}, K: {lab_k}, Mg: {lab_mg}). Iniciar dextrosa con precaución.")
        
        # 2. Alertas Renales y de Hidratación
        if lab_crea > 0:
            rel_bc = lab_bun / lab_crea
            if rel_bc > 20:
                st.warning(f"⚠️ Relación BUN/Crea elevada ({round(rel_bc,1)}): Sugiere deshidratación o carga proteica excesiva.")
        
        # 3. Alertas de Electrólitos vs NPT
        if lab_k >= 5.0 and any(d['Componente'] == "Potasio" for d in res_data):
            st.error(f"🚨 ALERTA DE SEGURIDAD: Paciente con hiperpotasemia ({lab_k}) recibiendo aporte de potasio en la mezcla.")
        
        if lab_na >= 148 and any(d['Componente'] == "Sodio" for d in res_data):
            st.warning(f"⚠️ HIPERNATREMIA: Sodio en {lab_na}. Evaluar reducción de Natrol.")
                    # 4. Alerta de Estabilidad
        if idx_precip > 35:
            st.error("🚨 CRÍTICO: Riesgo de precipitación de Fosfato de Calcio. Supera el umbral de seguridad de 35 mEq+mmol/L.")
    else:
        st.error("No se detectaron datos procesables en la formulación.")
        
