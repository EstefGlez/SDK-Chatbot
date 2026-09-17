import streamlit as st
import requests

# TODO: reemplazar por la URL real del backend cuando esté desplegado
BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Panel de chatbots", page_icon="💬")

# TODO: agregar login real antes de mostrar nada (cada cliente debe ver solo
# sus propios chatbots). Por ahora, panel abierto para poder probar el flujo.

st.title("Configura tu chatbot")

nombre = st.text_input("Nombre del chatbot", value="Mi chatbot")

modelo = st.selectbox(
    "Modelo de IA principal",
    ["deepseek-ai/deepseek-v4-flash-0731", "llama-3.3-70b-versatile", "gemini-3.1-pro"],
)

prompt_sistema = st.text_area(
    "Instrucciones para el chatbot (prompt de sistema)",
    value="Eres un asistente de atención al cliente, amable y breve.",
    height=120,
)

api_key_propia = st.text_input(
    "Tu propia API key (opcional, déjalo vacío para usar la de la plataforma)",
    type="password",
)

if st.button("Guardar configuración"):
    payload = {
        "nombre": nombre,
        "modelo_preferido": modelo,
        "prompt_sistema": prompt_sistema,
        "api_key": api_key_propia or None,
    }
    try:
        res = requests.post(f"{BACKEND_URL}/api/admin/chatbots", json=payload)
        st.success(f"Guardado: {res.json()}")
    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")

st.divider()
st.caption("Corre este panel con: streamlit run app.py")
