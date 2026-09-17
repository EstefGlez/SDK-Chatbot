from fastapi import APIRouter
from pydantic import BaseModel
import os
import requests
import uuid

router = APIRouter()

# InsForge REST API configuration (same as in chat.py)
INS_FORGE_BASE_URL = os.getenv("INS_FORGE_BASE_URL")
INS_FORGE_ANON_KEY = os.getenv("INS_FORGE_ANON_KEY")

def _insforge_headers():
    return {
        "Authorization": f"Bearer {INS_FORGE_ANON_KEY}",
        "Content-Type": "application/json"
    }

class ChatbotConfig(BaseModel):
    chatbot_id: str | None = None  # opcional: si se proporciona, se actualiza; sino, se crea nuevo
    nombre: str
    modelo_preferido: str
    prompt_sistema: str
    api_key: str | None = None  # opcional: si el cliente usa su propia key (debe encriptarse)

@router.post("/chatbots")
def create_or_update_chatbot(config: ChatbotConfig):
    """
    Crea o actualiza un chatbot en la base de datos de InsForge.
    - Genera un chatbot_id único si no se proporciona.
    - Si se proporciona api_key, debería encriptarse antes de guardar (por ahora se guarda en texto plano, TODO: agregar encriptación).
    - Inserta o actualiza el registro en la tabla `chatbots`.
    """
    try:
        # Determinar el ID: si se proporciona, usar ese; sino generar uno nuevo
        chatbot_id = config.chatbot_id
        if not chatbot_id:
            chatbot_id = str(uuid.uuid4())

        # Preparar los datos a guardar
        data = {
            "id": chatbot_id,
            "nombre": config.nombre,
            "modelo_preferido": config.modelo_preferido,
            "prompt_sistema": config.prompt_sistema,
            "api_key": config.api_key  # TODO: encriptar antes de guardar
            # dueno_id y creado_en se manejan por defecto o se pueden agregar si es necesario
            # Para dueno_id, necesitamos saber el usuario actual (no implementado aún)
            # creado_en tiene valor por defecto en la base de datos
        }

        # Intentar actualizar primero (si existe) o insertar
        # Primero verificamos si el registro existe
        url = f"{INS_FORGE_BASE_URL}/chatbots"
        params = {"id": f"eq.{chatbot_id}", "select": "id"}
        response = requests.get(url, headers=_insforge_headers(), params=params)
        response.raise_for_status()
        existing = response.json()

        if existing:
            # Actualizar registro existente
            response = requests.patch(url, headers=_insforge_headers(), params=params, json=[data])
            response.raise_for_status()
            action = "actualizado"
        else:
            # Insertar nuevo registro
            response = requests.post(url, headers=_insforge_headers(), json=[data])
            response.raise_for_status()
            action = "creado"

        return {"status": f"exitoso: chatbot {action}", "chatbot_id": chatbot_id}
    except Exception as e:
        print(f"Error en create_or_update_chatbot: {e}")
        return {"status": "error", "detalle": str(e)}

@router.get("/chatbots/{chatbot_id}/conversations")
def get_conversations(chatbot_id: str):
    """
    Obtiene el historial de conversaciones y mensajes para un chatbot dado.
    Regresa una lista de conversaciones, cada una con su ID, session_id, fecha de creación y mensajes.
    """
    try:
        # Obtener todas las conversaciones del chatbot
        url = f"{INS_FORGE_BASE_URL}/conversaciones"
        params = {"chatbot_id": f"eq.{chatbot_id}", "select": "id,session_id,creado_en", "order": "creado_en.desc"}
        response = requests.get(url, headers=_insforge_headers(), params=params)
        response.raise_for_status()
        conversations_data = response.json()

        result = []
        for conv in conversations_data:
            conv_id = conv["id"]
            # Obtener mensajes de esta conversación, ordenados por timestamp
            msg_url = f"{INS_FORGE_BASE_URL}/mensajes"
            msg_params = {"conversacion_id": f"eq.{conv_id}", "select": "rol,contenido,modelo_usado,timestamp", "order": "timestamp.asc"}
            msg_response = requests.get(msg_url, headers=_insforge_headers(), params=msg_params)
            msg_response.raise_for_status()
            messages_data = msg_response.json()

            # Formatear mensajes para el frontend
            messages = []
            for msg in messages_data:
                messages.append({
                    "rol": msg["rol"],
                    "contenido": msg["contenido"],
                    "modelo_usado": msg["modelo_usado"],
                    "timestamp": msg["timestamp"]
                })

            result.append({
                "id": conv_id,
                "session_id": conv["session_id"],
                "creado_en": conv["creado_en"],
                "mensajes": messages
            })

        return {"chatbot_id": chatbot_id, "conversaciones": result}
    except Exception as e:
        print(f"Error en get_conversations: {e}")
        return {"chatbot_id": chatbot_id, "conversaciones": [], "error": str(e)}