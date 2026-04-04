import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="XCO Weekly Coach", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("Configura la API Key.")

# --- LÓGICA DE PERSISTENCIA SEMANAL ---
# Obtenemos el número de la semana actual (ej. semana 14 del 2026)
semana_actual = datetime.datetime.now().isocalendar()[1]
año_actual = datetime.datetime.now().year
id_semana = f"{año_actual}-{semana_actual}"

# Si la semana cambió o no existe plan, inicializamos
if 'id_semana_guardada' not in st.session_state or st.session_state['id_semana_guardada'] != id_semana:
    st.session_state['plan_semanal'] = None
    st.session_state['id_semana_guardada'] = id_semana

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Objetivo")
    fecha_carrera = st.date_input("Fecha Carrera", datetime.date(2026, 4, 19))
    nivel = st.select_slider("Nivel", options=["Amateur", "Intermedio", "Elite"])
    st.markdown("---")
    if st.button("🔄 Generar Nueva Planificación Semanal"):
        st.session_state['plan_semanal'] = None # Forzar regeneración

# --- GENERACIÓN CON IA ---
if st.session_state['plan_semanal'] is None:
    with st.spinner("Generando microciclo semanal..."):
        dias_meta = (fecha_carrera - datetime.date.today()).days
        prompt = f"""
        Eres un coach de XCO. Genera un entrenamiento SEMANAL COMPLETO (Lunes a Domingo).
        Atleta nivel {nivel}, faltan {dias_meta} días para la carrera.
        Usa este formato estricto para cada día:
        [LUNES] ... [MARTES] ... [MIERCOLES] ... [JUEVES] ... [VIERNES] ... [SABADO] ... [DOMINGO]
        Dentro de cada día incluye: BICI, GYM/CORE y NUTRICIÓN breve.
        """
        response = model.generate_content(prompt).text
        st.session_state['plan_semanal'] = response

# --- EXTRACCIÓN DE DATOS ---
def extraer_dia(dia_nombre, texto):
    pattern = f"\[{dia_nombre}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL)
    return res[0].strip() if res else "Día no generado."

# --- INTERFAZ DE USUARIO ---
st.title(f"📅 Plan Semanal (Semana {semana_actual})")
st.info(f"Preparación para el {fecha_carrera}. Los entrenos se mantienen fijos toda la semana.")

# Pestañas para los días de la semana
dias_semana = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_semana)

for i, nombre_dia in enumerate(dias_semana):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, st.session_state['plan_semanal'])
        
        # Resaltar el día actual
        dia_hoy_nombre = datetime.datetime.now().strftime("%A").upper()
        # Traducción simple para match
        traduccion = {"MONDAY":"LUNES", "TUESDAY":"MARTES", "WEDNESDAY":"MIERCOLES", 
                      "THURSDAY":"JUEVES", "FRIDAY":"VIERNES", "SATURDAY":"SABADO", "SUNDAY":"DOMINGO"}
        
        if traduccion.get(dia_hoy_nombre) == nombre_dia:
            st.subheader(f"🌟 HOY: {nombre_dia}")
            st.markdown(f"**{contenido}**")
        else:
            st.subheader(nombre_dia)
            st.write(contenido)

st.markdown("---")
st.caption("Nota: El plan se guarda mientras la pestaña del navegador esté abierta. Para guardarlo permanentemente meses, el siguiente paso es conectar Google Sheets.")
