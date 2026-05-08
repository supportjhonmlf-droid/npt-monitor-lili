import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v9.1 - Soporte a la Decisión Clínica Avanzada
# =========================================================

st.set_page_config(
    page_title="SIMENP Pro", 
    layout="wide", 
    page_icon="🧪"
)

# --- BASES TÉCNICAS (ASPEN / ESPEN / CHOP 2024) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir": 5.0, "lip": 1.0},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir": 4.0, "lip": 1.0},
    "Adulto Obeso (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir": 4.0, "lip": 1.0},
    "Neonato Pretérmino (<1.5kg)": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir": 14.0, "lip": 3.0},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir": 10.0, "lip": 2.5}
}

# Factores de conversión SAP -> Nutrientes (Basado en TrophAmine/Gluconato/Dextrosa 50%)
SAP_CONV = {
    "Magnesio": {"f": 1.62, "u": "mEq", "k":},
    "Sodio": {"f": 2.0, "u": "mEq", "k":},
    "Potasio": {"f": 2.0, "u": "mEq", "k":},
    "Calcio": {"f": 0.46, "u": "mEq", "k":},
    "Fósforo": {"f": 1.0, "u": "mmol", "k":},
    "Dextrosa": {"f": 0.5, "u": "g", "k":},
    "Proteína": {"f": 0.1, "u": "g", "k":},
    "Lípidos": {"f": 0.2, "u": "g", "k":}
}

# --- INTERFAZ SIDEBAR ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("ID Paciente", "Paciente 01")
    p_cat = st.selectbox("Perfil Clínico", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.header("🔬 Bioquímica Clínica")
    lab_p = st.number_input("Fósforo sérico (mg/dL)", value=3.5)
    lab_tg = st.number_input("Triglicéridos (mg/dL)", value=150.0)
    lab_glu = st.number_input("Glucemia (mg/dL)", value=120.0)

# --- PANEL DE VALIDACIÓN ---
st.title("🥗 SIMENP-FVL v9.1")
st.caption("Sistema de Seguimiento Farmacoterapéutico Integral en Nutrición Parenteral")

sap_text = st.text_area("Introduzca las líneas de SAP (Componente + Volumen mL):", height=150)

if st.button("🚀 INICIAR ANÁLISIS CLÍNICO"):
    nutri = {k: 0.0 for k in SAP_CONV.keys()}
    vol_tot = 0
    
    # Procesamiento de datos de SAP
    for line in sap_text.strip().split('\n'):
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_CONV.items():
                if any(k in line.upper() for k in data["k"]):
                    nutri[comp] += (vol * data["f"])

    if vol_tot > 0:
        # Cálculos Metabólicos y de Estabilidad
        gir = (nutri * 1000) / (p_weight * horas_inf * 60)
        kcal_tot = (nutri * 3.4) + (nutri["Lípidos"] * 9.0) + (nutri["Proteína"] * 4.0)
        aa_final_perc = (nutri["Proteína"] / vol_tot) * 100
        
        # Fórmula de Solubilidad de Anderson (Factor de Solución)
        ca_m_eq_l = (nutri["Calcio"] / vol_tot) * 1000
        p_mmol_l = (nutri["Fósforo"] / vol_tot) * 1000
        sol_factor = (ca_m_eq_l * 0.863 * p_mmol_l * 1.19) / aa_final_perc if aa_final_perc > 0 else 0
        
        # --- UI: DASHBOARD DE MÉTRICAS ---
        st.subheader(f"📊 Dashboard de Control: {p_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GIR (Oxidación)", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir"] else "OK", delta_color="inverse")
        c2.metric("Kcal Totales", f"{kcal_tot:.0f}")
        c3.metric("Solubilidad (F.S.)", f"{sol_factor:.1f}", help="Límite: 100 (Adulto) / 200 (Neonato con Cisteína)")
        c4.metric("AA Final", f"{aa_final_perc:.1f}%")

        # --- TABLA DE EVALUACIÓN NUTRICIONAL ---
        st.subheader("📋 Evaluación según Metas ASPEN/ESPEN")
        eval_data = ["Proteína", f"{nutri['Proteína']/p_weight:.2f}", f"{GUIDES[p_cat]['prot']}-{GUIDES[p_cat]['prot'][1]}", "g/kg/d"],
           ['kcal']}-{GUIDES[p_cat]['kcal'][1]}", "kcal/kg/d"],
            ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f}", f"<{GUIDES[p_cat]['lip']}", "g/kg/d"],
            ["Fósforo", f"{nutri['Fósforo']/p_weight:.2f}", "1.0 - 2.0", "mmol/kg/d"]
        st.table(pd.DataFrame(eval_data, columns=))

        # --- ALERTAS DE SEGURIDAD Y SEGUIMIENTO ---
        st.subheader("🚩 Alertas de Seguridad y Sugerencias de Ajuste")
        
        # Estabilidad Ca-P
        limit_stab = 200 if "Neonato" in p_cat else 100
        if sol_factor > limit_stab:
            st.error(f"❌ RIESGO CRÍTICO DE PRECIPITACIÓN: El factor {sol_factor:.1f} excede el límite de seguridad ({limit_stab}).")
        
        # Alertas de Laboratorio
        if lab_p < 2.5:
            st.warning("⚠️ RIESGO DE REALIMENTACIÓN: Fósforo bajo. No incrementar GIR hasta estabilizar electrolitos.[7, 6]")
        
        if lab_tg > 400:
            st.error("🚨 HIPERTRIGLICERIDEMIA CRÍTICA: Suspender lípidos y reevaluar en 4-6 horas.[4, 5]")
        elif lab_tg > 250:
            st.info("⚠️ Hipertrigliceridemia moderada: Considerar reducción del 50% en el aporte de lípidos.")

        if lab_glu > 180:
            insu_sug = nutri * 0.1
            st.warning(f"🚨 HIPERGLUCEMIA: Se sugiere añadir {insu_sug:.1f} UI de Insulina Regular a la mezcla (0.1 UI/g dextrosa).[4, 5]")

        # Recomendaciones Adicionales
        if "Neonato" in p_cat:
            st.info("💡 Recordatorio: La NP neonatal requiere fotoprotección total y uso de filtros de 1.2 micras si incluye lípidos.[5, 8]")
    else:
        st.error("No se detectaron datos válidos. Verifique el formato de entrada de SAP.")

st.divider()
st.caption("Investigación base: ASPEN 2023, ESPEN 2024, Anderson et al. (Solubility Equation). Herramienta para uso profesional farmacéutico.")
        
