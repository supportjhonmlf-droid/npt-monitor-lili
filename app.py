import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v6.4 - Versión Ultra-Estable corregida
# =========================================================

st.set_page_config(page_title="SIMENP-FVL Pro", layout="wide", page_icon="💊")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; border: 1px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

st.title("💊 SIMENP-FVL v6.4")
st.markdown("### *Sistema de Soporte a la Decisión Clínica*")
st.caption("Fundación Valle del Lili - Estándares de Seguridad ASPEN 2019")
st.divider()

# --- GUÍAS DE DOSIFICACIÓN ASPEN 2019 ---
ESTANDARES = {
    "Adulto": {
        "Magnesio": (8, 20, "mEq/d"), "Calcio": (10, 15, "mEq/d"),
        "Fósforo": (20, 40, "mmol/d"), "Sodio": (1, 2, "mEq/kg/d"),
        "Potasio": (1, 2, "mEq/kg/d"), "Proteína": (0.8, 2.0, "g/kg/d")
    },
    "Neonato": {
        "Magnesio": (0.3, 0.5, "mEq/kg/d"), "Calcio": (2, 4, "mEq/kg/d"),
        "Fósforo": (1, 2, "mmol/kg/d"), "Sodio": (2, 5, "mEq/kg/d"),
        "Potasio": (2, 4, "mEq/kg/d"), "Proteína": (3.0, 4.0, "g/kg/d")
    }
}

# Factores de conversión: mEq/mL, mmol/mL o g/mL
FACTORES_DOSE = {
    "MAGNESIO": 1.62, "SODIO": 2.0, "POTASIO": 2.0, "CALCIO": 0.46, 
    "FOSFORO": 1.0, "PROTEINA": 0.1, "DEXTROSA": 0.5, "LIPIDOS": 0.2
}

# --- SIDEBAR: ENTRADA DE DATOS ---
with st.sidebar:
    st.header("👤 1. Perfil")
    nombre_p = st.text_input("Paciente", "Fanny")
    tipo_pac = st.selectbox("Guía ASPEN", list(ESTANDARES.keys()))
    peso_kg = st.number_input("Peso (kg)", value=76.85, min_value=0.1)
    
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

# --- PANEL PRINCIPAL ---
st.subheader(f"📋 Formulación SAP: {nombre_p}")
sap_input = st.text_area("Pegue las líneas de SAP aquí:", height=180)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    res_data = []
    nutri = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0}
    vol_sum = 0
    
    lines = sap_input.strip().split('\n')
    for l in lines:
        l_up = l.upper()
        match = re.search(r"(\d+[\.,]?\d*)$", l.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_sum += vol
            cid = None
            
            if "MAGNESIO" in l_up: cid = "Magnesio"
            elif "SODIO" in l_up or "NATROL" in l_up: cid = "Sodio"
            elif "POTASIO" in l_up or "KATROL" in l_up: cid = "Potasio"
            elif "CALCIO" in l_up: 
                cid = "Calcio"
                nutri["Ca_mEq"] += (vol * 0.46)
            elif "FOSFA" in l_up or "GLICERO" in l_up: 
                cid = "Fósforo"
                nutri["P_mmol"] += vol
            elif "DEXTRO" in l_up or "GLUCOSA" in l_up: 
                cid = "Dextrosa"
                nutri["Dex_g"] += (vol * 0.5)
            elif "AMINO" in l_up: 
                cid = "Proteína"
                nutri["Prot_g"] += (vol * 0.1)
            elif "LIPID" in l_up or "SMOF" in l_up:
                cid = "Lípidos"
                nutri["Lip_g"] += (vol * 0.2)
            
            if cid:
                f_c = FACTORES_DOSE.get(cid.upper().replace('Ó','O').replace('Í','I'), 1.0)
                aporte = vol * f_c
                if cid in ESTANDARES[tipo_pac]:
                    mi, ma, un = ESTANDARES[tipo_pac][cid]
                    r_min = mi if "/kg" not in un else mi * peso_kg
                    r_max = ma if "/kg" not in un else ma * peso_kg
                    st_val = "🟢 Óptimo" if r_min <= aporte <= r_max else "🔴 Sobredosis" if aporte > r_max else "🟡 Subdosis"
                    res_data.append({"Componente": cid, "Aporte": aporte, "Meta": f"{round(r_min,1)}-{round(r_max,1)}", "Estado": st_val})

    if res_data:
        df_f = pd.DataFrame(res_data)
        df_f["Aporte"] = df_f["Aporte"].map("{:.2f}".format)
        st.success(f"✅ Volumen Total: {round(vol_sum, 1)} mL")
        st.table(df_f)
        
        # --- CÁLCULOS METABÓLICOS ---
        c_dex, c_lip, c_prot = nutri["Dex_g"]*3.4, nutri["Lip_g"]*9, nutri["Prot_g"]*4
        total_kcal = c_dex + c_lip + c_prot
        nitrog = nutri["Prot_g"] / 6.25
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            gir = (nutri["Dex_g"] * 1000) / (1440 * peso_kg)
            st.metric("GIR (Oxidación)", f"{round(gir,2)}")
        with m2:
            rel_cnp_n = (c_dex + c_lip) / nitrog if nitrog > 0 else 0
            st.metric("Rel. Cal NP / N", f"{round(rel_cnp_n,1)}:1")
        with m3:
            idx = ((nutri["Ca_mEq"] + nutri["P_mmol"]) / vol_sum) * 1000 if vol_sum > 0 else 0
            st.metric("Índice Ca+P", f"{round(idx,1)}")
        with m4:
            st.metric("Total Kcal", f"{round(total_kcal,0)}")

        # --- GUÍA DE SOPORTE A LA DECISIÓN ---
        with st.expander("📘 Guía de Soporte a la Decisión"):
            st.markdown("""
            * **GIR (mg/kg/min):** Meta 4-7. Si > 7, riesgo de esteatosis hepática e hiperglucemia.
            * **Relación Cal NP / N:** Meta 100:1 (anabolismo). Si < 80:1, riesgo de usar proteína como energía.
            * **Índice Ca+P (mEq+mmol/L):** Mantener < 35 para evitar precipitación en la bolsa.
            * **BUN/Creatinina:** Relación > 20:1 sugiere deshidratación o exceso proteico.
            * **Refeeding:** P < 2.5 indica riesgo crítico al iniciar dextrosa.
            """)

        # --- ALERTAS ---
        st.divider()
        st.subheader("🚨 Hallazgos de Seguridad")
        if lab_p < 2.5:
            st.error(f"⚠️ RIESGO DE REALIMENTACIÓN: Fósforo bajo ({lab_p} mg/dL).")
        if lab_k >= 5.0 and any(d['Componente'] == "Potasio" for d in res_data):
            st.error("🚨 ALERTA CRÍTICA: Hiperpotasemia con aporte de potasio en la mezcla.")
        if idx > 35:
            st.warning(f"⚖️ RIESGO DE PRECIPITACIÓN: Índice Ca+P elevado ({round(idx,1)}).")
    else:
        st.error("No se detectaron datos válidos. Revise el formato de SAP.")
            
