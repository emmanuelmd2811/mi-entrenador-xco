import streamlit as st
import google.generativeai as genai
import datetime

st.set_page_config(page_title="XCO Coach AI", layout="wide")

# --- CONEXIÓN INTELIGENTE ---
def configurar_modelo():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("❌ No hay API Key en Secrets.")
        return None

    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    try:
        # Buscamos qué modelos tienes disponibles que soporten generación de contenido
        modelos_disponibles = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        if not modelos_disponibles:
            st.error("⚠️ Tu API Key no tiene modelos de generación permitidos.")
            return None
        
        # Priorizamos Gemini 1.5 Flash, si no, el primero de la lista
        modelo_nombre = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos_disponibles else modelos_disponibles[0]
        
        st.sidebar.success(f"Conectado a: {modelo_nombre}")
        return genai.GenerativeModel(modelo_nombre)
        
    except Exception as e:
        st.error(f"⚠️ Error al listar modelos: {e}")
        return None

model = configurar_modelo()

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎯 Objetivo")
    fecha_evento = st.date_input("Fecha de Carrera", datetime.date(2026, 4, 19))
    st.header("🔋 Estado")
    fatiga = st.slider("Fatiga (1-10)", 1, 10, 5)

# --- CUERPO ---
st.title("🚵‍♂️ Mi Entrenador XCO Pro")

if st.button("✨ Generar Entrenamiento") and model:
    try:
        dias = (fecha_evento - datetime.date.today()).days
        prompt = f"Actúa como coach de MTB XCO. Carrera en {dias} días. Fatiga {fatiga}/10. Dame un entrenamiento de 1h y uno de GYM/Core."
        
        response = model.generate_content(prompt)
        st.markdown(response.text)
        
    except Exception as e:
        st.error(f"Error al generar: {e}")
else:
    if not model:
        st.info("Esperando configuración correcta de la API Key...")

# Mostrar historial de modelos si falla (para depuración)
if st.checkbox("Debug: Ver modelos permitidos"):
    try:
        st.write([m.name for m in genai.list_models()])
    except:
        st.write("No se pudo listar. Revisa tu API Key.")
