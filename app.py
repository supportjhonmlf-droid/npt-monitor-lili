import streamlit as st
import pandas as pd
import re

# =========================================================
# NUTRIMET-LILI v12.4 - Institutional Standard (FVL)
# Desarrollado por: Jhon Maicol Lopez Florian
# =========================================================

st.set_page_config(page_title="Nutrimet-Lili Pro", layout="wide", page_icon="🧬")

# --- 1. CONFIGURACIÓN DE GUÍAS CLÍNICAS (ASPEN/ESPEN/ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {
        "prot": (0.8, 1.2), "kcal": (20, 25), "gir": (2.0, 3.0), "lip": (0.7, 1.0), "npcn": (100, 150), "aaf": 100,
        "elec": {"Sodio": (1.0, 2.0), "Potasio": (1.0, 2.0), "Magnesio": (0.1, 0.2), "Calcio": (0.1, 0.15), "Fósforo": (0.2, 0.5)},
        "ref": "ASPEN 2023 / ESPEN Clinical Nutrition."
    },
    "Adulto Crítico": {
        "prot": (1.2, 2.5), "kcal": (20, 30), "gir": (3.0, 4.0), "lip": (0.8, 1.2), "npcn": (80, 100), "aaf": 100,
        "elec": {"Sodio": (1.0, 2.0), "Potasio": (1.0, 2.0), "Magnesio": (0.1, 0.2), "Calcio": (0.1, 0.15), "Fósforo": (0.2, 0.5)},
        "ref": "ESPEN 2024: ICU Guidelines."
    },
    "Neonato Pretérmino": {
        "prot": (3.0, 4.0), "kcal": (90, 120), "gir": (10.0, 14.0), "lip": (2.0, 3.0), "npcn": (25, 40), "aaf": 200,
        "elec": {"Sodio": (2.0, 5.0), "Potasio": (2.0, 4.0), "Magnesio": (0.3, 0.5), "Calcio": (1.0, 3.0), "Fósforo": (1.0, 2.0)},
        "ref": "ESPGHAN 2022 / Protocolos Neonatología FVL."
    },
    "Pediátrico": {
        "prot": (1.5, 2.5), "kcal": (60, 80), "gir": (6.0, 10.0), "lip": (1.5, 2.5), "npcn": (60, 80), "aaf": 150,
        "elec": {"Sodio": (2.0, 4.0), "Potasio": (2.0, 3.0), "Magnesio": (0.2, 0.4), "Calcio": (0.2, 0.5), "Fósforo": (0.5, 1.0)},
        "ref": "ASPEN Pediatric Nutrition Support."
    }
}

SAP_CONV = {
    "Proteína": {"f": 0.1, "u": "g", "kw": ["AMINO", "TRAVASOL", "AMINOSTERIL"]},
    "Dextrosa": {"f": 0.5, "u": "g", "kw": ["DEXTROSA", "GLUCOSA"]},
    "Lípidos": {"f": 0.2, "u": "g", "kw": ["SMOF", "LIPID", "INTRALIPID", "ACIDO GRASO", "OMEGA"]},
    "Sodio": {"f": 2.0, "u": "mEq", "kw": ["SODIO", "NA", "GLYCOPHOS", "GLICEROFOSFATO"]},
    "Potasio": {"f": 2.0, "u": "mEq", "kw": ["POTASIO", "K"]},
    "Calcio": {"f": 0.46, "u": "mEq", "kw": ["CALCIO", "GLUCONATO"]},
    "Magnesio": {"f": 1.62, "u": "mEq", "kw": ["MAGNESIO", "MG", "SULFATO"]},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw": ["FOSFORO", "FÓSFORO", "P", "FOSFATO", "GLYCOPHOS", "GLICEROFOSFATO"]},
    "Vitamina": {"f": 1.0, "u": "mL", "kw": ["CERNEVIT", "MVI", "VITAMINA", "ASCORBICO"]},
    "Trazas": {"f": 1.0, "u": "mL", "kw": ["NULANZA", "PEDITRACE", "OLIGO", "TRAZA"]}
}

# --- 2. SIDEBAR E INPUTS ---
with st.sidebar:
    st.image("https://lili.org.co/wp-content/uploads/2021/04/Logo-FVL-Header.png", width=200) # Logo FVL si tienes acceso a la URL
    st.markdown("### 👤 PERFIL DEL PACIENTE")
    p_name = st.text_input("ID Paciente", "JMLF - FVL")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, min_value=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.markdown("---")
    with st.expander("🔬 LABORATORIOS (RANGOS REF)", expanded=True):
        na_val = st.number_input("Sodio (mEq/L)", 0.0)
        st.caption("Normal: 135 - 145 mEq/L")
        k_val = st.number_input("Potasio (mEq/L)", 0.0)
        st.caption("Normal: 3.5 - 5.0 mEq/L")
        p_val = st.number_input("Fósforo (mg/dL)", 0.0)
        st.caption("Normal: 2.5 - 4.5 mg/dL")
        mg_val = st.number_input("Magnesio (mg/dL)", 0.0)
        st.caption("Normal: 1.8 - 2.4 mg/dL")
        bun_val = st.number_input("BUN (mg/dL)", 0.0)
        st.caption("Normal: 7 - 20 mg/dL")
        cr_val = st.number_input("Creatinina (mg/dL)", 0.0)
        st.caption("Normal: 0.7 - 1.3 mg/dL")
        alb_val = st.number_input("Albúmina (g/dL)", 0.0)
        st.caption("Normal: 3.5 - 5.0 g/dL")
        glu_val = st.number_input("Glicemia (mg/dL)", 0.0)
        st.caption("Normal: 70 - 110 mg/dL")

        l = {"Na": na_val, "K": k_val, "Mg": mg_val, "P": p_val, 
             "BUN": bun_val, "Cr": cr_val, "Alb": alb_val, "Glu": glu_val}

# --- 3. INTERFAZ PRINCIPAL ---
st.title("Nutrimet-Lili Pro")
st.caption("Plataforma de Farmacia Clínica Parenteral | Fundación Valle del Lili")

t_main, t_man = st.tabs(["🚀 EJECUTAR ANÁLISIS", "📖 MANUAL DE USUARIO"])

with t_man:
    st.markdown("""
    ### Manual de Operación Nutrimet-Lili
    1. **Identificación:** Ingrese el ID y peso real del paciente en el panel izquierdo.
    2. **Monitorización:** Ingrese paraclínicos actuales. El sistema generará alertas cruzadas si el aporte de electrolitos en la NPT entra en conflicto con los niveles séricos.
    3. **Ingreso SAP:** Copie la sábana de la formulación directamente. El motor detecta sales orgánicas (Glycophos) para ajustar el análisis de estabilidad.
    4. **Resultados Técnicos:**
       * **Velocidad de Infusión:** Calculada como `(Volumen - 20 mL de Purga) / Horas`.
       * **Osmolaridad:** Indica el tipo de acceso venoso requerido.
       * **GIR:** Tasa de infusión de glucosa para prevenir esteatosis hepática.
    5. **Seguridad Institucional:** No se incluye recomendación de insulina en bolsa por protocolo FVL.
    """)

with t_main:
    sap_input = st.text_area("Pegue aquí la formulación SAP (Nombre + Volumen):", height=200, placeholder="Ej: AMINOACIDOS 10% 500\nGLYCOPHOS 15...")

    if st.button("ANALIZAR PRESCRIPCIÓN", type="primary"):
        nutri, vol_tot = {k: 0.0 for k in SAP_CONV}, 0
        for line in sap_input.strip().split('\n'):
            m = re.search(r"(\d+[\.,]?\d*)$", line.strip())
            if m:
                v = float(m.group(1).replace(',', '.'))
                vol_tot += v
                for k, data in SAP_CONV.items():
                    if any(kw in line.upper() for kw in data["kw"]): nutri[k] += (v * data["f"])

        if vol_tot > 0:
            # CÁLCULOS TÉCNICOS
            gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
            kcal_tot = (nutri["Dextrosa"]*3.4) + (nutri["Lípidos"]*9) + (nutri["Proteína"]*4)
            nitrog = nutri["Proteína"] / 6.25
            npc_n = (kcal_tot - (nutri["Proteína"]*4)) / nitrog if nitrog > 0 else 0
            osm = ((nutri["Dextrosa"]*5) + (nutri["Proteína"]*10) + (nutri["Sodio"]+nutri["Potasio"])*2) / (vol_tot/1000)
            vel_inf = (vol_tot - 20) / horas_inf
            aa_perc = (nutri["Proteína"] / vol_tot) * 100

            # --- HEADER DE MÉTRICAS ---
            st.markdown("### 📊 Indicadores Técnicos")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volumen Final", f"{vol_tot:.0f} mL")
            c2.metric("Vel. Infusión", f"{vel_inf:.1f} mL/H")
            c3.metric("Osmolaridad", f"{osm:.0f} mOsm/L")
            c4.metric("GIR", f"{gir:.2f} mg/kg/min")

            # --- TABS DE ANÁLISIS ---
            t_macro, t_elec, t_stab, t_lab = st.tabs(["🍎 Macros", "⚡ Electrolitos", "⚖️ Estabilidad", "🏥 Clínica"])

            def get_tag(val, rng):
                if val < rng[0]: return "🔴 BAJO"
                if val > rng[1]: return "🟡 ALTO"
                return "🟢 ÓPTIMO"

            with t_macro:
                m = GUIDES[p_cat]
                st.markdown(f"**Análisis de Macronutrientes (Guía: {m['ref']})**")
                macro_df = pd.DataFrame([
                    ["Proteína", f"{nutri['Proteína']/p_weight:.2f} g/kg/d", f"{m['prot'][0]}-{m['prot'][1]}", get_tag(nutri['Proteína']/p_weight, m['prot'])],
                    ["Energía", f"{kcal_tot/p_weight:.1f} kcal/kg/d", f"{m['kcal'][0]}-{m['kcal'][1]}", get_tag(kcal_tot/p_weight, m['kcal'])],
                    ["NPC:N", f"{npc_n:.1f}:1", f"{m['npcn'][0]}-{m['npcn'][1]}", get_tag(npc_n, m['npcn'])]
                ], columns=["Parámetro", "Actual", "Meta", "Estatus"])
                st.table(macro_df)

            with t_elec:
                me = GUIDES[p_cat]["elec"]
                elec_list = []
                for ion in ["Sodio", "Potasio", "Magnesio", "Calcio", "Fósforo"]:
                    val_kg = nutri[ion] / p_weight
                    elec_list.append([ion, f"{val_kg:.2f}", f"{me[ion][0]}-{me[ion][1]}", get_tag(val_kg, me[ion])])
                st.table(pd.DataFrame(elec_list, columns=["Electrolito", "Aporte/kg/d", "Rango Meta", "Estatus"]))
                
                if l["K"] > 5.0 and nutri["Potasio"] > 0:
                    st.error(f"🚨 ALERTA K: Hiperkalemia detectada ({l['K']}). El aporte de {nutri['Potasio']} mEq en NPT debe ser revisado.")

            with t_stab:
                ca_mql, p_mml = (nutri["Calcio"]/vol_tot)*1000, (nutri["Fósforo"]/vol_tot)*1000
                sf = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
                st.write(f"**Factor Anderson (SF):** {sf:.2f} | **Límite (PL):** {m['aaf']:.2f}")
                
                if "GLYCOPHOS" in sap_input.upper() or "GLICEROFOSFATO" in sap_input.upper():
                    st.success("✅ Estabilidad de Calcio/Fósforo asegurada por uso de Sal Orgánica.")
                elif sf > m['aaf']:
                    st.error("🚨 Riesgo inminente de precipitación Ca/P (Sal inorgánica).")
                
                div = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)
                if div > 20 and nutri["Lípidos"] > 0:
                    st.warning(f"⚠️ Cationes Divalentes en límite ({div:.1f} mEq/L): Riesgo para la emulsión lipídica.")

            with t_lab:
                if l["Alb"] > 0 and l["Alb"] < 3.0:
                    st.warning(f"📉 Albúmina Baja ({l['Alb']}): Sugiere estado proinflamatorio. Evaluar balance hídrico.")
                if l["BUN"] > 0 and l["Cr"] > 0 and (l["BUN"]/l["Cr"]) > 20:
                    st.info("💧 Relación BUN/Cr > 20: Compatible con azoemia prerrenal por hipovolemia.")
                if l["Glu"] > 180:
                    st.error(f"🩸 Hiperglucemia ({l['Glu']}): Realizar manejo de glucemias según protocolo FVL (No en bolsa).")

        else:
            st.error("Error: Formato de prescripción vacío o no reconocido.")
            
