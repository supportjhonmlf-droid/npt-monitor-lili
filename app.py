import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v9.0 - Sistema Avanzado de Nutrición Parenteral
# =========================================================

st.set_page_config(
    page_title="SIMENP Advanced Decision Support", 
    layout="wide", 
    page_icon="🧪"
)

# --- CONFIGURACIÓN TÉCNICA Y GUÍAS (ASPEN/ESPEN/ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir_max": 5.0, "lip": 1.0},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir_max": 4.0, "lip": 1.0},
    "Adulto Obeso (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir_max": 4.0, "lip": 1.0},
    "Neonato Pretérmino (<1.5kg)": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir_max": 14.0, "lip": 3.0},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir_max": 10.0, "lip": 2.5}
}

ELECTROLYTE_TARGETS = {
    "Adulto": {"Na": (135, 145), "K": (3.5, 5.0), "P": (2.5, 4.5), "Mg": (1.8, 2.4), "Gluc": (140, 180)},
    "Neonato": {"Na": (135, 145), "K": (3.5, 5.0), "P": (4.5, 6.5), "Mg": (1.6, 2.5), "Gluc": (60, 120)}
}

# Factores de conversión SAP -> Nutrientes
SAP_MAP = {
    "Magnesio": {"f": 1.62, "u": "mEq", "keywords":},
    "Sodio": {"f": 2.0, "u": "mEq", "keywords":},
    "Potasio": {"f": 2.0, "u": "mEq", "keywords":},
    "Calcio": {"f": 0.46, "u": "mEq", "keywords":},
    "Fósforo": {"f": 1.0, "u": "mmol", "keywords":},
    "Dextrosa": {"f": 0.5, "u": "g", "keywords":},
    "Proteína": {"f": 0.1, "u": "g", "keywords":},
    "Lípidos": {"f": 0.2, "u": "g", "keywords":}
}

# --- INTERFAZ SIDEBAR ---
with st.sidebar:
    st.header("👤 Datos del Paciente")
    p_name = st.text_input("ID Paciente", "SIM-001")
    p_cat = st.selectbox("Perfil Clínico", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    p_height = st.number_input("Talla (cm)", value=170.0)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    es_tna = st.checkbox("¿Es Mezcla 3-en-1 (Lípidos incluidos)?", value=True)
    
    st.header("🔬 Laboratorio Actual")
    v_na = st.number_input("Sodio sérico (mEq/L)", value=140.0)
    v_k = st.number_input("Potasio sérico (mEq/L)", value=4.0)
    v_p = st.number_input("Fósforo sérico (mg/dL)", value=3.5)
    v_tg = st.number_input("Triglicéridos (mg/dL)", value=150.0)
    v_glu = st.number_input("Glucemia (mg/dL)", value=130.0)
    v_uun = st.number_input("Nitrógeno Ureico Urinario (g/24h)", value=0.0, help="Para cálculo de Balance Nitrogenado")

# --- LÓGICA DE PROCESAMIENTO ---
st.title("🥗 SIMENP-FVL v9.0")
st.caption("Soporte de Decisión Avanzado para el Seguimiento Farmacoterapéutico en Nutrición Parenteral")
sap_input = st.text_area("Introducir Datos de SAP (Nombre Componente + Volumen Final):", height=150)

if st.button("🚀 VALIDAR TERAPIA E INICIAR SEGUIMIENTO"):
    nutri = {k: 0.0 for k in SAP_MAP.keys()}
    vol_tot = 0
    
    # Parsing de líneas SAP
    lines = sap_input.strip().split('\n')
    for line in lines:
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_MAP.items():
                if any(k in line.upper() for k in data["keywords"]):
                    nutri[comp] += (vol * data["f"])

    if vol_tot > 0:
        # 1. CÁLCULOS METABÓLICOS AVANZADOS
        gir = (nutri * 1000) / (p_weight * horas_inf * 60)
        kcal_dex = nutri * 3.4
        kcal_lip = nutri["Lípidos"] * 9.0
        kcal_prot = nutri["Proteína"] * 4.0
        kcal_tot = kcal_dex + kcal_lip + kcal_prot
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_dex + kcal_lip) / nitrog if nitrog > 0 else 0
        bal_nit = (nutri["Proteína"] / 6.25) - (v_uun + 4) if v_uun > 0 else None
        
        # 2. VALIDACIÓN DE ESTABILIDAD (Solubility Factor)
        # Formula: (Ca_mEq/L * 0.863 * P_mmol/L * 1.19) / AA_final_%
        aa_final_perc = (nutri["Proteína"] / vol_tot) * 100
        ca_m_eq_l = (nutri["Calcio"] / vol_tot) * 1000
        p_mmol_l = (nutri["Fósforo"] / vol_tot) * 1000
        sol_factor = (ca_m_eq_l * 0.863 * p_mmol_l * 1.19) / aa_final_perc if aa_final_perc > 0 else 999
        
        # --- UI: DASHBOARD DE MÉTRICAS ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("GIR (Oxidación)", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir_max"] else "OK", delta_color="inverse")
        col2.metric("Relación NPC:N", f"{npc_n:.1f}:1", help="Meta: 80:1 - 100:1 para anabolismo")
        col3.metric("Kcal Totales", f"{kcal_tot:.0f}")
        col4.metric("AA Final (%)", f"{aa_final_perc:.1f}%")

        # --- TABS DE ANÁLISIS ---
        tab_clin, tab_stab, tab_adj = st.tabs()
        
        with tab_clin:
            st.subheader("Cumplimiento de Metas (Dosis/kg/día)")
            eval_data = ["Proteína", f"{nutri['Proteína']/p_weight:.2f}", f"{GUIDES[p_cat]['prot']}-{GUIDES[p_cat]['prot'][1]}", "g/kg"],
               ['kcal']}-{GUIDES[p_cat]['kcal'][1]}", "kcal/kg"],
                ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f}", f"<{GUIDES[p_cat]['lip']}", "g/kg"]
            st.table(pd.DataFrame(eval_data, columns=["Parámetro", "Actual", "Meta Guía", "Unidad"]))
            
            if bal_nit is not None:
                st.info(f"**Balance Nitrogenado:** {bal_nit:.2f} g/día. " + 
                        ("Anabolismo detectado." if bal_nit > 2 else "Catabolismo persistente." if bal_nit < 0 else "Balance neutro."))

        with tab_stab:
            st.subheader("Análisis de Riesgo Fisicoquímico")
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Compatibilidad Calcio-Fósforo**")
                st.write(f"Factor de Solución: **{sol_factor:.2f}**")
                limit = 200 if "Neonato" in p_cat else 100
                if sol_factor > limit:
                    st.error(f"❌ RIESGO CRÍTICO DE PRECIPITACIÓN. El factor ({sol_factor:.1f}) excede el límite ({limit}).")
                else:
                    st.success("✅ Mezcla compatible según concentraciones de AA y pH estimado.")
            
            with c2:
                if es_tna:
                    st.write("**Estabilidad de Emulsión (TNA)**")
                    cat_div = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot / 1000)
                    if cat_div > 20:
                        st.warning(f"⚠️ Cationes divalentes elevados ({cat_div:.1f} mEq/L). Riesgo de coalescencia lipídica (>20 mEq/L).")
                    if aa_final_perc < 2.5:
                        st.warning("⚠️ Concentración de AA < 2.5%. Estabilidad de la emulsión comprometida.")

        with tab_adj:
            st.subheader("Seguimiento Farmacoterapéutico - Paraclínicos")
            # Algoritmos de ajuste basados en investigación
            if v_p < 2.5:
                st.error("🚨 **Hipofosfatemia severa:** Riesgo de Síndrome de Realimentación. Incrementar Fósforo en bolsa (+5-10 mmol) y ralentizar avance de GIR.")
            if v_k > 5.0 and nutri["Potasio"] > 0:
                st.warning(f"🚨 **Hiperpotasemia:** Se sugiere reducir el aporte de Potasio en la bolsa. (Regla: +/- 10 mEq en bolsa varía ~0.1 mEq/L sérico).")
            if v_tg > 400:
                st.error("🚨 **Hipertrigliceridemia (>400):** Suspender infusión de lípidos por 4-6h y reevaluar. Riesgo de pancreatitis.")
            elif v_tg > 250:
                st.warning("⚠️ **Triglicéridos elevados:** Reducir dosis de lípidos en un 50% y monitorear cada 24h.")
            if v_glu > 180:
                insu_sug = (nutri * 0.1)
                st.warning(f"🚨 **Hiperglucemia:** Glucemia > 180 mg/dL. Considerar añadir **{insu_sug:.1f} UI** de Insulina Regular a la bolsa (0.1 UI/g dextrosa).")

        # --- SECCIÓN DE ALERTAS GENERALES ---
        st.divider()
        st.subheader("🚩 Alertas de Seguridad de Preparación")
        if "Neonato" in p_cat:
            st.info("💡 **Fotoprotección:** Obligatoria en neonatos para evitar peróxidos tóxicos en lípidos y vitaminas.")
            st.info("💉 **Cisteína:** Verificar adición de L-Cisteína (40mg/g AA) para optimizar pH y solubilidad mineral.")
        
        filter_type = "1.2 micras" if es_tna else "0.22 micras"
        st.write(f"⚙️ **Filtro Recomendado:** Utilizar filtro de **{filter_type}** para la administración.")

    else:
        st.error("No se detectó volumen o componentes válidos. Revise el formato SAP.")

# Footer técnico
st.divider()
st.caption("Investigación base: ASPEN 2023, ESPEN 2024, Guías ESPGHAN de Micronutrientes 2024. SIMENP es una herramienta de apoyo, no sustituye el juicio del Químico Farmacéutico.")
            
