import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v8.1 - Base de Datos Actualizada (Nulanza/Paditrace)
# =========================================================

st.set_page_config(
    page_title="SIMENP-FVL Pro", 
    layout="wide", 
    page_icon="https://cdn-icons-png.flaticon.com/512/3063/3063822.png"
)

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stMetric { background-color: #ffffff; border: 1px solid #d1d8d6; border-radius: 12px; padding: 15px; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 12px; border: 1px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥗 SIMENP-FVL v8.1")
st.markdown("#### *Sistema de Monitoreo Integral y Soporte a la Decisión*")
st.caption("🔬 Farmacia Clínica | Soporte ASPEN 2019 | Purga: 20 mL")
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

# Configuración de Unidades y Factores
COMP_META = {
    "Magnesio": {"f": 1.62, "u": "mEq"}, "Sodio": {"f": 2.0, "u": "mEq"},
    "Potasio": {"f": 2.0, "u": "mEq"}, "Calcio": {"f": 0.46, "u": "mEq"},
    "Fósforo": {"f": 1.0, "u": "mmol"}, "Proteína": {"f": 0.1, "u": "g"},
    "Dextrosa": {"f": 0.5, "u": "g"}, "Lípidos": {"f": 0.2, "u": "g"},
    "Elementos Traza": {"f": 1.0, "u": "mL"}, "Vitaminas": {"f": 1.0, "u": "mL"}
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Perfil y Terapia")
    p_name = st.text_input("Nombre / ID", "Fanny")
    p_cat = st.selectbox("Categoría Clínica", list(ASPEN_GUIDES.keys()))
    p_weight = st.number_input("Peso (kg)", value=76.85, step=0.01)
    horas_inf = st.number_input("Horas de goteo", value=24, min_value=1)
    
    st.header("🧪 Laboratorios")
    cl1, cl2 = st.columns(2)
    with cl1:
        v_k = st.number_input("K+ (mEq/L)", value=4.0)
        v_p = st.number_input("P (mg/dL)", value=3.5)
    with cl2:
        v_na = st.number_input("Na+ (mEq/L)", value=140.0)
        v_crea = st.number_input("Crea (mg/dL)", value=0.8)
        v_bun = st.number_input("BUN (mg/dL)", value=15.0)

# --- PANEL PRINCIPAL ---
st.subheader(f"📋 Formulación SAP: {p_name}")
sap_text = st.text_area("Pegue las líneas de SAP aquí:", height=180)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    res_list = []
    nutri = {"Dex_g": 0, "Prot_g": 0, "Lip_g": 0, "Ca_mEq": 0, "P_mmol": 0, "K_mEq": 0}
    vol_tot = 0
    
    lines = sap_text.strip().split('\n')
    for line in lines:
        up_l = line.upper()
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            cid = None
            
            # Mapeo Inteligente (Base de Datos Actualizada)
            if "MAGNESIO" in up_l: cid = "Magnesio"
            elif any(x in up_l for x in ["SODIO", "NATROL", "CLORURO DE SODIO"]): cid = "Sodio"
            elif any(x in up_l for x in ["POTASIO", "KATROL", "CLORURO DE POTASIO"]):
                cid = "Potasio"; nutri["K_mEq"] += (vol * 2.0)
            elif any(x in up_l for x in ["CALCIO", "GLUCONATO"]): 
                cid = "Calcio"; nutri["Ca_mEq"] += (vol * 0.46)
            elif any(x in up_l for x in ["FOSFA", "GLICERO"]): 
                cid = "Fósforo"; nutri["P_mmol"] += vol
            elif any(x in up_l for x in ["DEXTRO", "GLUCOSA"]): 
                cid = "Dextrosa"; nutri["Dex_g"] += (vol * 0.5)
            elif any(x in up_l for x in ["AMINO", "PROTEINA"]): 
                cid = "Proteína"; nutri["Prot_g"] += (vol * 0.1)
            elif any(x in up_l for x in ["LIPID", "SMOF"]):
                cid = "Lípidos"; nutri["Lip_g"] += (vol * 0.2)
            elif any(x in up_l for x in ["NULANZA", "PADITRACE", "TRAZA", "ELEMENTOS"]):
                cid = "Elementos Traza"
            elif any(x in up_l for x in ["VITAMINA", "MVI", "ASCORBICO"]):
                cid = "Vitaminas"
            
            if cid:
                fact = COMP_META[cid]["f"]
                unit = COMP_META[cid]["u"]
                aporte = vol * fact
                if cid in ASPEN_GUIDES[p_cat]:
                    mi, ma, un = ASPEN_GUIDES[p_cat][cid]
                    rmin = mi if "/kg" not in un else mi * p_weight
                    rmax = ma if "/kg" not in un else ma * p_weight
                    est = "🟢 Óptimo" if rmin <= aporte <= rmax else "🔴 Sobre" if aporte > rmax else "🟡 Sub"
                    meta_str = f"{rmin:.1f}-{rmax:.1f}"
                else:
                    est = "✅ Validado"
                    meta_str = "S/R"
                
                res_list.append({
                    "Componente": cid, 
                    "Aporte": f"{aporte:.2f} {unit}", 
                    "Meta ASPEN": meta_str, 
                    "Estado": est
                })

    if res_list:
        vol_purg = vol_tot - 20
        tasa = vol_purg / horas_inf if horas_inf > 0 else 0
        st.success(f"📦 Volumen Total: {vol_tot:.1f} mL | Tasa: {tasa:.1f} mL/h (Post-purga)")
        st.table(pd.DataFrame(res_list))
        
        # --- PERFIL METABÓLICO ---
        st.subheader("🍏 Perfil Metabólico e Infusión")
        c_dex, c_lip, c_prot = nutri["Dex_g"]*3.4, nutri["Lip_g"]*9, nutri["Prot_g"]*4
        t_kcal = c_dex + c_lip + c_prot
        nitrog = nutri["Prot_g"] / 6.25
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            gir = (nutri["Dex_g"] * 1000) / (horas_inf * 60 * p_weight)
            st.metric("GIR (Real)", f"{gir:.2f}")
        with m2:
            rel = (c_dex + c_lip) / nitrog if nitrog > 0 else 0
            st.metric("Rel. Cal NP / N", f"{rel:.1f}:1")
        with m3:
            idx = ((nutri["Ca_mEq"] + nutri["P_mmol"]) / vol_tot) * 1000 if vol_tot > 0 else 0
            st.metric("Índice Ca+P", f"{idx:.1f}")
        with m4:
            st.metric("Total Kcal", f"{t_kcal:.0f}")

        with st.expander("📘 Guía de Referencia: Soporte a la Decisión"):
            st.markdown(f"""
            ### Interpretación Clínica:
            * **GIR:** Meta 4-7 mg/kg/min. Si es > 7, riesgo de esteatosis hepática.
            * **Cal NP/N:** Meta 100:1. Si es < 80:1, riesgo de usar proteína como energía.
            * **Índice Ca+P:** Límite < 35. Valor actual: **{idx:.1f}**.
            * **Trazas y Vitaminas:** Componentes como **Nulanza** y **Paditrace** han sido validados en volumen.
            """)
            
        st.divider()
        st.subheader("🚨 Hallazgos de Seguridad")
        if v_p < 2.5: st.error(f"⚠️ RIESGO DE REALIMENTACIÓN: Fósforo bajo ({v_p} mg/dL).")
        if v_k >= 5.0 and nutri["K_mEq"] > 0: st.error(f"🚨 ALERTA: Hiperpotasemia con aporte activo.")
        if idx > 35: st.warning(f"⚖️ ESTABILIDAD: Riesgo de precipitación Ca/P elevado.")
    else:
        st.error("No se detectaron datos válidos en SAP.")
        
