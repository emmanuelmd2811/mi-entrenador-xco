import streamlit as st
import google.generativeai as genai
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="XCO Pro AI Coach", layout="wide", page_icon="🚵‍♂️")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Falta GOOGLE_API_KEY en Secrets.")

# --- BARRA LATERAL: ENTRADA DE DATOS REALES ---
with st.sidebar:
    st.header("🎯 Configuración de Objetivo")
    # AQUÍ ELIGES TU CARRERA LIBREMENTE
    nombre_evento = st.text_input("Nombre de la carrera", "Campeonato Estatal")
    fecha_evento = st.date_input("Fecha del evento", datetime.date(2026, 4, 19))
    tipo_evento = st.selectbox("Tipo de carrera", ["XCO (Corto/Técnico)", "XCM (Maratón)", "Eliminator"])
    
    st.header("📊 Perfil Físico")
    fc_max = st.number_input("FC Máxima", value=190)
    experiencia = st.slider("Años de experiencia", 1, 20, 3)
    
    st.header("🔋 Estado Actual")
    sueno = st.select_slider("Calidad de sueño", options=["Mala", "Regular", "Buena", "Excelente"])
    dolor_piernas = st.slider("Dolor/Fatiga de piernas (1-10)", 1, 10, 3)

# --- CÁLCULO DE FASE DE ENTRENAMIENTO ---
hoy = datetime.date.today()
dias_para_meta = (fecha_evento - hoy).days

def obtener_fase(dias):
    if dias < 0: return "Post-Carrera / Recuperación"
    if dias <= 10: return "Tapering (Puesta a punto final)"
    if dias <= 40: return "Construcción (Intensidad y técnica)"
    return "Base (Resistencia y Fuerza)"

fase_actual = obtener_fase(dias_para_meta)

# --- GENERADOR DINÁMICO DE ENTRENAMIENTO (IA) ---
st.title(f"🚀 Coach IA: Fase de {fase_actual}")
st.write(f"Preparación para: **{nombre_evento}** | Faltan **{dias_para_meta}** días.")

# Botón para que la IA genere el entreno personalizado
if st.button("✨ Generar mi entrenamiento personalizado de hoy"):
    with st.spinner("La IA está analizando tu calendario y tu estado físico..."):
        
        # Este prompt es el que elimina los ejercicios predeterminados
        prompt_entreno = f"""
        Actúa como un entrenador de MTB nivel Copa del Mundo. 
        ATLETA: {experiencia} años de experiencia, FC Max {fc_max}.
        OBJETIVO: Carrera {tipo_evento} el {fecha_evento} (faltan {dias_para_meta} días).
        ESTADO HOY: Sueño {sueno}, Fatiga de piernas {dolor_piernas}/10.
        TAREA: 
        1. Genera una sesión de BICI (máximo 1h si es entre semana, más si es fin de semana).
        2. Genera una sesión de GYM o CORE que complemente la bici sin sobrecargar.
        3. Da un consejo técnico para los drops/curvas.
        No uses rutinas genéricas. Ajusta la intensidad a los días que faltan para la carrera.
        Responde con formato limpio usando negritas.
        """
        
        response = model.generate_content(prompt_entreno)
        
        # Mostrar el resultado
        st.markdown("---")
        st.markdown(response.text)

# --- SECCIÓN DE ANÁLISIS DE DATOS (FIT) ---
st.markdown("---")
st.header("📈 Cargar datos de entrenamiento (.FIT)")
archivo_fit = st.file_uploader("Sube tu archivo de Garmin/Wahoo para que el Coach te de feedback", type=["fit"])

if archivo_fit:
    st.success("Archivo cargado. En la versión Pro, aquí la IA compararía lo planeado vs lo realizado.")

# --- TABLA DE ZONAS DINÁMICA ---
with st.expander("Ver mis zonas de entrenamiento hoy"):
    st.write(f"Z1 (Recuperación): < {int(fc_max*0.6)} bpm")
    st.write(f"Z2 (Base): {int(fc_max*0.6)} - {int(fc_max*0.75)} bpm")
    st.write(f"Z3 (Tempo): {int(fc_max*0.75)} - {int(fc_max*0.85)} bpm")
    st.write(f"Z4 (Umbral): {int(fc_max*0.85)} - {int(fc_max*0.92)} bpm")
    st.write(f"Z5 (Anaeróbico): > {int(fc_max*0.92)} bpm")
