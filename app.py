import streamlit as st
import datetime

st.set_page_config(page_title="XCO AI Coach", page_icon="🚴‍♂️")

st.title("🚵‍♂️ Coach Digital XCO")

# --- SECCIÓN 1: ESTADO ACTUAL ---
st.header("1. Evaluación de Estado")
with st.expander("Haz clic aquí para reportar cómo vienes"):
    carga_previa = st.select_slider(
        "¿Cómo entrenaste la semana pasada?",
        options=["Nada", "Suave", "Moderado", "Muy Fuerte (Carga alta)"]
    )
    fatiga = st.slider("Nivel de fatiga actual (1-10)", 1, 10, 5)
    molestias = st.text_input("¿Alguna molestia física? (Ej: rodilla izq, espalda)")

# --- SECCIÓN 2: TU OBJETIVO ---
fecha_carrera = datetime.date(2026, 4, 19)
dias_faltantes = (fecha_carrera - datetime.date.today()).days

st.metric(label="Días para la Carrera (19 Abril)", value=dias_faltantes)

# --- SECCIÓN 3: LOGICA DE ENTRENAMIENTO ---
st.header("2. Tu Plan de Hoy")

# Lógica simple de ajuste
if fatiga >= 8:
    st.error("🚨 FATIGA ALTA detectada. Hoy toca: 45 min de Recuperación Activa (Zona 1) y estiramientos.")
else:
    # Mostramos el plan según el día de la semana
    dia_semana = datetime.datetime.now().strftime("%A")
    
    planes = {
        "Monday": "Descanso total o rodaje regenerativo (40 min Z1).",
        "Tuesday": "Series XCO: 15' calentamiento + 8x(30'' a tope / 30'' suave) x 2 bloques.",
        "Wednesday": "Técnica de Drops y Curvas: 1h 30min en sendero divertido, enfoque en fluidez.",
        "Thursday": "Umbral: 15' cal. + 3x8 min en Z4 con sprints de 10'' cada 2 min.",
        "Friday": "Descanso y revisión mecánica de la bici.",
        "Saturday": "Simulacro: 1h 15min a ritmo de carrera en circuito técnico.",
        "Sunday": "Fondo Aeróbico: 2h en Zona 2 constante."
    }
    
    # Traducción simple
    dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
    
    st.success(f"Hoy es {dias_es[dia_semana]}. Tu entrenamiento sugerido:")
    st.write(planes[dia_semana])

# --- SECCIÓN 4: ESCUCHA IA ---
st.header("3. Feedback para el Coach")
feedback = st.text_area("Cuéntame, ¿cómo te sentiste en el entrenamiento?")
if st.button("Enviar reporte"):
    st.info("Reporte guardado. Analizando datos para ajustar la sesión de mañana...")
