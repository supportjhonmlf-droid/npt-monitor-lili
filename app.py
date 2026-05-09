import streamlit as st
import pandas as pd
import re

# =========================================================
# NUTRIMET-LILI v14.0 - THE MASTER BUILD
# Desarrollado por: Jhon Maicol Lopez Florian (FVL)
# =========================================================

st.set_page_config(page_title="Nutrimet-Lili v14", layout="wide", page_icon="🧬")

# --- 1. MATRIZ DE REQUERIMIENTOS POR DIAGNÓSTICO (ASPEN / ESPEN) ---
DIAGNOSTIC_GUIDES = {
    "Paciente Crítico (Sepsis/Trauma)": {
        "prot": (1.2, 2.0), "kcal": (25, 30), "gir": (3.0, 4.0), "lip": (0.8, 1.2), "npcn": (80, 100), "aaf": 100,
        "elec": {"Sodio": (1.0, 2.0), "Potasio": (1.0, 2.0), "Magnesio": (0.2, 0.3), "Calcio": (0.1, 0.2), "Fósforo": (0.2, 0.5)},
        "desc": "Prioridad: Control de catabolismo proteico y evitar sobrecarga calórica inicial."
    },
    "Falla Renal (Sin Diálisis)": {
        "prot": (0.6, 0.8), "kcal": (20, 25), "gir": (2.0, 3.0), "lip": (0.6, 1.0), "npcn": (120, 150), "aaf": 80,
        "elec": {"Sodio": (0.5, 1.0), "Potasio": (0.5, 1.0), "Magnesio": (0.1, 0.15), "Calcio": (0.1, 0.2), "Fósforo": (0.1, 0.3)},
        "desc": "Restricción proteica y de electrolitos para minimizar azoemia y sobrecarga de volumen."
    },
    "Falla Renal (Con Diálisis/TRRC)": {
        "prot": (1.5, 2.5), "kcal": (25, 35), "gir": (3.0, 4.0), "lip": (1.0, 1.5), "npcn": (80, 100), "aaf": 100,
        "elec": {"Sodio": (1.0, 2.0), "Potasio": (1.0, 2.0), "Magnesio": (0.2, 0.4), "Calcio": (0.2, 0.3), "Fósforo": (0.3, 0.6)},
        "desc": "Compensación de pérdidas por filtrado. Requiere alto aporte proteico y calórico."
    },
    "Falla Hepática (Sin Encefalopatía)": {
        "prot": (1.0, 1.5), "kcal": (25, 35), "gir": (2.0, 3.0), "lip": (0.8, 1.2), "npcn": (100, 120), "aaf": 100,
        "elec": {"Sodio": (0.5, 1.0), "Potasio": (1.0, 2.0), "Magnesio": (0.2, 0.3), "Calcio": (0.1, 0.2), "Fósforo": (0.2, 0.4)},
        "desc": "Evitar hipoglucemia y mantener balance nitrogenado positivo sin inducir amonemia."
    },
    "Paciente Obeso Crítico (IMC >30)": {
        "prot": (2.0, 2.5), "kcal": (11, 14), "gir": (1.5, 2.5), "lip": (0.5, 0.8), "npcn": (70, 90), "aaf": 100,
        "elec": {"Sodio": (1.0, 2.0), "Potasio": (1.0, 2.0), "Magnesio": (0.2, 0.3), "Calcio": (0.1, 0.2), "Fósforo": (0.2, 0.5)},
        "desc": "Alimentación hipocalórica hiperproteica para movilizar grasa endógena preservando masa magra."
    },
    "Adulto Estable": {
        "prot": (0.8, 1.2), "kcal": (20, 25), "gir": (2.0, 3.0), "lip": (0.7, 1.0), "npcn": (100, 150), "aaf": 100,
        "elec": {"Sodio": (1.0, 2.0), "Potasio": (1.0, 2.0), "Magnesio": (0.1, 0.2), "Calcio": (0.1, 0.15), "Fósforo": (0.2, 0.5)},
        "desc": "Requerimientos basales estándar."
    },
    "Neonato Pretérmino / Pediátrico": {
        "prot": (3.0, 4.5), "kcal": (90, 120), "gir": (10.0, 14.0), "lip": (2.0, 3.5), "npcn": (25, 40), "aaf": 200,
        "elec": {"Sodio": (2.0, 5.0), "Potasio": (2.0, 4.0), "Magnesio": (0.3, 0.5), "Calcio": (1.5, 3.0), "Fósforo": (1.0, 2.0)},
        "desc": "Máximo requerimiento anabólico. Vigilancia estricta de relación Calcio/Fósforo."
    }
}

# --- 2. DICCIONARIO DE CONVERSIÓN TÉCNICA (SAP) ---
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

# --- 3. SIDEBAR E IDENTIFICACIÓN ---
with st.sidebar:
    st.image("https://lili.org.co/wp-content/uploads/2021/04/Logo-FVL-Header.png", width=200)
    st.markdown("### 🧬 CONFIGURACIÓN CLÍNICA")
    p_name = st.text_input("ID Paciente", "JMLF - FVL")
    diag_choice = st.selectbox("Diagnóstico Principal (ASPEN)", list(DIAGNOSTIC_GUIDES.keys()))
    p_weight = st.number_input("Peso Actual (kg)", value=70.0, min_value=0.1)
    horas_inf = st.number_input("Horas de infusión", value=24, min_value=1)
    
    st.markdown("---")
    with st.expander("🔬 MONITORIZACIÓN PARACLÍNICA", expanded=True):
        st.caption("Nota: Ingresar 0.0 omite la alerta respectiva.")
        na_val = st.number_input("Sodio (mEq/L)", 0.0, format="%.1f")
        st.caption("Ref normal: 135.0 - 145.0")
        k_val = st.number_input("Potasio (mEq/L)", 0.0, format="%.1f")
        st.caption("Ref normal: 3.5 - 5.0")
        p_val = st.number_input("Fósforo (mg/dL)", 0.0, format="%.1f")
        st.caption("Ref normal: 2.5 - 4.5")
        mg_val = st.number_input("Magnesio (mg/dL)", 0.0, format="%.1f")
        st.caption("Ref normal: 1.8 - 2.4")
        bun_val = st.number_input("BUN (mg/dL)", 0.0, format="%.1f")
        st.caption("Ref normal: 7.0 - 20.0")
        cr_val = st.number_input("Creatinina (mg/dL)", 0.0, format="%.1f")
        st.caption("Ref normal: 0.7 - 1.3")
        alb_val = st.number_input("Albúmina (g/dL)", 0.0, format="%.1f")
        st.caption("Ref normal: 3.5 - 5.0")
        glu_val = st.number_input("Glicemia (mg/dL)", 0.0, format="%.1f")
        st.caption("Ref normal: 70.0 - 110.0")
        
        labs = {"Na": na_val, "K": k_val, "P": p_val, "Mg": mg_val, "BUN": bun_val, "Cr": cr_val, "Alb": alb_val, "Glu": glu_val}

# --- 4. CUERPO PRINCIPAL ---
st.title("Nutrimet-Lili v14.0")
st.markdown(f"**Escenario Clínico Activo:** {diag_choice}")
st.info(f"💡 {DIAGNOSTIC_GUIDES[diag_choice]['desc']}")

t_main, t_man = st.tabs(["🚀 ANÁLISIS DE PRESCRIPCIÓN", "📖 MANUAL Y GUÍAS (ASPEN/ESPEN)"])

with t_man:
    st.markdown("### Manual de Selección y Manejo por Diagnóstico")
    st.markdown("""
    **Nutrimet-Lili** aplica criterios de la ASPEN/ESPEN para validar cada prescripción:
    * **Paciente Crítico:** Evitar el *overfeeding* (sobrealimentación) calórica garantizando un aporte proteico agresivo.
    * **Falla Renal:** En falla sin diálisis, manejo conservador. En diálisis (TRRC), la filtración remueve aminoácidos, por lo que las metas proteicas se duplican.
    * **Paciente Obeso:** Alimentación hipocalórica hiperproteica para usar grasa endógena preservando músculo.
    * **Reglas FVL:** El protocolo restringe la formulación de insulina dentro de la TPN.
    """)
    # Generar tabla resumen dinámica
    df_guias = pd.DataFrame.from_dict(DIAGNOSTIC_GUIDES, orient='index')[['prot', 'kcal', 'gir', 'lip']].rename(
        columns={'prot': 'Proteína (g/kg)', 'kcal': 'Calorías (kcal/kg)', 'gir': 'GIR (mg/kg/min)', 'lip': 'Lípidos (g/kg)'}
    )
    st.table(df_guias)

with t_main:
    sap_raw = st.text_area("Pegue la formulación SAP aquí (Componente + Volumen):", height=150, placeholder="DEXTROSA 50% 500\nAMINOACIDOS 10% 800...")

    if st.button("EJECUTAR ANÁLISIS INTEGRAL", type="primary"):
        nutri, vol_tot = {k: 0.0 for k in SAP_CONV}, 0
        for line in sap_raw.strip().split('\n'):
            match = re.search(r"(\d+[\.,]?\d*)$", line.strip())
            if match:
                val = float(match.group(1).replace(',', '.'))
                vol_tot += val
                for k, d in SAP_CONV.items():
                    if any(kw in line.upper() for kw in d["kw"]): nutri[k] += (val * d["f"])

        if vol_tot > 0:
            m = DIAGNOSTIC_GUIDES[diag_choice]
            gir = (nutri["Dextrosa"] * 1000) / (p_weight * horas_inf * 60)
            kcal_tot = (nutri["Dextrosa"]*3.4) + (nutri["Lípidos"]*9) + (nutri["Proteína"]*4)
            lip_kg = nutri["Lípidos"] / p_weight
            prot_kg = nutri["Proteína"] / p_weight
            nitrog = nutri["Proteína"] / 6.25
            npc_n = (kcal_tot - (nutri["Proteína"]*4)) / nitrog if nitrog > 0 else 0
            osm = ((nutri["Dextrosa"]*5) + (nutri["Proteína"]*10) + (nutri["Sodio"]+nutri["Potasio"])*2) / (vol_tot/1000)
            vel_inf = (vol_tot - 20) / horas_inf
            aa_final = (nutri["Proteína"] / vol_tot) * 100

            # --- HEADER DE MÉTRICAS GLOBALES ---
            st.markdown("### 📊 Indicadores Técnicos de Infusión")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volumen Final", f"{vol_tot:.0f} mL")
            c2.metric("Vel. Infusión", f"{vel_inf:.1f} mL/h", help="Descuenta 20mL de purga")
            c3.metric("Osmolaridad", f"{osm:.0f} mOsm/L", "CENTRAL" if osm > 900 else "PERIFÉRICA")
            c4.metric("AA Final", f"{aa_final:.1f} %")

            # Función para semaforización
            def check(val, target):
                if val < target[0]: return "🔴 BAJO (Subterapéutico)"
                if val > target[1]: return "🟡 ALTO (Excesivo)"
                return "🟢 ÓPTIMO"

            st.markdown("---")
            # --- PESTAÑAS DE PROFUNDIDAD ---
            t_mac, t_elc, t_fis, t_lab = st.tabs(["🍎 MACRONUTRIENTES", "⚡ ELECTROLITOS Y MICROS", "⚖️ FISICOQUÍMICA", "🏥 CLÍNICA Y PARACLÍNICOS"])

            with t_mac:
                st.markdown("#### Desglose Metabólico y Aportes")
                res_table = [
                    ["Proteína", f"{prot_kg:.2f} g/kg/día", f"{m['prot'][0]} - {m['prot'][1]}", check(prot_kg, m['prot'])],
                    ["Energía Total", f"{kcal_tot/p_weight:.1f} kcal/kg/día", f"{m['kcal'][0]} - {m['kcal'][1]}", check(kcal_tot/p_weight, m['kcal'])],
                    ["Lípidos", f"{lip_kg:.2f} g/kg/día", f"{m['lip'][0]} - {m['lip'][1]}", check(lip_kg, m['lip'])],
                    ["GIR (Dextrosa)", f"{gir:.2f} mg/kg/min", f"{m['gir'][0]} - {m['gir'][1]}", check(gir, m['gir'])],
                    ["Relación NPC:N", f"{npc_n:.1f}:1", f"{m['npcn'][0]} - {m['npcn'][1]}", check(npc_n, m['npcn'])]
                ]
                st.table(pd.DataFrame(res_table, columns=["Componente", "Aporte Actual", "Rango Meta", "Estado"]))
                
                if gir > m['gir'][1]:
                    st.warning(f"⚠️ **Alerta GIR:** Riesgo de esteatosis hepática y retención de CO2 por exceso de carbohidratos.")

            with t_elc:
                st.markdown("#### Aporte Electrolítico y Trazas")
                me = m["elec"]
                elec_list = []
                # Cálculo dinámico de todos los iones
                for ion in ["Sodio", "Potasio", "Magnesio", "Calcio", "Fósforo"]:
                    val_kg = nutri[ion] / p_weight
                    elec_list.append([ion, f"{val_kg:.2f} mEq-mmol/kg", f"{me[ion][0]} - {me[ion][1]}", check(val_kg, me[ion])])
                st.table(pd.DataFrame(elec_list, columns=["Electrolito", "Aporte Actual", "Rango Meta", "Estado"]))

                st.markdown("#### 🚨 Alertas Cruzadas (Laboratorio vs NPT)")
                alertas_elec = 0
                if labs["K"] > 5.0 and nutri["Potasio"] > 0:
                    st.error(f"🚨 **HIPERKALEMIA DETECTADA ({labs['K']}):** Retirar aporte de Potasio de la mezcla NPT inmediatamente.")
                    alertas_elec += 1
                if labs["Na"] > 145 and nutri["Sodio"] > 0:
                    st.error(f"⚠️ **HIPERNATREMIA DETECTADA ({labs['Na']}):** Evaluar restricción de Sodio en la prescripción actual.")
                    alertas_elec += 1
                if labs["P"] > 0 and labs["P"] < 2.5 and (nutri["Fósforo"]/p_weight) < me["Fósforo"][0]:
                    st.warning(f"⚠️ **HIPOFOSFATEMIA ({labs['P']}):** Aporte de Fósforo en NPT subterapéutico. Optimizar rescate IV.")
                    alertas_elec += 1
                if alertas_elec == 0:
                    st.success("✔️ Sin conflictos críticos entre laboratorios ingresados y aportes electrolíticos.")

                st.markdown("#### Micronutrientes")
                c_m1, c_m2 = st.columns(2)
                c_m1.info(f"🧬 **Elementos Traza:** {nutri['Trazas']} mL detectados.")
                c_m2.info(f"💊 **Vitaminas:** {nutri['Vitamina']} mL detectados.")

            with t_fis:
                st.markdown("#### Compatibilidad y Emulsión")
                ca_mql, p_mml = (nutri["Calcio"]/vol_tot)*1000, (nutri["Fósforo"]/vol_tot)*1000
                sf = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_final if aa_final > 0 else 0
                
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    st.markdown("**Riesgo de Precipitación Ca/P**")
                    if "GLYCOPHOS" in sap_raw.upper() or "GLICEROFOSFATO" in sap_raw.upper():
                        st.success("✅ **Sal Orgánica Detectada:** Riesgo de precipitación mitigado por uso de Glycophos.")
                        st.write(f"*Nota:* El sistema ya sumó los {nutri['Fósforo']} mmol de Fósforo y el Sodio aportado por esta sal.")
                    else:
                        st.write(f"Factor Anderson (SF): **{sf:.2f}** | Límite (PL): **{m['aaf']:.2f}**")
                        if sf > m['aaf']: st.error("🚨 **CRÍTICO:** Factor Anderson excedido. La mezcla precipitará.")
                        else: st.success("✅ Sal inorgánica estable.")

                with c_f2:
                    st.markdown("**Estabilidad Lipídica**")
                    div = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)
                    st.write(f"Cationes Divalentes: **{div:.1f} mEq/L**")
                    if div > 20 and nutri["Lípidos"] > 0:
                        st.error("🚨 **RIESGO DE RUPTURA:** Cationes > 20 mEq/L. Posible coalescencia de lípidos.")
                    elif nutri["Lípidos"] > 0:
                        st.success("✅ Emulsión lipídica estable.")
                    else: st.info("NPT Libre de Lípidos.")

            with t_lab:
                st.markdown("#### Integración Sistémica FVL")
                if labs["Alb"] > 0 and labs["Alb"] < 3.0:
                    st.warning(f"📉 **Hipoalbuminemia ({labs['Alb']} g/dL):** Sugiere estado proinflamatorio severo. El peso actual podría estar sobreestimado por edema de tercer espacio.")
                if labs["BUN"] > 0 and labs["Cr"] > 0:
                    ratio = labs["BUN"] / labs["Cr"]
                    if ratio > 20:
                        st.warning(f"💧 **Relación BUN/Cr ({ratio:.1f} > 20):** Sugiere Azoemia Prerrenal. Evaluar volemia.")
                    elif ratio < 10:
                        st.info(f"🫘 **Relación BUN/Cr ({ratio:.1f} < 10):** Posible daño renal intrínseco.")
                if labs["Glu"] > 180:
                    st.error(f"🩸 **Hiperglucemia ({labs['Glu']} mg/dL):** Requiere manejo con esquema de insulina externa. *Por protocolo de seguridad institucional, NO formular insulina dentro de la mezcla NPT.*")

        else:
            st.error("Error de Lectura: Asegúrese de pegar el formato SAP correcto (Componente + Volumen).")
                
