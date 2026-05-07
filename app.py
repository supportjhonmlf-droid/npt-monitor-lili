import streamlit as st
import pandas as pd
import re

# ==========================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ==========================================
st.set_page_config(page_title="Monitor NPT Advanced", layout="wide", page_icon="⚕️")
st.title("⚕️ Monitor Farmacoterapéutico Avanzado - NPT")
st.markdown("*Validación clínica y seguridad metabólica para pacientes Neonatales, Pediátricos y Adultos.*")
st.divider()

# ==========================================
# BASE DE DATOS CLÍNICA (Guías ASPEN)
# ==========================================
# Formato: (Límite Inferior, Límite Superior, Unidad)
GUIAS = {
    "Adulto": {
        "Magnesio": (8, 20, "mEq/día"),
        "Calcio": (10, 15, "mEq/día"),
        "Sodio": (1, 2, "mEq/kg/día"),
        "Potasio": (1, 2, "mEq/kg/día"),
        "Fosforo": (20, 40, "mmol/día"),
        "Aminoacidos": (0.8, 2.0, "g/kg/día"),
        "Lipidos": (1.0, 1.5, "g/kg/día")
    },
    "Pediatrico": {
        "Magnesio": (0.3, 0.5, "mEq/kg/día"),
        "Calcio": (0.5, 4, "mEq/kg/día"),
        "Sodio": (2, 5, "mEq/kg/día"),
        "Potasio": (2, 4, "mEq/kg/día"),
        "Fosforo": (0.5, 2, "mmol/kg/día"),
        "Aminoacidos": (1.5, 3.0, "g/kg/día"),
        "Lipidos": (1.0, 3.0, "g/kg/día")
    },
    "Neonato": {
        "Magnesio": (0.3, 0.5, "mEq/kg/día"),
        "Calcio": (2, 4, "mEq/kg/día"),
        "Sodio": (2, 5, "mEq/kg/día"),
        "Potasio": (2, 4, "mEq/kg/día"),
        "Fosforo": (1, 2, "mmol/kg/día"),
        "Aminoacidos": (2.0, 4.0, "g/kg/día"),
        "Lipidos": (1.0, 3.0, "g/kg/día")
    }
}

# Factores de conversión institucional (1 mL = X mEq/mmol/g)
FACTORES = {
    "MAGNESIO": 1.62,   # Sulfato Mg 20%
    "SODIO": 2.0,      # Natrol / NaCl 11.7%
    "POTASIO": 2.0,    # Katrol / KCl 14.9%
    "CALCIO": 0.46,    # Gluconato Ca 10%
    "DEXTROSA": 0.5,   # DAD 50%
    "AMINOACIDOS": 0.1,# Solución 10%
    "LIPIDOS": 0.2     # Emulsión 20%
}

# ==========================================
# MÓDULO 1: PACIENTE Y PARACLÍNICOS (Sidebar)
# ==========================================
with st.sidebar:
    st.header("👤 1. Perfil del Paciente")
    tipo_paciente = st.selectbox("Grupo Etario", ["Adulto", "Pediatrico", "Neonato"])
    peso = st.number_input("Peso Actual (kg)", min_value=0.1, value=70.0 if tipo_paciente == "Adulto" else 1.5, step=0.1)
    
    st.header("🧪 2. Laboratorios (Paraclínicos)")
    lab_k = st.number_input("Potasio (mEq/L)", value=4.0, step=0.1, help="Rango normal: 3.5 - 5.0")
    lab_na = st.number_input("Sodio (mEq/L)", value=140.0, step=1.0, help="Rango normal: 135 - 145")
    lab_mg = st.number_input("Magnesio (mg/dL)", value=2.0, step=0.1, help="Rango normal: 1.7 - 2.2")

# ==========================================
# MÓDULO 2: INGRESO DE SAP
# ==========================================
st.subheader("📋 3. Formulación SAP")
st.info("Pegue las líneas de la formulación directamente desde el sistema. El motor detectará el componente y el volumen final.")
sap_input = st.text_area("Texto de SAP:", "MAGNESIO 2G/10ML 20\nKATROL 10\nNATROL 15\nDEXTROSA 50% 100", height=150)

# ==========================================
# MÓDULO 3: ANÁLISIS Y CRUCE CLÍNICO
# ==========================================
if st.button("🚀 Ejecutar Validación Farmacoterapéutica", type="primary"):
    if sap_input.strip():
        resultados = []
        lineas = sap_input.strip().split('\n')
        
        for linea in lineas:
            linea = linea.upper()
            # Parser: Extrae el último número de la línea (Ej: "MAGNESIO ... 20" -> 20.0)
            match = re.search(r"(\d+\.?\d*)$", linea.strip())
            if match:
                volumen = float(match.group(1))
                comp = None
                
                # Identificación inteligente del componente
                if "MAGNESIO" in linea: comp = "Magnesio"
                elif "SODIO" in linea or "NATROL" in linea: comp = "Sodio"
                elif "POTASIO" in linea or "KATROL" in linea: comp = "Potasio"
                elif "CALCIO" in linea: comp = "Calcio"
                elif "DEXTROSA" in linea: comp = "Dextrosa"
                elif "AMINO" in linea: comp = "Aminoacidos"
                elif "LIPID" in linea or "SMOF" in linea: comp = "Lipidos"
                
                if comp:
                    factor = FACTORES.get(comp.upper(), 1.0)
                    aporte_total = volumen * factor
                    resultados.append({"Componente": comp, "Volumen (mL)": volumen, "Aporte": aporte_total})

        if resultados:
            df_resultados = pd.DataFrame(resultados)
            
            st.subheader("📊 Análisis de Dosificación vs ASPEN")
            analisis_visual = []
            
            for index, row in df_resultados.iterrows():
                comp = row["Componente"]
                aporte = row["Aporte"]
                
                if comp in GUIAS[tipo_paciente]:
                    min_guia, max_guia, unidad = GUIAS[tipo_paciente][comp]
                    
                    # Ajuste si la guía exige cálculo por kilo de peso
                    if "/kg/" in unidad:
                        rango_min = min_guia * peso
                        rango_max = max_guia * peso
                    else:
                        rango_min = min_guia
                        rango_max = max_guia
                    
                    # Definición de semáforo
                    if aporte < rango_min:
                        estado = "🟡 SUBDOSIFICADO"
                    elif aporte > rango_max:
                        estado = "🔴 SOBREDOSIFICADO"
                    else:
                        estado = "🟢 ÓPTIMO"
                    
                    analisis_visual.append({
                        "Componente": comp,
                        "Aporte Calculado": f"{round(aporte, 2)} {unidad.split('/')[0]}",
                        "Rango Recomendado": f"{round(rango_min, 2)} - {round(rango_max, 2)}",
                        "Estado Clínico": estado
                    })
            
            # Tabla interactiva
            if analisis_visual:
                st.dataframe(pd.DataFrame(analisis_visual), use_container_width=True)
            
            # ----------------------------------------
            # CRUCE CLÍNICO CON PARACLÍNICOS
            # ----------------------------------------
            st.subheader("🚨 Alertas Clínicas (Labs vs NPT)")
            alertas = 0
            
            # Cruce Potasio
            if lab_k >= 5.0 and any(df_resultados["Componente"] == "Potasio"):
                st.error(f"**HIPERPOTASEMIA:** Lab en {lab_k} mEq/L. Alto riesgo al mantener aportes de Katrol en la mezcla. Sugerencia: Suspender o reducir drásticamente.")
                alertas += 1
            elif lab_k < 3.5 and any(r["Estado Clínico"] == "🟡 SUBDOSIFICADO" for r in analisis_visual if r["Componente"] == "Potasio"):
                 st.warning(f"**HIPOPOTASEMIA:** Lab en {lab_k} mEq/L, pero el aporte en NPT está subdosificado. Sugerencia: Incrementar aporte.")
                 alertas += 1

            # Cruce Sodio
            if lab_na >= 145 and any(df_resultados["Componente"] == "Sodio"):
                 st.error(f"**HIPERNATREMIA:** Lab en {lab_na} mEq/L. Evaluar retiro de Natrol para evitar sobrecarga osmolar.")
                 alertas += 1
                 
            # Cruce Magnesio
            if lab_mg < 1.7 and any(r["Estado Clínico"] == "🟡 SUBDOSIFICADO" for r in analisis_visual if r["Componente"] == "Magnesio"):
                st.warning(f"**HIPOMAGNESEMIA:** Lab en {lab_mg} mg/dL con aporte insuficiente en NPT para corrección.")
                alertas += 1

            if alertas == 0:
                st.success("✅ No se detectaron cruces de riesgo crítico entre laboratorios y los aportes de la NPT.")

            # ----------------------------------------
            # CÁLCULOS METABÓLICOS EXTRA
            # ----------------------------------------
            if any(df_resultados["Componente"] == "Dextrosa"):
                st.subheader("⚙️ Seguridad Metabólica")
                dex_g = df_resultados[df_resultados["Componente"] == "Dextrosa"]["Aporte"].sum()
                gir = (dex_g * 1000) / (1440 * peso)
                
                # Fórmula usando LaTeX para claridad
                st.latex(r"GIR = \frac{\text{Gramos de Dextrosa} \times 1000}{1440 \times \text{Peso (kg)}}")
                
                if tipo_paciente == "Neonato" and gir > 12:
                     st.error(f"**Tasa de Infusión de Glucosa (GIR):** {round(gir, 2)} mg/kg/min ⚠️ PELIGRO: Riesgo de esteatosis hepática / lipogénesis.")
                else:
                     st.info(f"**Tasa de Infusión de Glucosa (GIR):** {round(gir, 2)} mg/kg/min")
                     
        else:
            st.warning("No se pudieron procesar los datos. Verifique que el volumen esté al final de cada línea (Ej: 'MAGNESIO 10').")
            