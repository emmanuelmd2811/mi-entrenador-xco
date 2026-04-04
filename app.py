import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="XCO Elite Coach", layout="wide", page_icon="🚵‍♂️")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura la API Key en Secrets.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Objetivo")
    evento = st.text_input("Carrera", "Campeonato Estatal")
    fecha_carrera = st.date_input("Fecha", datetime.date(2026, 4, 19))
    st.header("🔋 Mi Estado")
    nivel = st.select_slider("Nivel", options=["Amateur", "Intermedio", "Elite"])
    fatiga = st.slider("Fatiga (1-10)", 1, 10, 3)
    st.markdown("---")
    dias = (fecha_carrera - datetime.date.today()).days
    st.metric("Días restantes", dias)

st.title(f"🏆 Planificación: {evento}")

# --- BOTÓN DE GENERACIÓN ---
if st.button("🔄 Generar / Actualizar Entrenamiento de Hoy"):
    with st.spinner("El Coach está diseñando tu día..."):
        prompt = f"""
        Eres un coach de XCO. Genera el plan para un atleta {nivel} con carrera en {dias} días y fatiga {fatiga}/10.
        
        Debes separar la respuesta EXACTAMENTE con estas etiquetas para que mi sistema las procese:
        [BICI] aquí el entrenamiento de ciclismo de 1h con intervalos o técnica.
        [GYM] aquí la rutina de fuerza y core específica.
        [NUTRICION] qué comer antes, durante y después hoy.
        """
        try:
            response = model.generate_content(prompt).text
            # Guardamos en sesión para que no se borre al cambiar de pestaña
            st.session_state['plan_completo'] = response
        except Exception as e:
            st.error(f"Error: {e}")

# --- LÓGICA DE SEPARACIÓN DE CONTENIDO ---
plan = st.session_state.get('plan_completo', "")

# Función para extraer secciones usando etiquetas
def extraer_seccion(tag, texto):
    pattern = f"\[{tag}\](.*?)(?=\[|$)"
    resultado = re.findall(pattern, texto, re.DOTALL)
    return resultado[0].strip() if resultado else "Haz clic en el botón para generar."

# --- DISEÑO DE PESTAÑAS (TABS) ---
tab_bici, tab_gym, tab_nutri, tab_check = st.tabs(["🚲 Ciclismo", "🏋️ Fuerza & Core", "🍎 Nutrición", "🛠️ Mecánica"])

with tab_bici:
    st.subheader("Planificación de Rodaje / Series")
    contenido_bici = extraer_seccion("BICI", plan)
    st.info(contenido_bici)

with tab_gym:
    st.subheader("Complemento de Fuerza")
    contenido_gym = extraer_seccion("GYM", plan)
    st.warning(contenido_gym)

with tab_nutri:
    st.subheader("Estrategia Alimentaria")
    contenido_nutri = extraer_seccion("NUTRICION", plan)
    st.success(contenido_nutri)

with tab_check:
    st.subheader("Checklist Pre-Salida")
    c1, c2 = st.columns(2)
    with c1:
        st.checkbox("Presión neumáticos (XCO: ~18-22 psi)")
        st.checkbox("Carga de cambios electrónicos (si aplica)")
    with c2:
        st.checkbox("Suspensión (SAG correcto)")
        st.checkbox("Herramienta y mechas listas")
