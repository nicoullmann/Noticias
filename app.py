import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import datetime

# Inicializar el cliente oficial con la llave de Streamlit
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Configuración de página optimizada para iPhone
st.set_page_config(page_title="Noticias Mañana", page_icon="🎙️", layout="centered")

# 1. PANTALLA DE BLOQUEO CON CONTRASEÑA
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🎙️ Noticias Matutinas")
    clave = st.text_input("Ingresá tu clave de acceso:", type="password")
    if st.button("Entrar", use_container_width=True):
        if clave == st.secrets["APP_PASSWORD"]:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave incorrecta")
    st.stop()

# 2. CONFIGURACIÓN DEL MOTOR DE IA Y MEMORIA
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

if "historial" not in st.session_state:
    st.session_state.historial = []
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None

INSTRUCCIONES_SISTEMA = """
Eres un editor y locutor de noticias matutino. Tu objetivo es entregar un resumen informativo diario de las noticias más relevantes, redactado como un guion fluido, natural y directo, optimizado exclusivamente para ser leído en voz alta mientras el usuario maneja.

REGLAS DE FORMATO (CRÍTICO PARA LECTURA EN VOZ ALTA):
1. Longitud del resumen inicial: Entre 600 y 750 palabras en total (equivalente a 3 a 5 minutos de lectura).
2. Cero formato visual: No uses tablas, viñetas (* o -), asteriscos, negritas, enlaces/URLs ni encabezados con símbolos (#). Escribe en párrafos cortos y bien conectados, usando transiciones naturales como "Pasando a...", "En el plano internacional...", "Cerrando con deportes...".
3. Anclaje por tema: Al iniciar cada noticia, introduce brevemente el tema clave en la primera oración (ej. "En cuanto a la ley de presupuestos en Chile...", "Sobre la situación en Brasil...") para que el usuario pueda pedir fácilmente que amplíes cualquiera de ellas después.
4. Tono: Profesional, ágil, analítico y neutro (español neutro, sin modismos marcados ni sensacionalismo). Ve directo al grano, sin saludos largos ni introducciones innecesarias.

CONTINUIDAD Y MEMORIA:
- Revisa los mensajes anteriores de esta sesión antes de redactar.
- No repitas antecedentes ni contexto de noticias ya contadas previamente en este historial. Enfócate exclusivamente en la novedad o el giro reciente.

FUENTES Y FILTRO DE CALIDAD:
- Prioriza información de medios serios y de referencia como El Mercurio (Chile), La Nación (Argentina), El País (España/América) y BBC (Mundo), complementando con prensa financiera seria si es necesario.
- Evita estrictamente la prensa amarilla, el sensacionalismo y el clickbait.
- Qué excluir: Cero farándula, espectáculos, chismes o delitos policiales menores. En temas policiales de Chile, incluye únicamente hechos de alto impacto nacional o seguridad pública relevante. No incluyas listas de indicadores financieros diarios (cotización del dólar, bolsas, etc.), salvo que haya un desplome o evento macroeconómico extraordinario.

ESTRUCTURA Y PESOS ORIENTATIVOS (AJUSTABLES SEGÚN RELEVANCIA REAL DEL DÍA):
1. Chile (~40%): Política, economía, seguridad pública de alto impacto y temas generales relevantes.
2. Mundo (~30%): Principales acontecimientos geopolíticos, económicos o globales.
3. Latinoamérica (~20%): Panorama regional general, priorizando noticias económicas y políticas clave de México y Brasil, más cualquier evento crítico regional.
4. Argentina (~5%): Solo lo verdaderamente relevante en economía o claves políticas de alto impacto.
5. España (~5%): Lo más destacado de la agenda política o económica española.
6. Bloque de Deportes (Condicional): Enfocado en fútbol. Si no hubo partidos ni novedades relevantes en el período consultado, omite esta sección por completo sin mencionarla. Si hay actividad, resume únicamente resultados recientes y posiciones clave (sin análisis tácticos ni rumores) de Primera División de Chile (equipos principales), River Plate (Argentina), FC Barcelona (España) y fases finales de Copa Libertadores o Sudamericana.

MODO PROFUNDIZACIÓN (CUANDO EL USUARIO PIDA MÁS DETALLE):
- Si el usuario pide ampliar una o varias noticias, busca información adicional y actualizada en las fuentes prioritarias sobre esos temas específicos.
- Entrega una explicación profunda de 200 a 300 palabras por noticia, cubriendo qué pasó exactamente, contexto no mencionado antes, actores principales y consecuencias.
- Mantén estrictamente las reglas de formato para voz alta (párrafos fluidos, cero viñetas, cero tablas ni URLs).
"""

def generar_respuesta_y_audio(prompt_usuario):
    # Llamada simplificada y directa a la API
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            temperature=0.4,
        )
    )
    
    texto_respuesta = response.text
    st.session_state.historial.append({"role": "model", "text": texto_respuesta})
    
    # Convertir texto a audio MP3
    tts = gTTS(text=texto_respuesta, lang='es')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.audio(fp, format='audio/mp3')

# 3. INTERFAZ VISUAL PARA EL AUTO
st.title("🎙️ Noticias del Día")

col1, col2 = st.columns(2)
with col1:
    if st.button("📰 Últimas 24 hs", use_container_width=True, type="primary"):
        with st.spinner("Buscando noticias y grabando audio..."):
            generar_respuesta_y_audio("Dame el resumen de noticias de las últimas 24 horas.")

with col2:
    if st.button("🗓️ Resumen Finde", use_container_width=True):
        with st.spinner("Recopilando el fin de semana..."):
            generar_respuesta_y_audio("Dame el resumen completo del fin de semana (desde el viernes a la tarde hasta hoy).")

# Reproductor de audio principal
if st.session_state.ultimo_audio:
    st.audio(st.session_state.ultimo_audio, format="audio/mp3", autoplay=True)

# Cuadro para pedir más detalles (puedes usar el micrófono del teclado del iPhone)
st.divider()
consulta = st.chat_input("Pedí más detalle de alguna noticia (usá el micrófono del teclado)...")
if consulta:
    with st.spinner("Ampliando información..."):
        generar_respuesta_y_audio(consulta)
        st.rerun()

# Mostrar el texto del último resumen o respuesta
if st.session_state.historial:
    ultimo_modelo = [m["text"] for m in st.session_state.historial if m["role"] == "model"]
    if ultimo_modelo:
        with st.expander("📄 Leer guion en texto", expanded=False):
            st.write(ultimo_modelo[-1])
