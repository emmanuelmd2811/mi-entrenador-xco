# --- 5. GENERACIÓN SEMANAL (CON PROMPT REFORZADO) ---
if st.session_state.get('plan_semanal_id') != semana_id or st.session_state.get('plan_semanal') is None:
    with st.spinner("🤖 El Coach está redactando tu semana..."):
        # Instrucciones mucho más agresivas sobre el formato
        prompt = f"""
        Eres un Coach de MTB XCO de nivel Pro. 
        ATLETA: Nivel {st.session_state['nivel']}, faltan {dias_meta} días para la carrera {st.session_state['nombre_carrera']}.
        
        TAREA: Genera un plan de lunes a domingo.
        REGLA DE FORMATO OBLIGATORIA: 
        Empieza CADA DÍA con el nombre entre corchetes, así: [LUNES], [MARTES], [MIERCOLES], [JUEVES], [VIERNES], [SABADO], [DOMINGO].
        
        Dentro de cada día DEBES incluir estas 3 secciones con negritas:
        **BICICLETA**: (Detalla intervalos, zonas de pulso y técnica)
        **GYM/CORE**: (Ejercicios de fuerza o estabilidad)
        **NUTRICIÓN**: (Consejo de hidratación o comida)
        
        Si un día es descanso, pon: [DIA] **BICICLETA**: Descanso total.
        """
        try:
            res = model.generate_content(prompt)
            # Guardamos la respuesta y forzamos que sea texto
            st.session_state['plan_semanal'] = str(res.text)
            st.session_state['plan_semanal_id'] = semana_id
        except Exception as e:
            st.error(f"Error al conectar con la IA: {e}")

# --- 6. INTERFAZ FINAL (CON EXTRACCIÓN MEJORADA) ---
st.title(f"📅 Microciclo: Semana {hoy.isocalendar()[1]}")

def extraer_dia(dia, texto):
    if not texto: return "Cargando plan..."
    # Buscamos el día ignorando mayúsculas/minúsculas y espacios
    pattern = rf"\[{dia}\](.*?)(?=\[|$)"
    res = re.findall(pattern, texto, re.DOTALL | re.IGNORECASE)
    if res:
        return res[0].strip()
    return "Día de recuperación o formato no detectado por la IA."

dias_lista = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
tabs = st.tabs(dias_lista)
traduccion = {"Monday":"LUNES", "Tuesday":"MARTES", "Wednesday":"MIERCOLES", 
              "Thursday":"JUEVES", "Friday":"VIERNES", "Saturday":"SABADO", "Sunday":"DOMINGO"}
dia_hoy = traduccion.get(hoy.strftime("%A"))

if st.session_state.get('plan_semanal'):
    for i, nombre_dia in enumerate(dias_lista):
        with tabs[i]:
            contenido = extraer_dia(nombre_dia, st.session_state['plan_semanal'])
            
            if nombre_dia == dia_hoy:
                st.markdown(f"### ⚡ HOY: {nombre_dia}")
            else: 
                st.markdown(f"### {nombre_dia}")
            
            # Dividir por secciones para las tarjetas visuales
            # Buscamos los títulos que pedimos en el prompt
            if "**BICICLETA**" in contenido.upper() or "**GYM" in contenido.upper():
                partes = re.split(r'(\*\*BICICLETA\*\*|\*\*GYM/CORE\*\*|\*\*NUTRICIÓN\*\*)', contenido, flags=re.IGNORECASE)
                
                for j in range(1, len(partes), 2):
                    titulo = partes[j].replace("*", "")
                    texto_seccion = partes[j+1] if j+1 < len(partes) else ""
                    
                    if "BICICLETA" in titulo.upper():
                        with st.container(border=True):
                            st.markdown(f"#### 🚵‍♂️ {titulo}")
                            st.write(texto_seccion)
                    elif "GYM" in titulo.upper():
                        with st.container(border=True):
                            st.markdown(f"#### 🏋️ {titulo}")
                            st.write(texto_seccion)
                    elif "NUTRICIÓN" in titulo.upper():
                        with st.expander("🍎 Ver Nutrición"):
                            st.write(texto_seccion)
            else:
                # Si la IA no usó negritas pero sí dio texto, lo mostramos normal
                st.write(contenido)
