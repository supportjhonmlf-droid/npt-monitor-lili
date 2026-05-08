import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v9.2 - Soporte a la Decisión Clínica Avanzada
# =========================================================

st.set_page_config(
    page_title="SIMENP-FVL Pro", 
    layout="wide", 
    page_icon="🧪"
)

# --- GUÍAS DE DOSIFICACIÓN (ASPEN 2023 / ESPEN 2024 / ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir": 5.0, "lip": 1.0, "aaf": 100},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Adulto Obeso (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino (<1.5kg)": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir": 10.0, "lip": 2.5, "aaf": 150}
}

# Factores de conversión SAP -> Nutrientes
SAP_MAP = {
    "Magnesio": {"f": 1.62, "u": "mEq", "kw":},
    "Sodio": {"f": 2.0, "u": "mEq", "kw":},
    "Potasio": {"f": 2.0, "u": "mEq", "kw":},
    "Calcio": {"f": 0.46, "u": "mEq", "kw":},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw":},
    "Dextrosa": {"f": 0.5, "u": "g", "kw":},
    "Proteína": {"f": 0.1, "u": "g", "kw":},
    "Lípidos": {"f": 0.2, "u": "g", "kw":}
}

# --- SIDEBAR: DATOS DEL PACIENTE ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("Nombre / ID Paciente", "Paciente 01")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.header("🔬 Paraclínicos Actuales")
    v_p = st.number_input("P sérico (mg/dL)", value=3.5)
    v_tg = st.number_input("Triglicéridos (mg/dL)", value=150.0)
    v_glu = st.number_input("Glucemia (mg/dL)", value=120.0)
    v_uun = st.number_input("UUN (g/24h)", value=0.0, help="Nitrógeno Ureico Urinario")
    v_cys = st.number_input("Cisteína (mg/g AA)", value=40 if "Neonato" in p_cat else 0)

# --- PANEL PRINCIPAL ---
st.title("🥗 SIMENP-FVL v9.2")
st.caption("Sistema de Monitorización Farmacoterapéutica Avanzada en Nutrición Parenteral")

sap_input = st.text_area("Pegue las líneas de SAP aquí (Nombre Componente + Volumen Final):", height=150)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    nutri = {k: 0.0 for k in SAP_MAP.keys()}
    vol_tot = 0
    
    # Procesamiento de líneas de SAP
    lines = sap_input.strip().split('\n')
    for line in lines:
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_MAP.items():
                if any(k in line.upper() for k in data["kw"]):
                    nutri[comp] += (vol * data["f"])
    
    if vol_tot > 0:
        # --- 1. CÁLCULOS METABÓLICOS ---
        gir = (nutri * 1000) / (p_weight * horas_inf * 60)
        kcal_dex = nutri * 3.4
        kcal_lip = nutri["Lípidos"] * 9.0
        kcal_prot = nutri["Proteína"] * 4.0
        kcal_tot = kcal_dex + kcal_lip + kcal_prot
        
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_dex + kcal_lip) / nitrog if nitrog > 0 else 0
        bal_nit = nitrog - (v_uun + 4) if v_uun > 0 else None
        
        # --- 2. CÁLCULOS DE ESTABILIDAD (ANDERSON FORMULA) ---
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        ca_mql = (nutri["Calcio"] / vol_tot) * 1000
        p_mml = (nutri["Fósforo"] / vol_tot) * 1000
        
        # Factor de Solución (SF)
        sol_factor = (ca_mql * 0.863 * p_mml * 1.19) / aa_perc if aa_perc > 0 else 0
        
        # Límite de Precipitación (PL)
        aaf = GUIDES[p_cat]["aaf"]
        precip_limit = aaf + (v_cys * aaf / 100)
        if nutri["Lípidos"] > 0:
            lip_g_kg = nutri["Lípidos"] / p_weight
            precip_limit -= (lip_g_kg * aaf / (nutri["Proteína"]/p_weight * 10))

        # --- UI: DASHBOARD PRINCIPAL ---
        st.subheader(f"📊 Dashboard Farmacoterapéutico: {p_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GIR (Oxidación)", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir"] else "OK", delta_color="inverse")
        c2.metric("Relación NPC:N", f"{npc_n:.1f}:1", help="Relación Calorías No Proteicas : Nitrógeno")
        c3.metric("Kcal/kg/día", f"{kcal_tot/p_weight:.1f}")
        c4.metric("AA Final (%)", f"{aa_perc:.1f}%")
        
        # --- TABS DE ANÁLISIS ---
        t_clin, t_stab, t_adj = st.tabs()
        
        with t_clin:
            st.subheader("Cumplimiento de Metas (ASPEN/ESPEN)")
            eval_data = ["Proteína", f"{nutri['Proteína']/p_weight:.2f}", f"{GUIDES[p_cat]['prot']}-{GUIDES[p_cat]['prot'][1]}", "g/kg/d"],
               ['kcal']}-{GUIDES[p_cat]['kcal'][1]}", "kcal/kg/d"],
                ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f}", f"<{GUIDES[p_cat]['lip']}", "g/kg/d"],
                ["Fósforo", f"{nutri['Fósforo']/p_weight:.2f}", "1.0 - 2.0", "mmol/kg/d"]
            st.table(pd.DataFrame(eval_data, columns=["Parámetro", "Actual", "Meta Guía", "Unidad"]))
            if bal_nit: st.info(f"**Balance Nitrogenado Estimado:** {bal_nit:.2f} g/día (Meta: +2 a +4 para anabolismo)")

        with t_stab:
            st.subheader("Análisis de Riesgo de Precipitación")
            st.write(f"**Factor de Solución (SF):** {sol_factor:.2f}")
            st.write(f"**Límite de Precipitación (PL):** {precip_limit:.2f}")
            if sol_factor > precip_limit:
                st.error("❌ RIESGO CRÍTICO DE PRECIPITACIÓN CALCIO-FÓSFORO. Verifique concentraciones.")
            else:
                st.success("✅ Mezcla estable fisicoquímicamente.")
            
            # Estabilidad de la emulsión
            divalentes = ca_mql + (nutri["Magnesio"]/vol_tot*1000)
            if divalentes > 20 and nutri["Lípidos"] > 0:
                st.warning(f"⚠️ Cationes divalentes elevados ({divalentes:.1f} mEq/L). Riesgo de ruptura de emulsión.")

        with t_adj:
            st.subheader("Algoritmos de Seguimiento")
            if v_p < 2.5:
                st.error("🚨 Hipofosfatemia detected. Riesgo de Síndrome de Realimentación. Mantener GIR estable.")
            if v_tg > 400:
                st.error("🚨 Hipertrigliceridemia (>400). Suspender aporte de lípidos por 4-6h.")
            if v_glu > 180:
                insu_sug = nutri * 0.1
                st.warning(f"🚨 Hiperglucemia detectada. Sugerencia: {insu_sug:.1f} UI de Insulina Regular en bolsa.")
            
            if aa_perc < 2.5 and nutri["Lípidos"] > 0:
                st.warning("💡 Concentración de AA < 2.5%. Se recomienda subir AA para mejorar estabilidad de lípidos.")

        st.divider()
        if "Neonato" in p_cat:
            st.info("💡 Recordatorio: La NP neonatal requiere fotoprotección total y filtros de 1.2 micras si es TNA.")

    else:
        st.error("No se detectaron datos válidos. Asegúrese de que el formato en SAP termine con el volumen numérico.")

st.caption("Investigación de soporte: ASPEN 2023, ESPEN 2024, Fórmula de Anderson (Hospital Pharmacy 57:6).")
            
