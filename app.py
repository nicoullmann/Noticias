import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
import io
import datetime

st.set_page_config(page_title="Noticias Matutinas", page_icon="🎙️", layout="centered")

# 1. VALIDACIÓN DE SECRETS
if "GEMINI_API_KEY" not in st.secrets or "APP_PASSWORD" not in st.secrets:
    st.error("⚠️ Faltan configurar los Secrets en Streamlit Cloud. Asegurate de incluir GEMINI_API_KEY y APP_PASSWORD.")
    st.stop()

# 2. INICIALIZAR CLIENTE DE GEMINI
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# 3. PANTALLA DE BLOQUEO CON CONTRASEÑA
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("### 🎙️ Noticias Matutinas")
    password_ingresada = st.text_input("Ingresá tu clave de acceso:", type="password")
    if st.button("Entrar"):
        if password_ingresada == st.secrets["APP_PASSWORD"]:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop()

# 4. APLICACIÓN PRINCIPAL
st.markdown("# 🎙️ Noticias Matutinas")

if "historial" not in st.session_state:
    st.session_state.historial = []

INSTRUCCIONES_SISTEMA = (
    "Eres un locutor profesional de noticias matutinas. "
    "Busca información reciente de las últimas 24 horas sobre tecnología, economía y actualidad global, "
    "y redacta un resumen fluido, ameno y estructurado para ser escuchado en audio en el auto."
)

def generar_respuesta_y_audio(prompt_usuario):
    import time
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=INSTRUCCIONES_SISTEMA,
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
            return # Salimos si salió todo bien
            
        except Exception as e:
            if ("503" in str(e) or "UNAVAILABLE" in str(e)) and intento < max_intentos - 1:
                time.sleep(5) 
                continue
            else:
                st.error(f"Error al conectar con la API de Gemini: {e}")
                break

# Botón para activar el resumen de noticias
if st.button("📰 Generar resumen de las últimas 24 horas"):
    with st.spinner("Buscando noticias y preparando la locución..."):
        generar_respuesta_y_audio("Dame el resumen de noticias de las últimas 24 horas.")

# Mostrar historial en pantalla
for mensaje in st.session_state.historial:
    if mensaje["role"] == "model":
        st.write(mensaje["text"])
