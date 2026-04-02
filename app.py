import streamlit as st
import google.generativeai as genai
from fitparse import FitFile
import pandas as pd
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="XCO Coach AI", layout="wide")

# Conectar con la API de Google (La llave la pondrás en Secrets de Streamlit)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash') # Modelo rápido y gratuito
else:
    st.error("⚠️ Falta la configuración de la API Key en Secrets.")

# --- LÓGICA DE PROCESAMIENTO ---
def analizar_entreno(archivo, comentarios):
    # Simulación de extracción de datos del archivo .FIT
    # (Para simplificar, extraemos duración y pulso si el archivo es válido)
    try:
        fitfile = FitFile(archivo)
        puntos = []
        for record in fitfile.get_messages('record'):
            puntos.append(record.get_value('heart_rate'))
        
        fc_media = sum(filter(None, puntos)) / len(puntos) if puntos else 0
        duracion = len(puntos) // 60
        
        # PROMPT PARA LA IA
        prompt = f"""
        Eres un entrenador experto en MTB XCO. 
        Datos del atleta: 3 años de experiencia, 4º lugar estatal.
        Meta: Carrera técnica con drops el 19 de Abril.
        Datos de hoy: {duracion} minutos, FC Media: {int(fc_media)} bpm.
        Feedback del atleta: "{comentarios}"
        Analiza si el entrenamiento fue efectivo y da una recomendación específica para mañana considerando que estamos en fase de Tapering.
        Responde corto y motivador en español.
        """
        response = model.generate_content(prompt)
        return response.text, fc_media, duracion
    except Exception as e:
        return f"Error leyendo el archivo: {e}", 0, 0

# --- INTERFAZ ---
st.title("🚵‍♂️ XCO AI-Coach (Powered by Gemini)")

col_plan, col_coach = st.columns([1, 1])

with col_plan:
    st.header("📅 Tu Plan")
    dias = (datetime.date(2026, 4, 19) - datetime.date.today()).days
    st.metric("Días para el 19-Abr", dias)
    
    # Lógica de días (Ejemplo Jueves)
    st.info("**Hoy toca (1h Máx):** Intervalos Z4 + Sprints cortos. ¡No te pases de tiempo!")

with col_coach:
    st.header("🤖 Análisis del Coach")
    archivo = st.file_uploader("Sube tu archivo .FIT de Garmin/Wahoo", type=["fit"])
    feedback_usuario = st.text_area("¿Cómo sentiste las piernas y la técnica hoy?")
    
    if st.button("Enviar al Coach"):
        if archivo and feedback_usuario:
            with st.spinner("Analizando con IA..."):
                respuesta, fc, tiempo = analizar_entreno(archivo, feedback_usuario)
                st.subheader("Dictamen del Coach:")
                st.write(respuesta)
                st.sidebar.write(f"Última FC Media: {int(fc)}")
        else:
            st.warning("Sube el archivo y escribe tus sensaciones.")
