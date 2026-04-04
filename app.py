import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILO ---
st.set_page_config(page_title="XCO Elite Coach AI", layout="wide", page_icon="認")

# CSS Ajustado para legibilidad (Menos contraste agresivo)
st.markdown("""
    <style>
    /* Fondo Gris Oscuro Suave (no negro total) */
    .stApp { 
        background-color: #1C1E23; 
    }
    
    /* Texto Principal en Gris Claro (no blanco puro para no deslumbrar) */
    .stMarkdown, p, span { 
        color: #D1D5DB !important; 
    }
    
    /* Títulos en un color suave pero definido */
    h1, h2, h3 { 
        color: #E5E7EB !important; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Tabs con colores de bajo contraste */
    div.stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #2D3139;
        padding: 8px;
        border-radius: 12px;
    }
    div.stTabs [data-baseweb="tab"] {
        background-color: #374151;
        border-radius: 8px;
        color: #9CA3AF !important;
        padding: 8px 16px;
    }
    /* Tab seleccionado: Verde Esmeralda Suave */
    div.stTabs [aria-selected="true"] {
        background-color: #10B981 !important;
        color: white !important;
        font-weight: bold;
    }
    
    /* Contenedores (Cards) con bordes sutiles */
    div[data-testid="stVerticalBlock"] > div.element-container div.stMarkdown div.stContainer {
        border: 1px solid #4B5563;
        border-radius: 15px;
        background-color: #262B33;
        padding: 15px;
        margin-bottom: 10px;
    }

    /* Estilo para los expanders (Nutrición) */
    .stExpander {
        border: 1px solid #4B5563 !important;
        background-color: #262B33 !important;
        border-radius: 12px !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { 
        background-color: #111827; 
        border-right: 1px solid #374151; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 3. LÓGICA DE MEMORIA Y ONBOARDING ---
hoy = datetime.date.today()

if 'configurado' not in st.session_state:
    st.session_state['configurado'] = False

if st.session_state.get('fecha_carrera') and hoy > st.session_state['fecha_carrera']:
    st.session_state['configurado'] = False

if not st.session_state['configurado']:
    st.title("🎯 Planificación de Temporada")
    with st.container(border=True):
        with st.form("onboarding"):
            c1, c2 = st.columns(2)
            with c1:
                nombre_c = st.text_input("Carrera Objetivo", "Copa Nacional")
                fecha_c = st.date_input("Fecha", hoy + datetime.timedelta(days=30))
                nivel = st.select_slider("Nivel", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
            with c2:
                dias_w = st.slider("Días entreno/semana", 1, 7, 5)
                exp = st.number_input("Años experiencia", 0, 30, 2)
            
            btn = st.form_submit_button("🔥 Generar Plan Maestro")
            if btn:
                st.session_state.update({'nombre_carrera': nombre_c, 'fecha_carrera': fecha_c, 
                                        'nivel': nivel, 'dias_w': dias_w, 'configurado': True, 'plan_semanal': None})
                st.rerun()
    st.stop()

# --- 4. DASHBOARD ---
semana_id = f"{hoy.year}-{hoy.isocalendar()[1]}"
dias_meta = (st.session_state['fecha_carrera'] - hoy).days

with st.sidebar:
    st.header("🏆 Mi Objetivo")
    st.subheader(st.session_state['nombre_carrera'])
    st.metric("Días restantes", dias_meta)
    if st.button("🗑️ Cambiar Objetivo"):
        st.session_state['configurado'] = False
        st.rerun()

# --- 5. GENERACIÓN SEMANAL ---
if st.session_state.get('plan_semanal_id') != semana_id or st.session_state.get('plan_semanal') is None:
    with st.spinner("🤖 El Coach está redactando tu semana..."):
        prompt = f"Coach XCO. Atleta {st.session_state['nivel']}, faltan {dias_meta} días para {st.session_state['nombre_carrera']}. Genera plan Lunes a Domingo. Formato: [LUNES], [MARTES]... Usa subtítulos **BICICLETA**, **GYM/CORE**, **NUTRICIÓN**."
        try:
            res = model.generate_content(prompt)
            st.session_state['plan_semanal'] = res.text
            st.session_state['plan_semanal_id'] = semana_id
        except: st.error("Error al conectar con la IA.")

# --- 6. INTERFAZ FINAL ---
st.title(f"📅 Microciclo: Semana {hoy.isocalendar()[1]}")

def extraer_dia(dia, texto):
    pattern = f"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL)
    return res[0].strip() if res else "Descanso."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)
traduccion = {"Monday":"LUNES", "Tuesday":"MARTES", "Wednesday":"MIERCOLES", "Thursday":"JUEVES", "Friday":"VIERNES", "Saturday":"SABADO", "Sunday":"DOMINGO"}
dia_hoy = traduccion.get(hoy.strftime("%A"))

for i, nombre_dia in enumerate(dias_lista):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, st.session_state['plan_semanal'])
        if nombre_dia == dia_hoy:
            st.markdown(f"### ⚡ HOY: {nombre_dia}")
        else: st.markdown(f"### {nombre_dia}")
        
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
                with st.expander("🍎 Nutrición"):
                    st.write(clean_b)
            else: st.write(clean_b)
