import streamlit as st
import pandas as pd
import re

# =========================================================
# SIMENP-FVL v10.7 - Optimizado y Compacto
# =========================================================

st.set_page_config(page_title="SIMENP Pro", layout="wide", page_icon="🧪")

# --- CONFIGURACIÓN TÉCNICA ---
GUIDES = {
    "Adulto Crítico": {"prot": (1.2, 2.5), "kcal": (20, 30), "gir": 4.0, "lip": 1.0, "aaf": 100},
    "Neonato Pretérmino": {"prot": (3.0, 4.0), "kcal": (90, 120), "gir": 14.0, "lip": 3.0, "aaf": 200},
    "Pediátrico": {"prot": (1.5, 2.5), "kcal": (60, 80), "gir": 10.0, "lip": 2.5, "aaf": 150}
}

SAP_CONV = {
    "Proteína": (0.1, "g", ["AMINO", "TRAVASOL", "AMINOSTERIL"]),
    "Dextrosa": (0.5, "g", ["DEXTROSA", "GLUCOSA"]),
    "Lípidos": (0.2, "g", ["SMOF", "LIPID", "INTRALIPID"]),
    "Sodio": (2.0, "mEq", ["SODIO", "NA"]),
    "Potasio": (2.0, "mEq", ["POTASIO", "K"]),
    "Calcio": (0.46, "mEq", ["CALCIO", "GLUCONATO"]),
    "Magnesio": (1.62, "mEq", ["MAGNESIO", "MG"]),
    "Fósforo": (1.0, "mmol", ["FOSFORO", "FÓSFORO", "P", "FOSFATO"]),
    "Trazas": (1.0, "mL", ["NULANZA", "PEDITRACE", "OLIGO"])
}

# --- INTERFAZ ---
with st.sidebar:
    st.header("👤 Paciente")
    cat = st.selectbox("Categoría", list(GUIDES.keys()))
    weight = st.number_input("Peso (kg)", 70.0)
    hrs = st.number_input("Horas", 24)
    with st.expander("🔬 Laboratorios"):
        labs = {
            "Glu": st.number_input("Glu", 120), "TG": st.number_input("TG", 150),
            "P": st.number_input("P", 3.5), "BUN": st.number_input("BUN", 15),
            "Cr": st.number_input("Cr", 0.9), "Cys": st.number_input("Cisteína", 0)
        }

st.title("🥗 SIMENP-FVL v10.7")
sap_input = st.text_area("Formulación SAP (Nombre + Volumen):", height=150)

if st.button("🚀 PROCESAR ANÁLISIS CLÍNICO"):
    nutri, vol_tot = {k: 0.0 for k in SAP_CONV}, 0
    
    for line in sap_input.strip().split('\n'):
        m = re.search(r"(\d+[\.,]?\d*)$", line.strip())
        if m:
            v = float(m.group(1).replace(',', '.'))
            vol_tot += v
            for k, (f, u, keywords) in SAP_CONV.items():
                if any(kw in line.upper() for kw in keywords): nutri[k] += (v * f)

    if vol_tot > 0:
        # --- CÁLCULOS CLAVE ---
        gir = (nutri["Dextrosa"] * 1000) / (weight * hrs * 60)
        kcal = (nutri["Dextrosa"]*3.4) + (nutri["Lípidos"]*9) + (nutri["Proteína"]*4)
        aa_perc = (nutri["Proteína"] / vol_tot) * 100
        
        # Estabilidad Anderson
        ca_mql, p_mml = (nutri["Calcio"]/vol_tot)*1000, (nutri["Fósforo"]/vol_tot)*1000
        sf = ((ca_mql * 0.863) * (p_mml * 1.19)) / aa_perc if aa_perc > 0 else 0
        pl = GUIDES[cat]["aaf"] + (labs["Cys"] * GUIDES[cat]["aaf"] / 100)

        # --- REPORTE DE NUTRIENTES ---
        st.subheader("📊 Seguimiento de Nutrientes")
        df = pd.DataFrame([[k, f"{v:.2f} {SAP_CONV[k][1]}", f"{v/weight:.2f}"] for k, v in nutri.items()], 
                          columns=["Componente", "Total Día", "Por kg/día"])
        st.table(df)

        # --- MÓDULOS DE INTERPRETACIÓN ---
        t1, t2 = st.tabs(["⚖️ Estabilidad Fisicoquímica", "🏥 Interpretación Metabólica"])
        
        with t1:
            c1, c2 = st.columns(2)
            c1.metric("Factor Anderson (SF)", f"{sf:.2f}", help="Límite de precipitación Ca-P")
            c2.metric("Límite Seguro (PL)", f"{pl:.2f}")
            
            if sf > pl: st.error("🚨 ALERTA: Riesgo de precipitación de Fosfato de Calcio.")
            else: st.success("✅ Mezcla estable para 24h.")
            
            divalentes = (nutri["Calcio"] + nutri["Magnesio"]) / (vol_tot/1000)
            if divalentes > 20 and nutri["Lípidos"] > 0:
                st.warning(f"⚠️ Cationes Divalentes: {divalentes:.1f} mEq/L. Riesgo de inestabilidad lipídica (>20).")

        with t2:
            st.markdown(f"**GIR:** {gir:.2f} | **Kcal/kg:** {kcal/weight:.1f} | **NPC:N:** {(kcal-(nutri['Proteína']*4))/(nutri['Proteína']/6.25):.1f}:1")
            
            if labs["TG"] > 400: st.error("🚨 Hipertrigliceridemia severa: Suspender lípidos.")
            if labs["P"] < 2.5: st.error("🚨 Hipofosfatemia: Riesgo de Realimentación. Limitar GIR.")
            if labs["Cr"] > 0 and (labs["BUN"]/labs["Cr"]) > 20: 
                st.info("💧 Relación BUN/Cr > 20: Sugiere azoemia prerrenal (Optimizar hidratación).")
            
            if "NULANZA" in sap_input.upper(): st.caption("🧪 Elementos traza identificados como Nulanza (Adulto).")
            if "PEDITRACE" in sap_input.upper(): st.caption("🧪 Elementos traza identificados como Peditrace (Pediátrico).")

    else: st.error("Error en el formato del SAP.")
        
