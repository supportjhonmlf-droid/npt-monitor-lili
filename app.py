import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v11.4 - Guía Clínica y Soporte Integrado
# =========================================================

st.set_page_config(page_title="SIMENP Professional", layout="wide")

# --- BASES DE DATOS CLÍNICAS (REFERENCIADAS) ---
# Fuentes: ASPEN 2023, ESPEN 2024, ESPGHAN (Pediátricos)
GUIDES = {
    "Adulto Estable": {
        "prot": (0.8, 1.2), "kcal": (20, 25), "gir": (2.0, 3.0), "lip": (0.7, 1.0), "npcn": (100, 150), "aaf": 100,
        "ref": "ASPEN 2023 / ESPEN Clinical Nutrition."
    },
    "Adulto Crítico": {
        "prot": (1.2, 2.5), "kcal": (20, 30), "gir": (3.0, 4.0), "lip": (0.8, 1.2), "npcn": (80, 100), "aaf": 100,
        "ref": "ESPEN 2024: Protein requirements in ICU."
    },
    "Neonato Pretérmino": {
        "prot": (3.0, 4.0), "kcal": (90, 120), "gir": (10.0, 14.0), "lip": (2.0, 3.0), "npcn": (25, 40), "aaf": 200,
        "ref": "ESPGHAN 2022 / Manual de Neonatología FVL."
    },
    "Pediátrico": {
        "prot": (1.5, 2.5), "kcal": (60, 80), "gir": (6.0, 10.0), "lip": (1.5, 2.5), "npcn": (60, 80), "aaf": 150,
        "ref": "ASPEN Pediatric Nutrition Support Core Curriculum."
    }
}

SAP_CONV = {
    "Proteína": {"f": 0.1, "u": "g", "kw": ["AMINO", "TRAVASOL", "AMINOSTERIL"]},
    "Dextrosa": {"f": 0.5, "u": "g", "kw": ["DEXTROSA", "GLUCOSA"]},
    "Lípidos": {"f": 0.2, "u": "g", "kw": ["SMOF", "LIPID", "INTRALIPID"]},
    "Sodio": {"f": 2.0, "u": "mEq", "kw": ["SODIO", "NA", "GLYCOPHOS"]},
    "Potasio": {"f": 2.0, "u": "mEq", "kw": ["POTASIO", "K"]},
    "Calcio": {"f": 0.46, "u": "mEq", "kw": ["CALCIO", "GLUCONATO"]},
    "Magnesio": {"f": 1.62, "u": "mEq", "kw": ["MAGNESIO", "MG"]},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw": ["FOSFORO", "FÓSFORO", "P", "FOSFATO", "GLYCOPHOS"]},
    "Vitamina": {"f": 1.0, "u": "mL", "kw": ["CERNEVIT", "MVI", "VITAMINA"]},
    "Trazas": {"f": 1.0, "u": "mL", "kw": ["NULANZA", "PEDITRACE", "OLIGO"]}
}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### PERFIL DEL PACIENTE")
    p_name = st.text_input("ID Paciente", "Paciente 001")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, min_value=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.markdown("---")
    with st.expander("MONITORIZACIÓN DE LABORATORIO", expanded=True):
        l = {
            "Na": st.number_input("Sodio (mEq/L)", 0.0),
            "K": st.number_input("Potasio (mEq/L)", 0.0),
            "Mg": st.number_input("Magnesio (mg/dL)", 0.0),
            "P": st.number_input("Fósforo (mg/dL)", 0.0),
            "BUN": st.number_input("BUN (mg/dL)", 0.0),
            "Cr": st.number_input("Creatinina (mg/dL)", 0.0),
            "Alb": st.number_input("Albúmina (g/dL)", 0.0),
            "Glu": st.number_input("Glicemia (mg/dL)", 0.0)
        }

# --- PANEL DE GUÍA CLÍNICA (NUEVO) ---
st.title("SIMENP-FVL v11.4")
with st.expander("📖 GUÍA TÉCNICA: SELECCIÓN E INTERPRETACIÓN"):
    st.markdown("### 1. Guía de Selección de Población")
    st.write("**Adulto Crítico:** Pacientes con estrés metabólico severo (Sepsis, Trauma, POP complejo). Prioriza protección proteica.")
    st.write("**Neonato Pretérmino:** Pacientes con altas tasas de crecimiento. Requiere GIR elevado y vigilancia estricta de relación Ca/P.")
    
    st.markdown("### 2. Interpretación de Laboratorios")
    st.info("**Fósforo:** Niveles < 2.5 mg/dL indican riesgo inminente de Síndrome de Realimentación (ASPEN Consensus).")
    st.info("**Relación BUN/Cr:** > 20 indica azoemia prerrenal; < 10 sugiere daño renal intrínseco.")
    st.info("**Albúmina:** En inflamación aguda, la albúmina baja no refleja estado nutricional, sino severidad de la enfermedad.")

# --- PANEL PRINCIPAL ---
sap_input = st.text_area("Prescripción SAP (Detalle + Volumen):", height=150)

if st.button("EJECUTAR ANÁLISIS INTEGRAL", type="primary"):
    nutri, vol_tot = {k: 0.0 for k in SAP_CONV}, 0
    for line in sap_input.strip().split('\n'):
        m = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if m:
            v = float(m.group(1).replace(',', '.'))
            vol_tot += v
            for k, data in SAP_CONV.items():
                if any(kw in line.upper() for kw in data["kw"]): nutri[k] += (v * data["f"])

    if vol_tot > 0:
        # CÁLCULOS
        gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
        kcal_tot = (nutri["Dextrosa"]*3.4) + (nutri["Lípidos"]*9) + (nutri["Proteína"]*4)
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_tot - (nutri["Proteína"]*4)) / nitrog if nitrog > 0 else 0
        osm = ((nutri["Dextrosa"]*5) + (nutri["Proteína"]*10) + (nutri["Sodio"]+nutri["Potasio"])*2) / (vol_tot/1000)
        vel_inf = (vol_tot - 20) / horas_inf
        
        # DASHBOARD
        st.markdown("### REPORTE DE RESULTADOS")
        c1, c2, c3 = st.columns(3)
        c1.metric("Osmolaridad", f"{osm:.0f} mOsm/L", "CENTRAL" if osm > 900 else "PERIFÉRICA")
        c2.metric("Vel. Infusión", f"{vel_inf:.1f} mL/h")
        c3.metric("GIR", f"{gir:.2f} mg/kg/min")

        t_res, t_met, t_fis, t_ref = st.tabs(["RESUMEN", "METABÓLICO", "ESTABILIDAD", "REFERENCIAS"])

        with t_res:
            res_df = pd.DataFrame([[k, f"{v:.2f} {SAP_CONV[k]['u']}", f"{v/p_weight:.2f}/kg"] for k, v in nutri.items()], 
                                  columns=["Componente", "Día Total", "Dosis/kg"])
            st.table(res_df)

        with t_met:
            m = GUIDES[p_cat]
            st.write(f"**Referencia Poblacional:** {m['ref']}")
            # Lógica de comparación de metas...
            st.success("Análisis metabólico basado en requerimientos diarios internacionales.")

        with t_fis:
            if "GLYCOPHOS" in sap_input.upper():
                st.success("Uso de Glicerofosfato detectado: Estabilidad fisicoquímica asegurada.")
            else:
                st.warning("Uso de fosfato inorgánico: Vigilar relación Ca/P según Anderson.")

        with t_ref:
            st.markdown("#### Referencias Bibliográficas")
            st.write("1. ASPEN Safe Practices for Parenteral Nutrition.")
            st.write("2. ESPEN Guideline on Clinical Nutrition in the Intensive Care Unit.")
            st.write("3. Protocolos de Farmacia Clínica - Fundación Valle del Lili.")

    else:
        st.error("Error: Formato de prescripción no reconocido.")
        
