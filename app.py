import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v6.1 - Sistema Integral de Monitoreo
# Módulo de Farmacia Clínica y Mezclas Parenterales
# =========================================================

st.set_page_config(page_title="SIMENP-FVL Pro", layout="wide", page_icon="💊")

# --- ESTILOS VISUALES PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; }
    .stAlert { border-radius: 10px; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💊 SIMENP-FVL v6.1")
st.markdown("### *Sistema Integral de Monitoreo Electrónico de Nutrición Parenteral*")
st.caption("Fundación Valle del Lili - Soporte de Decisión Farmacoterapéutica (ASPEN 2019)")
st.divider()

# --- BASE DE DATOS TÉCNICA (Guías ASPEN 2019) ---
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

# --- BARRA LATERAL: ENTRADA DE DATOS CLÍNICOS ---
with st.sidebar:
    st.header("👤 1. Perfil del Paciente")
    nombre_p = st.text_input("Nombre del Paciente", "Fanny")
    tipo_pac = st.selectbox("Categoría de Guía (ASPEN)", list(ESTANDARES.keys()))
    peso_kg = st.number_input("Peso Actual (kg)", value=76.85, step=0.01, min_value=0.1)
    
    st.header("🧪 2. Panel de Laboratorios")
    st.caption("El sistema validará riesgos de seguridad con estos valores.")
    c1, c2 = st.columns(2)
    with c1:
        lab_k = st.number_input("K+ (mEq/L)", value=4.0, min_value=0.0)
        lab_p = st.number_input("P (mg/dL)", value=3.5, min_value=0.0)
        lab_bun = st.number_input("BUN (mg/dL)", value=15.0, min_value=0.0)
    with c2:
        lab_na = st.number_input("Na+ (mEq/L)", value=140.0, min_value=0.0)
        lab_mg = st.number_input("Mg (mg/dL)", value=2.0, min_value=0.0)
        lab_crea = st.number_input("Crea (mg/dL)", value=0.8, min_value=0.0)

# --- PANEL PRINCIPAL: FORMULACIÓN ---
st.subheader(f"📋 Análisis de Formulación: {nombre_p}")
sap_input = st.text_area("Pegue las líneas de SAP aquí (El volumen debe estar al final):", height=200,
                         placeholder="Ejemplo:\nMAGNESIO SULFATO 10\nKATROL 30\nNATROL 30\n...")

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    val_results = []
    nutri_tot = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0}
    vol_sum = 0
    
    # Procesamiento de líneas
    lines = sap_input.strip().split('\n')
    for l in lines:
        l_up = l.upper()
        # Regex para capturar el volumen al final de la línea (acepta puntos y comas)
        match = re.search(r"(\d+[\.,]?\d*)$", l.strip())
        
        if match:
            vol_val = float(match.group(1).replace(',', '.'))
            vol_sum += vol_val
            cid = None
            
            # Clasificación de componentes para cálculos de seguridad
            if "MAGNESIO" in l_up: cid = "Magnesio"
            elif "SODIO" in l_up or "NATROL" in l_up: cid = "Sodio"
            elif "POTASIO" in l_up or "KATROL" in l_up: cid = "Potasio"
            elif "CALCIO" in l_up: 
                cid = "Calcio"
                nutri_tot["Ca_mEq"] += (vol_val * 0.46)
            elif "FOSFA" in l_up or "GLICERO" in l_up: 
                cid = "Fósforo"
                nutri_tot["P_mmol"] += vol_val
            elif "DEXTRO" in l_up or "GLUCOSA" in l_up: 
                cid = "Dextrosa"
                nutri_tot["Dex_g"] += (vol_val * 0.5) # Asumiendo DAD 50%
            elif "AMINO" in l_up: 
                cid = "Proteína"
                nutri_tot["Prot_g"] += (vol_val * 0.1) # Asumiendo AA 10%
            elif "LIPID" in l_up or "SMOF" in l_up:
                cid = "Lípidos"
                nutri_tot["Lip_g"] += (vol_val * 0.2) # Asumiendo Emulsión 20%
            
            if cid:
                # Factores: Mg(1.62), Na/K(2.0), Ca(0.46)
                f_conv = 1.62 if cid=="Magnesio" else 2.0 if cid in ["Sodio", "Potasio"] else 0.46 if cid=="Calcio" else 1.0
                aporte_actual = vol_val * f_conv
                
                if cid in ESTANDARES[tipo_pac]:
                    min_a, max_a, unit_a = ESTANDARES[tipo_pac][cid]
                    range_min = min_a if "/kg" not in unit_a else min_a * peso_kg
                    range_max = max_a if "/kg" not in unit_a else max_a * peso_kg
                    
                    if aporte_actual < range_min: est = "🟡 Subdosificado"
                    elif aporte_actual > range_max: est = "🔴 Sobredosificado"
                    else: est = "🟢 Óptimo"
                    
                    val_results.append({
                        "Componente": cid, "Aporte": round(aporte_actual, 2), 
                        "Meta ASPEN": f"{round(range_min,1)}-{round(range_max,1)}", "Estado": est
                    })

    if val_results:
        # 1. Tabla de validación
        st.success(f"✅ Volumen Total de Mezcla: {round(vol_sum, 1)} mL")
        st.table(pd.DataFrame(val_results))
        
        # 2. Métricas Metabólicas y Estabilidad
        st.subheader("🍏 Perfil Nutricional y Estabilidad")
        cal_d, cal_l, cal_p = nutri_tot["Dex_g"]*3.4, nutri_tot["Lip_g"]*9, nutri_tot["Prot_g"]*4
        t_kcal = cal_d + cal_l + cal_p
        nitrog = nutri_tot["Prot_g"] / 6.25
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            gir_val = (nutri_tot["Dex_g"] * 1000) / (1440 * peso_kg)
            st.metric("GIR (Oxidación)", f"{round(gir_val,2)}", help="mg/kg/min de glucosa")
        with m2:
            rel_cnp_n = (cal_d + cal_l) / nitrog if nitrog > 0 else 0
            st.metric("Rel. Cal NP / N", f"{round(rel_cnp_n,1)}:1")
        with m3:
            # Índice de Precipitación Ca+P
            idx_precip = ((nutri_tot["Ca_mEq"] + nutri_tot["P_mmol"]) / vol_sum) * 1000 if vol_sum > 0 else 0
            st.metric("Índice Precipitación", f"{round(idx_precip,1)}", help="Sumatoria Ca + P por Litro")
        with m4:
            st.metric("Energía Total", f"{round(t_kcal,0)} Kcal")

        # --- SECCIÓN: GUÍA DE REFERENCIA (ADICIÓN) ---
        with st.expander("📘 Guía de Referencia: Seguridad y Estabilidad"):
            st.markdown("""
            ### 1. Tasa de Oxidación de Glucosa (GIR)
            * **Rango Recomendado (Adultos):** 4 - 7 mg/kg/min.
            * **Significado:** Evalúa la capacidad metabólica del hígado para procesar la glucosa.
            * **Riesgos:** Un GIR > 7 en adultos se asocia a **hiperglucemia y esteatosis hepática**.

            ### 2. Relación Calorías No Proteicas / Nitrógeno (CNP:N)
            * **Pacientes Críticos:** 80:1 a 100:1.
            * **Pacientes Estables:** 100:1 a 150:1.
            * **Significado:** Indica si el aporte de energía es suficiente para preservar la proteína.

            ### 3. Estabilidad Físico-Química (Índice Ca + P)
            * **Límite de Seguridad:** < 35 - 45 (sumatoria de mEq/L de Ca + mmol/L de P).
            * **Significado:** Predice el riesgo de formación de cristales de fosfato cálcico.
            * **Recomendación:** Si el índice supera 35, valide con las curvas de solubilidad.

            ### 4. Función Renal (BUN/Creatinina)
            * **Relación > 20:1:** Sugiere deshidratación o carga de proteínas superior a la capacidad renal.
            """)

        # 3. Diagnóstico Farmacoterapéutico
        st.divider()
        st.subheader("🚨 Hallazgos de Seguridad")
        
        # Alertas de Realimentación
        if lab_p < 2.5 or lab_k < 3.5 or lab_mg < 1.7:
            st.error(f"⚠️ RIESGO DE REALIMENTACIÓN: Electrólitos críticos bajos (P: {lab_p}, K: {lab_k}, Mg: {lab_mg}). Riesgo detectado según guías ASPEN.")
        
        # Alertas de Estabilidad
        if idx_precip > 35:
            st.error(f"🚨 CRÍTICO: El Índice de Precipitación ({round(idx_precip,1)}) es elevado. Riesgo de cristales de Ca/P en la bolsa.")
            
        # Alertas Renales
        if lab_crea > 0:
            rel_bc = lab_bun / lab_crea
            if rel_bc > 20:
                st.warning(f"⚠️ Relación BUN/Crea elevada ({round(rel_bc,1)}): Sugiere deshidratación o balance proteico a ajustar.")
        
        # Alertas de Cruce K+
        if lab_k >= 5.0 and any(d['Componente'] == "Potasio" for d in val_results):
            st.error(f"🚨 ALERTA: Paciente con hiperpotasemia ({lab_k}) recibiendo potasio en la NPT. Evaluar retiro de Katrol.")

    else:
        st.error("No se detectaron datos procesables. Verifique que el volumen esté al final de cada línea en SAP.")
        
