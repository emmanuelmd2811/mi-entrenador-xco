import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Multi-Sport Adaptive Coach", layout="wide", page_icon="🏆")

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

# --- 3. LÓGICA DE ESTADO ---
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

# --- 4. CONFIGURACIÓN MULTIDEPORTE (ONBOARDING) ---
if not st.session_state['configurado']:
    st.title("🎯 Tu Nuevo Plan de Entrenamiento")
    st.info("Configura tu deporte y objetivo para empezar.")
    
    with st.container(border=True):
        with st.form("onboarding_multisport"):
            c1, c2 = st.columns(2)
            with c1:
                deporte = st.selectbox("Deporte Principal", ["Ciclismo", "Running", "Trail Running", "Triatlón"])
                
                # Sub-modalidades dinámicas
                if deporte == "Ciclismo":
                    modalidad = st.selectbox("Modalidad", ["XCO (Cross Country)", "XCM (Maratón)", "Ruta", "Enduro", "Gravel"])
                elif deporte == "Running":
                    modalidad = st.selectbox("Distancia", ["5K", "10K", "21K (Medio Maratón)", "42K (Maratón)"])
                else:
                    modalidad = st.text_input("Tipo de evento", "General")
                
                nombre_evento = st.text_input("Nombre de la competencia", "Mi Gran Reto")
            
            with c2:
                fecha_c = st.date_input("Fecha del Evento", hoy + datetime.timedelta(days=60))
                nivel = st.select_slider("Tu Nivel", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
                dias_w = st.slider("Días disponibles a la semana", 1, 7, 5)
            
            if st.form_submit_button("🔥 Generar Plan de Alto Rendimiento"):
                st.session_state.update({
                    'deporte': deporte,
                    'modalidad': modalidad,
                    'nombre_carrera': nombre_evento,
                    'fecha_carrera': fecha_c,
                    'nivel': nivel,
                    'dias_w': dias_w,
                    'configurado': True
                })
                st.rerun()
    st.stop()

# --- 5. AJUSTE SEMANAL (INTELIGENCIA ADAPTATIVA) ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_es})")
    
    with st.container(border=True):
        st.subheader(f"👋 ¡Hola! Es {dia_actual_es}. Cuéntame cómo vas:")
        with st.form("ajuste_semanal"):
            resumen = st.text_area("Resumen de tus entrenos previos (si aplica):", placeholder="Ej: He entrenado bien, o estuve enfermo lunes y martes...")
            fatiga = st.slider("Fatiga acumulada (1-10)", 1, 10, 4)
            
            if st.form_submit_button("Generar Plan Adaptado"):
                prompt = f"""
                Actúa como un Coach de {st.session_state['deporte']} especializado en {st.session_state['modalidad']}.
                OBJETIVO: {st.session_state['nombre_carrera']} el {st.session_state['fecha_carrera']}.
                ATLETA: Nivel {st.session_state['nivel']}, entrena {st.session_state['dias_w']} días/semana.
                SITUACIÓN ACTUAL: Hoy es {dia_actual_es}. El atleta reporta: '{resumen}'. Fatiga: {fatiga}/10.
                
                TAREA: Genera el plan desde HOY {dia_actual_es} hasta el DOMINGO.
                FORMATO: [DIA_NOMBRE]
                Secciones internas: **ENTRENAMIENTO PRINCIPAL**, **FUERZA/MOVILIDAD**, **NUTRICIÓN**.
                (Adapta el lenguaje al deporte: si es running habla de ritmos, si es bici de potencia/cadencia).
                """
                res = model.generate_content(prompt)
                st.session_state['historial_entrenamientos'][semana_id] = res.text
                st.rerun()
    st.stop()

# --- 6. DASHBOARD PRINCIPAL ---
st.title(f"🏆 Coach: {st.session_state['nombre_carrera']}")

with st.sidebar:
    st.header("📊 Perfil")
    st.info(f"**{st.session_state['deporte']}** - {st.session_state['modalidad']}")
    
    semanas_log = list(st.session_state['historial_entrenamientos'].keys())
    sem_sel = st.selectbox("Historial de Semanas:", semanas_log, index=len(semanas_log)-1)
    
    dias_restantes = (st.session_state['fecha_carrera'] - hoy).days
    st.metric("Días para la Meta", dias_restantes)
    
    st.divider()
    if st.button("🔄 Re-ajustar esta semana"):
        del st.session_state['historial_entrenamientos'][semana_id]
        st.rerun()
    if st.button("🗑️ Cambiar Deporte / Objetivo"):
        st.session_state.clear()
        st.rerun()

# --- 7. VISUALIZACIÓN DE ENTRENAMIENTOS ---
plan_actual = st.session_state['historial_entrenamientos'][sem_sel]

def extraer_dia(dia, texto):
    pattern = rf"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    return res[0].strip() if res else "Día de descanso o recuperación."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)

# Iconos dinámicos según el deporte
icon_principal = "🏃‍♂️" if st.session_state['deporte'] != "Ciclismo" else "🚵‍♂️"

for i, nombre_dia in enumerate(dias_lista):
    with tabs[i]:
        contenido = extraer_dia(nombre_dia, plan_actual)
        if nombre_dia == dia_actual_es and sem_sel == semana_id:
            st.success("⚡ OBJETIVO DE HOY")
            
        if "**ENTRENAMIENTO" in contenido.upper() or "**FUERZA" in contenido.upper():
            # Buscamos las secciones principales
            partes = re.split(r'(\*\*ENTRENAMIENTO PRINCIPAL\*\*|\*\*FUERZA/MOVILIDAD\*\*|\*\*NUTRICIÓN\*\*|\*\*NUTRICION\*\*)', contenido, flags=re.IGNORECASE)
            
            for j in range(1, len(partes), 2):
                titulo = partes[j].replace("*", "")
                texto_seccion = partes[j+1].strip()
                
                with st.container(border=True):
                    if "ENTRENAMIENTO" in titulo.upper(): icon = icon_principal
                    elif "FUERZA" in titulo.upper(): icon = "🏋️"
                    else: icon = "🍎"
                    
                    st.markdown(f"#### {icon} {titulo}")
                    st.write(texto_seccion)
        else:
            st.info(contenido)
