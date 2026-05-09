import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v12.1 - Full Clinical Spectrum (Electrolitos Integrados)
# =========================================================

st.set_page_config(page_title="SIMENP Pro - FVL", layout="wide", page_icon="🧬")

# --- BASES DE DATOS CLÍNICAS (ASPEN / ESPEN / ESPGHAN) ---
# Se agregan requerimientos diarios de electrolitos por kg de peso (Na, K, Mg, Ca en mEq/kg | P en mmol/kg)
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
    "Lípidos": {"f": 0.2, "u": "g", "kw": ["SMOF", "LIPID", "INTRALIPID", "ACIDO GRASO"]},
    "Sodio": {"f": 2.0, "u": "mEq", "kw": ["SODIO", "NA", "GLYCOPHOS", "GLICEROFOSFATO"]},
    "Potasio": {"f": 2.0, "u": "mEq", "kw": ["POTASIO", "K"]},
    "Calcio": {"f": 0.46, "u": "mEq", "kw": ["CALCIO", "GLUCONATO"]},
    "Magnesio": {"f": 1.62, "u": "mEq", "kw": ["MAGNESIO", "MG", "SULFATO"]},
    "Fósforo": {"f": 1.0, "u": "mmol", "kw": ["FOSFORO", "FÓSFORO", "P", "FOSFATO", "GLYCOPHOS", "GLICEROFOSFATO"]},
    "Vitamina": {"f": 1.0, "u": "mL", "kw": ["CERNEVIT", "MVI", "VITAMINA"]},
    "Trazas": {"f": 1.0, "u": "mL", "kw": ["NULANZA", "PEDITRACE", "OLIGO", "TRAZA"]}
}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 👤 PERFIL DEL PACIENTE")
    p_name = st.text_input("ID Paciente", "JMLF - UCI")
    p_cat = st.selectbox("Categoría Clínica", list(GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, min_value=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.markdown("---")
    with st.expander("🔬 MONITORIZACIÓN PARACLÍNICA", expanded=True):
        st.caption("Valores en 0.0 omiten el cálculo de alerta.")
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

# --- PANEL PRINCIPAL ---
st.title("SIMENP-FVL")
st.subheader("Sistema Integral de Monitorización Enteral y Parenteral Avanzada")

sap_input = st.text_area("Pegar Sábana SAP (Componente + Volumen):", height=150)

if st.button("EJECUTAR ANÁLISIS FARMACOTERAPÉUTICO", type="primary"):
    nutri, vol_tot = {k: 0.0 for k in SAP_CONV}, 0
    
    # Parser
    for line in sap_input.strip().split('\n'):
        m = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if m:
            v = float(m.group(1).replace(',', '.'))
            vol_tot += v
            for k, data in SAP_CONV.items():
                if any(kw in line.upper() for kw in data["kw"]): nutri[k] += (v * data["f"])

    if vol_tot > 0:
        # CÁLCULOS FUNDAMENTALES
        gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
        kcal_tot = (nutri["Dextrosa"]*3.4) + (nutri["Lípidos"]*9) + (nutri["Proteína"]*4)
        nitrog = nutri["Proteína"] / 6.25
        npc_n = (kcal_tot - (nutri["Proteína"]*4)) / nitrog if nitrog > 0 else 0
        osm = ((nutri["Dextrosa"]*5) + (nutri["Proteína"]*10) + (nutri["Sodio"]+nutri["Potasio"])*2) / (vol_tot/1000)
        vel_inf = (vol_tot - 20) / horas_inf
        aa_perc = (nutri["Proteína"] / vol_tot) * 100

        # Función de Etiquetado Global
        def tag(val, rng):
            if val < rng[0]: return "🔴 SUBTERAPÉUTICO"
            elif val > rng[1]: return "🟡 EXCESIVO"
            else: return "🟢 ÓPTIMO"

        # --- PANEL SUPERIOR: MÉTRICAS E INTERPRETACIÓN ---
        st.markdown("### 1. PARÁMETROS TÉCNICOS DE INFUSIÓN")
        c1, c2, c3, c4 = st.columns(4)
        
        c1.metric("Volumen Total", f"{vol_tot:.0f} mL")
        c2.metric("Vel. Infusión", f"{vel_inf:.1f} mL/h")
        c3.metric("Osmolaridad", f"{osm:.0f} mOsm/L", "CENTRAL" if osm > 900 else "PERIFÉRICA")
        c4.metric("AA Final", f"{aa_perc:.1f} %")

        with st.container():
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"💧 **Velocidad de Infusión:** Se programan {vel_inf:.1f} mL/h asumiendo un volumen de purga estándar de equipo de 20 mL, garantizando la entrega exacta de los aportes en {horas_inf}h.")
            with col_b:
                if osm > 900:
                    st.error(f"🩸 **Osmolaridad ({osm:.0f} mOsm/L):** Excede el umbral periférico (900 mOsm/L). **Obligatorio uso de Vía Venosa Central (CVC/PICC)**.")
                else:
                    st.success(f"🩸 **Osmolaridad ({osm:.0f} mOsm/L):** Apta para infusión por vía periférica.")

        # --- TABS DE PROFUNDIDAD ---
        st.markdown("---")
        st.markdown("### 2. CONTROL FARMACOTERAPÉUTICO PROFUNDO")
        t_met, t_elec, t_fis, t_lab, t_gui = st.tabs(["🧬 MACRONUTRIENTES", "⚡ ELECTROLITOS Y MICROS", "⚖️ FISICOQUÍMICA", "🏥 PARACLÍNICOS", "📖 GUÍAS"])

        # ==========================================
        # TAB 1: MACRONUTRIENTES (Metabólico)
        # ==========================================
        with t_met:
            st.markdown(f"**Referencia:** {GUIDES[p_cat]['ref']} | **Peso Analizado:** {p_weight} kg")
            metas = GUIDES[p_cat]
            
            res_data = [
                ["Proteína", f"{nutri['Proteína']/p_weight:.2f} g/kg/d", f"{metas['prot'][0]} - {metas['prot'][1]}", tag(nutri['Proteína']/p_weight, metas['prot'])],
                ["Energía", f"{kcal_tot/p_weight:.1f} kcal/kg/d", f"{metas['kcal'][0]} - {metas['kcal'][1]}", tag(kcal_tot/p_weight, metas['kcal'])],
                ["GIR (Glucosa)", f"{gir:.2f} mg/kg/min", f"{metas['gir'][0]} - {metas['gir'][1]}", tag(gir, metas['gir'])],
                ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f} g/kg/d", f"{metas['lip'][0]} - {metas['lip'][1]}", tag(nutri['Lípidos']/p_weight, metas['lip'])],
                ["NPC:N", f"{npc_n:.1f}:1", f"{metas['npcn'][0]} - {metas['npcn'][1]}", tag(npc_n, metas['npcn'])]
            ]
            st.table(pd.DataFrame(res_data, columns=["Parámetro", "Aporte Actual", "Requerimiento (Guía)", "Interpretación"]))

        # ==========================================
        # TAB 2: ELECTROLITOS Y MICRONUTRIENTES (NUEVO)
        # ==========================================
        with t_elec:
            metas_e = GUIDES[p_cat]["elec"]
            st.markdown(f"**Análisis de Aporte Electrolítico Base ({p_cat})**")
            
            elec_data = []
            for ion in ["Sodio", "Potasio", "Magnesio", "Calcio", "Fósforo"]:
                aporte_kg = nutri[ion] / p_weight
                unidad = "mmol/kg/d" if ion == "Fósforo" else "mEq/kg/d"
                rango = metas_e[ion]
                elec_data.append([ion, f"{aporte_kg:.2f} {unidad}", f"{rango[0]} - {rango[1]}", tag(aporte_kg, rango)])
                
            st.table(pd.DataFrame(elec_data, columns=["Electrolito", "Aporte Actual", "Requerimiento (Guía)", "Interpretación"]))
            
            # Alertas Clínicas Cruzadas (Laboratorio vs Aporte)
            st.markdown("#### 🚨 Alertas Cruzadas (Prescripción vs. Laboratorio)")
            alertas_elec = 0
            if l["Na"] > 145 and nutri["Sodio"] > 0:
                st.error(f"⚠️ **HIPERNATREMIA ({l['Na']} mEq/L):** El paciente está recibiendo {nutri['Sodio']:.0f} mEq de Sodio en la mezcla. Considerar restricción o retiro.")
                alertas_elec += 1
            if l["K"] > 5.0 and nutri["Potasio"] > 0:
                st.error(f"🚨 **HIPERKALEMIA ({l['K']} mEq/L):** Contraindicación absoluta. Retirar Potasio de la NPT inmediatamente.")
                alertas_elec += 1
            if l["P"] > 0 and l["P"] < 2.5 and (nutri["Fósforo"]/p_weight) < metas_e["Fósforo"][0]:
                st.warning(f"⚠️ **HIPOFOSFATEMIA:** Paciente con Fósforo bajo ({l['P']}) y aporte en NPT subterapéutico. Optimizar aporte de Fósforo IV.")
                alertas_elec += 1
            
            if alertas_elec == 0:
                st.success("✔️ No se detectaron conflictos críticos entre los aportes electrolíticos y el perfil de laboratorio actual.")

            st.markdown("#### Micronutrientes (Trazas y Vitaminas)")
            c_m1, c_m2 = st.columns(2)
            c_m1.write(f"🧪 **Elementos Traza:** {nutri['Trazas']} mL detectados.")
            c_m2.write(f"💊 **Vitaminas:** {nutri['Vitamina']} mL detectados.")
            if nutri['Trazas'] == 0 or nutri['Vitamina'] == 0:
                st.warning("⚠️ Faltan micronutrientes en la prescripción. Su omisión prolongada puede causar síndromes carenciales severos.")

        # ==========================================
        # TAB 3: ESTABILIDAD FISICOQUÍMICA
        # ==========================================
        with t_fis:
            ca_mql = (nutri["Calcio"]/vol_tot)*1000
            p_mml = (nutri["Fósforo"]/vol_tot)*1000
            sf = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
            pl = GUIDES[p_cat]["aaf"]
            divalentes = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)

            c_f1, c_f2 = st.columns(2)
            
            with c_f1:
                st.markdown("**Riesgo de Precipitación (Ca/P):**")
                if "GLYCOPHOS" in sap_input.upper() or "GLICEROFOSFATO" in sap_input.upper():
                    st.success("✅ **Sal Orgánica Detectada:** El Glicerofosfato elimina el riesgo de precipitación termodinámica.")
                else:
                    st.write(f"Factor Anderson (SF): **{sf:.2f}** | Límite (PL): **{pl:.2f}**")
                    if sf > pl: st.error("🚨 **CRÍTICO:** Factor Anderson excedido. Riesgo de precipitación.")
                    else: st.success("✅ Sal inorgánica dentro del margen seguro.")

            with c_f2:
                st.markdown("**Estabilidad de Emulsión (Cationes):**")
                st.write(f"Divalentes (Ca++ y Mg++): **{divalentes:.1f} mEq/L**")
                if divalentes > 20 and nutri["Lípidos"] > 0:
                    st.error("🚨 **RIESGO DE RUPTURA:** Cationes > 20 mEq/L. Riesgo de creaming/coalescencia.")
                elif nutri["Lípidos"] > 0:
                    st.success("✅ Emulsión lipídica estable.")
                else: st.info("NPT Libre de Lípidos.")

        # ==========================================
        # TAB 4: PARACLÍNICOS Y ALERTAS METABÓLICAS
        # ==========================================
        with t_lab:
            st.markdown("#### Integración Bioquímica Sistémica")
            if l["Glu"] > 180:
                st.error(f"🩸 **Hiperglucemia ({l['Glu']} mg/dL):** Sugerida prescripción de **{nutri['Dextrosa'] * 0.1:.1f} UI de Insulina Regular** a la bolsa NPT.")
            if l["Alb"] > 0 and l["Alb"] < 3.0:
                st.warning(f"📉 **Hipoalbuminemia ({l['Alb']} g/dL):** Estado inflamatorio. El peso puede estar sobreestimado por edema.")
            if l["BUN"] > 0 and l["Cr"] > 0:
                ratio = l["BUN"] / l["Cr"]
                if ratio > 20: st.warning(f"💧 **Relación BUN/Cr ({ratio:.1f}):** Sugiere Azoemia Prerrenal / Hipoperfusión.")
                elif ratio < 10: st.warning(f"🫘 **Relación BUN/Cr ({ratio:.1f}):** Posible daño renal intrínseco.")

        # ==========================================
        # TAB 5: MANUAL DE GUÍAS
        # ==========================================
        with t_gui:
            st.markdown("### Tabla de Dosificación (Estándar Internacional)")
            guias_df = pd.DataFrame.from_dict(GUIDES, orient='index')
            guias_df['Proteína (g/kg)'] = guias_df['prot'].apply(lambda x: f"{x[0]} - {x[1]}")
            guias_df['Kcal (kcal/kg)'] = guias_df['kcal'].apply(lambda x: f"{x[0]} - {x[1]}")
            guias_df['GIR'] = guias_df['gir'].apply(lambda x: f"{x[0]} - {x[1]}")
            guias_df['Lípidos'] = guias_df['lip'].apply(lambda x: f"{x[0]} - {x[1]}")
            
            st.table(guias_df[['Proteína (g/kg)', 'Kcal (kcal/kg)', 'GIR', 'Lípidos', 'ref']])

    else:
        st.error("Sintaxis de prescripción vacía o incorrecta.")
        
