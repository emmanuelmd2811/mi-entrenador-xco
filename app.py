import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="XCO Adaptive Coach", layout="wide", page_icon="🚵‍♂️")

st.markdown("""
    <style>
    .stApp { background-color: #1C1E23; }
    .stMarkdown, p, span { color: #D1D5DB !important; }
    h1, h2, h3 { color: #E5E7EB !important; font-family: 'Inter', sans-serif; }
    div.stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #2D3139; padding: 8px; border-radius: 12px; }
    div.stTabs [data-baseweb="tab"] { background-color: #374151; border-radius: 8px; color: #9CA3AF !important; padding: 8px 16px; }
    div.stTabs [aria-selected="true"] { background-color: #10B981 !important; color: white !important; font-weight: bold; }
    div[data-testid="stVerticalBlock"] > div.element-container div.stMarkdown div.stContainer {
        border: 1px solid #4B5563; border-radius: 15px; background-color: #262B33; padding: 18px; margin-bottom: 12px;
    }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 3. LÓGICA DE TIEMPO Y MEMORIA DE LARGO PLAZO ---
hoy = datetime.date.today()
nombre_dia_hoy = hoy.strftime("%A").upper()
# Diccionario de traducción para lógica interna
traduccion_dias = {"MONDAY":"LUNES", "TUESDAY":"MARTES", "WEDNESDAY":"MIERCOLES", 
                  "THURSDAY":"JUEVES", "FRIDAY":"VIERNES", "SATURDAY":"SABADO", "SUNDAY":"DOMINGO"}
dia_actual_es = traduccion_dias.get(nombre_dia_hoy)
num_semana = hoy.isocalendar()[1]
semana_id = f"{hoy.year}-W{num_semana}"

# Inicializar historial y estado
if 'historial_entrenamientos' not in st.session_state:
    st.session_state['historial_entrenamientos'] = {}
if 'configurado' not in st.session_state:
    st.session_state['configurado'] = False

# --- 4. ONBOARDING (CONFIGURACIÓN INICIAL) ---
if not st.session_state['configurado']:
    st.title("🎯 Bienvenida al Coach XCO Adaptativo")
    with st.form("onboarding"):
        c1, c2 = st.columns(2)
        with c1:
            nombre_c = st.text_input("Carrera Objetivo", "Epic MTB")
            fecha_c = st.date_input("Fecha Carrera", hoy + datetime.timedelta(days=30))
        with c2:
            nivel = st.selectbox("Tu Nivel", ["Principiante", "Intermedio", "Avanzado", "Elite"])
            dias_w = st.slider("Días de entreno/semana", 1, 7, 5)
        if st.form_submit_button("🔥 Empezar Temporada"):
            st.session_state.update({'nombre_carrera': nombre_c, 'fecha_carrera': fecha_c, 
                                    'nivel': nivel, 'dias_w': dias_w, 'configurado': True})
            st.rerun()
    st.stop()

# --- 5. DETECCIÓN AUTOMÁTICA DE NUEVA SEMANA ---
# Si la semana actual no está en el historial, es lunes o primera vez que entra en la semana
if semana_id not in st.session_state['historial_entrenamientos']:
    # Si es LUNES, generamos semana completa limpia
    if dia_actual_es == "LUNES":
        with st.spinner("🌞 ¡Feliz Lunes! Diseñando tu semana completa..."):
            prompt = f"Eres un Coach XCO. Genera un plan de LUNES a DOMINGO para un atleta {st.session_state['nivel']} con carrera el {st.session_state['fecha_carrera']}. Formato: [LUNES], [MARTES]... con secciones **BICICLETA**, **GYM/CORE**, **NUTRICIÓN**."
            res = model.generate_content(prompt)
            st.session_state['historial_entrenamientos'][semana_id] = res.text
    else:
        # SI NO ES LUNES, pedimos feedback antes de generar el resto
        st.warning(f"👋 Ya estamos a {dia_actual_es}. Necesito saber cómo te fue para ajustar el resto de la semana.")
        with st.form("feedback_ajuste"):
            resumen = st.text_area("¿Cómo entrenaste los días pasados de esta semana? (Ej: El martes no pude, lunes hice rodaje corto)")
            fatiga_hoy = st.slider("¿Qué tan cansado te sientes hoy (1-10)?", 1, 10, 5)
            if st.form_submit_button("Generar Ajuste de Semana"):
                prompt = f"Eres Coach XCO. Hoy es {dia_actual_es}. El atleta reporta: '{resumen}' y fatiga {fatiga_hoy}/10. Carrera el {st.session_state['fecha_carrera']}. Genera el plan desde HOY {dia_actual_es} hasta el DOMINGO. Formato: [{dia_actual_es}], [SIGUIENTE DIA]... con **BICICLETA**, **GYM/CORE**, **NUTRICIÓN**."
                res = model.generate_content(prompt)
                st.session_state['historial_entrenamientos'][semana_id] = res.text
                st.rerun()
        st.stop()

# --- 6. INTERFAZ Y NAVEGACIÓN ---
st.title(f"🚵‍♂️ Coach XCO - {semana_id}")

# Selector de semanas (Historial)
semanas_disponibles = list(st.session_state['historial_entrenamientos'].keys())
semana_seleccionada = st.sidebar.selectbox("📅 Consultar Semana", semanas_disponibles, index=len(semanas_disponibles)-1)

with st.sidebar:
    st.divider()
    st.metric("Días para la Carrera", (st.session_state['fecha_carrera'] - hoy).days)
    if st.button("🔄 Forzar Re-ajuste de esta semana"):
        del st.session_state['historial_entrenamientos'][semana_id]
        st.rerun()
    if st.button("🗑️ Reiniciar Todo el Objetivo"):
        st.session_state.clear()
        st.rerun()

# --- 7. VISUALIZACIÓN ---
plan_actual = st.session_state['historial_entrenamientos'][semana_seleccionada]

def extraer_dia(dia, texto):
    pattern = rf"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    return res[0].strip() if res else "Día no planificado o descanso."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)

for i, nombre_dia in enumerate(dias_lista):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, plan_actual)
        
        if nombre_dia == dia_actual_es and semana_seleccionada == semana_id:
            st.success("⚡ ¡ESTE ES TU OBJETIVO DE HOY!")
        
        if "**BICICLETA**" in contenido.upper() or "**GYM" in contenido.upper():
            partes = re.split(r'(\*\*BICICLETA\*\*|\*\*GYM/CORE\*\*|\*\*NUTRICIÓN\*\*|\*\*NUTRICION\*\*)', contenido, flags=re.IGNORECASE)
            for j in range(1, len(partes), 2):
                titulo = partes[j].replace("*", "")
                texto_seccion = partes[j+1].strip()
                with st.container(border=True):
                    icon = "🚵‍♂️" if "BICI" in titulo.upper() else "🏋️" if "GYM" in titulo.upper() else "🍎"
                    st.markdown(f"#### {icon} {titulo}")
                    st.write(texto_seccion)
        else:
            st.info(contenido)
