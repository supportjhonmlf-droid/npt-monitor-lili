import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v10.4 - Soporte de Decisión Clínica Robusto
# =========================================================

st.set_page_config(page_title="SIMENP Professional", layout="wide", page_icon="🧪")

# --- GUÍAS TÉCNICAS (ASPEN / ESPEN / ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir_max": 5.0, "lip": 1.5, "aaf": 100},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir_max": 4.0, "lip": 1.0, "aaf": 100},
    "Obesidad (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir_max": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir_max": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir_max": 10.0, "lip": 2.5, "aaf": 150}
}

# Factores de conversión SAP
SAP_CONV = {
    "Magnesio": {"f": 1.62, "u": "mEq", "kw": ["MAGNESIO", "MG"]},
    "Sodio": {"f": 2.0, "u": "mEq", "kw": ["SODIO", "NA"]},
    "Potasio": {"f": 2.0, "u": "mEq", "kw": ["POTASIO", "K"]},
    "Calcio": {"f": 0.46, "u": "mEq", "kw": ["CALCIO", "CA"]},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw": ["FOSFORO", "FÓSFORO", "P"]},
    "Dextrosa": {"f": 0.5, "u": "g", "kw": ["DEXTROSA", "GLUCOSA"]},
    "Proteína": {"f": 0.1, "u": "g", "kw": ["AMINOACIDO", "AMINOÁCIDO", "PROTEINA", "PROTEÍNA"]},
    "Lípidos": {"f": 0.2, "u": "g", "kw": ["LIPIDO", "LÍPIDO", "SMOF", "INTRALIPID"]}
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("Nombre / ID", "Paciente 01")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    horas_inf = st.number_input("Horas de goteo", value=24, min_value=1)
    
    st.header("🔬 Monitorización Básica")
    v_glu = st.number_input("Glucemia (mg/dL)", value=120.0)
    v_tg = st.number_input("TG séricos (mg/dL)", value=150.0)
    v_uun = st.number_input("UUN (Nitrógeno Ureico Urinario)", value=0.0)
    v_cys = st.number_input("Cisteína (mg/g AA)", value=40 if "Neonato" in p_cat else 0)

    # --- NUEVA SECCIÓN DE LABORATORIOS OPCIONALES ---
    with st.expander("🧪 Electrolitos y Función Renal", expanded=False):
        v_p = st.number_input("Fósforo sérico (mg/dL)", value=3.5, step=0.1)
        v_na = st.number_input("Sodio sérico (mEq/L)", value=140.0, step=1.0)
        v_mg = st.number_input("Magnesio sérico (mg/dL)", value=2.0, step=0.1)
        v_cr = st.number_input("Creatinina sérica (mg/dL)", value=0.9, step=0.1)

# --- PANEL PRINCIPAL ---
st.title("🥗 SIMENP-FVL v10.4")
st.caption("Seguimiento Farmacoterapéutico Avanzado e Integral")
sap_input = st.text_area("Pegue las líneas de SAP aquí (Nombre + Volumen mL):", height=150)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    nutri = {k: 0.0 for k in SAP_CONV.keys()}
    vol_tot = 0
    
    # Parser funcional
    for line in sap_input.strip().split('\n'):
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_CONV.items():
                if any(k in line.upper() for k in data["kw"]):
                    nutri[comp] += (vol * data["f"])

    if vol_tot > 0 and p_weight > 0:
        # 1. CÁLCULOS METABÓLICOS
        gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
        kcal_dex = nutri["Dextrosa"] * 3.4
        kcal_lip = nutri["Lípidos"] * 9.0
        kcal_prot = nutri["Proteína"] * 4.0
        kcal_tot = kcal_dex + kcal_lip + kcal_prot
        
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_dex + kcal_lip) / nitrog if nitrog > 0 else 0
        bal_nit = nitrog - (v_uun + 4) if v_uun > 0 else None
        
        # 2. ESTABILIDAD ANDERSON
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        ca_mql = (nutri["Calcio"] / vol_tot) * 1000
        p_mml = (nutri["Fósforo"] / vol_tot) * 1000
        sol_factor = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
        
        aaf_val = GUIDES[p_cat]["aaf"]
        precip_limit = aaf_val + (v_cys * aaf_val / 100)
        if nutri["Lípidos"] > 0:
            aa_g_kg = nutri["Proteína"] / p_weight
            lip_g_kg = nutri["Lípidos"] / p_weight
            precip_limit -= (lip_g_kg * aaf_val / (aa_g_kg * 10 if aa_g_kg > 0 else 1))

        # --- Dashboard de Métricas ---
        st.subheader(f"📊 Dashboard Farmacoterapéutico: {p_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GIR (Oxidación)", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir_max"] else None, delta_color="inverse")
        c2.metric("Relación NPC:N", f"{npc_n:.1f}:1", help="Meta 80:1-100:1")
        c3.metric("Kcal/kg/día", f"{kcal_tot/p_weight:.1f}")
        c4.metric("AA Final (%)", f"{aa_perc:.1f}%")

        # --- Tabla de Evaluación ---
        st.subheader("📋 Cumplimiento de Metas Nutricionales")
        metas = GUIDES[p_cat]
        eval_data = [
            ["Proteína", f"{nutri['Proteína']/p_weight:.2f}", f"{metas['prot'][0]} - {metas['prot'][1]}", "g/kg/d"],
            ["Calorías", f"{kcal_tot/p_weight:.2f}", f"{metas['kcal'][0]} - {metas['kcal'][1]}", "kcal/kg/d"],
            ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f}", f"< {metas['lip']}", "g/kg/d"],
            ["Fósforo (Aporte)", f"{nutri['Fósforo']/p_weight:.2f}", "1.0 - 2.0", "mmol/kg/d"]
        ]
        st.table(pd.DataFrame(eval_data, columns=["Parámetro", "Actual", "Meta Guía", "Unidad"]))

        # --- TABS DE ANÁLISIS ---
        t_stab, t_adj = st.tabs(["⚖️ Estabilidad Fisicoquímica", "🏥 Ajustes Paraclínicos"])
        
        with t_stab:
            st.write(f"**Solución (SF):** {sol_factor:.2f} | **Límite (PL):** {precip_limit:.2f}")
            if sol_factor > precip_limit:
                st.error("❌ RIESGO CRÍTICO DE PRECIPITACIÓN: El factor SF excede el límite Anderson (PL).")
            else:
                st.success("✅ Mezcla estable físico-químicamente para 24 horas.")
            
            div = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)
            if div > 20 and nutri["Lípidos"] > 0:
                st.warning(f"⚠️ Cationes divalentes elevados ({div:.1f} mEq/L). Riesgo de ruptura de emulsión (>20 mEq/L).")

        with t_adj:
            # Alertas Metabólicas y Nutricionales Originales
            if v_tg > 400: st.error("🚨 TRIGLICÉRIDOS > 400 mg/dL: Suspender aporte de lípidos por 4-6h.[7]")
            elif v_tg > 250: st.warning("⚠️ TG > 250: Considerar reducción del 50% de lípidos.")
            
            if v_glu > 180:
                insu = nutri["Dextrosa"] * 0.1
                st.warning(f"🚨 HIPERGLUCEMIA: Sugerencia de añadir {insu:.1f} UI de Insulina Regular a la bolsa (0.1 UI/g Dex).")
            
            if bal_nit: st.info(f"**Balance Nitrogenado Estimado:** {bal_nit:.2f} g/día (Meta: +2 a +4 para anabolismo).[8]")

            st.divider()
            st.markdown("#### 🔬 Alertas de Electrolitos y Función Renal")
            
            # Nuevas Alertas de Electrolitos y Renal
            if v_p < 2.5: 
                st.error("🚨 HIPOFOSFATEMIA (< 2.5 mg/dL): Riesgo de Síndrome de Realimentación. Bloquear aumento de GIR o aportar Fósforo IV periférico.")
            if v_mg < 1.8:
                st.error("🚨 HIPOMAGNESEMIA (< 1.8 mg/dL): Riesgo de arritmias y alteración en bomba Na/K. Considerar suplementación.")
            
            if v_na > 145:
                st.warning(f"⚠️ HIPERNATREMIA ({v_na} mEq/L): Evaluar estado de hidratación (déficit de agua libre) y reducir aporte de Sodio en NPT.")
            elif v_na < 135:
                st.warning(f"⚠️ HIPONATREMIA ({v_na} mEq/L): Evaluar sobrecarga hídrica o pérdidas. Ajustar concentración de Sodio en la mezcla.")
                
            if v_cr >= 1.2:  # Umbral de advertencia general para adultos
                if "Adulto" in p_cat or "Obesidad" in p_cat:
                    st.warning(f"⚠️ CREATININA ELEVADA ({v_cr} mg/dL): Monitorear Tasa de Filtración Glomerular (TFG). Puede requerir ajuste de aporte proteico según estadio AKI/ERC.")
                elif "Neonato" in p_cat or "Pediátrico" in p_cat:
                    st.error(f"🚨 ALERTA RENAL PEDIÁTRICA ({v_cr} mg/dL): Creatinina elevada para población pediátrica/neonatal. Ajuste de líquidos y nitrógeno estricto.")

        st.divider()
        if "Neonato" in p_cat:
            st.info("💡 Recordatorio Farmacéutico: Uso obligatorio de FOTOPROTECCIÓN y filtros de 1.2 micras para esta mezcla.[2, 9]")

    else:
        st.error("Error: Verifique el peso del paciente y el formato SAP (volumen numérico al final de la línea).")

st.caption("Investigación de soporte: ASPEN 2023, ESPEN 2024, Ecuación de Anderson (Hospital Pharmacy 57:6). Liderado por el Químico Farmacéutico.")
