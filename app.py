import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v11.0 - Interfaz Clínica Profesional
# =========================================================

st.set_page_config(page_title="SIMENP Professional", layout="wide")

# --- GUÍAS TÉCNICAS (RANGOS DE REFERENCIA) ---
GUIDES = {
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
    "Elem. Traza": {"f": 1.0, "u": "mL", "kw": ["NULANZA", "PEDITRACE", "OLIGO"]}
}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### PERFIL DEL PACIENTE")
    p_name = st.text_input("Nombre / Identificación", "Paciente Crítico 01")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, min_value=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.markdown("---")
    
    with st.expander("MONITORIZACIÓN PARACLÍNICA", expanded=False):
        st.caption("Nota: Dejar en 0.0 los laboratorios no disponibles.")
        v_glu = st.number_input("Glucemia (mg/dL)", value=0.0)
        v_tg = st.number_input("Triglicéridos (mg/dL)", value=0.0)
        v_p = st.number_input("Fósforo (mg/dL)", value=0.0)
        v_bun = st.number_input("BUN (mg/dL)", value=0.0)
        v_cr = st.number_input("Creatinina (mg/dL)", value=0.0)
        v_cys = st.number_input("Cisteína (mg/g AA)", value=40 if "Neonato" in p_cat else 0.0)

# --- PANEL PRINCIPAL ---
st.title("SIMENP-FVL")
st.subheader("Sistema Integral de Monitorización Enteral y Parenteral")
st.markdown("---")

sap_input = st.text_area("Formulación SAP (Detalle y Volumen en mL):", height=150)

if st.button("EJECUTAR ANÁLISIS CLÍNICO", type="primary"):
    nutri, vol_tot = {k: 0.0 for k in SAP_CONV}, 0
    for line in sap_input.strip().split('\n'):
        m = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if m:
            v = float(m.group(1).replace(',', '.'))
            vol_tot += v
            for k, data in SAP_CONV.items():
                if any(kw in line.upper() for kw in data["kw"]): nutri[k] += (v * data["f"])

    if vol_tot > 0:
        # 1. CÁLCULOS METABÓLICOS
        gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
        kcal_tot = (nutri["Dextrosa"]*3.4) + (nutri["Lípidos"]*9) + (nutri["Proteína"]*4)
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_tot - (nutri["Proteína"]*4)) / nitrog if nitrog > 0 else 0
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        
        # 2. ESTABILIDAD (Anderson)
        ca_mql, p_mml = (nutri["Calcio"]/vol_tot)*1000, (nutri["Fósforo"]/vol_tot)*1000
        sf = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
        pl = GUIDES[p_cat]["aaf"] + (v_cys * GUIDES[p_cat]["aaf"] / 100)

        # --- DASHBOARD DE CUMPLIMIENTO ---
        st.markdown("### REPORTE DE METAS NUTRICIONALES")
        metas = GUIDES[p_cat]
        
        def check_meta(val, meta_range):
            if isinstance(meta_range, tuple):
                if val < meta_range[0]: return "BAJO"
                if val > meta_range[1]: return "EXCESIVO"
                return "ÓPTIMO"
            return "N/D"

        res_table = [
            ["Proteína (g/kg/d)", f"{nutri['Proteína']/p_weight:.2f}", f"{metas['prot'][0]} - {metas['prot'][1]}", check_meta(nutri['Proteína']/p_weight, metas['prot'])],
            ["Calorías (kcal/kg/d)", f"{kcal_tot/p_weight:.2f}", f"{metas['kcal'][0]} - {metas['kcal'][1]}", check_meta(kcal_tot/p_weight, metas['kcal'])],
            ["Lípidos (g/kg/d)", f"{nutri['Lípidos']/p_weight:.2f}", f"Máx. {metas['lip']}", "CUMPLE" if nutri['Lípidos']/p_weight <= metas['lip'] else "NO CUMPLE"],
            ["GIR (mg/kg/min)", f"{gir:.2f}", f"{metas['gir'][0]} - {metas['gir'][1]}", check_meta(gir, metas['gir'])],
            ["Relación NPC:N", f"{npc_n:.1f}", f"{metas['npcn'][0]} - {metas['npcn'][1]}", check_meta(npc_n, metas['npcn'])]
        ]
        st.table(pd.DataFrame(res_table, columns=["Parámetro Clínico", "Aporte Actual", "Rango Guía", "Estatus"]))

        # --- TABS DE INTERPRETACIÓN AVANZADA ---
        st.markdown("<br>", unsafe_allow_html=True)
        t_met, t_stab, t_lab = st.tabs(["ANÁLISIS METABÓLICO", "ESTABILIDAD FISICOQUÍMICA", "INTERPRETACIÓN PARACLÍNICA"])

        with t_met:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Evaluación de GIR y Aporte Energético**")
                if gir > metas['gir'][1]: st.error("[ADVERTENCIA] GIR Excesivo. Riesgo documentado de hiperglucemia, esteatosis hepática y aumento en la producción de CO2.")
                elif gir < metas['gir'][0]: st.warning("[OBSERVACIÓN] GIR Subterapéutico. Riesgo de activación de gluconeogénesis a partir de reserva de aminoácidos.")
                st.info(f"Aporte calórico total estimado: {kcal_tot:.0f} kcal/día. Concentración final de aminoácidos: {aa_perc:.1f}%.")
            with c2:
                st.markdown("**Eficiencia del Nitrógeno (NPC:N)**")
                if npc_n < metas['npcn'][0]: st.warning("[OBSERVACIÓN] Relación NPC:N baja. Los aminoácidos administrados presentan alto riesgo de ser oxidados como fuente de energía, limitando la síntesis proteica.")
                elif npc_n > metas['npcn'][1]: st.warning("[OBSERVACIÓN] Relación NPC:N alta. Posible sobrecarga de sustratos no proteicos o aporte de nitrógeno insuficiente para el estado catabólico.")

        with t_stab:
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Factor de Solubilidad (SF)", f"{sf:.2f}")
            col_s2.metric("Límite de Seguridad (PL)", f"{pl:.2f}")
            
            if sf > pl:
                st.error("[CRÍTICO] Riesgo de precipitación de Fosfato de Calcio. La relación de electrolitos excede el umbral de seguridad de Anderson.")
                st.markdown("""
                **Intervenciones Farmacéuticas Recomendadas:**
                * **Modificación de Volumen:** Aumentar el volumen total del solvente para disminuir las concentraciones absolutas.
                * **Ajuste de pH:** Confirmar requerimiento de Cisteína (especialmente en población neonatal/pediátrica).
                * **Administración Alterna:** Considerar infusión de Fósforo por vía periférica independiente.
                * **Secuencia de Preparación:** Garantizar adición de Fósforo en etapas iniciales y Calcio al finalizar la mezcla.
                """)
            elif sf > (pl * 0.8):
                st.warning("[PRECAUCIÓN] Relación Ca-P en rango limítrofe. Requiere control estricto de temperatura de almacenamiento y revisión visual detallada.")
            else:
                st.success("[ESTABLE] Las concentraciones de Fósforo y Calcio se encuentran dentro del margen de seguridad para el volumen actual.")

        with t_lab:
            if v_glu > 0 and v_glu > 180: st.warning(f"[ADVERTENCIA METABÓLICA] Glucemia de {v_glu} mg/dL. Se sugiere la adición profiláctica de {nutri['Dextrosa']*0.1:.1f} UI de Insulina Regular a la formulación.")
            if v_p > 0 and v_p < 2.5: st.error(f"[ALERTA CLÍNICA] Hipofosfatemia severa ({v_p} mg/dL). Riesgo inminente de Síndrome de Realimentación. Bloquear escalamiento de GIR.")
            if v_bun > 0 and v_cr > 0:
                ratio = v_bun / v_cr
                if ratio > 20: st.warning(f"[ALERTA RENAL] Relación BUN/Cr de {ratio:.1f}. Perfil compatible con azoemia prerrenal; evaluar el estado de hidratación del paciente.")
            if (v_glu+v_tg+v_p+v_bun+v_cr) == 0: st.info("[INFO] Parámetros no registrados para el corte clínico actual.")

        st.markdown("---")
        st.caption("Validación Técnica: ASPEN 2023, ESPEN 2024. Modelo de Solubilidad de Anderson. Responsable Técnico: JMLF.")
    else:
        st.error("Error de validación: La estructura de la formulación SAP no contiene volúmenes cuantificables.")
        
