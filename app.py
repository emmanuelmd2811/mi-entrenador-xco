import streamlit as st
import google.generativeai as genai
import datetime
import json
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Elite Coach", layout="wide")
CONFIG_FILE = "datos_entrenamiento.json"

# --- 2. PERSISTENCIA (Lo que me pediste para no rellenar todo) ---
def guardar_datos():
    # Preparamos los datos para guardar (convertimos la fecha a texto)
    datos = dict(st.session_state)
    if 'fecha_carrera' in datos:
        datos['fecha_carrera'] = str(datos['fecha_carrera'])
    # Quitamos el objeto del modelo porque no se puede guardar en JSON
    datos.pop('model_ai', None)
    with open(CONFIG_FILE, "w") as f:
        json.dump(datos, f)

def cargar_datos():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            d = json.load(f)
            if d.get('fecha_carrera'):
                d['fecha_carrera'] = datetime.date.fromisoformat(d['fecha_carrera'])
            return d
    return None

# --- 3. CONEXIÓN IA (Regresando a la forma simple que funcionaba) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # USAMOS EL NOMBRE DIRECTO (SIN "models/")
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Configura la API KEY")
    st.stop()

# --- 4. INICIALIZACIÓN DE SESIÓN ---
if 'configurado' not in st.session_state:
    datos_viejos = cargar_datos()
    if datos_viejos:
        st.session_state.update(datos_viejos)
    else:
        st.session_state.update({'configurado': False, 'historial': {}})

# --- 5. INTERFAZ: REGISTRO ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Plan")
    with st.form("registro"):
        dep = st.selectbox("Deporte", ["Ciclismo", "Running"])
        meta = st.text_input("Nombre de la meta")
        fec = st.date_input("Fecha evento")
        if st.form_submit_button("Crear mi Plan"):
            st.session_state.update({'deporte': dep, 'nombre_meta': meta, 'fecha_carrera': fec, 'configurado': True})
            guardar_datos() # <--- GUARDAMOS PARA QUE NO SE PIERDA
            st.rerun()
    st.stop()

# --- 6. GENERACIÓN SEMANAL ---
hoy = datetime.date.today()
semana_id = f"{hoy.year}-W{hoy.isocalendar()[1]}"

if semana_id not in st.session_state['historial']:
    st.title("📅 Tu semana")
    with st.form("generar"):
        feedback = st.text_area("¿Cómo te sientes hoy?")
        if st.form_submit_button("Generar Plan"):
            prompt = f"Soy coach. Crea plan para {st.session_state['deporte']} hasta el domingo. Feedback: {feedback}. Formato: [DIA] con detalles."
            res = model_ai.generate_content(prompt)
            st.session_state['historial'][semana_id] = res.text
            guardar_datos() # <--- GUARDAMOS EL PLAN GENERADO
            st.rerun()
    st.stop()

# --- 7. DASHBOARD ---
st.title(f"🏆 {st.session_state['nombre_meta']}")
st.write(f"Deporte: {st.session_state['deporte']}")

if st.sidebar.button("🗑️ Reset (Borrar todo)"):
    if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
    st.session_state.clear()
    st.rerun()

# Mostrar el plan
plan = st.session_state['historial'][semana_id]
st.markdown(plan)
