import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Elite Multi-Sport Coach", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #1C1E23; }
    .stMarkdown, p, span { color: #D1D5DB !important; }
    h1, h2, h3 { color: #10B981 !important; font-family: 'Inter', sans-serif; }
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

# --- 3. LÓGICA DE TIEMPO ---
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

# --- 4. ONBOARDING DINÁMICO (DEPORTE -> DISCIPLINA) ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Perfil de Atleta")
    
    with st.container(border=True):
        # Usamos columnas para que no se vea amontonado
        col_a, col_b = st.columns(2)
        
        with col_a:
            deporte = st.selectbox("Selecciona tu Deporte", ["Ciclismo", "Running", "Trail Running", "Triatlón"])
            
            # Lógica de Modalidades Anidadas
            if deporte == "Ciclismo":
                disciplina = st.selectbox("Especialidad de Ciclismo", 
                                        ["XCO (Cross Country)", "XCM (Maratón)", "Ruta / Gran Fondo", "Enduro", "Gravel", "Pista"])
            elif deporte == "Running":
                disciplina = st.selectbox("Distancia Objetivo", 
                                        ["5K", "10K", "21K (Medio Maratón)", "42K (Maratón)", "Ultra Running"])
            elif deporte == "Trail Running":
                disciplina = st.selectbox("Tipo de Trail", 
                                        ["Short Trail (<21km)", "Trail Media Distancia (21-42km)", "Ultra Trail (>42km)", "Vertical KM"])
            elif deporte == "Triatlón":
                disciplina = st.selectbox("Distancia Triatlón", 
                                        ["Sprint", "Olímpico", "70.3 (Medio Ironman)", "140.6 (Ironman Full)"])
        
        with col_b:
            nombre_evento = st.text_input("Nombre de la Carrera / Meta", "Mi Gran Competencia")
            fecha_c = st.date_input("Fecha del Evento", hoy + datetime.timedelta(days=60))
            nivel = st.select_slider("Nivel actual", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
        
        dias_w = st.slider("¿Cuántos días puedes entrenar a la semana?", 1, 7, 5)
        
        if st.button("🚀 Crear mi Plan Adaptativo"):
            st.session_state.update({
                'deporte': deporte,
                'modalidad': disciplina,
                'nombre_carrera': nombre_evento,
                'fecha_carrera': fecha_c,
                'nivel': nivel,
                'dias_w': dias_w,
                'configurado': True
            })
            st.rerun()
    st.stop()

# --- 5. LÓGICA DE AJUSTE (Misma que antes, pero con Prompt enriquecido) ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_es})")
    with st.form("ajuste"):
        resumen = st.text_area("¿Cómo entrenaste los días anteriores de esta semana?")
        fatiga = st.slider("Nivel de fatiga (1-10)", 1, 10, 5)
        if st.form_submit_button("Generar mi Plan"):
            prompt = f"""
            Actúa como un Coach experto en {st.session_state['deporte']} ({st.session_state['modalidad']}).
            OBJETIVO: {st.session_state['nombre_carrera']} el {st.session_state['fecha_carrera']}.
            ATLETA: Nivel {st.session_state['nivel']}.
            SITUACIÓN: Hoy es {dia_actual_es}. Reporte: '{resumen}'. Fatiga: {fatiga}.
            TAREA: Genera el plan desde hoy hasta el domingo con:
            **ENTRENAMIENTO PRINCIPAL**, **FUERZA/MOVILIDAD**, **NUTRICIÓN**.
            Usa términos específicos de {st.session_state['modalidad']}.
            """
            res = model.generate_content(prompt)
            st.session_state['historial_entrenamientos'][semana_id] = res.text
            st.rerun()
    st.stop()

# --- 6. DASHBOARD Y VISUALIZACIÓN ---
st.title(f"🏆 {st.session_state['modalidad']} - {st.session_state['nombre_carrera']}")

with st.sidebar:
    st.header("📊 Perfil")
    st.write(f"**Deporte:** {st.session_state['deporte']}")
    st.write(f"**Disciplina:** {st.session_state['modalidad']}")
    st.metric("Días para el evento", (st.session_state['fecha_carrera'] - hoy).days)
    if st.button("🗑️ Cambiar Todo"):
        st.session_state.clear()
        st.rerun()

# Tabs y Renderizado (Se mantiene igual que la versión exitosa anterior)
plan_actual = st.session_state['historial_entrenamientos'][semana_id]
tabs = st.tabs(["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"])

def extraer_dia(dia, texto):
    pattern = rf"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    return res[0].strip() if res else "Descanso."

for i, nombre_dia in enumerate(["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, plan_actual)
        if nombre_dia == dia_actual_es: st.success("⚡ OBJETIVO DE HOY")
        
        partes = re.split(r'(\*\*ENTRENAMIENTO PRINCIPAL\*\*|\*\*FUERZA/MOVILIDAD\*\*|\*\*NUTRICIÓN\*\*|\*\*NUTRICION\*\*)', contenido, flags=re.IGNORECASE)
        if len(partes) > 1:
            for j in range(1, len(partes), 2):
                titulo = partes[j].replace("*", "")
                with st.container(border=True):
                    st.markdown(f"#### {titulo}")
                    st.write(partes[j+1].strip())
        else:
            st.info(contenido)
