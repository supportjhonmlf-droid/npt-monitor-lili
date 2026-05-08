import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v11.2 - Soporte de Decisión Clínica de Alta Densidad
# =========================================================

st.set_page_config(page_title="SIMENP Professional", layout="wide")

# --- GUÍAS TÉCNICAS ACTUALIZADAS ---
GUIDES = {
    "Adulto Estable": {"prot": (0.8, 1.2), "kcal": (20, 25), "gir": (2.0, 3.0), "lip": (0.7, 1.0), "npcn": (100, 150), "aaf": 100},
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir": (3.0, 4.0), "lip": (0.8, 1.2), "npcn": (80, 100), "aaf": 100},
    "Neonato Pretérmino": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir": (10.0, 14.0), "lip": (2.0, 3.0), "npcn": (25, 40), "aaf": 200},
    "Pediátrico": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir": (6.0, 10.0), "lip": (1.5, 2.5), "npcn": (60, 80), "aaf": 150}
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
        st.caption("Deje en 0.0 si el dato no está disponible")
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

# --- LÓGICA DE PROCESAMIENTO ---
st.title("SIMENP-FVL")
st.subheader("Sistema de Monitorización Farmacoterapéutica de Nutrición Parenteral")
sap_input = st.text_area("Prescripción SAP (Componente + Volumen mL):", height=150)

if st.button("EJECUTAR EVALUACIÓN INTEGRAL", type="primary"):
    nutri, vol_tot = {k: 0.0 for k in SAP_CONV}, 0
    for line in sap_input.strip().split('\n'):
        m = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if m:
            v = float(m.group(1).replace(',', '.'))
            vol_tot += v
            for k, data in SAP_CONV.items():
                if any(kw in line.upper() for kw in data["kw"]): nutri[k] += (v * data["f"])

    if vol_tot > 0:
        # CÁLCULOS METABÓLICOS Y TÉCNICOS
        gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
        kcal_tot = (nutri["Dextrosa"]*3.4) + (nutri["Lípidos"]*9) + (nutri["Proteína"]*4)
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_tot - (nutri["Proteína"]*4)) / nitrog if nitrog > 0 else 0
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        
        # Osmolaridad Estimada (mOsm/L)
        osm = ((nutri["Dextrosa"]*5) + (nutri["Proteína"]*10) + (nutri["Sodio"]+nutri["Potasio"]+nutri["Magnesio"]+nutri["Calcio"])*2 + nutri["Fósforo"]) / (vol_tot/1000)
        # Velocidad de infusión con purga
        vel_inf = (vol_tot - 20) / horas_inf
        
        # Estabilidad Anderson (Sin Cisteína por protocolo)
        ca_mql, p_mml = (nutri["Calcio"]/vol_tot)*1000, (nutri["Fósforo"]/vol_tot)*1000
        sf = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
        pl = GUIDES[p_cat]["aaf"]

        # --- SECCIÓN 1: REPORTE DE COMPONENTES ---
        st.markdown("### 1. ANÁLISIS DE COMPONENTES (MACRO Y MICRONUTRIENTES)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Volumen Total", f"{vol_tot:.0f} mL")
        c2.metric("Velocidad Infusión", f"{vel_inf:.1f} mL/h", help="(Volumen - 20 mL purga) / Horas")
        c3.metric("Osmolaridad", f"{osm:.0f} mOsm/L", delta="CENTRAL" if osm > 900 else "PERIFÉRICA")
        c4.metric("Densidad Calórica", f"{kcal_tot/vol_tot:.2f} kcal/mL")

        nutri_df = pd.DataFrame([[k, f"{v:.2f} {SAP_CONV[k]['u']}", f"{v/p_weight:.2f} {SAP_CONV[k]['u']}/kg"] for k, v in nutri.items()], 
                                columns=["Componente", "Aporte Total Día", "Aporte por kg"])
        st.table(nutri_df)

        # --- SECCIÓN 2: PANELES DE ESTABILIDAD ---
        st.markdown("### 2. PANELES DE SEGURIDAD Y ESTABILIDAD")
        t_met, t_fis, t_sup = st.tabs(["ESTABILIDAD METABÓLICA", "ESTABILIDAD FISICOQUÍMICA", "SOPORTE E INTERPRETACIÓN"])

        with t_met:
            metas = GUIDES[p_cat]
            st.markdown("**Cumplimiento de Metas (Metabólico)**")
            def meta_tag(val, r): return "ÓPTIMO" if r[0] <= val <= r[1] else ("BAJO" if val < r[0] else "EXCESIVO")
            
            m_data = [
                ["GIR (mg/kg/min)", f"{gir:.2f}", f"{metas['gir'][0]}-{metas['gir'][1]}", meta_tag(gir, metas['gir'])],
                ["Kcal Totales (kcal/kg)", f"{kcal_tot/p_weight:.1f}", f"{metas['kcal'][0]}-{metas['kcal'][1]}", meta_tag(kcal_tot/p_weight, metas['kcal'])],
                ["Relación NPC:N", f"{npc_n:.1f}", f"{metas['npcn'][0]}-{metas['npcn'][1]}", meta_tag(npc_n, metas['npcn'])]
            ]
            st.table(pd.DataFrame(m_data, columns=["Parámetro", "Actual", "Rango Guía", "Estatus"]))
            if l["Alb"] > 0 and l["Alb"] < 3.0: st.warning(f"[ALERTA] Albúmina baja ({l['Alb']} g/dL): Posible sobreestimación de requerimientos calóricos por edema o inflamación.")

        with t_fis:
            col1, col2 = st.columns(2)
            col1.metric("Factor Anderson (SF)", f"{sf:.2f}")
            col2.metric("Límite Anderson (PL)", f"{pl:.2f}")
            
            if sf > pl: st.error("[CRÍTICO] Riesgo de precipitación de Fosfato de Calcio detectado.")
            elif sf > (pl * 0.85): st.warning("[PRECAUCIÓN] Mezcla en rango limítrofe de solubilidad.")
            else: st.success("[ESTABLE] Relación de electrolitos segura para el volumen prescrito.")
            
            divalentes = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)
            if divalentes > 20 and nutri["Lípidos"] > 0: st.warning(f"[ADVERTENCIA] Cationes divalentes: {divalentes:.1f} mEq/L. Riesgo de ruptura de emulsión lipídica.")

        with t_sup:
            st.markdown("#### GUÍA DE INTERPRETACIÓN CLÍNICA")
            with st.expander("Interpretación de Osmolaridad"):
                st.write("Mezclas > 900 mOsm/L deben administrarse estrictamente por vía Central. Vías periféricas con osmolaridades altas presentan riesgo inminente de flebitis química.")
            with st.expander("Interpretación de Perfil Renal (BUN/Cr)"):
                if l["BUN"] > 0 and l["Cr"] > 0:
                    r = l["BUN"]/l["Cr"]
                    st.write(f"Relación BUN/Cr actual: **{r:.1f}**")
                    if r > 20: st.info("Sugerencia: Azoemia Prerrenal. Evaluar balance hídrico y necesidad de optimizar volumen.")
                else: st.write("Datos insuficientes para cálculo de relación renal.")
            with st.expander("Soporte en Hiperglucemia"):
                if l["Glu"] > 180:
                    insu = nutri["Dextrosa"] * 0.1
                    st.write(f"Glucemia elevada detectada. Considerar adición de **{insu:.1f} UI** de Insulina Regular (Factor 0.1 UI/g Dex).")
            with st.expander("Interpretación Proteica (NPC:N)"):
                st.write("Una relación NPC:N fuera de rango indica que los aminoácidos no se están utilizando para síntesis de tejido (anabolismo), sino que se están desviando hacia la producción de energía (oxidación).")

        st.markdown("---")
        st.caption("Investigación de soporte: ASPEN 2023, ESPEN 2024. Algoritmos de Central de Mezclas. Validado por JMLF.")
    else:
        st.error("Error: La formulación ingresada no es válida o carece de volúmenes.")
        
