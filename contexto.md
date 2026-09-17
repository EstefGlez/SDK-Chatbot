# Contexto del Proyecto: SDK de Chatbot IA Embebible para Sitios Web

## Objetivo (Fase 1)

Construir una plataforma que permita a cualquier dueño de sitio web agregar un chatbot de IA a su sitio, insertando un pequeño fragmento de JavaScript. El sistema debe ser:

- Fácil de instalar (pegar un `<script>` y listo, sin tocar el resto del sitio)
- Configurable sin programar (elegir modelo de IA, personalizar el comportamiento del bot)
- Económico de operar (proveedores de IA gratuitos/baratos, con fallback automático si uno falla)

**Fases futuras (no implementar todavía, solo tenerlas en mente):** chatbots para WhatsApp, Instagram, agentes más complejos para ecommerce, fine-tuning de un modelo propio.

## Arquitectura general: 3 capas independientes

1. **Widget de chat (JavaScript vanilla)** — corre en el navegador del visitante, dentro del sitio web del cliente. No sabe nada de configuración ni de IA.
2. **Backend API (Python + FastAPI)** — el cerebro del sistema: recibe mensajes, llama a los proveedores de IA con fallback, guarda todo en base de datos.
3. **Panel de administración (Streamlit)** — donde el dueño del sitio configura su chatbot. Vive en una URL propia, sin autenticación por decisión de diseño. Los visitantes del sitio del cliente nunca la ven.

### Regla de oro (seguridad)

El widget de JavaScript **jamás** debe contener API keys, nombres de modelos, ni configuración sensible. Solo conoce un `chatbot_id` público que manda con cada mensaje. El backend resuelve ese ID contra la base de datos para saber qué API key y modelo usar. Las dos capas (widget JS y panel Streamlit) nunca se comunican directamente entre sí — ambas hablan por separado con el mismo backend.

## 1. Widget de JavaScript

- Un solo archivo `widget.js`, sin dependencias pesadas.
- Se incrusta así en el sitio del cliente:
  ```html
  <script src="https://tudominio.com/widget.js" data-chatbot-id="ID_UNICO"></script>
  ```
- Responsabilidades:
  - Dibujar una burbuja de chat flotante (HTML/CSS inyectado dinámicamente por el propio script).
  - Mandar `POST` a `/api/chat` con `{ chatbot_id, message, session_id }`.
  - Mostrar la respuesta que regresa el backend.
  - Guardar `session_id` en `localStorage` del navegador para dar memoria de conversación corta.
- **No debe incluir:** API keys, nombres de modelos, lógica de fallback, ni nada de configuración del backend.

## 2. Backend (Python + FastAPI)

### Endpoints principales

- `POST /api/chat` — recibe el mensaje del widget, resuelve la configuración del `chatbot_id`, llama al proveedor de IA (con fallback si falla), guarda el log de la conversación, y regresa la respuesta.
- `POST /api/admin/chatbots` — crea o edita la configuración de un chatbot (usado por el panel de Streamlit).
- `GET /api/admin/chatbots/{id}/conversations` — devuelve el historial de conversaciones (para mostrarlo en el panel).

### Cadena de fallback de proveedores de IA

La cadena de fallback es la siguiente (de más rápido a más lento):

1. `deepseek-ai/deepseek-v4-flash-0731` vía **NVIDIA NIM** — modelo principal, optimizado para velocidad (MoE con solo 13B parámetros activos).
2. `nvidia/nemotron-3-ultra-550b-a55b` vía NVIDIA NIM — respaldo de velocidad.
3. `gemini-3.1-pro-preview` — último recurso. Aquí ya no importa la velocidad, solo que no falle.

La lógica de fallback debe ir de más rápido a más lento, para que un fallo en el primer proveedor no te mande directo al más lento antes de intentar con uno rápido intermedio.

### Fallback personalizado por chatbot

Si un chatbot tiene su propia `api_key` y `modelo_preferido` guardados en la base de datos, el backend los usa como **primera opción** antes de caer en la cadena de fallback de la plataforma descrita arriba. Esto permite a los dueños de sitios usar sus propias claves y modelos si lo desean.

## 3. Panel de administración (Streamlit)

- Interfaz donde el dueño del sitio configura su chatbot: elegir modelo de IA, pegar su propia API key (o usar la de la plataforma por defecto), personalizar el prompt de sistema, ver historial de conversaciones y feedback.
- Al guardar cambios, escribe/actualiza el registro correspondiente en la base de datos.
- **No hay autenticación** por decisión de diseño; cada cliente ve solo sus propios chatbots porque el filtrado se hace por `chatbot_id` asociado al usuario que lo crea (en un entorno real, se añadiría login).

## 4. Base de datos (InsForge)

Usamos **InsForge** como backend as a service, que proporciona una base de datos PostgreSQL gestionada.

Tablas mínimas para empezar:

- **`chatbots`**: `id`, `nombre`, `api_key` (encriptada), `modelo_preferido`, `prompt_sistema`, `dueño_id`, `creado_en`
- **`conversaciones`**: `id`, `chatbot_id`, `session_id`, `creado_en`
- **`mensajes`**: `id`, `conversacion_id`, `rol` (user/assistant), `contenido`, `modelo_usado`, `timestamp`
- **`feedback`**: `id`, `mensaje_id`, `calificacion`, `sugerencia_ia_auditora`, `aprobado` (booleano)

### Seguridad

Las API keys se guardan en texto plano por ahora (encriptación pendiente, ver Próximos pasos).

## 5. Stack tecnológico (resumen)

| Pieza | Tecnología |
|---|---|
| Widget embebible | JavaScript vanilla |
| Backend | Python 3.x + FastAPI + Uvicorn |
| Panel de administración | Streamlit |
| Base de datos | InsForge (PostgreSQL) |
| Proveedores de IA | NVIDIA NIM (DeepSeek V4 Flash, Nemotron 3 Ultra), Gemini 3.1 Pro Preview |
| Hosting del backend | Render u otro servicio compatible (sugerencia) |
| Hosting del admin | Streamlit Community Cloud u otro (sugerencia) |

## Estructura de carpetas real

Todos los archivos están directamente en la raíz del proyecto:

```
SDK-Chatbot/
├── widget.js
├── test.html
├── .env.example
├── .gitignore
├── README.md
├── contexto.md
├── requirements.txt
├── main.py
├── chat.py
├── admin.py
├── app.py
```

## Próximos pasos

- [x] Crear la estructura de carpetas base del proyecto.
- [x] Backend: endpoint `/api/chat` funcional con un solo proveedor (DeepSeek vía NVIDIA NIM), sin fallback todavía.
- [x] Backend: agregar la lógica de fallback a los demás proveedores (Nemotron, Gemini) y fallback personalizado por chatbot.
- [x] Widget: HTML/CSS/JS básico, hablando con el backend corriendo en local.
- [x] Base de datos: definir el esquema real y conectar el backend a InsForge.
- [x] Panel de Streamlit: formulario básico de configuración de un chatbot (sin login).
- [ ] Probar todo el flujo de punta a punta: configurar en Streamlit → pegar el widget en una página HTML de prueba → chatear → ver el log en la base de datos.

## Notas para Claude Code

- Este proyecto usa **Nemotron 3 Ultra / DeepSeek V4 Flash vía NVIDIA NIM** como modelo de asistencia de código (conectado a través de un proxy llamado Free Claude Code), no el modelo real de Anthropic. Ten esto en cuenta si el modelo alguna vez "alucina" ser otra cosa o inventa comandos que no existen — verificar siempre con `/help` dentro de la sesión.
- Prioriza avanzar en el orden de la lista de "Próximos pasos" de arriba, un punto a la vez, en vez de intentar construir todo de golpe.
- Cuando falte una decisión (por ejemplo, si se incluye Groq en el fallback — actualmente no), pregunta en vez de asumir.

## Repositorio en GitHub

El código fuente ya está disponible en:  
https://github.com/EstefGlez/SDK-Chatbot