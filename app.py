import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="XCO Elite Coach AI", layout="wide", page_icon="🚵‍♂️")

# CSS Personalizado para Look Pro (Dark Mode & Neon)
st.markdown("""
    <style>
    .stApp { background-color: #0D1117; }
    
    /* Estilo de los Títulos */
    h1, h2, h3 { color: #2EA043 !important; font-family: 'Inter', sans-serif; }
    
    /* Tabs Estilo Deportivo */
    div.stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161B22;
        padding: 8px;
        border-radius: 12px;
    }
    div.stTabs [data-baseweb="tab"] {
        background-color: #21262D;
        border-radius: 8px;
        color: #8B949E;
        padding: 8px 16px;
    }
    div.stTabs [aria-selected="true"] {
        background-color: #238636 !important;
        color: white !important;
        font-weight: bold;
    }
    
    /* Contenedores de Entrenamiento */
    [data-testid="stExpander"], .stChatMessage, div[data-testid="stVerticalBlock"] > div.element-container div.stMarkdown div.stContainer {
        border: 1px solid #30363D;
        border-radius: 15px;
        background-color: #161B22;
        padding: 10px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #090C10; border-right: 1px solid #30363D; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos el modelo más potente detectado en tu cuenta
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 3. LÓGICA DE MEMORIA Y ONBOARDING ---
hoy = datetime.date.today()

# Inicializar estados si no existen
if 'configurado' not in st.session_state:
    st.session_state['configurado'] = False

# Verificar si el objetivo ya pasó para reiniciar
if st.session_state.get('fecha_carrera') and hoy > st.session_state['fecha_carrera']:
    st.session_state['configurado'] = False

# PANTALLA DE REGISTRO (Solo se ve la primera vez o al reiniciar)
if not st.session_state['configurado']:
    st.title("🎯 Configuración de Temporada XCO")
    with st.container(border=True):
        st.subheader("Crea tu perfil de rendimiento")
        with st.form("onboarding"):
            c1, c2 = st.columns(2)
            with c1:
                nombre_c = st.text_input("Nombre de la Carrera", "Copa Nacional")
                fecha_c = st.date_input("Fecha de la Carrera", hoy + datetime.timedelta(days=30))
                nivel = st.select_slider("Nivel", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
            with c2:
                dias_w = st.slider("Días para entrenar/semana", 1, 7, 5)
                exp = st.number_input("Años de experiencia", 0, 30, 2)
                horas_w = st.number_input("Horas disponibles/semana", 1, 30, 8)
            
            btn = st.form_submit_button("🔥 Generar Plan Maestro")
            
            if btn:
                st.session_state['nombre_carrera'] = nombre_c
                st.session_state['fecha_carrera'] = fecha_c
                st.session_state['nivel'] = nivel
                st.session_state['dias_w'] = dias_w
                st.session_state['configurado'] = True
                st.session_state['plan_semanal'] = None # Reset para nueva IA
                st.rerun()
    st.stop()

# --- 4. DASHBOARD PRINCIPAL (OBJETIVO FIJADO) ---
semana_id = f"{hoy.year}-{hoy.isocalendar()[1]}"
dias_meta = (st.session_state['fecha_carrera'] - hoy).days

with st.sidebar:
    st.header("🏆 Objetivo Activo")
    st.success(f"**{st.session_state['nombre_carrera']}**")
    st.metric("Días para la meta", dias_meta)
    st.write(f"Nivel: {st.session_state['nivel']}")
    st.divider()
    if st.button("🗑️ Reiniciar Objetivo"):
        st.session_state['configurado'] = False
        st.rerun()

# --- 5. GENERACIÓN SEMANAL CON IA ---
if st.session_state.get('plan_semanal_id') != semana_id or st.session_state.get('plan_semanal') is None:
    with st.spinner("🤖 El Coach IA está diseñando tu semana..."):
        prompt = f"""
        Eres un Coach de MTB XCO de nivel profesional.
        ATLETA: Nivel {st.session_state['nivel']}, faltan {dias_meta} días para la carrera {st.session_state['nombre_carrera']}.
        TAREAS: Genera un plan de lunes a domingo. 
        FORMATO OBLIGATORIO:
        [LUNES] [MARTES] [MIERCOLES] [JUEVES] [VIERNES] [SABADO] [DOMINGO]
        Dentro de cada día separa con: **BICICLETA**, **GYM/CORE**, **NUTRICIÓN**. 
        Hazlo muy visual, con puntos y que no se vea amontonado.
        """
        try:
            res = model.generate_content(prompt)
            st.session_state['plan_semanal'] = res.text
            st.session_state['plan_semanal_id'] = semana_id
        except Exception as e:
            st.error(f"Error IA: {e}")

# --- 6. INTERFAZ DE ENTRENAMIENTO LIMPIA ---
st.title(f"📅 Planificación: Semana {hoy.isocalendar()[1]}")

def extraer_dia(dia, texto):
    pattern = f"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL)
    return res[0].strip() if res else "Día de recuperación."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)

# Diccionario para marcar el día de hoy
traduccion = {"Monday":"LUNES", "Tuesday":"MARTES", "Wednesday":"MIERCOLES", 
              "Thursday":"JUEVES", "Friday":"VIERNES", "Saturday":"SABADO", "Sunday":"DOMINGO"}
dia_hoy = traduccion.get(hoy.strftime("%A"))

for i, nombre_dia in enumerate(dias_lista):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, st.session_state['plan_semanal'])
        
        if nombre_dia == dia_hoy:
            st.markdown(f"### ⚡ HOY: {nombre_dia}")
        else:
            st.markdown(f"### {nombre_dia}")
        
        # Separación inteligente por bloques para evitar que se vea amontonado
        bloques = contenido.split("**")
        for bloque in bloques:
            clean_b = bloque.strip()
            if not clean_b: continue
            
            if "BICICLETA" in clean_b.upper():
                with st.container(border=True):
                    st.markdown(f"#### 🚵‍♂️ {clean_b}")
            elif "GYM" in clean_b.upper() or "CORE" in clean_b.upper():
                with st.container(border=True):
                    st.markdown(f"#### 🏋️ {clean_b}")
            elif "NUTRICIÓN" in clean_b.upper() or "NUTRICION" in clean_b.upper():
                with st.expander("🍎 Ver Nutrición Sugerida"):
                    st.write(clean_b)
            else:
                st.write(clean_b)
