import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v9.3 - Sistema de Soporte Farmacoterapéutico
# =========================================================

st.set_page_config(
    page_title="SIMENP-FVL Advanced", 
    layout="wide", 
    page_icon="🧪"
)

# --- BASES DE DATOS TÉCNICAS (ASPEN / ESPEN / ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir": 5.0, "lip": 1.0, "aaf": 100},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Adulto Obeso (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino (<1.5kg)": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir": 10.0, "lip": 2.5, "aaf": 150}
}

# Factores de conversión SAP -> Nutrientes (Basados en formulaciones estándar en Colombia)
SAP_CONV = {
    "Magnesio": {"f": 1.62, "u": "mEq", "kw":},
    "Sodio": {"f": 2.0, "u": "mEq", "kw":},
    "Potasio": {"f": 2.0, "u": "mEq", "kw":},
    "Calcio": {"f": 0.46, "u": "mEq", "kw":},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw":},
    "Dextrosa": {"f": 0.5, "u": "g", "kw":},
    "Proteína": {"f": 0.1, "u": "g", "kw":},
    "Lípidos": {"f": 0.2, "u": "g", "kw":}
}

# --- INTERFAZ DE USUARIO ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("ID Paciente", "Paciente 01")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.header("🔬 Bioquímica y Monitorización")
    v_p = st.number_input("Fósforo sérico (mg/dL)", value=3.5)
    v_tg = st.number_input("Triglicéridos (mg/dL)", value=150.0)
    v_glu = st.number_input("Glucemia (mg/dL)", value=120.0)
    v_uun = st.number_input("UUN (Nitrógeno Ureico Urinario g/24h)", value=0.0)
    v_cys = st.number_input("Cisteína añadida (mg/g AA)", value=40 if "Neonato" in p_cat else 0)

st.title("🥗 SIMENP-FVL v9.3")
st.markdown("### *Sistema Avanzado de Soporte a la Decisión en Nutrición Parenteral*")
sap_input = st.text_area("Pegue las líneas de SAP aquí (Nombre Componente + Volumen Final en mL):", height=150)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    nutri = {k: 0.0 for k in SAP_CONV.keys()}
    vol_tot = 0
    
    # --- PROCESAMIENTO DE SAP ---
    for line in sap_input.strip().split('\n'):
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_CONV.items():
                if any(k in line.upper() for k in data["kw"]):
                    nutri[comp] += (vol * data["f"])

    if vol_tot > 0:
        # --- 1. CÁLCULOS METABÓLICOS AVANZADOS ---
        # Tasa de Oxidación de Glucosa (GIR)
        gir = (nutri * 1000) / (p_weight * horas_inf * 60)
        
        # Calorías por sustrato
        kcal_dex = nutri * 3.4
        kcal_lip = nutri["Lípidos"] * 9.0
        kcal_prot = nutri["Proteína"] * 4.0
        kcal_tot = kcal_dex + kcal_lip + kcal_prot
        
        # Balance Nitrogenado
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_dex + kcal_lip) / nitrog if nitrog > 0 else 0
        bal_nit = nitrog - (v_uun + 4) if v_uun > 0 else None
        
        # --- 2. CÁLCULO DE ESTABILIDAD (ANDERSON FORMULA) ---
        # Solution Factor (SF) = ((Ca_mEq/L * 0.863) * (P_mmol/L * 1.19)) / AA_final_%
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        ca_mql = (nutri["Calcio"] / vol_tot) * 1000
        p_mml = (nutri["Fósforo"] / vol_tot) * 1000
        sol_factor = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
        
        # Límite de Precipitación (PL) adaptado a 3-en-1
        aaf = GUIDES[p_cat]["aaf"]
        precip_limit = aaf + (v_cys * aaf / 100)
        if nutri["Lípidos"] > 0:
            # Factor de corrección por lípidos alcalinos
            precip_limit -= ((nutri["Lípidos"]/p_weight) * aaf / ((nutri["Proteína"]/p_weight) * 10))

        # --- 3. UI: DASHBOARD DE MÉTRICAS ---
        st.subheader(f"📊 Dashboard Farmacoterapéutico: {p_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GIR (Oxidación)", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir"] else "OK", delta_color="inverse")
        c2.metric("Relación NPC:N", f"{npc_n:.1f}:1", help="Meta 80:1-100:1")
        c3.metric("Osmolaridad Est.", f"{int((vol_tot*1.1)/vol_tot*1000) if vol_tot > 0 else 0} mOsm/L")
        c4.metric("AA Final (%)", f"{aa_perc:.1f}%")

        # --- 4. TABLA DE EVALUACIÓN (CORREGIDA) ---
        st.subheader("📋 Evaluación de Metas Nutricionales")
        eval_data = ["Proteína", f"{nutri['Proteína']/p_weight:.2f}", f"{GUIDES[p_cat]['prot']} - {GUIDES[p_cat]['prot'][4]}", "g/kg/d"],
           ['kcal']} - {GUIDES[p_cat]['kcal'][4]}", "kcal/kg/d"],
            ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f}", f"< {GUIDES[p_cat]['lip']}", "g/kg/d"],
            ["Calcio", f"{nutri['Calcio']/p_weight:.2f}", "0.5 - 4.0", "mEq/kg/d"]
        st.table(pd.DataFrame(eval_data, columns=["Parámetro", "Aporte Actual", "Meta Guía", "Unidad"]))
        
        # --- 5. TABS DE ANÁLISIS PROFUNDO ---
        t_stab, t_adj = st.tabs(["⚖️ Estabilidad Fisicoquímica", "🏥 Ajustes Paraclínicos"])
        
        with t_stab:
            st.write(f"**Factor de Solución (SF):** {sol_factor:.2f} | **Límite de Precipitación (PL):** {precip_limit:.2f}")
            if sol_factor > precip_limit:
                st.error("❌ RIESGO CRÍTICO DE PRECIPITACIÓN CALCIO-FÓSFORO. Reducir concentraciones o aumentar volumen.")
            else:
                st.success("✅ Mezcla estable para 24 horas a temperatura ambiente.")
            
            # Estabilidad de la emulsión
            divalentes = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot / 1000)
            if divalentes > 20 and nutri["Lípidos"] > 0:
                st.warning(f"⚠️ Cationes divalentes elevados ({divalentes:.1f} mEq/L). Riesgo de ruptura de emulsión (>20 mEq/L).")

        with t_adj:
            if v_p < 2.5:
                st.error("🚨 HIPOFOSFATEMIA: Riesgo de Síndrome de Realimentación. No aumentar GIR hasta normalizar P.")
            if v_tg > 400:
                st.error("🚨 HIPERTRIGLICERIDEMIA (>400 mg/dL): Suspender lípidos y reevaluar en 6h.")
            if v_glu > 180:
                insu = nutri * 0.1
                st.warning(f"🚨 HIPERGLUCEMIA: Sugerencia de añadir {insu:.1f} UI de Insulina Regular a la bolsa (0.1 UI/g Dex).")
            if bal_nit:
                st.info(f"**Balance Nitrogenado:** {bal_nit:.2f} g/día (Meta anabólica: +2 a +4).")

        st.divider()
        if "Neonato" in p_cat:
            st.info("💡 Recordatorio: Uso obligatorio de FOTOPROTECCIÓN y filtro de 1.2 micras para NP con lípidos.")
    else:
        st.error("No se detectaron datos válidos. El formato SAP debe terminar con el volumen (ej: Dextrosa 50% 500.0).")

st.caption("Validado según: ASPEN 2023, ESPEN 2024, Ecuación de Anderson (PMC9631008). Liderado por el Químico Farmacéutico.")
