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

# --- 2. FUNCIONES DE APOYO (ROBUSTEZ MEJORADA) ---
def normalizar(texto):
    """Limpia el texto de tildes y caracteres especiales para comparaciones seguras."""
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto))
                  if unicodedata.category(c) != 'Mn').upper().strip()

def guardar_en_disco(datos):
    try:
        # Convertimos session_state a un dict limpio para JSON
        copia = {k: v for k, v in datos.items() if k != 'model'}
        if 'fecha_carrera' in copia:
            copia['fecha_carrera'] = str(copia['fecha_carrera'])
        with open(CONFIG_FILE, "w") as f:
            json.dump(copia, f)
    except Exception as e:
        st.error(f"Error al guardar: {e}")

def cargar_desde_disco():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                datos = json.load(f)
                if 'fecha_carrera' in datos and datos['fecha_carrera']:
                    datos['fecha_carrera'] = datetime.date.fromisoformat(datos['fecha_carrera'])
                return datos
        except: return None
    return None

# --- 3. CONEXIÓN IA (Actualizado a modelo estable) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Se recomienda gemini-1.5-flash por estabilidad y velocidad
    model = genai.GenerativeModel('gemini-1.5-flash')
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
    else:
        st.session_state['configurado'] = False
        st.session_state['historial_entrenamientos'] = {}

# --- 5. ONBOARDING ---
if not st.session_state.get('configurado'):
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
            guardar_en_disco(st.session_state)
            st.rerun()
    st.stop()

# --- 6. AJUSTE SEMANAL ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_nombre})")
    with st.form("ajuste"):
        resumen = st.text_area("¿Cómo entrenaste los últimos días?")
        fatiga = st.slider("Fatiga (1-10)", 1, 10, 5)
        if st.form_submit_button("Generar Plan Adaptado"):
            with st.spinner("El Coach está diseñando tu plan..."):
                prompt = f"""Coach experto. Genera un plan desde hoy {dia_actual_nombre} hasta el domingo para {st.session_state['deporte']}.
                Objetivo: {st.session_state['nombre_carrera']}. Feedback: {resumen}. Fatiga: {fatiga}.
                Es obligatorio usar este formato para cada día:
                [NOMBRE DEL DIA]
                **ENTRENAMIENTO PRINCIPAL**: ...
                **FUERZA/MOVILIDAD**: ...
                **NUTRICIÓN**: ...
                """
                try:
                    res = model.generate_content(prompt)
                    st.session_state['historial_entrenamientos'][semana_id] = res.text
                    guardar_en_disco(st.session_state)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error con la IA: {e}")
    st.stop()

# --- 7. DASHBOARD ---
st.title(f"🏆 {st.session_state['modalidad']} - {st.session_state['nombre_carrera']}")
with st.sidebar:
    st.metric("Días para meta", (st.session_state['fecha_carrera'] - hoy).days)
    if st.button("🔄 Re-ajustar semana"):
        if semana_id in st.session_state['historial_entrenamientos']:
            del st.session_state['historial_entrenamientos'][semana_id]
            guardar_en_disco(st.session_state)
            st.rerun()
    if st.button("🗑️ Reset Todo"):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        st.session_state.clear()
        st.rerun()

# --- 8. VISUALIZACIÓN (BÚSQUEDA ROBUSTA REESCRITA) ---
plan_actual = st.session_state['historial_entrenamientos'].get(semana_id, "")
dias_visibles = dias_semana_es[indice_hoy:] 
tabs = st.tabs([f"🟢 {d}" if d == dia_actual_nombre else d for d in dias_visibles])

def extraer_dia_inteligente(dia_buscado, texto_original):
    if not texto_original: return "No hay plan generado."
    
    texto_norm = normalizar(texto_original)
    dia_norm = normalizar(dia_buscado)
    
    # Patrones de búsqueda: [DIA], **DIA**, DIA:
    patrones = [f"[{dia_norm}]", f"**{dia_norm}**", f"{dia_norm}:"]
    
    inicio = -1
    for p in patrones:
        inicio = texto_norm.find(p)
        if inicio != -1:
            inicio += len(p)
            break
            
    if inicio == -1:
        return "Día de descanso o descanso activo según el Coach."
    
    # El final es el inicio del siguiente día mencionado en el texto
    fin = len(texto_norm)
    for d in dias_semana_es:
        dn = normalizar(d)
        # Buscamos la posición de cualquier otro día después del inicio actual
        for p_fin in [f"[{dn}]", f"**{dn}**"]:
            pos = texto_norm.find(p_fin, inicio)
            if pos != -1 and pos < fin:
                fin = pos
                
    return texto_original[inicio:fin].strip()

for i, nombre_dia in enumerate(dias_visibles):
    with tabs[i]:
        if nombre_dia == dia_actual_nombre: st.success(f"⚡ OBJETIVO DE HOY")
        
        contenido = extraer_dia_inteligente(nombre_dia, plan_actual)
        
        # Split inteligente que captura las secciones principales
        # Busca cualquier variante de negritas para Entrenamiento, Fuerza o Nutrición
        secciones = re.split(r'(\*\*ENTRENAMIENTO.*?\*\*|\*\*FUERZA.*?\*\*|\*\*NUTRICI.*?\*\*)', contenido, flags=re.IGNORECASE)
        
        if len(secciones) > 1:
            for j in range(1, len(secciones), 2):
                titulo = secciones[j].replace('*', '').strip()
                texto = secciones[j+1].strip() if (j+1) < len(secciones) else ""
                if texto:
                    with st.container(border=True):
                        st.markdown(f"#### {titulo}")
                        st.write(texto)
        else:
            st.info(contenido)
