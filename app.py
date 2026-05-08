import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v6.2 - Edición Limpia (Sin exceso de decimales)
# =========================================================

st.set_page_config(page_title="SIMENP-FVL Pro", layout="wide", page_icon="💊")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; }
    .stAlert { border-radius: 10px; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💊 SIMENP-FVL v6.2")
st.markdown("### *Sistema Integral de Monitoreo Electrónico de Nutrición Parenteral*")
st.caption("Fundación Valle del Lili - Soporte de Decisión Farmacoterapéutica (ASPEN 2019)")
st.divider()

# --- GUÍAS ASPEN 2019 ---
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

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 1. Perfil del Paciente")
    nombre_p = st.text_input("Nombre del Paciente", "Fanny")
    tipo_pac = st.selectbox("Categoría ASPEN", list(ESTANDARES.keys()))
    peso_kg = st.number_input("Peso Actual (kg)", value=76.85, step=0.01, min_value=0.1)
    
    st.header("🧪 2. Panel de Laboratorios")
    c1, c2 = st.columns(2)
    with c1:
        lab_k = st.number_input("K+ (mEq/L)", value=4.0, min_value=0.0)
        lab_p = st.number_input("P (mg/dL)", value=3.5, min_value=0.0)
        lab_bun = st.number_input("BUN (mg/dL)", value=15.0, min_value=0.0)
    with c2:
        lab_na = st.number_input("Na+ (mEq/L)", value=140.0, min_value=0.0)
        lab_mg = st.number_input("Mg (mg/dL)", value=2.0, min_value=0.0)
        lab_crea = st.number_input("Crea (mg/dL)", value=0.8, min_value=0.0)

# --- PANEL PRINCIPAL ---
st.subheader(f"📋 Análisis: {nombre_p}")
sap_input = st.text_area("Pegue líneas de SAP:", height=180)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    res_data = []
    nutri_tot = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0}
    vol_sum = 0
    
    lines = sap_input.strip().split('\n')
    for l in lines:
        l_up = l.upper()
        match = re.search(r"(\d+[\.,]?\d*)$", l.strip())
        
        if match:
            vol_val = float(match.group(1).replace(',', '.'))
            vol_sum += vol_val
            cid = None
            
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
                nutri_tot["Dex_g"] += (vol_val * 0.5)
            elif "AMINO" in l_up: 
                cid = "Proteína"
                nutri_tot["Prot_g"] += (vol_val * 0.1)
            elif "LIPID" in l_up or "SMOF" in l_up:
                cid = "Lípidos"
                nutri_tot["Lip_g"] += (vol_val * 0.2)
            
            if cid:
                f_conv = 1.62 if cid=="Magnesio" else 2.0 if cid in ["Sodio", "Potasio"] else 0.46 if cid=="Calcio" else 1.0
                total = vol_val * f_conv
                
                if cid in ESTANDARES[tipo_pac]:
                    mi, ma, un = ESTANDARES[tipo_pac][cid]
                    r_min = mi if "/kg" not in un else mi * peso_kg
                    r_max = ma if "/kg" not in un else ma * peso_kg
                    st_val = "🟢 Óptimo" if r_min <= total <= r_max else "🔴 Sobredosificado" if total > r_max else "🟡 Subdosificado"
                    
                    res_data.append({
                        "Componente": cid, "Aporte": total, 
                        "Meta ASPEN": f"{round(r_min,1)}-{round(r_max,1)}", "Estado": st_val
                    })

    if res_data:
        df_final = pd.DataFrame(res_data)
        # --- SOLUCIÓN A LOS DECIMALES: Formatear la columna 'Aporte' ---
        df_final["Aporte"] = df_final["Aporte"].map("{:.2f}".format)
        
        st.success(f"✅ Volumen Total Detectado: {round(vol_sum, 1)} mL")
        st.table(df_final)
        
        # Métricas Metabólicas
        st.subheader("🍏 Perfil Nutricional y Estabilidad")
        c_dex, c_lip, c_prot = nutri_tot["Dex_g"]*3.4, nutri_tot["Lip_g"]*9, nutri_tot["Prot_g"]*4
        t_kcal = c_dex + c_lip + c_prot
        nitrog = nutri_tot["Prot_g"] / 6.25
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            gir = (nutri_tot["Dex_g"] * 1000) / (1440 * peso_kg)
            st.metric("GIR (Oxidación)", f"{round(gir,2)}")
        with m2:
            rel_cnp_n = (c_dex + c_lip) / nitrog if nitrog > 0 else 0
            st.metric("Rel. Cal NP / N", f"{round(rel_cnp_n,1)}:1")
        with m3:
            idx = ((nutri_tot["Ca_mEq"] + nutri_tot["P_mmol"]) / vol_sum) * 1000 if vol_sum > 0 else 0
            st.metric("Índice Precipitación", f"{round(idx,1)}")
        with m4:
            st.metric("Energía Total", f"{round(t_kcal,0)} Kcal")

        with st.expander("📘 Guía de Referencia"):
            st.markdown
                    
