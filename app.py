import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v7.2 - Versión Integral con Soporte Clínico
# =========================================================

st.set_page_config(page_title="SIMENP-FVL v7.2", layout="wide", page_icon="💊")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stMetric { background-color: #ffffff; border: 1px solid #d1d8d6; border-radius: 12px; padding: 15px; }
    .stAlert { border-radius: 12px; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

st.title("💊 SIMENP-FVL v7.2")
st.markdown("#### *Monitoreo Metabólico e Infusión con Purga de Equipo*")
st.caption("🔬 Farmacia Clínica | Fundación Valle del Lili | Guías ASPEN 2019")
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

# --- SIDEBAR: DATOS DE INFUSIÓN Y CLÍNICA ---
with st.sidebar:
    st.header("👤 Perfil y Terapia")
    p_name = st.text_input("Nombre / ID", "Fanny")
    p_cat = st.selectbox("Categoría Clínica", list(ASPEN_GUIDES.keys()))
    p_weight = st.number_input("Peso (kg)", value=76.85, step=0.01, min_value=0.1)
    
    st.header("⏲️ Programación de Infusión")
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1, max_value=24)
    st.info("Fórmula: (Volumen Total - 20 mL) / Horas")
    
    st.header("🧪 Panel de Laboratorios")
    cl1, cl2 = st.columns(2)
    with cl1:
        v_k = st.number_input("K+ (mEq/L)", value=4.0)
        v_p = st.number_input("P (mg/dL)", value=3.5)
        v_bun = st.number_input("BUN (mg/dL)", value=15.0)
    with cl2:
        v_na = st.number_input("Na+ (mEq/L)", value=140.0)
        v_mg = st.number_input("Mg (mg/dL)", value=2.0)
        v_crea = st.number_input("Crea (mg/dL)", value=0.8)

# --- PANEL PRINCIPAL ---
st.subheader(f"📋 Formulación SAP: {p_name}")
sap_text = st.text_area("Pegue las líneas de SAP aquí:", height=150)

if st.button("🚀 EJECUTAR ANÁLISIS INTEGRAL", type="primary"):
    res_list = []
    nutri = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0, "K_mEq": 0, "Na_mEq": 0}
    vol_tot = 0
    
    lines = sap_text.strip().split('\n')
    for line in lines:
        up_l = line.upper()
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            cid = None
            
            if "MAGNESIO" in up_l: cid = "Magnesio"
            elif "SODIO" in up_l or "NATROL" in up_l:
                cid = "Sodio"; nutri["Na_mEq"] += (vol * 2.0)
            elif "POTASIO" in up_l or "KATROL" in up_l:
                cid = "Potasio"; nutri["K_mEq"] += (vol * 2.0)
            elif "CALCIO" in up_l: 
                cid = "Calcio"; nutri["Ca_mEq"] += (vol * 0.46)
            elif "FOSFA" in up_l or "GLICERO" in up_l: 
                cid = "Fósforo"; nutri["P_mmol"] += vol
            elif "DEXTRO" in up_l or "GLUCOSA" in up_l: 
                cid = "Dextrosa"; nutri["Dex_g"] += (vol * 0.5)
            elif "AMINO" in up_l: 
                cid = "Proteína"; nutri["Prot_g"] += (vol * 0.1)
            elif "LIPID" in up_l or "SMOF" in up_l:
                cid = "Lípidos"; nutri["Lip_g"] += (vol * 0.2)
            
            if cid:
                f_c = FACTORES_CONVERSION.get(cid.upper().replace('Ó','O').replace('Í','I'), 1.0)
                aporte = vol * f_c
                if cid in ASPEN_GUIDES[p_cat]:
                    mi, ma, un = ASPEN_GUIDES[p_cat][cid]
                    rmin = mi if "/kg" not in un else mi * p_weight
                    rmax = ma if "/kg" not in un else ma * p_weight
                    est = "🟢 Óptimo" if rmin <= aporte <= rmax else "🔴 Sobredosis" if aporte > rmax else "🟡 Subdosis"
                    res_list.append({"Componente": cid, "Aporte": aporte, "Meta ASPEN": f"{round(rmin,1)}-{round(rmax,1)}", "Estado": est})

    if res_list:
        # 1. Tabla de validación limpia
        df_show = pd.DataFrame(res_list)
        df_show["Aporte"] = df_show["Aporte"].map("{:.2f}".format)
        vol_purg = vol_tot - 20
        tasa = vol_purg / horas_inf if horas_inf > 0 else 0
        
        st.success(f"📦 Volumen Total: {round(vol_tot, 1)} mL | Tasa: {round(tasa,1)} mL/h (Post-purga)")
        st.table(df_show)
        
        # 2. Métricas de Perfil Metabólico
        st.subheader("🍏 Perfil Metabólico e Infusión")
        c_dex, c_lip, c_prot = nutri["Dex_g"]*3.4, nutri["Lip_g"]*9, nutri["Prot_g"]*4
        t_kcal = c_dex + c_lip + c_prot
        nitrog = nutri["Prot_g"] / 6.25
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            gir = (nutri["Dex_g"] * 1000) / (horas_inf * 60 * p_weight)
            st.metric("GIR (Real)", f"{round(gir,2)}", help="mg/kg/min ajustado al tiempo de goteo")
        with m2:
            rel_cnp_n = (c_dex + c_lip) / nitrog if nitrog > 0 else 0
            st.metric("Rel. Cal NP / N", f"{round(rel_cnp_n,1)}:1")
        with m3:
            idx_precip = ((nutri["Ca_mEq"] + nutri["P_mmol"]) / vol_tot) * 1000 if vol_tot > 0 else 0
            st.metric("Índice Precipitación", f"{round(idx_precip,1)}")
        with m4:
            st.metric("Energía Total", f"{round(t_kcal,0)} Kcal")

        # 3. GUÍA DE SOPORTE A LA DECISIÓN (LO QUE FALTABA)
        with st.expander("📘 Guía de Referencia: Soporte a la Decisión"):
            st.markdown(f"""
            ### Interpretación Clínica para {p_name}:
            * **GIR (mg/kg/min):** Rango meta 4-7. Un **GIR de {round(gir,2)}** indica la carga de glucosa en el tiempo seleccionado. Si es > 7 en adultos, considere reducir dextrosa.
            * **Relación Cal NP / N:** Una relación de **{round(rel_cnp_n,1)}:1** indica si las calorías protegen la síntesis de proteínas. Ideal 100:1.
            * **Índice de Precipitación:** Valor actual de **{round(idx_precip,1)}**. Si es > 35, riesgo elevado de formación de cristales de fosfato de calcio.
            * **Balance Renal:** Relación BUN/Crea > 20 ({round(v_bun/v_crea,1) if v_crea > 0 else 0}) sugiere deshidratación o carga proteica excesiva.
            * **Riesgo de Realimentación:** Si P < 2.5, se debe iniciar con 50% de la meta de dextrosa.
            """)

        # 4. Alertas de Seguridad
        st.divider()
        st.subheader("🚨 Hallazgos de Seguridad")
        if v_p < 2.5:
            st.error(f"⚠️ RIESGO DE REALIMENTACIÓN: Fósforo sérico bajo ({v_p} mg/dL).")
        if v_k >= 5.0 and nutri["K_mEq"] > 0:
            st.error(f"🚨 ALERTA CRÍTICA: Hiperpotasemia ({v_k}) con aporte activo en la mezcla.")
        if idx_precip > 35:
            st.warning(f"⚖️ ESTABILIDAD: Riesgo de precipitación Ca/P elevado ({round(idx_precip,1)}).")
    else:
        st.error("No se detectaron datos válidos en SAP.")
                                                              
