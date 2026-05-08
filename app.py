import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v9.4 - Sistema Profesional de Nutrición Parenteral
# =========================================================

st.set_page_config(
    page_title="SIMENP-FVL Pro", 
    layout="wide", 
    page_icon="🧪"
)

# --- CONFIGURACIÓN TÉCNICA (ASPEN 2023 / ESPEN 2024) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir": 5.0, "lip": 1.0, "aaf": 100},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Adulto Obeso (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino (<1.5kg)": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir": 10.0, "lip": 2.5, "aaf": 150}
}

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

# --- SIDEBAR: DATOS DEL PACIENTE ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("ID Paciente", "Paciente 01")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.header("🔬 Monitorización")
    v_p = st.number_input("Fósforo sérico (mg/dL)", value=3.5)
    v_tg = st.number_input("Triglicéridos (mg/dL)", value=150.0)
    v_glu = st.number_input("Glucemia (mg/dL)", value=120.0)
    v_uun = st.number_input("Nitrógeno Ureico Urinario (g/24h)", value=0.0)
    v_cys = st.number_input("Cisteína (mg/g AA)", value=40 if "Neonato" in p_cat else 0)

# --- PANEL CENTRAL ---
st.title("🥗 SIMENP-FVL v9.4")
st.markdown("#### *Seguimiento Farmacoterapéutico Avanzado*")
sap_input = st.text_area("Introduzca líneas de SAP (Componente + Volumen mL):", height=150)

if st.button("🚀 INICIAR EVALUACIÓN", type="primary"):
    nutri = {k: 0.0 for k in SAP_CONV.keys()}
    vol_tot = 0
    
    # Procesamiento de SAP
    for line in sap_input.strip().split('\n'):
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_CONV.items():
                if any(k in line.upper() for k in data["kw"]):
                    nutri[comp] += (vol * data["f"])

    if vol_tot > 0:
        # 1. Cálculos Metabólicos
        gir = (nutri * 1000) / (p_weight * horas_inf * 60)
        kcal_tot = (nutri * 3.4) + (nutri["Lípidos"] * 9.0) + (nutri["Proteína"] * 4.0)
        nitrog = nutri["Proteína"] / 6.25
        npc_n = ((nutri * 3.4) + (nutri["Lípidos"] * 9.0)) / nitrog if nitrog > 0 else 0
        bal_nit = nitrog - (v_uun + 4) if v_uun > 0 else None
        
        # 2. Estabilidad de Anderson (Ca-P)
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        ca_mql = (nutri["Calcio"] / vol_tot) * 1000
        p_mml = (nutri["Fósforo"] / vol_tot) * 1000
        sol_factor = (ca_mql * p_mml) / aa_perc if aa_perc > 0 else 0
        
        aaf_val = GUIDES[p_cat]["aaf"]
        precip_limit = aaf_val + (v_cys * aaf_val / 100)
        if nutri["Lípidos"] > 0:
            precip_limit -= ((nutri["Lípidos"]/p_weight) * aaf_val / ((nutri["Proteína"]/p_weight) * 10))

        # --- Dashboard de Métricas ---
        st.subheader(f"📊 Control Farmacoterapéutico: {p_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GIR (Oxidación)", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir"] else "OK", delta_color="inverse")
        c2.metric("Relación NPC:N", f"{npc_n:.1f}:1")
        c3.metric("Osmolaridad Est.", f"{int(kcal_tot/vol_tot*1000 if vol_tot >0 else 0)} mOsm/L")
        c4.metric("AA Final", f"{aa_perc:.1f}%")

        # --- Tabla de Evaluación (CORREGIDA) ---
        st.subheader("📋 Evaluación de Metas Nutricionales")
        data_table = ["Proteína", f"{nutri['Proteína']/p_weight:.2f}", f"{GUIDES[p_cat]['prot']} - {GUIDES[p_cat]['prot'][4]}", "g/kg/d"],
           ['kcal']} - {GUIDES[p_cat]['kcal'][4]}", "kcal/kg/d"],
            ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f}", f"< {GUIDES[p_cat]['lip']}", "g/kg/d"],
            ["Calcio (Aporte)", f"{nutri['Calcio']/p_weight:.2f}", "2.0 - 4.0", "mEq/kg/d"]
        st.table(pd.DataFrame(data_table, columns=["Parámetro", "Actual", "Meta Guía", "Unidad"]))

        # --- Análisis de Estabilidad y Ajustes ---
        t1, t2 = st.tabs(["⚖️ Estabilidad Física", "🏥 Ajuste de Paraclínicos"])
        
        with t1:
            st.write(f"**Solution Factor (SF):** {sol_factor:.2f} | **Precipitation Limit (PL):** {precip_limit:.2f}")
            if sol_factor > precip_limit:
                st.error("❌ RIESGO CRÍTICO DE PRECIPITACIÓN. Reducir concentraciones de Ca/P o aumentar volumen.")
            else:
                st.success("✅ Mezcla fisicoquímicamente compatible.")
            
            divalentes = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot / 1000)
            if divalentes > 20 and nutri["Lípidos"] > 0:
                st.warning(f"⚠️ Cationes divalentes elevados ({divalentes:.1f} mEq/L). Riesgo de ruptura de emulsión.")

        with t2:
            if v_p < 2.5:
                st.error("🚨 Hipofosfatemia: Riesgo de Realimentación. No aumentar GIR.[5]")
            if v_tg > 400:
                st.error("🚨 Hipertrigliceridemia (>400). Suspender lípidos 4-6h.[6]")
            if v_glu > 180:
                insu = nutri * 0.1
                st.warning(f"🚨 Hiperglucemia: Sugerencia de añadir {insu:.1f} UI de Insulina Regular en bolsa (0.1 UI/g Dex).")
            if bal_nit:
                st.info(f"**Balance Nitrogenado:** {bal_nit:.2f} g/día (Meta: +2 a +4 para anabolismo).")

    else:
        st.error("Formato de SAP no reconocido. El volumen debe estar al final de la línea.")

st.divider()
st.caption("Validado según ASPEN 2023 / ESPEN 2024 / Ecuación de Anderson. Supervisión del Químico Farmacéutico requerida.")
            
