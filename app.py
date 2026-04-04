import streamlit as st
import google.generativeai as genai
import datetime
import re
import json
import os
import unicodedata

# --- 1. CONFIGURACIÓN Y ESTILO (Mantenemos tu interfaz favorita) ---
st.set_page_config(page_title="Elite Adaptive Coach Pro", layout="wide", page_icon="🏆")

CONFIG_FILE = "user_data.json"

st.markdown("""
    <style>
    .stApp { background-color: #1C1E23; }
    .stMarkdown, p, span { color: #D1D5DB !important; }
    h1, h2, h3 { color: #10B981 !important; }
    div.stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #2D3139; padding: 8px; border-radius: 12px; }
    div.stTabs [data-baseweb="tab"] { background-color: #374151; border-radius: 8px; color: #9CA3AF !important; padding: 8px 16px; }
    div.stTabs [aria-selected="true"] { background-color: #10B981 !important; color: white !important; font-weight: bold; border: 2px solid #34D399; }
    div[data-testid="stVerticalBlock"] > div.element-container div.stMarkdown div.stContainer {
        border: 1px solid #4B5563; border-radius: 15px; background-color: #262B33; padding: 18px; margin-bottom: 12px;
    }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE PERSISTENCIA (Sin errores de serialización) ---
def normalizar(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto))
                  if unicodedata.category(c) != 'Mn').upper().strip()

def guardar_datos():
    """Guarda el estado actual de la sesión en un archivo físico."""
    datos_a_guardar = {
        'deporte': st.session_state.get('deporte'),
        'modalidad': st.session_state.get('modalidad'),
        'nombre_carrera': st.session_state.get('nombre_carrera'),
        'fecha_carrera': str(st.session_state.get('fecha_carrera')),
        'nivel': st.session_state.get('nivel'),
        'dias_w': st.session_state.get('dias_w'),
        'configurado': st.session_state.get('configurado'),
        'historial_entrenamientos': st.session_state.get('historial_entrenamientos', {})
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(datos_a_guardar, f)

def cargar_datos():
    """Carga datos del disco a la sesión."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                datos = json.load(f)
                if datos.get('fecha_carrera'):
                    datos['fecha_carrera'] = datetime.date.fromisoformat(datos['fecha_carrera'])
                return datos
        except: return None
    return None

# --- 3. CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 4. LÓGICA DE TIEMPO ---
hoy = datetime.date.today()
dias_semana_es = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
indice_hoy = hoy.weekday() 
dia_actual_nombre = dias_semana_es[indice_hoy]
semana_id = f"{hoy.year}-W{hoy.isocalendar()[1]}"

# Inicialización de sesión
if 'configurado' not in st.session_state:
    datos_persistentes = cargar_datos()
    if datos_persistentes:
        st.session_state.update(datos_persistentes)
    else:
        st.session_state['configurado'] = False
        st.session_state['historial_entrenamientos'] = {}

# --- 5. ONBOARDING REACTIVO ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Perfil")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            dep = st.selectbox("Deporte", ["Ciclismo", "Running", "Trail Running", "Triatlón"])
            mods = {"Ciclismo": ["XCO", "XCM", "Ruta", "Gravel"], "Running": ["5K", "10K", "21K", "42K"], 
                    "Trail Running": ["Short", "Medium", "Ultra"], "Triatlón": ["Sprint", "Olímpico", "70.3", "140.6"]}
            mod = st.selectbox("Especialidad", mods.get(dep, ["General"]))
            nom = st.text_input("Meta", "Mi Competencia")
        with col2:
            fec = st.date_input("Fecha", hoy + datetime.timedelta(days=60))
            niv = st.select_slider("Nivel", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
            dias = st.slider("Días/semana", 1, 7, 5)
        
        if st.button("🚀 Crear mi Plan Maestro"):
            st.session_state.update({'deporte': dep, 'modalidad': mod, 'nombre_carrera': nom,
                                    'fecha_carrera': fec, 'nivel': niv, 'dias_w': dias, 
                                    'configurado': True, 'historial_entrenamientos': {}})
            guardar_datos()
            st.rerun()
    st.stop()

# --- 6. AJUSTE SEMANAL ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_nombre})")
    with st.form("ajuste"):
        resumen = st.text_area("¿Cómo entrenaste los días anteriores?")
        fatiga = st.slider("Fatiga (1-10)", 1, 10, 5)
        if st.form_submit_button("Generar Plan"):
            with st.spinner("El Coach está analizando tu semana..."):
                prompt = f"Coach experto. Atleta nivel {st.session_state['nivel']} en {st.session_state['deporte']}. Hoy es {dia_actual_nombre}. Feedback: {resumen}. Genera el plan hasta el domingo con secciones **ENTRENAMIENTO PRINCIPAL**, **FUERZA/MOVILIDAD**, **NUTRICIÓN**. Formato: [DIA]."
                try:
                    res = model.generate_content(prompt)
                    st.session_state['historial_entrenamientos'][semana_id] = res.text
                    guardar_datos()
                    st.rerun()
                except: st.error("Error al conectar con el Coach. Reintenta.")
    st.stop()

# --- 7. DASHBOARD ---
st.title(f"🏆 {st.session_state['modalidad']} - {st.session_state['nombre_carrera']}")
with st.sidebar:
    st.metric("Días para meta", (st.session_state['fecha_carrera'] - hoy).days)
    if st.button("🔄 Re-ajustar semana"):
        if semana_id in st.session_state['historial_entrenamientos']:
            del st.session_state['historial_entrenamientos'][semana_id]
            guardar_datos()
            st.rerun()
    if st.button("🗑️ Reset Todo"):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        st.session_state.clear()
        st.rerun()

# --- 8. VISUALIZACIÓN ULTRA-ROBUSTA ---
plan_actual = st.session_state['historial_entrenamientos'].get(semana_id, "")
# FILTRO: Solo hoy y días futuros
dias_visibles = dias_semana_es[indice_hoy:] 
tabs = st.tabs([f"🟢 {d}" if d == dia_actual_nombre else d for d in dias_visibles])

def extraer_dia_blindado(dia_target, texto):
    if not texto: return ""
    texto_norm = normalizar(texto)
    dia_norm = normalizar(dia_target)
    
    # Buscamos el inicio con múltiples posibilidades de formato
    posibles_tags = [f"[{dia_norm}]", f"**{dia_norm}**", f"{dia_norm}:", f"### {dia_norm}"]
    inicio = -1
    for tag in posibles_tags:
        inicio = texto_norm.find(tag)
        if inicio != -1:
            inicio += len(tag)
            break
            
    if inicio == -1: return "Día de recuperación o no especificado."

    # Buscamos el final (inicio del siguiente día)
    fin = len(texto_norm)
    for d in dias_semana_es:
        dn = normalizar(d)
        for tag in [f"[{dn}]", f"**{dn}**", f"### {dn}"]:
            p = texto_norm.find(tag, inicio)
            if p != -1 and p < fin: fin = p
            
    return texto[inicio:fin].strip()

for i, nombre_dia in enumerate(dias_visibles):
    with tabs[i]:
        if nombre_dia == dia_actual_nombre: st.success(f"⚡ OBJETIVO DE HOY")
        contenido = extraer_dia_blindado(nombre_dia, plan_actual)
        
        # Separar por secciones de forma segura
        secciones = re.split(r'(\*\*.*?\*\*)', contenido)
        if len(secciones) > 1:
            for j in range(1, len(secciones), 2):
                tit = secciones[j].replace("*", "").strip()
                val = secciones[j+1].strip() if j+1 < len(secciones) else ""
                if val:
                    with st.container(border=True):
                        st.markdown(f"#### {tit}")
                        st.write(val)
        else:
            st.info(contenido)
