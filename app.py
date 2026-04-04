import streamlit as st
import google.generativeai as genai
import datetime
import re
import json
import os
import unicodedata

# --- 1. CONFIGURACIÓN Y ESTILO ---
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

# --- 2. FUNCIONES DE APOYO (LIMPIEZA DE TEXTO) ---
def normalizar(texto):
    """Elimina tildes y pasa a mayúsculas para comparar sin errores."""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn').upper()

def guardar_en_disco(datos):
    with open(CONFIG_FILE, "w") as f:
        # Usamos una copia para no modificar el objeto original
        copia = datos.copy()
        if 'fecha_carrera' in copia:
            copia['fecha_carrera'] = str(copia['fecha_carrera'])
        json.dump(copia, f)

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

# --- 3. CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 4. LÓGICA DE TIEMPO ---
hoy = datetime.date.today()
dias_semana_es = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
indice_hoy = hoy.weekday() 
dia_actual_nombre = dias_semana_es[indice_hoy]
semana_id = f"{hoy.year}-W{hoy.isocalendar()[1]}"

if 'configurado' not in st.session_state:
    datos_viejos = cargar_desde_disco()
    if datos_viejos:
        st.session_state.update(datos_viejos)
        st.session_state['configurado'] = True
    else:
        st.session_state['configurado'] = False
        st.session_state['historial_entrenamientos'] = {}

# --- 5. ONBOARDING ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Perfil")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            deporte_sel = st.selectbox("Deporte", ["Ciclismo", "Running", "Trail Running", "Triatlón"])
            mods = {"Ciclismo": ["XCO", "XCM", "Ruta", "Gravel"], "Running": ["5K", "10K", "21K", "42K"], 
                    "Trail Running": ["Short", "Medium", "Ultra"], "Triatlón": ["Sprint", "Olímpico", "70.3", "140.6"]}
            modalidad_sel = st.selectbox("Especialidad", mods.get(deporte_sel, ["General"]))
            nombre_evento = st.text_input("Nombre de la meta", "Mi Competencia")
        with col2:
            fecha_c = st.date_input("Fecha", hoy + datetime.timedelta(days=60))
            nivel = st.select_slider("Nivel", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
            dias_w = st.slider("Días/semana", 1, 7, 5)
        
        if st.button("🚀 Crear mi Plan Maestro"):
            st.session_state.update({'deporte': deporte_sel, 'modalidad': modalidad_sel, 'nombre_carrera': nombre_evento,
                                    'fecha_carrera': fecha_c, 'nivel': nivel, 'dias_w': dias_w, 'configurado': True, 'historial_entrenamientos': {}})
            guardar_en_disco(st.session_state.to_dict())
            st.rerun()
    st.stop()

# --- 6. AJUSTE SEMANAL ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_nombre})")
    with st.form("ajuste"):
        resumen = st.text_area("¿Cómo entrenaste de lunes a ayer?")
        fatiga = st.slider("Fatiga (1-10)", 1, 10, 5)
        if st.form_submit_button("Generar Plan Adaptado"):
            prompt = f"""Coach de {st.session_state['deporte']} {st.session_state['modalidad']}. Carrera {st.session_state['nombre_carrera']}. 
            Hoy es {dia_actual_nombre}. Feedback previo: {resumen}. Fatiga: {fatiga}. 
            Genera plan hasta el domingo. Formato OBLIGATORIO: [DIA] (Ej: [SABADO], [DOMINGO]) 
            con secciones **ENTRENAMIENTO PRINCIPAL**, **FUERZA/MOVILIDAD**, **NUTRICIÓN**."""
            res = model.generate_content(prompt)
            st.session_state['historial_entrenamientos'][semana_id] = res.text
            guardar_en_disco(st.session_state.to_dict())
            st.rerun()
    st.stop()

# --- 7. DASHBOARD ---
st.title(f"🏆 {st.session_state['modalidad']} - {st.session_state['nombre_carrera']}")
with st.sidebar:
    st.metric("Días para meta", (st.session_state['fecha_carrera'] - hoy).days)
    if st.button("🔄 Re-ajustar semana"):
        del st.session_state['historial_entrenamientos'][semana_id]
        guardar_en_disco(st.session_state.to_dict())
        st.rerun()
    if st.button("🗑️ Reset Todo"):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        st.session_state.clear()
        st.rerun()

# --- 8. VISUALIZACIÓN (CORRECCIÓN "PLAN NO DISPONIBLE") ---
plan_actual = st.session_state['historial_entrenamientos'][semana_id]
dias_visibles = dias_semana_es[indice_hoy:] 
tabs = st.tabs([f"🟢 {d}" if d == dia_actual_nombre else d for d in dias_visibles])

def extraer_dia_ultra(dia_buscado, texto_completo):
    # Normalizamos el texto de la IA para quitar tildes y facilitar la búsqueda
    texto_norm = normalizar(texto_completo)
    dia_norm = normalizar(dia_buscado)
    
    # Buscamos la posición del día normalizado
    # Intentamos con corchetes [SABADO] o solo SABADO:
    posibles_formatos = [f"[{dia_norm}]", f"**{dia_norm}**", f"{dia_norm}:"]
    
    inicio = -1
    for fmt in posibles_formatos:
        inicio = texto_norm.find(fmt)
        if inicio != -1: 
            inicio += len(fmt)
            break
            
    if inicio == -1: return "Día de descanso o formato no detectado por el Coach."
    
    # Buscamos dónde termina el bloque (el inicio del siguiente día o el final del texto)
    fin = len(texto_norm)
    for d in dias_semana_es:
        d_norm = normalizar(d)
        pos_siguiente = texto_norm.find(f"[{d_norm}]", inicio)
        if pos_siguiente == -1: pos_siguiente = texto_norm.find(f"**{d_norm}**", inicio)
        
        if pos_siguiente != -1 and pos_siguiente < fin:
            fin = pos_siguiente
            
    return texto_completo[inicio:fin].strip()

for i, nombre_dia in enumerate(dias_visibles):
    with tabs[i]:
        contenido = extraer_dia_ultra(nombre_dia, plan_actual)
        if nombre_dia == dia_actual_nombre: st.success(f"⚡ OBJETIVO DE HOY")
        
        # Identificar secciones por palabras clave
        if "**ENTRENAMIENTO" in contenido.upper() or "**FUERZA" in contenido.upper():
            partes = re.split(r'(\*\*ENTRENAMIENTO PRINCIPAL\*\*|\*\*FUERZA/MOVILIDAD\*\*|\*\*NUTRICIÓN\*\*|\*\*NUTRICION\*\*)', contenido, flags=re.IGNORECASE)
            for j in range(1, len(partes), 2):
                with st.container(border=True):
                    st.markdown(f"#### {partes[j].replace('*', '')}")
                    st.write(partes[j+1].strip())
        else:
            st.info(contenido)
