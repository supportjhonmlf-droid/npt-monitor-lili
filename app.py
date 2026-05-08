import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v7.0 - Sistema de Monitoreo Integral (Final)
# =========================================================

st.set_page_config(page_title="SIMENP-FVL v7.0", layout="wide", page_icon="💊")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stMetric { background-color: #ffffff; border: 1px solid #d1d8d6; border-radius: 12px; padding: 15px; }
    .stAlert { border-radius: 12px; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

st.title("💊 SIMENP-FVL v7.0")
st.markdown("#### *Sistema Integral de Monitoreo Electrónico de Nutrición Parenteral*")
st.caption("🔬 Farmacia Clínica | Fundación Valle del Lili | Soporte ASPEN 2019")
st.divider()

# --- GUÍAS ASPEN 2019 ---
ASPEN_GUIDES = {
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

FACTORES_CONVERSION = {
    "MAGNESIO": 1.62, "SODIO": 2.0, "POTASIO": 2.0, "CALCIO": 0.46, 
    "FOSFORO": 1.0, "PROTEINA": 0.1, "DEXTROSA": 0.5, "LIPIDOS": 0.2
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("Nombre / ID", "Fanny")
    p_cat = st.selectbox("Categoría Clínica", list(ASPEN_GUIDES.keys()))
    p_weight = st.number_input("Peso (kg)", value=76.85, step=0.01, min_value=0.1)
    
    st.header("🧪 Panel de Laboratorios")
    cl1, cl2 = st.columns(2)
    with cl1:
        v_k = st.number_input("K+ (mEq/L)", value=4.0, min_value=0.0)
        v_p = st.number_input("P (mg/dL)", value=3.5, min_value=0.0)
        v_bun = st.number_input("BUN (mg/dL)", value=15.0, min_value=0.0)
    with cl2:
        v_na = st.number_input("Na+ (mEq/L)", value=140.0, min_value=0.0)
        v_mg = st.number_input("Mg (mg/dL)", value=2.0, min_value=0.0)
        v_crea = st.number_input("Crea (mg/dL)", value=0.8, min_value=0.0)

# --- CUERPO PRINCIPAL ---
st.subheader(f"📋 Formulación SAP: {p_name}")
sap_text = st.text_area("Pegue las líneas de SAP aquí:", height=150)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    analysis_results = []
    nutri = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0, "K_mEq": 0, "Na_mEq": 0}
    calculated_vol = 0
    
    lines = sap_text.strip().split('\n')
    for line in lines:
        upper_line = line.upper()
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            calculated_vol += vol
            comp = None
            
            if "MAGNESIO" in upper_line: comp = "Magnesio"
            elif "SODIO" in upper_line or "NATROL" in upper_line:
                comp = "Sodio"; nutri["Na_mEq"] += (vol * 2.0)
            elif "POTASIO" in upper_line or "KATROL" in upper_line:
                comp = "Potasio"; nutri["K_mEq"] += (vol * 2.0)
            elif "CALCIO" in upper_line: 
                comp = "Calcio"; nutri["Ca_mEq"] += (vol * 0.46)
            elif "FOSFA" in upper_line or "GLICERO" in upper_line: 
                comp = "Fósforo"; nutri["P_mmol"] += vol
            elif "DEXTRO" in upper_line or "GLUCOSA" in upper_line: 
                comp = "Dextrosa"; nutri["Dex_g"] += (vol * 0.5)
            elif "AMINO" in upper_line: 
                comp = "Proteína"; nutri["Prot_g"] += (vol * 0.1)
            elif "LIPID" in upper_line or "SMOF" in upper_line:
                comp = "Lípidos"; nutri["Lip_g"] += (vol * 0.2)
            
            if comp:
                fact = FACTORES_CONVERSION.get(comp.upper().replace('Ó','O').replace('Í','I'), 1.0)
                total_val = vol * fact
                if comp in ASPEN_GUIDES[p_cat]:
                    mi, ma, un = ASPEN_GUIDES[p_cat][comp]
                    rmin = mi if "/kg" not in un else mi * p_weight
                    rmax = ma if "/kg" not in un else ma * p_weight
                    status = "🟢 Óptimo" if rmin <= total_val <= rmax else "🔴 Sobredosis" if total_val > rmax else "🟡 Subdosis"
                    analysis_results.append({"Componente": comp, "Aporte": total_val, "Meta ASPEN": f"{round(rmin,1)}-{round(rmax,1)}", "Estado": status})
    
    if analysis_results:
        # 1. Tabla de Aportes
        df_display = pd.DataFrame(analysis_results)
        df_display["Aporte"] = df_display["Aporte"].map("{:.2f}".format)
        st.success(f"✅ Volumen Total Calculado: {round(calculated_vol, 1)} mL")
        st.table(df_display)
        
        # 2. Métricas de Soporte
        st.subheader("🍏 Perfil Nutricional y Estabilidad")
        cal_d, cal_l, cal_p = nutri["Dex_g"]*3.4, nutri["Lip_g"]*9, nutri["Prot_g"]*4
        total_kcal = cal_d + cal_l + cal_p
        nitrog = nutri["Prot_g"] / 6.25
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            gir = (nutri["Dex_g"] * 1000) / (1440 * p_weight)
            st.metric("GIR (Oxidación)", f"{round(gir,2)}")
        with m2:
            rel_cnp_n = (cal_d + cal_l) / nitrog if nitrog > 0 else 0
            st.metric("Rel. Cal NP / N", f"{round(rel_cnp_n,1)}:1")
        with m3:
            idx_p = ((nutri["Ca_mEq"] + nutri["P_mmol"]) / calculated_vol) * 1000 if calculated_vol > 0 else 0
            st.metric("Índice Precipitación", f"{round(idx_p,1)}")
        with m4:
            st.metric("Energía Total", f"{round(total_kcal,0)} Kcal")
            
        # 3. GUÍA DE SOPORTE (RECOMENDACIONES)
        with st.expander("📘 Guía de Soporte a la Decisión Farmacoterapéutica"):
            st.markdown(f"""
            **Interpretación para {p_name}:**
            * **GIR:** Meta 4-7 mg/kg/min en adultos. Si es > 7, sugiere reducir dextrosa para evitar esteatosis hepática.
            * **Relación Cal NP / N:** Meta 100:1. Si es < 80:1, se está usando proteína como energía.
            * **Índice Ca+P:** Límite < 35. Si es mayor, riesgo de cristales en la mezcla.
            * **Balance Renal:** BUN/Crea > 20 sugiere deshidratación o exceso proteico.
            """)
            
        # 4. HALLAZGOS DE SEGURIDAD (ALERTAS)
        st.divider()
        st.subheader("🚨 Hallazgos de Seguridad Farmacoterapéutica")
        if v_p < 2.5 or v_k < 3.5:
            st.error(f"⚠️ RIESGO DE REALIMENTACIÓN: Fósforo ({v_p}) o Potasio ({v_k}) bajos. Riesgo crítico al iniciar dextrosa.")
        if v_k >= 5.0 and nutri["K_mEq"] > 0:
            st.error(f"🚨 ALERTA: Hiperpotasemia ({v_k}) con aporte activo de potasio en la mezcla.")
        if idx_p > 35:
            st.warning(f"⚖️ ESTABILIDAD: Riesgo de precipitación Ca/P elevado ({round(idx_p,1)}).")
        if v_crea > 0 and (v_bun / v_crea) > 20:
            st.warning(f"⚠️ CARGA RENAL: Relación BUN/Crea elevada ({round(v_bun/v_crea,1)}). Evaluar balance de fluidos.")
    else:
        st.error("No se detectaron datos válidos. Revise el formato de SAP.")
        
