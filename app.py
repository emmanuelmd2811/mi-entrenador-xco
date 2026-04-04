import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="XCO Elite Coach", layout="wide", page_icon="🚵‍♂️")

# --- CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("Configura la API Key en Secrets.")

# --- LÓGICA DE MEMORIA (PERFIL DEL ATLETA) ---
# Inicializamos el estado si no existe
if 'configurado' not in st.session_state:
    st.session_state['configurado'] = False

# Verificar si el objetivo ya expiró
hoy = datetime.date.today()
if st.session_state.get('fecha_carrera') and hoy > st.session_state['fecha_carrera']:
    st.session_state['configurado'] = False # Reiniciar para nuevo objetivo

# --- PANTALLA DE CONFIGURACIÓN INICIAL ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Temporada de XCO")
    st.subheader("Cuéntame de ti para crear tu plan maestro")
    
    with st.form("registro_atleta"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_carrera = st.text_input("¿Cómo se llama tu carrera objetivo?", "Copa Nacional")
            fecha_carrera = st.date_input("¿Qué día es la carrera?", hoy + datetime.timedelta(days=60))
            nivel = st.select_slider("Nivel actual", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
        with col2:
            dias_semana = st.slider("¿Cuántos días puedes entrenar por semana?", 1, 7, 5)
            exp_años = st.number_input("Años de experiencia en ciclismo", 0, 40, 3)
            fc_max = st.number_input("Tu Frecuencia Cardíaca Máxima", 150, 220, 190)
        
        enviar = st.form_submit_button("Establecer Objetivo y Generar Plan")
        
        if enviar:
            st.session_state['nombre_carrera'] = nombre_carrera
            st.session_state['fecha_carrera'] = fecha_carrera
            st.session_state['nivel'] = nivel
            st.session_state['dias_entreno'] = dias_semana
            st.session_state['configurado'] = True
            st.session_state['plan_semanal'] = None # Forzar primera generación
            st.rerun()
    st.stop() # Detiene la ejecución aquí hasta que se configure

# --- DASHBOARD PRINCIPAL (Si ya está configurado) ---
semana_id = f"{hoy.year}-{hoy.isocalendar()[1]}"

with st.sidebar:
    st.title("🛡️ Tu Perfil")
    st.write(f"**Evento:** {st.session_state['nombre_carrera']}")
    st.write(f"**Nivel:** {st.session_state['nivel']}")
    dias_restantes = (st.session_state['fecha_carrera'] - hoy).days
    st.metric("Días para la meta", dias_restantes)
    
    if st.button("🗑️ Reiniciar Objetivo"):
        st.session_state['configurado'] = False
        st.rerun()

# --- GENERACIÓN/CARGA DE PLAN SEMANAL ---
if st.session_state.get('plan_semanal_id') != semana_id:
    with st.spinner("Diseñando tu semana de entrenamiento..."):
        prompt = f"""
        Como Coach XCO Elite, genera un plan SEMANAL para un atleta {st.session_state['nivel']} con {st.session_state['dias_entreno']} días disponibles.
        Carrera: {st.session_state['nombre_carrera']} en {dias_restantes} días.
        Formato: Usa [LUNES], [MARTES], etc. 
        Dentro de cada día separa con subtítulos: **BICICLETA**, **GYM/CORE**, **NUTRICIÓN**.
        Usa un lenguaje motivador y limpio.
        """
        st.session_state['plan_semanal'] = model.generate_content(prompt).text
        st.session_state['plan_semanal_id'] = semana_id

# --- INTERFAZ DE ENTRENAMIENTO ---
st.title(f"📅 Semana {hoy.isocalendar()[1]}: {st.session_state['nombre_carrera']}")

def extraer_dia(dia_nombre, texto):
    pattern = f"\[{dia_nombre}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL)
    return res[0].strip() if res else "Día de descanso o recuperación activa."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)

traduccion = {"Monday":"LUNES", "Tuesday":"MARTES", "Wednesday":"MIERCOLES", 
              "Thursday":"JUEVES", "Friday":"VIERNES", "Saturday":"SABADO", "Sunday":"DOMINGO"}
dia_hoy = traduccion.get(hoy.strftime("%A"))

for i, nombre_dia in enumerate(dias_lista):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, st.session_state['plan_semanal'])
        
        if nombre_dia == dia_hoy:
            st.success(f"⚡ ¡ESTE ES TU ENTRENAMIENTO DE HOY!")
        
        # Limpiamos el contenido para que no se vea amontonado
        secciones = contenido.split("**")
        for seccion in secciones:
            if seccion.strip():
                if any(keyword in seccion.upper() for keyword in ["BICICLETA", "GYM", "NUTRICIÓN"]):
                    st.subheader(f"🔹 {seccion.strip()}")
                else:
                    st.write(seccion.strip())
        st.divider()
