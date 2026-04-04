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

# --- 2. FUNCIONES DE PERSISTENCIA Y NORMALIZACIÓN ---
def normalizar(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto))
                  if unicodedata.category(c) != 'Mn').upper().strip()

def guardar_datos():
    datos = {
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
        json.dump(datos, f)

def cargar_datos():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                d = json.load(f)
                if d.get('fecha_carrera'):
                    d['fecha_carrera'] = datetime.date.fromisoformat(d['fecha_carrera'])
                return d
        except: return None
    return None

# --- 3. CONEXIÓN IA (Actualizado a Gemini 1.5 Flash - Máxima compatibilidad) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Intentamos con el modelo más reciente y compatible
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-pro')
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
    persistido = cargar_datos()
    if persistido:
        st.session_state.update(persistido)
    else:
        st.session_state['configurado'] = False
        st.session_state['historial_entrenamientos'] = {}

# --- 5. ONBOARDING DINÁMICO ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Perfil de Atleta")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            dep_sel = st.selectbox("Deporte", ["Ciclismo", "Running", "Trail Running", "Triatlón"])
            mods = {"Ciclismo": ["XCO", "XCM", "Ruta", "Gravel", "Enduro"], 
                    "Running": ["5K", "10K", "21K", "42K", "Milla"],
                    "Trail Running": ["Short Trail", "Trail", "Ultra Trail"],
                    "Triatlón": ["Sprint", "Olímpico", "70.3", "140.6"]}
            mod_sel = st.selectbox("Especialidad / Distancia", mods.get(dep_sel, ["General"]))
            nom_evento = st.text_input("Nombre de la meta", "Mi Gran Competencia")
        with c2:
            fec_c = st.date_input("Fecha del Evento", hoy + datetime.timedelta(days=60))
            niv = st.select_slider("Nivel actual", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
            dias = st.slider("Días disponibles/semana", 1, 7, 5)
        
        if st.button("🚀 Crear mi Plan Maestro"):
            st.session_state.update({
                'deporte': dep_sel, 'modalidad': mod_sel, 'nombre_carrera': nom_evento,
                'fecha_carrera': fec_c, 'nivel': niv, 'dias_w': dias, 
                'configurado': True, 'historial_entrenamientos': {}
            })
            guardar_datos()
            st.rerun()
    st.stop()

# --- 6. AJUSTE SEMANAL ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_nombre})")
    with st.container(border=True):
        st.write(f"Es **{dia_actual_nombre}**. Cuéntame tu progreso para cerrar la semana:")
        with st.form("ajuste_semanal"):
            resumen = st.text_area("¿Cómo entrenaste de lunes a ayer?", placeholder="Ej: Cumplí todo / Salté el miércoles...")
            fatiga = st.slider("Fatiga acumulada (1-10)", 1, 10, 5)
            
            if st.form_submit_button("Generar Plan Adaptado"):
                if not resumen:
                    st.warning("Escribe un breve resumen para que el Coach pueda ayudarte mejor.")
                else:
                    with st.spinner("Consultando al Coach..."):
                        prompt = f"""Actúa como un Coach experto en {st.session_state['deporte']} ({st.session_state['modalidad']}).
                        Planifica los días restantes (de hoy {dia_actual_nombre} a domingo).
                        Feedback: {resumen}. Fatiga: {fatiga}/10. Nivel: {st.session_state['nivel']}.
                        Formato requerido para cada día:
                        [NOMBRE_DIA]
                        **ENTRENAMIENTO PRINCIPAL**: (detalles)
                        **FUERZA/MOVILIDAD**: (ejercicios)
                        **NUTRICIÓN**: (consejos)"""
                        try:
                            # Llamada limpia sin especificar versión v1beta para evitar el 404
                            response = model.generate_content(prompt)
                            if response and response.text:
                                st.session_state['historial_entrenamientos'][semana_id] = response.text
                                guardar_datos()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error de conexión: {str(e)}. Intenta de nuevo.")
    st.stop()

# --- 7. DASHBOARD PRINCIPAL ---
st.title(f"🏆 {st.session_state['modalidad']} - {st.session_state['nombre_carrera']}")
with st.sidebar:
    st.info(f"**Deporte:** {st.session_state['deporte']}")
    st.metric("Días para la meta", (st.session_state.get('fecha_carrera', hoy) - hoy).days)
    st.divider()
    if st.button("🔄 Re-ajustar esta semana"):
        if semana_id in st.session_state['historial_entrenamientos']:
            del st.session_state['historial_entrenamientos'][semana_id]
            guardar_datos()
            st.rerun()
    if st.button("🗑️ Reset Todo (Nuevo Objetivo)"):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        st.session_state.clear()
        st.rerun()

# --- 8. VISUALIZACIÓN FILTRADA ---
plan_actual = st.session_state['historial_entrenamientos'].get(semana_id, "")
dias_visibles = dias_semana_es[indice_hoy:] 
tabs = st.tabs([f"🟢 {d}" if d == dia_actual_nombre else d for d in dias_visibles])

def extraer_dia_blindado(dia_target, texto):
    if not texto: return ""
    texto_norm = normalizar(texto)
    dia_norm = normalizar(dia_target)
    tags = [f"[{dia_norm}]", f"**{dia_norm}**", f"{dia_norm}:", f"### {dia_norm}"]
    inicio = -1
    for t in tags:
        inicio = texto_norm.find(t)
        if inicio != -1:
            inicio += len(t)
            break
    if inicio == -1: return "Día de recuperación o no planificado."
    fin = len(texto_norm)
    for d in dias_semana_es:
        dn = normalizar(d)
        for t in [f"[{dn}]", f"**{dn}**", f"### {dn}"]:
            p = texto_norm.find(t, inicio)
            if p != -1 and p < fin: fin = p
    return texto[inicio:fin].strip()

for i, nombre_dia in enumerate(dias_visibles):
    with tabs[i]:
        if nombre_dia == dia_actual_nombre: st.success("⚡ OBJETIVO DE HOY")
        contenido = extraer_dia_blindado(nombre_dia, plan_actual)
        secciones = re.split(r'(\*\*.*?\*\*)', contenido)
        if len(secciones) > 1:
            for j in range(1, len(secciones), 2):
                tit = secciones[j].replace("*", "").strip()
                val = secciones[j+1].strip() if j+1 < len(secciones) else ""
                if val:
                    with st.container(border=True):
                        st.markdown(f"#### {tit}")
                        st.write(val)
        else: st.info(contenido)
