import os
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter()

# InsForge REST API configuration
INS_FORGE_BASE_URL = os.getenv("INS_FORGE_BASE_URL")
INS_FORGE_ANON_KEY = os.getenv("INS_FORGE_ANON_KEY")

def _insforge_headers():
    return {
        "Authorization": f"Bearer {INS_FORGE_ANON_KEY}",
        "Content-Type": "application/json"
    }

def get_chatbot_config(chatbot_id: str) -> dict:
    """
    Obtiene la configuración del chatbot desde la base de datos de InsForge.
    Regresa al menos el prompt de sistema, y opcionalmente el modelo preferido y la API key personalizada.
    """
    try:
        url = f"{INS_FORGE_BASE_URL}/chatbots"
        params = {"id": f"eq.{chatbot_id}", "select": "prompt_sistema,modelo_preferido,api_key"}
        response = requests.get(url, headers=_insforge_headers(), params=params)
        print(f"DEBUG InsForge response: status={response.status_code}, body={response.text}")
        response.raise_for_status()
        data = response.json()
        if data:
            record = data[0]
            return {
                "system_prompt": record.get("prompt_sistema", "Eres un asistente de atención al cliente, amable y breve."),
                "modelo_preferido": record.get("modelo_preferido"),
                "api_key": record.get("api_key")
            }
    except Exception as e:
        print(f"Error fetching chatbot config from InsForge: {e}")
        # Fallback to default configuration
        pass
    # Fallback configuration (original)
    return {
        "system_prompt": "Eres un asistente de atención al cliente, amable y breve."
    }

def get_or_create_conversation(chatbot_id: str, session_id: str) -> str:
    """
    Obtiene o crea una conversación para el chatbot_id y session_id dados.
    Regresa el ID de la conversación.
    """
    try:
        # Try to find existing conversation
        url = f"{INS_FORGE_BASE_URL}/conversaciones"
        params = {
            "chatbot_id": f"eq.{chatbot_id}",
            "session_id": f"eq.{session_id}",
            "select": "id"
        }
        response = requests.get(url, headers=_insforge_headers(), params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]["id"]
        # Create new conversation
        url = f"{INS_FORGE_BASE_URL}/conversaciones"
        payload = [{"chatbot_id": chatbot_id, "session_id": session_id}]
        response = requests.post(url, headers=_insforge_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]["id"]
    except Exception as e:
        print(f"Error getting/creating conversation in InsForge: {e}")
        # Print response text if available (for InsForge API error details)
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"InsForge response: {e.response.text}")
            except:
                print(f"InsForge response status: {e.response.status_code}")
        # Fallback: generate a temporary UUID-based ID (not persisted)
        import uuid
        return str(uuid.uuid4())
    # Fallback
    import uuid
    return str(uuid.uuid4())

def save_message(conversacion_id: str, rol: str, contenido: str, modelo_usado: str | None) -> None:
    """
    Guarda un mensaje en la tabla `mensajes`.
    """
    try:
        url = f"{INS_FORGE_BASE_URL}/mensajes"
        payload = [{
            "conversacion_id": conversacion_id,
            "rol": rol,
            "contenido": contenido,
            "modelo_usado": modelo_usado
        }]
        response = requests.post(url, headers=_insforge_headers(), json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error saving message to InsForge: {e}")
        # Print response text if available (for InsForge API error details)
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"InsForge response: {e.response.text}")
            except:
                print(f"InsForge response status: {e.response.status_code}")
        # In a production system, we might want to retry or handle this more gracefully
        pass

class ChatRequest(BaseModel):
    chatbot_id: str
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    model_used: str


# --- Proveedores de IA ---
# Los tres son compatibles con el formato de API de OpenAI, así que se pueden
# llamar con el mismo cliente cambiando solo base_url, api_key y model.

PROVIDERS = [
    {
        "name": "deepseek_nim",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-ai/deepseek-v4-flash-0731",
    },
    {
        "name": "nemotron_nim",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key_env": "NEMOTRON_API_KEY",
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
    },
    {
        "name": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model": "gemini-3.1-pro-preview",  # TODO: confirmar el nombre exacto vigente
    },
]


def call_with_fallback(messages: list, chatbot_config: dict | None = None) -> tuple[str, str]:
    """Intenta primero la configuración del chatbot (si tiene API key y modelo preferido),
    luego cae en la cadena fija de proveedores de la plataforma."""
    last_error = None

    # 1. Intentar con la API key y modelo propios del chatbot (si están disponibles)
    if chatbot_config and chatbot_config.get("api_key"):
        api_key = chatbot_config["api_key"]
        model = chatbot_config.get("modelo_preferido")
        if model:
            # DEBUG: imprimir el modelo del chatbot y la lista de modelos de PROVIDERS
            # Buscar un proveedor en la lista que use este modelo
            matching_provider = None
            for provider in PROVIDERS:
                if provider["model"] == model:
                    matching_provider = provider
                    break
            if matching_provider:
                try:
                    client = OpenAI(base_url=matching_provider["base_url"], api_key=api_key)
                    completion = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=512,
                    )
                    return completion.choices[0].message.content, matching_provider["name"]
                except Exception as e:
                    last_error = e
                    # Si falla, continuamos con el fallback de la plataforma
            # Si no se encuentra un proveedor con el modelo, seguimos con el fallback

    # 2. Fallback: intentar con los proveedores de la plataforma en orden
    for provider in PROVIDERS:
        api_key = os.getenv(provider["api_key_env"])
        if not api_key:
            continue  # proveedor sin key configurada, se salta

        try:
            client = OpenAI(base_url=provider["base_url"], api_key=api_key)
            completion = client.chat.completions.create(
                model=provider["model"],
                messages=messages,
                temperature=0.7,
                max_tokens=512,
            )
            reply = completion.choices[0].message.content
            return reply, provider["name"]
        except Exception as e:
            last_error = e
            continue  # pasa al siguiente proveedor de la cadena

    # Si todos fallan
    raise RuntimeError(f"Todos los proveedores fallaron. Último error: {last_error}")


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    config = get_chatbot_config(req.chatbot_id)
    conversation_id = get_or_create_conversation(req.chatbot_id, req.session_id)

    # Guardar mensaje del usuario
    save_message(conversation_id, "user", req.message, None)

    # Construir mensajes para la IA (solo system prompt y mensaje actual por ahora)
    # TODO: recuperar historial de la conversación para dar memoria real
    messages = [
        {"role": "system", "content": config["system_prompt"]},
        {"role": "user", "content": req.message}
    ]

    reply, model_used = call_with_fallback(messages, config)

    # Guardar respuesta del asistente
    save_message(conversation_id, "assistant", reply, model_used)

    return ChatResponse(reply=reply, model_used=model_used)