import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="XCO Adaptive Coach Pro", layout="wide", page_icon="🚵‍♂️")

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

# --- 3. LÓGICA DE ESTADO Y TIEMPO ---
hoy = datetime.date.today()
nombre_dia_hoy = hoy.strftime("%A").upper()
traduccion_dias = {"MONDAY":"LUNES", "TUESDAY":"MARTES", "WEDNESDAY":"MIERCOLES", 
                  "THURSDAY":"JUEVES", "FRIDAY":"VIERNES", "SATURDAY":"SABADO", "SUNDAY":"DOMINGO"}
dia_actual_es = traduccion_dias.get(nombre_dia_hoy)
semana_id = f"{hoy.year}-W{hoy.isocalendar()[1]}"

if 'configurado' not in st.session_state:
    st.session_state['configurado'] = False
if 'historial_entrenamientos' not in st.session_state:
    st.session_state['historial_entrenamientos'] = {}

# --- 4. PASO 1: CONFIGURACIÓN DEL OBJETIVO (OBLIGATORIO) ---
if not st.session_state['configurado']:
    st.title("🎯 Configuración de Temporada XCO")
    st.info("Antes de ver tu entrenamiento, necesito conocer tus objetivos.")
    with st.container(border=True):
        with st.form("onboarding"):
            c1, c2 = st.columns(2)
            with c1:
                nombre_c = st.text_input("¿Cómo se llama tu carrera objetivo?", "Copa Nacional")
                fecha_c = st.date_input("¿Qué día es la carrera?", hoy + datetime.timedelta(days=45))
            with c2:
                nivel = st.selectbox("Tu Nivel Actual", ["Principiante", "Intermedio", "Avanzado", "Elite"])
                dias_w = st.slider("Días disponibles para entrenar/semana", 1, 7, 5)
            
            if st.form_submit_button("🔥 Establecer Objetivo"):
                st.session_state.update({
                    'nombre_carrera': nombre_c,
                    'fecha_carrera': fecha_c,
                    'nivel': nivel,
                    'dias_w': dias_w,
                    'configurado': True
                })
                st.rerun()
    st.stop()

# --- 5. PASO 2: AJUSTE SEMANAL (Detección de Sábado/Media semana) ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_es})")
    
    if dia_actual_es == "LUNES":
        # Generación automática de lunes
        with st.spinner("Iniciando semana completa..."):
            prompt = f"Coach XCO. Genera plan LUNES a DOMINGO. Atleta {st.session_state['nivel']}, meta {st.session_state['nombre_carrera']} en {st.session_state['fecha_carrera']}. Formato [LUNES]... con **BICICLETA**, **GYM/CORE**, **NUTRICIÓN**."
            res = model.generate_content(prompt)
            st.session_state['historial_entrenamientos'][semana_id] = res.text
            st.rerun()
    else:
        # Si es Sábado u otro día, pedimos feedback
        with st.container(border=True):
            st.subheader(f"👋 Es {dia_actual_es}. Cuéntame cómo te fue esta semana:")
            with st.form("ajuste_semanal"):
                resumen = st.text_area("¿Cómo entrenaste de lunes a ayer?", placeholder="Ej: Cumplí todo, o el miércoles no pude salir...")
                fatiga = st.slider("Nivel de fatiga actual (1-10)", 1, 10, 5)
                
                if st.form_submit_button("Generar Plan para el resto de la semana"):
                    prompt = f"""
                    Coach XCO. Hoy es {dia_actual_es}. Atleta {st.session_state['nivel']}. 
                    Feedback semana: '{resumen}', Fatiga: {fatiga}/10. 
                    Carrera: {st.session_state['nombre_carrera']} el {st.session_state['fecha_carrera']}.
                    Genera el plan desde HOY {dia_actual_es} hasta el DOMINGO.
                    Formato obligatorio: [{dia_actual_es}], [SIGUIENTE DÍA]... 
                    Incluye secciones **BICICLETA**, **GYM/CORE**, **NUTRICIÓN**.
                    """
                    res = model.generate_content(prompt)
                    st.session_state['historial_entrenamientos'][semana_id] = res.text
                    st.rerun()
        st.stop()

# --- 6. DASHBOARD PRINCIPAL ---
st.title(f"🚵‍♂️ Plan Semanal: {st.session_state['nombre_carrera']}")

# Sidebar: Historial y Control
with st.sidebar:
    st.header("📊 Mi Estado")
    semanas_log = list(st.session_state['historial_entrenamientos'].keys())
    sem_sel = st.selectbox("Ver Semana:", semanas_log, index=len(semanas_log)-1)
    
    st.metric("Días para la Carrera", (st.session_state['fecha_carrera'] - hoy).days)
    st.write(f"Nivel: {st.session_state['nivel']}")
    st.divider()
    if st.button("🔄 Re-ajustar esta semana"):
        del st.session_state['historial_entrenamientos'][semana_id]
        st.rerun()
    if st.button("🗑️ Nuevo Objetivo (Reset)"):
        st.session_state.clear()
        st.rerun()

# --- 7. VISUALIZACIÓN ---
plan_actual = st.session_state['historial_entrenamientos'][sem_sel]

def extraer_dia(dia, texto):
    pattern = rf"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    return res[0].strip() if res else "Día de recuperación o no planificado."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)

for i, nombre_dia in enumerate(dias_lista):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, plan_actual)
        
        if nombre_dia == dia_actual_es and sem_sel == semana_id:
            st.success("⚡ OBJETIVO DE HOY")
            
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
