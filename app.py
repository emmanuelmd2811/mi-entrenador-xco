import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="XCO Elite Coach AI", layout="wide", page_icon="🚵‍♂️")

# CSS Profesional (Soft Dark Mode & Material Design)
st.markdown("""
    <style>
    .stApp { background-color: #1C1E23; }
    .stMarkdown, p, span { color: #D1D5DB !important; }
    h1, h2, h3 { color: #E5E7EB !important; font-family: 'Inter', sans-serif; }
    
    /* Tabs Estilo Deportivo */
    div.stTabs [data-baseweb="tab-list"] {
        gap: 8px; background-color: #2D3139; padding: 8px; border-radius: 12px;
    }
    div.stTabs [data-baseweb="tab"] {
        background-color: #374151; border-radius: 8px; color: #9CA3AF !important; padding: 8px 16px;
    }
    div.stTabs [aria-selected="true"] {
        background-color: #10B981 !important; color: white !important; font-weight: bold;
    }
    
    /* Tarjetas de Entrenamiento (Cards) */
    div[data-testid="stVerticalBlock"] > div.element-container div.stMarkdown div.stContainer {
        border: 1px solid #4B5563; 
        border-radius: 15px; 
        background-color: #262B33; 
        padding: 18px; 
        margin-bottom: 12px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 3. LÓGICA DE TIEMPO Y MEMORIA ---
hoy = datetime.date.today()
semana_id = f"{hoy.year}-{hoy.isocalendar()[1]}"

if 'configurado' not in st.session_state:
    st.session_state['configurado'] = False

# Reiniciar si la fecha de carrera ya pasó
if st.session_state.get('fecha_carrera') and hoy > st.session_state['fecha_carrera']:
    st.session_state['configurado'] = False

# PANTALLA DE REGISTRO INICIAL (Onboarding)
if not st.session_state['configurado']:
    st.title("🎯 Configuración de Temporada XCO")
    with st.container(border=True):
        st.subheader("Crea tu perfil de rendimiento")
        with st.form("onboarding"):
            c1, c2 = st.columns(2)
            with c1:
                nombre_c = st.text_input("Nombre de tu Carrera Objetivo", "Copa Nacional")
                fecha_c = st.date_input("Fecha del Evento", hoy + datetime.timedelta(days=30))
                nivel = st.select_slider("Nivel Actual", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
            with c2:
                dias_w = st.slider("Días disponibles para entrenar/semana", 1, 7, 5)
                exp = st.number_input("Años de experiencia en MTB", 0, 40, 2)
            
            btn = st.form_submit_button("🔥 Generar Plan Maestro")
            if btn:
                st.session_state.update({
                    'nombre_carrera': nombre_c, 'fecha_carrera': fecha_c, 
                    'nivel': nivel, 'dias_w': dias_w, 'configurado': True, 
                    'plan_semanal': None, 'plan_semanal_id': None
                })
                st.rerun()
    st.stop()

# --- 4. DASHBOARD LATERAL ---
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
    with st.spinner("🤖 El Coach IA está diseñando tu microciclo semanal..."):
        prompt = f"""
        Eres un Coach de MTB XCO Pro. 
        ATLETA: Nivel {st.session_state['nivel']}, faltan {dias_meta} días para {st.session_state['nombre_carrera']}.
        Días de entreno: {st.session_state['dias_w']} a la semana.
        
        TAREA: Genera un plan de lunes a domingo.
        REGLA DE FORMATO: Empieza CADA DÍA con corchetes: [LUNES], [MARTES], etc.
        Dentro de cada día DEBES usar exactamente estos títulos en negritas:
        **BICICLETA**: (instrucciones detalladas)
        **GYM/CORE**: (rutina de fuerza)
        **NUTRICIÓN**: (estrategia de alimentación)
        """
        try:
            res = model.generate_content(prompt)
            st.session_state['plan_semanal'] = res.text
            st.session_state['plan_semanal_id'] = semana_id
        except Exception as e:
            st.error(f"Error al conectar con la IA: {e}")

# --- 6. INTERFAZ DE ENTRENAMIENTO ---
st.title(f"📅 Planificación: Semana {hoy.isocalendar()[1]}")

def extraer_dia(dia, texto):
    if not texto: return "Cargando..."
    pattern = rf"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    return res[0].strip() if res else "Día de recuperación o descanso activo."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)
traduccion = {"Monday":"LUNES", "Tuesday":"MARTES", "Wednesday":"MIERCOLES", 
              "Thursday":"JUEVES", "Friday":"VIERNES", "Saturday":"SABADO", "Sunday":"DOMINGO"}
dia_hoy = traduccion.get(hoy.strftime("%A"))

if st.session_state.get('plan_semanal'):
    for i, nombre_dia in enumerate(dias_lista):
        with tabs[i]:
            contenido = extraer_dia(nombre_dia, st.session_state['plan_semanal'])
            
            if nombre_dia == dia_hoy:
                st.markdown(f"### ⚡ HOY: {nombre_dia}")
            else: 
                st.markdown(f"### {nombre_dia}")
            
            # Separación visual por bloques (Tarjetas para Bici, Gym y Nutrición)
            if "**BICICLETA**" in contenido.upper() or "**GYM" in contenido.upper() or "**NUTRICIÓN" in contenido.upper():
                partes = re.split(r'(\*\*BICICLETA\*\*|\*\*GYM/CORE\*\*|\*\*NUTRICIÓN\*\*|\*\*NUTRICION\*\*)', contenido, flags=re.IGNORECASE)
                
                for j in range(1, len(partes), 2):
                    titulo = partes[j].replace("*", "")
                    texto_seccion = partes[j+1].strip() if j+1 < len(partes) else ""
                    
                    if "BICICLETA" in titulo.upper():
                        with st.container(border=True):
                            st.markdown(f"#### 🚵‍♂️ {titulo}")
                            st.write(texto_seccion)
                    elif "GYM" in titulo.upper():
                        with st.container(border=True):
                            st.markdown(f"#### 🏋️ {titulo}")
                            st.write(texto_seccion)
                    elif "NUTRI" in titulo.upper():
                        with st.container(border=True):
                            st.markdown(f"#### 🍎 {titulo}")
                            st.write(texto_seccion)
            else:
                # Si el formato falla, mostramos el texto completo de forma segura
                st.info(contenido)
