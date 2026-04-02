import streamlit as st
import google.generativeai as genai
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="XCO Pro-Elite Coach", layout="wide", page_icon="🧪")

# --- CONEXIÓN IA (GEMINI) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit.")

# --- BARRA LATERAL: CONFIGURACIÓN DEL ATLETA ---
with st.sidebar:
    st.header("👤 Perfil del Atleta")
    experiencia = st.selectbox("Nivel", ["Amateur", "Competitivo Estatal", "Elite"])
    fc_max = st.number_input("Frecuencia Cardíaca Máxima (BPM)", value=190)
    
    st.header("🎯 Mi Gran Carrera")
    fecha_carrera = st.date_input("¿Cuándo es tu evento?", datetime.date(2026, 4, 19))
    tipo_circuito = st.multiselect("Características", ["Técnico", "Subidas Cortas", "Drops", "Rodador"], default=["Técnico", "Subidas Cortas"])
    
    st.markdown("---")
    st.write("📌 **Zonas de Pulso sugeridas:**")
    st.caption(f"Z2 (Base): {int(fc_max*0.6)} - {int(fc_max*0.7)} bpm")
    st.caption(f"Z4 (Umbral): {int(fc_max*0.85)} - {int(fc_max*0.9)} bpm")

# --- LÓGICA DE DÍAS ---
dias_restantes = (fecha_carrera - datetime.date.today()).days
if dias_restantes <= 10: fase = "Tapering (Puesta a punto)"
elif dias_restantes <= 30: fase = "Construcción Específica"
else: fase = "Base Aeróbica"

# --- CUERPO PRINCIPAL ---
st.title(f"🏆 Plan de Entrenamiento: {fase}")
st.subheader(f"Faltan {dias_restantes} días para tu objetivo")

tab_bici, tab_gym, tab_ia = st.tabs(["🚲 Sesión Bici", "🏋️ Gym & Core", "🧠 Consultar al Coach"])

with tab_bici:
    st.header("Entrenamiento en Ruta/Trail")
    dia = datetime.datetime.now().strftime("%A")
    planes_bici = {
        "Tuesday": "1h Intervalos 30/30: 15' cal + 2 bloques de 8x(30'' Z5 / 30'' Z2) + 10' soltar.",
        "Thursday": "1h Umbral: 15' cal + 3x8' Z4 con sprint 10'' cada 2 min + 10' soltar.",
        "Saturday": "1.5h Simulacro: Ritmo carrera en circuito técnico. Enfócate en los drops.",
        "Sunday": "2.5h Fondo Z2: Rodaje constante, cadencia fluida."
    }
    st.success(planes_bici.get(dia, "Hoy toca descanso activo o rodaje muy suave (45 min Z1)."))

with tab_gym:
    st.header("Fortalecimiento XCO")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏋️ Fuerza (Martes/Jueves)")
        st.write("- **Sentadilla Búlgara:** 3x8 (Potencia en cada pierna).")
        st.write("- **Peso Muerto Rumano:** 3x10 (Cadena posterior para subidas).")
        st.write("- **Push Press:** 3x8 (Para absorber impactos de drops).")
    with col2:
        st.subheader("🧘 Core Específico (Lunes/Miércoles/Viernes)")
        st.write("- **Plancha con toque de hombros:** 3x1 min (Estabilidad en manillar).")
        st.write("- **Deadbug:** 3x15 (Control pélvico al pedalear sentado).")
        st.write("- **Lumbar (Superman):** 3x12 (Evita dolor de espalda en subidas largas).")

with tab_ia:
    st.header("Análisis de Sesión")
    feedback = st.text_area("Cuéntame: ¿Cómo te sentiste? ¿Hubo dolor? ¿Cumpliste los tiempos?")
    if st.button("Obtener Feedback del Coach"):
        with st.spinner("Analizando con Gemini..."):
            prompt = f"""Atleta {experiencia} con carrera {tipo_circuito} en {dias_restantes} días. 
            Dijo: {feedback}. 
            Dame feedback técnico de XCO y ajusta el entreno de mañana si es necesario."""
            response = model.generate_content(prompt)
            st.markdown(f"**🤖 AI Coach dice:** {response.text}")

# --- ELEMENTOS "APP TOP" ---
st.markdown("---")
st.subheader("🛠️ Check-list Mecánico Pro")
c1, c2, c3, c4 = st.columns(4)
c1.checkbox("Presión de llantas")
c2.checkbox("Lubricación de cadena")
c3.checkbox("Presión de suspensiones")
c4.checkbox("Tornillería general")
