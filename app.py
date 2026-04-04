import streamlit as st
import google.generativeai as genai
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="XCO AI-Coach Pro", layout="wide", page_icon="🚴‍♂️")

# --- CONEXIÓN CON EL MODELO DETECTADO ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos el modelo 2.5 Flash que apareció en tu lista (Rápido y potente)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura la API Key en los Secrets de Streamlit.")

# --- BARRA LATERAL: TU CONFIGURACIÓN ---
with st.sidebar:
    st.header("🎯 Mi Objetivo")
    evento = st.text_input("Nombre del evento", "Campeonato Estatal")
    fecha_carrera = st.date_input("Fecha de la carrera", datetime.date(2026, 4, 19))
    
    st.header("📊 Perfil y Estado")
    nivel = st.select_slider("Nivel actual", options=["Principiante", "Intermedio", "Avanzado/Elite"])
    fatiga = st.slider("Fatiga acumulada (1-10)", 1, 10, 3)
    
    st.markdown("---")
    dias_faltantes = (fecha_carrera - datetime.date.today()).days
    st.metric("Días para el gran día", dias_faltantes)

# --- CUERPO DE LA APP ---
st.title(f"🏆 Coach XCO: {evento}")

tab1, tab2, tab3 = st.tabs(["🔥 Entrenamiento Hoy", "🏋️ Fuerza y Core", "📝 Historial y Notas"])

# --- LÓGICA DE IA ---
if st.button("✨ Generar Plan Personalizado del Día"):
    with st.spinner("Consultando al experto..."):
        # Prompt ultra-específico para XCO
        prompt = f"""
        Actúa como un entrenador de MTB XCO de élite. 
        CONTEXTO: Atleta nivel {nivel}, faltan {dias_faltantes} días para la carrera '{evento}'.
        ESTADO: Fatiga percibida de {fatiga}/10.
        TAREA:
        1. Sesión de BICI: Máximo 1 hora (si es entre semana) enfocada en técnica y potencia explosiva según la fase.
        2. Sesión de GYM/CORE: Ejercicios específicos para estabilidad en drops y fuerza en subidas cortas.
        3. NUTRICIÓN: ¿Qué debería comer hoy para este entrenamiento?
        
        Usa un tono motivador, profesional y directo. Formatea con negritas y puntos.
        """
        
        try:
            response = model.generate_content(prompt)
            st.session_state['ultimo_plan'] = response.text
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Error al generar: {e}")

with tab1:
    if 'ultimo_plan' not in st.session_state:
        st.info("Haz clic en el botón superior para generar tu plan de hoy.")
    else:
        st.write("Plan de Bici generado arriba 👆")

with tab2:
    st.subheader("Rutina de Complemento")
    st.write("La IA integrará aquí ejercicios como Sentadilla Búlgara, Planchas dinámicas y trabajo de explosividad.")

with tab3:
    st.subheader("Notas del Atleta")
    notas = st.text_area("Registra aquí tus sensaciones post-entreno:")
    if st.button("Guardar Notas"):
        st.success("Notas guardadas (En el futuro esto irá a Google Sheets).")

# --- CHECKLIST DE SEGURIDAD ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1: st.checkbox("Presión de llantas OK")
with col2: st.checkbox("Suspensión configurada")
with col3: st.checkbox("Hidratación lista")
