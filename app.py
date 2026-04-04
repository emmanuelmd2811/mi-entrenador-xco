import streamlit as st
import google.generativeai as genai
import datetime
import re
import json
import os

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Elite Adaptive Coach Pro", layout="wide", page_icon="🏆")

# Archivo de persistencia
CONFIG_FILE = "user_data.json"

st.markdown("""
    <style>
    .stApp { background-color: #1C1E23; }
    .stMarkdown, p, span { color: #D1D5DB !important; }
    h1, h2, h3 { color: #10B981 !important; font-family: 'Inter', sans-serif; }
    div.stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #2D3139; padding: 8px; border-radius: 12px; }
    div.stTabs [data-baseweb="tab"] { background-color: #374151; border-radius: 8px; color: #9CA3AF !important; padding: 8px 16px; }
    div.stTabs [aria-selected="true"] { background-color: #10B981 !important; color: white !important; font-weight: bold; border: 2px solid #34D399; }
    div[data-testid="stVerticalBlock"] > div.element-container div.stMarkdown div.stContainer {
        border: 1px solid #4B5563; border-radius: 15px; background-color: #262B33; padding: 18px; margin-bottom: 12px;
    }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE PERSISTENCIA ---
def guardar_en_disco(datos):
    with open(CONFIG_FILE, "w") as f:
        # Convertimos fechas a string para que JSON pueda guardarlas
        json.dump(datos, f, default=str)

def cargar_desde_disco():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                datos = json.load(f)
                # Convertir la fecha de string de vuelta a objeto date
                if 'fecha_carrera' in datos and datos['fecha_carrera']:
                    datos['fecha_carrera'] = datetime.date.fromisoformat(datos['fecha_carrera'])
                return datos
        except:
            return None
    return None

# --- 3. CONEXIÓN IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("⚠️ Configura 'GOOGLE_API_KEY' en los Secrets.")
    st.stop()

# --- 4. LÓGICA DE TIEMPO Y CARGA INICIAL ---
hoy = datetime.date.today()
dias_semana_es = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
indice_hoy = hoy.weekday() 
dia_actual_nombre = dias_semana_es[indice_hoy]
semana_id = f"{hoy.year}-W{hoy.isocalendar()[1]}"

# Intentar cargar datos guardados si no están en la sesión
if 'configurado' not in st.session_state:
    datos_viejos = cargar_desde_disco()
    if datos_viejos:
        st.session_state.update(datos_viejos)
        st.session_state['configurado'] = True
    else:
        st.session_state['configurado'] = False
        st.session_state['historial_entrenamientos'] = {}

# --- 5. ONBOARDING REACTIVO ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Perfil")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            deporte_sel = st.selectbox("Deporte", ["Ciclismo", "Running", "Trail Running", "Triatlón"])
            if deporte_sel == "Ciclismo": mods = ["XCO", "XCM", "Ruta", "Enduro", "Gravel"]
            elif deporte_sel == "Running": mods = ["5K", "10K", "21K", "42K", "Milla"]
            elif deporte_sel == "Trail Running": mods = ["Short Trail", "Trail", "Ultra Trail"]
            else: mods = ["Sprint", "Olímpico", "70.3", "140.6"]
            
            modalidad_sel = st.selectbox("Especialidad", mods)
            nombre_evento = st.text_input("Nombre de la meta", "Mi Competencia")
        with col2:
            fecha_c = st.date_input("Fecha del Evento", hoy + datetime.timedelta(days=60))
            nivel = st.select_slider("Nivel", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
            dias_w = st.slider("Días/semana", 1, 7, 5)
        
        if st.button("🚀 Crear mi Plan Maestro"):
            nuevos_datos = {
                'deporte': deporte_sel, 'modalidad': modalidad_sel, 'nombre_carrera': nombre_evento,
                'fecha_carrera': fecha_c, 'nivel': nivel, 'dias_w': dias_w, 'configurado': True,
                'historial_entrenamientos': {}
            }
            st.session_state.update(nuevos_datos)
            guardar_en_disco(nuevos_datos)
            st.rerun()
    st.stop()

# --- 6. AJUSTE SEMANAL ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_nombre})")
    with st.container(border=True):
        with st.form("ajuste"):
            resumen = st.text_area("¿Cómo entrenaste de lunes a ayer?")
            fatiga = st.slider("Fatiga (1-10)", 1, 10, 5)
            if st.form_submit_button("Generar Plan Adaptado"):
                prompt = f"Coach de {st.session_state['deporte']} {st.session_state['modalidad']}. Carrera {st.session_state['nombre_carrera']}. Hoy es {dia_actual_nombre}. Feedback: {resumen}. Fatiga: {fatiga}. Genera plan hasta el domingo en formato [DIA] con **ENTRENAMIENTO PRINCIPAL**, **FUERZA/MOVILIDAD**, **NUTRICIÓN**."
                res = model.generate_content(prompt)
                st.session_state['historial_entrenamientos'][semana_id] = res.text
                # Guardamos el nuevo historial en el disco
                guardar_en_disco(st.session_state.to_dict())
                st.rerun()
    st.stop()

# --- 7. DASHBOARD ---
st.title(f"🏆 {st.session_state['modalidad']} - {st.session_state['nombre_carrera']}")
with st.sidebar:
    st.info(f"**{st.session_state['deporte']}**")
    st.metric("Días para meta", (st.session_state['fecha_carrera'] - hoy).days)
    if st.button("🔄 Re-ajustar semana"):
        del st.session_state['historial_entrenamientos'][semana_id]
        guardar_en_disco(st.session_state.to_dict())
        st.rerun()
    if st.button("🗑️ Reset (Borrar todo)"):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        st.session_state.clear()
        st.rerun()

# --- 8. VISUALIZACIÓN FILTRADA ---
plan_actual = st.session_state['historial_entrenamientos'][semana_id]
dias_visibles = dias_semana_es[indice_hoy:] 
tabs = st.tabs([f"🟢 {d}" if d == dia_actual_nombre else d for d in dias_visibles])

def extraer_dia_robusto(dia, texto):
    pattern = rf"\[\s*{dia}\s*\](.*?)(?=\[\s*\w+\s*\]|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    return res[0].strip() if res else "Plan no disponible."

for i, nombre_dia in enumerate(dias_visibles):
    with tabs[i]:
        contenido = extraer_dia_robusto(nombre_dia, plan_actual)
        if nombre_dia == dia_actual_nombre: st.success(f"⚡ OBJETIVO DE HOY")
        
        if "**ENTRENAMIENTO" in contenido.upper():
            partes = re.split(r'(\*\*ENTRENAMIENTO PRINCIPAL\*\*|\*\*FUERZA/MOVILIDAD\*\*|\*\*NUTRICIÓN\*\*)', contenido, flags=re.IGNORECASE)
            for j in range(1, len(partes), 2):
                with st.container(border=True):
                    st.markdown(f"#### {partes[j].replace('*', '')}")
                    st.write(partes[j+1].strip())
        else: st.info(contenido)
