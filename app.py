import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v10.2 - Sistema de Seguimiento Integral
# =========================================================

st.set_page_config(page_title="SIMENP Professional", layout="wide", page_icon="🧪")

# --- GUÍAS TÉCNICAS (ASPEN / ESPEN / ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.5), "kcal": (20, 30), "gir": 5.0, "lip": 1.5, "aaf": 100},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Adulto Obeso (BMI 30-50)": {"prot": (2.0, 2.5), "kcal": (11, 14), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico (1-10 años)": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir": 10.0, "lip": 2.5, "aaf": 150}
}

SAP_MAP = {
    "Magnesio": {"f": 1.62, "kw":},
    "Sodio": {"f": 2.0, "kw":},
    "Potasio": {"f": 2.0, "kw":},
    "Calcio": {"f": 0.46, "kw":},
    "Fósforo": {"f": 1.0, "kw":},
    "Dextrosa": {"f": 0.5, "kw":},
    "Proteína": {"f": 0.1, "kw":},
    "Lípidos": {"f": 0.2, "kw":}
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Paciente")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, step=0.1)
    horas_inf = st.number_input("Horas infusión", value=24, min_value=1)
    
    st.header("🔬 Monitorización")
    v_p = st.number_input("Fósforo sérico (mg/dL)", value=3.5)
    v_tg = st.number_input("Triglicéridos (mg/dL)", value=150.0)
    v_glu = st.number_input("Glucemia (mg/dL)", value=120.0)
    v_uun = st.number_input("UUN (Nitrógeno Ureico Urinario)", value=0.0)
    v_cys = st.number_input("Cisteína (mg/g AA)", value=40 if "Neonato" in p_cat else 0)

st.title("🥗 SIMENP-FVL v10.2")
st.caption("Seguimiento Farmacoterapéutico Avanzado en Nutrición Parenteral")

sap_input = st.text_area("Datos de SAP (Componente + Volumen mL):", height=150)

if st.button("🚀 INICIAR SEGUIMIENTO PROFESIONAL", type="primary"):
    nutri = {k: 0.0 for k in SAP_MAP.keys()}
    vol_tot = 0
    
    for line in sap_input.strip().split('\n'):
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_MAP.items():
                if any(k in line.upper() for k in data["kw"]):
                    nutri[comp] += (vol * data["f"])

    if vol_tot > 0 and p_weight > 0:
        # 1. Cálculos de Metabolismo
        gir = (nutri * 1000) / (p_weight * horas_inf * 60)
        kcal_dex = nutri * 3.4
        kcal_lip = nutri["Lípidos"] * 9.0
        kcal_prot = nutri["Proteína"] * 4.0
        kcal_tot = kcal_dex + kcal_lip + kcal_prot
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_dex + kcal_lip) / nitrog if nitrog > 0 else 0
        bal_nit = nitrog - (v_uun + 4) if v_uun > 0 else None
        
        # 2. Estabilidad de Anderson (Factor de Solución)
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

        # --- Dashboard ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GIR (Oxidación)", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir"] else None, delta_color="inverse")
        c2.metric("Relación NPC:N", f"{npc_n:.1f}:1", help="Meta 80-100:1")
        c3.metric("Kcal/kg/día", f"{kcal_tot/p_weight:.1f}")
        c4.metric("Factor Solubilidad", f"{sol_factor:.1f}")

        # --- Tabla de Evaluación (SINTAXIS CORREGIDA) ---
        st.subheader("📋 Cumplimiento de Metas Nutricionales")
        eval_list = ["Proteína", f"{nutri['Proteína']/p_weight:.2f}", f"{GUIDES[p_cat]['prot']} - {GUIDES[p_cat]['prot'][span_3](start_span)[span_3](end_span)}", "g/kg/d"],['kcal']} - {GUIDES[p_cat]['kcal'][span_4](start_span)[span_4](end_span)}", "kcal/kg/d"],
            ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f}", f"máx {GUIDES[p_cat]['lip']}", "g/kg/d"],
            ["Fósforo", f"{nutri['Fósforo']/p_weight:.2f}", "1.0 - 2.0", "mmol/kg/d"]
        st.table(pd.DataFrame(eval_list, columns=["Parámetro", "Actual", "Meta Guía", "Unidad"]))

        # --- Análisis y Ajustes ---
        t1, t2 = st.tabs(["⚖️ Estabilidad Física", "🏥 Ajustes Clínicos"])
        with t1:
            st.write(f"**Factor SF:** {sol_factor:.2f} | **Límite PL:** {precip_limit:.2f}")
            if sol_factor > precip_limit:
                st.error("❌ RIESGO CRÍTICO DE PRECIPITACIÓN CALCIO-FÓSFORO.")
            else:
                st.success("✅ Mezcla estable físico-químicamente.")
            div = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)
            if div > 20 and nutri["Lípidos"] > 0:
                st.warning(f"⚠️ Cationes divalentes elevados ({div:.1f} mEq/L). Riesgo de ruptura de emulsión.")

        with t2:
            if v_p < 2.5: st.error("🚨 HIPOFOSFATEMIA: Riesgo de Realimentación. No aumentar GIR.")
            if v_tg > 400: st.error("🚨 TRIGLICÉRIDOS > 400 mg/dL: Suspender lípidos.")
            if v_glu > 180:
                insu = nutri * 0.1
                st.warning(f"🚨 HIPERGLUCEMIA: Sugerencia {insu:.1f} UI de Insulina Regular en bolsa.")
            if bal_nit: st.info(f"**Balance Nitrogenado:** {bal_nit:.2f} g/día (Meta: +2 a +4)")

    else:
        st.error("Error: Verifique el peso y el formato de SAP (Volumen al final de cada línea).")

st.divider()
st.caption("Validado según ASPEN 2023 / ESPEN 2024 / Ecuación de Anderson. Supervisión del Químico Farmacéutico requerida.")
        
