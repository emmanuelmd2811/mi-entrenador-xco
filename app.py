import streamlit as st
import google.generativeai as genai
import datetime
import re
import json
import os
import unicodedata

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Elite Coach Pro", layout="wide", page_icon="🏆")
CONFIG_FILE = "user_data.json"

st.markdown("""
    <style>
    .stApp { background-color: #1C1E23; }
    .stMarkdown, p, span { color: #D1D5DB !important; }
    h1, h2, h3 { color: #10B981 !important; }
    div[data-testid="stVerticalBlock"] > div.element-container div.stMarkdown div.stContainer {
        border: 1px solid #4B5563; border-radius: 15px; background-color: #262B33; padding: 18px; margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE APOYO ---
def normalizar(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto))
                  if unicodedata.category(c) != 'Mn').upper().strip()

def guardar_en_disco():
    datos = {k: v for k, v in st.session_state.items() if k != 'model'}
    if 'fecha_carrera' in datos:
        datos['fecha_carrera'] = str(datos['fecha_carrera'])
    with open(CONFIG_FILE, "w") as f:
        json.dump(datos, f)

def cargar_desde_disco():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                datos = json.load(f)
                if 'fecha_carrera' in datos:
                    datos['fecha_carrera'] = datetime.date.fromisoformat(datos['fecha_carrera'])
                return datos
        except: return None
    return None

# --- 3. CONEXIÓN IA (SOLUCIÓN AL ERROR 404) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # USAMOS SOLO EL NOMBRE DEL MODELO, SIN PREFIJOS
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 4. INICIALIZACIÓN ---
if 'configurado' not in st.session_state:
    viejos = cargar_desde_disco()
    if viejos: st.session_state.update(viejos)
    else:
        st.session_state.update({'configurado': False, 'historial_entrenamientos': {}})

hoy = datetime.date.today()
dias_semana = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
semana_id = f"{hoy.year}-W{hoy.isocalendar()[1]}"

# --- 5. REGISTRO ---
if not st.session_state['configurado']:
    st.title("🎯 Configuración")
    with st.form("reg"):
        dep = st.selectbox("Deporte", ["Ciclismo", "Running", "Trail"])
        meta = st.text_input("Meta", "Mi Competencia")
        fec = st.date_input("Fecha", hoy + datetime.timedelta(days=60))
        if st.form_submit_button("Crear Plan"):
            st.session_state.update({'deporte': dep, 'nombre_carrera': meta, 'fecha_carrera': fec, 'configurado': True})
            guardar_en_disco()
            st.rerun()
    st.stop()

# --- 6. GENERACIÓN ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title("📅 Ajuste Semanal")
    with st.form("aj"):
        resumen = st.text_area("¿Cómo vas?")
        if st.form_submit_button("Generar Plan"):
            with st.spinner("Coach trabajando..."):
                prompt = f"Coach de {st.session_state['deporte']}. Genera plan hasta domingo. Feedback: {resumen}. Formato: [DIA] con secciones **ENTRENAMIENTO**, **FUERZA**, **NUTRICION**."
                try:
                    res = model.generate_content(prompt)
                    st.session_state['historial_entrenamientos'][semana_id] = res.text
                    guardar_en_disco()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    st.stop()

# --- 7. DASHBOARD ---
st.title(f"🏆 {st.session_state['nombre_carrera']}")
with st.sidebar:
    if st.button("🔄 Re-ajustar semana"):
        del st.session_state['historial_entrenamientos'][semana_id]
        guardar_en_disco()
        st.rerun()
    if st.button("🗑️ Reset Todo"):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        st.session_state.clear()
        st.rerun()

# --- 8. VISUALIZACIÓN (BUSCADOR ULTRA-ROBUSTO) ---
plan_actual = st.session_state['historial_entrenamientos'][semana_id]
tabs = st.tabs(dias_semana[hoy.weekday():])

def extraer_contenido(dia_target, texto):
    t_norm = normalizar(texto)
    d_norm = normalizar(dia_target)
    
    # Busca [DIA], **DIA**, o DIA:
    inicio = -1
    for fmt in [f"[{d_norm}]", f"**{d_norm}**", f"{d_norm}:"]:
        inicio = t_norm.find(fmt)
        if inicio != -1:
            inicio += len(fmt)
            break
            
    if inicio == -1: return "Descanso o plan no detectado."
    
    # El fin es el inicio del siguiente día
    fin = len(t_norm)
    for d in dias_semana:
        dn = normalizar(d)
        for f_fin in [f"[{dn}]", f"**{dn}**"]:
            pos = t_norm.find(f_fin, inicio)
            if pos != -1 and pos < fin: fin = pos
            
    return texto[inicio:fin].strip()

for i, dia in enumerate(dias_semana[hoy.weekday():]):
    with tabs[i]:
        contenido = extraer_contenido(dia, plan_actual)
        # Separar por secciones de forma flexible
        secciones = re.split(r'(\*\*ENTRENAMIENTO.*?\*\*|\*\*FUERZA.*?\*\*|\*\*NUTRICI.*?\*\*)', contenido, flags=re.IGNORECASE)
        if len(secciones) > 1:
            for j in range(1, len(secciones), 2):
                with st.container(border=True):
                    st.markdown(f"#### {secciones[j].replace('*','')}")
                    st.write(secciones[j+1].strip())
        else:
            st.info(contenido)
