import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v12.0 - Deep Clinical Intelligence
# =========================================================

st.set_page_config(page_title="SIMENP Pro - FVL", layout="wide", page_icon="🧬")

# --- BASES DE DATOS CLÍNICAS (ASPEN / ESPEN / ESPGHAN) ---
GUIDES = {
    "Adulto Estable": {
        "prot": (0.8, 1.2), "kcal": (20, 25), "gir": (2.0, 3.0), "lip": (0.7, 1.0), "npcn": (100, 150), "aaf": 100,
        "ref": "ASPEN 2023 / ESPEN Clinical Nutrition."
    },
    "Adulto Crítico": {
        "prot": (1.2, 2.5), "kcal": (20, 30), "gir": (3.0, 4.0), "lip": (0.8, 1.2), "npcn": (80, 100), "aaf": 100,
        "ref": "ESPEN 2024: Protein requirements in ICU."
    },
    "Neonato Pretérmino": {
        "prot": (3.0, 4.0), "kcal": (90, 120), "gir": (10.0, 14.0), "lip": (2.0, 3.0), "npcn": (25, 40), "aaf": 200,
        "ref": "ESPGHAN 2022 / Protocolos Neonatología FVL."
    },
    "Pediátrico": {
        "prot": (1.5, 2.5), "kcal": (60, 80), "gir": (6.0, 10.0), "lip": (1.5, 2.5), "npcn": (60, 80), "aaf": 150,
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

        # --- PANEL SUPERIOR: MÉTRICAS E INTERPRETACIÓN ---
        st.markdown("### 1. PARÁMETROS TÉCNICOS DE INFUSIÓN")
        c1, c2, c3, c4 = st.columns(4)
        
        c1.metric("Volumen Total", f"{vol_tot:.0f} mL")
        c2.metric("Vel. Infusión", f"{vel_inf:.1f} mL/h")
        c3.metric("Osmolaridad", f"{osm:.0f} mOsm/L", "CENTRAL" if osm > 900 else "PERIFÉRICA")
        c4.metric("AA Final", f"{aa_perc:.1f} %")

        with st.container():
            st.markdown("**Análisis Técnico:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"💧 **Velocidad de Infusión:** Se programan {vel_inf:.1f} mL/h asumiendo un volumen de purga estándar de equipo de 20 mL, garantizando la entrega exacta de los aportes en {horas_inf}h.")
            with col_b:
                if osm > 900:
                    st.error(f"🩸 **Osmolaridad ({osm:.0f} mOsm/L):** Excede el umbral de seguridad periférica (900 mOsm/L). **Obligatorio uso de Vía Venosa Central (CVC/PICC)** para evitar flebitis química severa.")
                else:
                    st.success(f"🩸 **Osmolaridad ({osm:.0f} mOsm/L):** Apta para infusión por vía periférica.")

        # --- TABS DE PROFUNDIDAD ---
        st.markdown("---")
        st.markdown("### 2. CONTROL FARMACOTERAPÉUTICO PROFUNDO")
        t_met, t_fis, t_lab, t_gui = st.tabs(["🧬 ANÁLISIS METABÓLICO", "⚖️ ESTABILIDAD FISICOQUÍMICA", "🏥 PARACLÍNICOS", "📖 GUÍAS ASPEN/ESPEN"])

        # ==========================================
        # TAB 1: METABÓLICO (Comparación y Alertas)
        # ==========================================
        with t_met:
            st.markdown(f"**Referencia:** {GUIDES[p_cat]['ref']} | **Peso Analizado:** {p_weight} kg")
            metas = GUIDES[p_cat]
            
            def tag(val, rng):
                if val < rng[0]: return "🔴 SUBTERAPÉUTICO"
                elif val > rng[1]: return "🟡 EXCESIVO"
                else: return "🟢 ÓPTIMO"

            res_data = [
                ["Proteína", f"{nutri['Proteína']/p_weight:.2f} g/kg/d", f"{metas['prot'][0]} - {metas['prot'][1]}", tag(nutri['Proteína']/p_weight, metas['prot'])],
                ["Energía", f"{kcal_tot/p_weight:.1f} kcal/kg/d", f"{metas['kcal'][0]} - {metas['kcal'][1]}", tag(kcal_tot/p_weight, metas['kcal'])],
                ["GIR (Glucosa)", f"{gir:.2f} mg/kg/min", f"{metas['gir'][0]} - {metas['gir'][1]}", tag(gir, metas['gir'])],
                ["Lípidos", f"{nutri['Lípidos']/p_weight:.2f} g/kg/d", f"{metas['lip'][0]} - {metas['lip'][1]}", tag(nutri['Lípidos']/p_weight, metas['lip'])],
                ["NPC:N", f"{npc_n:.1f}:1", f"{metas['npcn'][0]} - {metas['npcn'][1]}", tag(npc_n, metas['npcn'])]
            ]
            st.table(pd.DataFrame(res_data, columns=["Parámetro", "Aporte Actual", "Requerimiento (Guía)", "Interpretación"]))

            st.markdown("#### Justificación Metabólica:")
            if gir > metas['gir'][1]:
                st.warning("⚠️ **GIR Excesivo:** La tasa de oxidación de carbohidratos supera la capacidad hepática. Existe un alto riesgo documentado de esteatosis hepática, hiperglucemia y retención de CO2 (dificultad para destete ventilatorio).")
            elif gir < metas['gir'][0]:
                st.warning("⚠️ **GIR Subterapéutico:** El aporte de carbohidratos es insuficiente. El organismo iniciará gluconeogénesis, catabolizando la reserva de aminoácidos para obtener energía.")
            
            if npc_n < metas['npcn'][0]:
                st.info("💡 **NPC:N Baja:** Hay exceso de nitrógeno o déficit de calorías no proteicas. Los aminoácidos están siendo oxidados como fuente de energía en lugar de usarse para la síntesis muscular.")

        # ==========================================
        # TAB 2: ESTABILIDAD FISICOQUÍMICA
        # ==========================================
        with t_fis:
            st.markdown("#### Matriz de Solubilidad y Emulsión")
            ca_mql = (nutri["Calcio"]/vol_tot)*1000
            p_mml = (nutri["Fósforo"]/vol_tot)*1000
            sf = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
            pl = metas["aaf"]
            divalentes = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)

            c_f1, c_f2 = st.columns(2)
            
            # Lógica Fósforo (Orgánico vs Inorgánico)
            with c_f1:
                st.markdown("**Riesgo de Precipitación (Ca/P):**")
                if "GLYCOPHOS" in sap_input.upper() or "GLICEROFOSFATO" in sap_input.upper():
                    st.success("✅ **Sal Orgánica Detectada:** El uso de Glicerofosfato de Sodio elimina virtualmente el riesgo de precipitación termodinámica con el Calcio. Mezcla intrínsecamente segura.")
                    st.write(f"*Aporte de Fósforo Orgánico:* {nutri['Fósforo']} mmol")
                else:
                    st.write(f"Factor Anderson (SF): **{sf:.2f}** | Límite (PL): **{pl:.2f}**")
                    if sf > pl:
                        st.error("🚨 **CRÍTICO:** Factor Anderson excedido. La mezcla precipitará formando sales insolubles de Fosfato de Calcio. *Acción: Aumentar volumen o cambiar a sal orgánica.*")
                    else:
                        st.success("✅ Sal inorgánica dentro del margen de solubilidad seguro.")

            # Lógica Emulsión Lipídica
            with c_f2:
                st.markdown("**Estabilidad de la Emulsión (Cationes):**")
                st.write(f"Cationes Divalentes (Ca++ y Mg++): **{divalentes:.1f} mEq/L**")
                if divalentes > 20 and nutri["Lípidos"] > 0:
                    st.error("🚨 **RIESGO DE RUPTURA:** Concentración de cationes divalentes > 20 mEq/L. Riesgo de neutralización del potencial Zeta de las micelas lipídicas (creaming/coalescencia).")
                elif nutri["Lípidos"] > 0:
                    st.success("✅ Emulsión lipídica estable (Cationes < 20 mEq/L).")
                else:
                    st.info("NPT Libre de Lípidos.")

        # ==========================================
        # TAB 3: PARACLÍNICOS Y ALERTAS (FVL Protocols)
        # ==========================================
        with t_lab:
            st.markdown("#### Integración Bioquímica (Alertas Activas)")
            alertas = 0
            if l["Glu"] > 180:
                insu = nutri["Dextrosa"] * 0.1
                st.error(f"🩸 **Hiperglucemia ({l['Glu']} mg/dL):** Se sugiere prescripción profiláctica de **{insu:.1f} UI de Insulina Regular** a la bolsa NPT (Factor de 0.1 UI por gramo de Dextrosa).")
                alertas += 1
            if l["P"] > 0 and l["P"] < 2.5:
                st.error(f"📉 **Hipofosfatemia ({l['P']} mg/dL):** Riesgo inminente de Síndrome de Realimentación. Bloquear escalamiento calórico (GIR) y reponer electrolitos IV.")
                alertas += 1
            if l["Alb"] > 0 and l["Alb"] < 3.0:
                st.warning(f"📉 **Hipoalbuminemia ({l['Alb']} g/dL):** Estado inflamatorio severo o desnutrición. *Precaución:* El peso actual puede estar sobreestimado por edema. Vigilar sobrealimentación.")
                alertas += 1
            if l["BUN"] > 0 and l["Cr"] > 0:
                ratio = l["BUN"] / l["Cr"]
                if ratio > 20:
                    st.warning(f"💧 **Relación BUN/Cr ({ratio:.1f} > 20):** Sugiere Azoemia Prerrenal / Hipoperfusión. Evaluar aumento del volumen hídrico basal.")
                    alertas += 1
                elif ratio < 10:
                    st.warning(f"🫘 **Relación BUN/Cr ({ratio:.1f} < 10):** Posible daño renal intrínseco. Ajustar carga proteica según TFG.")
                    alertas += 1
            
            if alertas == 0:
                st.success("Sin alertas críticas en laboratorios ingresados.")

        # ==========================================
        # TAB 4: MANUAL DE GUÍAS DE DOSIFICACIÓN
        # ==========================================
        with t_gui:
            st.markdown("### Tabla de Dosificación (Estándar Internacional)")
            st.caption("Central de Mezclas - Formato de Consulta Rápida")
            guias_df = pd.DataFrame.from_dict(GUIDES, orient='index')
            # Formatear la vista del dataframe
            guias_df['Proteína (g/kg)'] = guias_df['prot'].apply(lambda x: f"{x[0]} - {x[1]}")
            guias_df['Kcal (kcal/kg)'] = guias_df['kcal'].apply(lambda x: f"{x[0]} - {x[1]}")
            guias_df['GIR (mg/kg/min)'] = guias_df['gir'].apply(lambda x: f"{x[0]} - {x[1]}")
            guias_df['Lípidos (g/kg)'] = guias_df['lip'].apply(lambda x: f"{x[0]} - {x[1]}")
            guias_df['Rel. NPC:N'] = guias_df['npcn'].apply(lambda x: f"{x[0]} - {x[1]}")
            
            st.table(guias_df[['Proteína (g/kg)', 'Kcal (kcal/kg)', 'GIR (mg/kg/min)', 'Lípidos (g/kg)', 'Rel. NPC:N', 'ref']])

    else:
        st.error("Sintaxis de prescripción vacía o incorrecta.")
            
