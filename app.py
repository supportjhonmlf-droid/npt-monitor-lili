import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v10.8 - Soporte Clínico con Datos Incompletos
# =========================================================

st.set_page_config(page_title="SIMENP Professional", layout="wide", page_icon="🧪")

# --- BASES TÉCNICAS ---
GUIDES = {
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir_max": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir_max": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir_max": 10.0, "lip": 2.5, "aaf": 150}
}

SAP_CONV = {
    "Proteína": {"f": 0.1, "u": "g", "kw": ["AMINO", "TRAVASOL", "AMINOSTERIL"]},
    "Dextrosa": {"f": 0.5, "u": "g", "kw": ["DEXTROSA", "GLUCOSA"]},
    "Lípidos": {"f": 0.2, "u": "g", "kw": ["SMOF", "LIPID", "INTRALIPID"]},
    "Sodio": {"f": 2.0, "u": "mEq", "kw": ["SODIO", "NA"]},
    "Potasio": {"f": 2.0, "u": "mEq", "kw": ["POTASIO", "K"]},
    "Calcio": {"f": 0.46, "u": "mEq", "kw": ["CALCIO", "GLUCONATO"]},
    "Magnesio": {"f": 1.62, "u": "mEq", "kw": ["MAGNESIO", "MG"]},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw": ["FOSFORO", "FÓSFORO", "P", "FOSFATO"]},
    "Elem. Traza": {"f": 1.0, "u": "mL", "kw": ["NULANZA", "PEDITRACE", "OLIGO"]}
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Perfil del Paciente")
    p_name = st.text_input("Nombre / ID", "Paciente Ejemplo")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, min_value=0.1)
    horas_inf = st.number_input("Horas de goteo", value=24, min_value=1)
    
    st.header("🔬 Monitorización (Opcional)")
    st.caption("Deje en 0 si no cuenta con el dato")
    v_glu = st.number_input("Glucemia (mg/dL)", value=0.0)
    v_tg = st.number_input("TG séricos (mg/dL)", value=0.0)
    v_p = st.number_input("Fósforo sérico (mg/dL)", value=0.0)
    v_bun = st.number_input("BUN (mg/dL)", value=0.0)
    v_cr = st.number_input("Creatinina (mg/dL)", value=0.0)
    v_cys = st.number_input("Cisteína añadida (mg/g AA)", value=0.0)

# --- PANEL PRINCIPAL ---
st.title("🥗 SIMENP-FVL v10.8")
sap_input = st.text_area("Pegue las líneas de SAP aquí (Nombre + Volumen mL):", height=150)

if st.button("🚀 INICIAR SEGUIMIENTO INTEGRAL", type="primary"):
    nutri = {k: 0.0 for k in SAP_CONV.keys()}
    vol_tot = 0
    
    # Parser de texto
    for line in sap_input.strip().split('\n'):
        match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if match:
            vol = float(match.group(1).replace(',', '.'))
            vol_tot += vol
            for comp, data in SAP_CONV.items():
                if any(k in line.upper() for k in data["kw"]):
                    nutri[comp] += (vol * data["f"])

    if vol_tot > 0:
        # 1. CÁLCULOS METABÓLICOS
        gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
        kcal_dex, kcal_lip, kcal_prot = nutri["Dextrosa"]*3.4, nutri["Lípidos"]*9, nutri["Proteína"]*4
        kcal_tot = kcal_dex + kcal_lip + kcal_prot
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_dex + kcal_lip) / nitrog if nitrog > 0 else 0
        
        # 2. ESTABILIDAD (Anderson)
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        ca_mql, p_mml = (nutri["Calcio"]/vol_tot)*1000, (nutri["Fósforo"]/vol_tot)*1000
        sol_factor = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
        precip_limit = GUIDES[p_cat]["aaf"] + (v_cys * GUIDES[p_cat]["aaf"] / 100)

        # --- DASHBOARD ---
        st.subheader(f"📊 Dashboard Farmacoterapéutico: {p_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("GIR", f"{gir:.2f}", delta="ALTO" if gir > GUIDES[p_cat]["gir_max"] else None, delta_color="inverse")
        c2.metric("Kcal/kg/día", f"{kcal_tot/p_weight:.1f}")
        c3.metric("Relación NPC:N", f"{npc_n:.1f}:1")
        c4.metric("AA Final", f"{aa_perc:.1f}%")

        # --- TABLA DE NUTRIENTES COMPLETA ---
        st.subheader("📋 Resumen de Aportes")
        resumen_data = []
        for n, val in nutri.items():
            resumen_data.append([n, f"{val:.2f} {SAP_CONV[n]['u']}", f"{val/p_weight:.2f} {SAP_CONV[n]['u']}/kg"])
        st.table(pd.DataFrame(resumen_data, columns=["Componente", "Aporte Total", "Aporte/kg"]))

        # --- TABS DE ANÁLISIS ---
        t_stab, t_adj = st.tabs(["⚖️ Estabilidad Fisicoquímica", "🏥 Ajustes e Interpretación"])
        
        with t_stab:
            st.write(f"**Factor SF:** {sol_factor:.2f} | **Límite PL:** {precip_limit:.2f}")
            if sol_factor > precip_limit: st.error("🚨 RIESGO DE PRECIPITACIÓN CA-P.")
            else: st.success("✅ Mezcla estable físico-químicamente.")
            
            div = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)
            if div > 20 and nutri["Lípidos"] > 0:
                st.warning(f"⚠️ Cationes divalentes elevados ({div:.1f} mEq/L). Riesgo para la emulsión.")

        with t_adj:
            # Lógica de "No Registra" para evitar falsas alertas
            st.markdown("#### 🔬 Análisis de Laboratorio")
            
            if v_glu > 0:
                if v_glu > 180: st.warning(f"🚨 Hiperglucemia ({v_glu}): Sugerido {nutri['Dextrosa']*0.1:.1f} UI Insulina.")
            else: st.info("ℹ️ Glucemia: No registra.")

            if v_tg > 0:
                if v_tg > 400: st.error(f"🚨 TG Críticos ({v_tg}): Suspender lípidos.")
                elif v_tg > 250: st.warning("⚠️ TG Elevados: Reducir aporte lipídico.")
            else: st.info("ℹ️ Triglicéridos: No registra.")

            if v_p > 0:
                if v_p < 2.5: st.error(f"🚨 Hipofosfatemia ({v_p}): Riesgo de Realimentación.")
            else: st.info("ℹ️ Fósforo sérico: No registra.")

            if v_bun > 0 and v_cr > 0:
                ratio = v_bun / v_cr
                if ratio > 20: st.warning(f"💧 Relación BUN/Cr ({ratio:.1f}): Sugiere Azoemia Prerrenal.")
            else: st.info("ℹ️ Perfil Renal (BUN/Cr): Incompleto para cálculo de relación.")

        if "NULANZA" in sap_input.upper(): st.caption("Marca detectada: Nulanza (Adulto)")
        if "PEDITRACE" in sap_input.upper(): st.caption("Marca detectada: Peditrace (Pediátrico)")

    else:
        st.error("Error: Verifique el formato SAP.")
        
