import streamlit as st
import google.generativeai as genai
import datetime

st.set_page_config(page_title="XCO Coach AI", layout="wide")

# --- CONEXIÓN SEGURA ---
if "GOOGLE_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # Intentamos usar el modelo pro que es el más estable
        model = genai.GenerativeModel('gemini-pro')
        # Prueba de conexión rápida
        test_response = model.generate_content("Hola") 
    except Exception as e:
        st.error(f"⚠️ Error de Conexión: {e}")
        st.write("Tip: Revisa que tu API Key sea correcta y tenga permisos.")
else:
    st.error("❌ No se encontró la llave GOOGLE_API_KEY en los Secrets.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎯 Objetivo")
    fecha_evento = st.date_input("Fecha de Carrera", datetime.date(2026, 4, 19))
    st.header("🔋 Estado")
    fatiga = st.slider("Fatiga (1-10)", 1, 10, 5)

# --- CUERPO ---
st.title("🚵‍♂️ Mi Entrenador XCO")

if st.button("✨ Generar Entrenamiento"):
    try:
        dias = (fecha_evento - datetime.date.today()).days
        prompt = f"Soy ciclista XCO, mi carrera es en {dias} días. Mi fatiga es {fatiga}/10. Dame un entreno pro de 1h."
        
        # Usamos gemini-pro que es el nombre universal
        response = model.generate_content(prompt)
        st.markdown(response.text)
        
    except Exception as e:
        st.error(f"Hubo un problema: {e}")
        st.info("Intentando listar modelos disponibles para tu cuenta...")
        # Esto te ayudará a saber qué nombre poner
        models = [m.name for m in genai.list_models()]
        st.write("Modelos que tu llave permite usar:", models)
