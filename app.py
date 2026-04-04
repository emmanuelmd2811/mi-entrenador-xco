import streamlit as st
import google.generativeai as genai
import datetime
import re

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Elite Adaptive Coach", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #1C1E23; }
    .stMarkdown, p, span { color: #D1D5DB !important; }
    h1, h2, h3 { color: #10B981 !important; font-family: 'Inter', sans-serif; }
    
    /* Tabs Estilo Deportivo */
    div.stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #2D3139; padding: 8px; border-radius: 12px; }
    div.stTabs [data-baseweb="tab"] { background-color: #374151; border-radius: 8px; color: #9CA3AF !important; padding: 8px 16px; }
    
    /* Color para el Tab del día Actual (Resaltado) */
    div.stTabs [aria-selected="true"] { background-color: #10B981 !important; color: white !important; font-weight: bold; border: 2px solid #34D399; }
    
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
dias_semana_es = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
# Obtener índice del día actual (Lunes=0, Domingo=6)
indice_hoy = hoy.weekday() 
dia_actual_nombre = dias_semana_es[indice_hoy]
semana_id = f"{hoy.year}-W{hoy.isocalendar()[1]}"

if 'configurado' not in st.session_state:
    st.session_state['configurado'] = False
if 'historial_entrenamientos' not in st.session_state:
    st.session_state['historial_entrenamientos'] = {}

# --- 4. ONBOARDING ---
if not st.session_state['configurado']:
    st.title("🎯 Configura tu Perfil")
    with st.container(border=True):
        with st.form("onboarding"):
            c1, c2 = st.columns(2)
            with c1:
                deporte = st.selectbox("Deporte", ["Ciclismo", "Running", "Trail", "Triatlón"])
                modalidad = st.text_input("Disciplina (XCO, 21K, etc.)", "XCO")
                nombre_e = st.text_input("Nombre del evento", "Competencia")
            with c2:
                fecha_c = st.date_input("Fecha", hoy + datetime.timedelta(days=60))
                nivel = st.select_slider("Nivel", options=["Principiante", "Intermedio", "Avanzado", "Elite"])
                dias_w = st.slider("Días/semana", 1, 7, 5)
            if st.form_submit_button("🚀 Crear Plan"):
                st.session_state.update({'deporte': deporte, 'modalidad': modalidad, 'nombre_carrera': nombre_e,
                                        'fecha_carrera': fecha_c, 'nivel': nivel, 'dias_w': dias_w, 'configurado': True})
                st.rerun()
    st.stop()

# --- 5. AJUSTE SEMANAL ---
if semana_id not in st.session_state['historial_entrenamientos']:
    st.title(f"📅 Ajuste de Semana ({dia_actual_nombre})")
    with st.container(border=True):
        with st.form("ajuste"):
            resumen = st.text_area("¿Cómo entrenaste los días pasados?")
            fatiga = st.slider("Fatiga (1-10)", 1, 10, 5)
            if st.form_submit_button("Generar Plan"):
                prompt = f"""Coach de {st.session_state['deporte']} {st.session_state['modalidad']}.
                Genera el plan desde HOY {dia_actual_nombre} hasta el DOMINGO.
                Usa este formato exacto para cada día:
                [{dia_actual_nombre}]
                **ENTRENAMIENTO PRINCIPAL**: ...
                **FUERZA/MOVILIDAD**: ...
                **NUTRICIÓN**: ...
                """
                res = model.generate_content(prompt)
                st.session_state['historial_entrenamientos'][semana_id] = res.text
                st.rerun()
    st.stop()

# --- 6. DASHBOARD PRINCIPAL ---
st.title(f"🏆 {st.session_state['modalidad']} - {st.session_state['nombre_carrera']}")

with st.sidebar:
    st.header("📊 Perfil")
    st.write(f"Deporte: {st.session_state['deporte']}")
    st.metric("Días para meta", (st.session_state['fecha_carrera'] - hoy).days)
    if st.button("🔄 Re-ajustar semana"):
        del st.session_state['historial_entrenamientos'][semana_id]
        st.rerun()
    if st.button("🗑️ Reset"):
        st.session_state.clear()
        st.rerun()

# --- 7. VISUALIZACIÓN DINÁMICA (Solo días futuros) ---
plan_actual = st.session_state['historial_entrenamientos'][semana_id]

# Solo mostramos los días desde HOY hasta el final de la semana
dias_visibles = dias_semana_es[indice_hoy:] 
tabs = st.tabs([f"🟢 {d}" if d == dia_actual_nombre else d for d in dias_visibles])

def extraer_dia_robusto(dia, texto):
    # Regex mejorada: busca el día entre corchetes, ignorando espacios o basura
    pattern = rf"\[\s*{dia}\s*\](.*?)(?=\[\s*\w+\s*\]|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    if res:
        return res[0].strip()
    # Si no encuentra [DIA], busca DIA: o DIA -
    pattern_alt = rf"{dia}:(.*?)(?={dias_semana_es}|$)"
    res_alt = re.findall(pattern_alt, texto, re.DOTALL | re.IGNORECASE)
    return res_alt[0].strip() if res_alt else "Día de descanso o consulta el plan completo."

for i, nombre_dia in enumerate(dias_visibles):
    with tabs[i]:
        contenido = extraer_dia_robusto(nombre_dia, plan_actual)
        
        if nombre_dia == dia_actual_nombre:
            st.success(f"⚡ OBJETIVO DE HOY: {nombre_dia}")
        
        # Renderizado de secciones
        if "**ENTRENAMIENTO" in contenido.upper() or "**FUERZA" in contenido.upper():
            partes = re.split(r'(\*\*ENTRENAMIENTO PRINCIPAL\*\*|\*\*FUERZA/MOVILIDAD\*\*|\*\*NUTRICIÓN\*\*)', contenido, flags=re.IGNORECASE)
            for j in range(1, len(partes), 2):
                titulo = partes[j].replace("*", "")
                with st.container(border=True):
                    st.markdown(f"#### {titulo}")
                    st.write(partes[j+1].strip())
        else:
            st.info(contenido)
