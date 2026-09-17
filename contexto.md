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
3. **Panel de administración (Streamlit)** — donde el dueño del sitio configura su chatbot. Vive en una URL propia, protegida con login. Los visitantes del sitio del cliente nunca la ven.

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

Pendiente de confirmar si se incluyen 2 o 3 proveedores (ver nota abajo). Todos compatibles con el formato de API de OpenAI, por lo que el código de llamada es casi idéntico entre ellos:

1. `deepseek-ai/deepseek-v4-flash-0731` vía **NVIDIA NIM** — modelo principal, optimizado para velocidad (MoE con solo 13B parámetros activos).
2. **Groq** (`llama-3.3-70b-versatile` o similar) — respaldo de velocidad. *Nota: Groq (con "q") tiene tier gratis real y vigente en 2026 — no confundir con Grok (con "k") de xAI, que sí es de paga. Si se descartó por esta confusión, se puede reincorporar.*
3. `nvidia/nemotron-3-super-120b-a12b` vía NVIDIA NIM — respaldo adicional. **Se descontinúa el 2 de octubre de 2026** — reemplazar por la versión vigente de Nemotron cuando llegue esa fecha.
4. **Gemini** (la versión más capaz disponible, no la más rápida) — último recurso. Aquí ya no importa la velocidad, solo que no falle.

La lógica de fallback debe ir de más rápido a más lento, para que un fallo en el primer proveedor no te mande directo al más lento antes de intentar con uno rápido intermedio.

## 3. Panel de administración (Streamlit)

- Login simple, cada cliente ve solo sus propios chatbots.
- Formulario para: elegir modelo de IA, pegar su propia API key (o usar la de la plataforma por defecto), personalizar el prompt de sistema, ver historial de conversaciones y feedback.
- Al guardar cambios, escribe/actualiza el registro correspondiente en la base de datos.

## 4. Base de datos (Neon o Supabase)

Tablas mínimas para empezar:

- **`chatbots`**: `id`, `nombre`, `api_key` (encriptada), `modelo_preferido`, `prompt_sistema`, `dueño_id`, `creado_en`
- **`conversaciones`**: `id`, `chatbot_id`, `session_id`, `creado_en`
- **`mensajes`**: `id`, `conversacion_id`, `rol` (user/assistant), `contenido`, `modelo_usado`, `timestamp`
- **`feedback`**: `id`, `mensaje_id`, `calificacion`, `sugerencia_ia_auditora`, `aprobado` (booleano)

## 5. Seguridad

- Las API keys se guardan siempre encriptadas en la base de datos, nunca en texto plano.
- El widget de JS solo maneja el `chatbot_id` público, nunca una key real.
- CORS configurado para aceptar solicitudes solo desde los dominios registrados por cada chatbot (evita que alguien copie el snippet y lo use sin permiso) — se puede dejar para una segunda iteración si complica el desarrollo inicial.
- El archivo `.env` con las keys propias del backend (NVIDIA, Gemini, etc.) nunca se sube a git — debe estar en `.gitignore` desde el primer commit.

## Stack tecnológico (resumen)

| Pieza | Tecnología |
|---|---|
| Widget embebible | JavaScript vanilla |
| Backend | Python 3.x + FastAPI + Uvicorn |
| Panel de administración | Streamlit |
| Base de datos | Neon o Supabase (Postgres) |
| Proveedores de IA | NVIDIA NIM (DeepSeek V4 Flash, Nemotron), Groq, Gemini |
| Hosting del backend | Render o Vercel (a decidir) |

## Estructura de carpetas sugerida

```
proyecto/
├── widget/
│   └── widget.js
├── backend/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   │   ├── chat.py
│   │   └── admin.py
│   ├── db/
│   └── requirements.txt
├── admin_panel/
│   └── app.py          (Streamlit)
└── .env
```

## Próximos pasos (para ir marcando conforme se avance)

- [ ] Crear la estructura de carpetas base del proyecto.
- [ ] Backend: endpoint `/api/chat` funcional con un solo proveedor (DeepSeek vía NVIDIA NIM), sin fallback todavía.
- [ ] Backend: agregar la lógica de fallback a los demás proveedores.
- [ ] Widget: HTML/CSS/JS básico, hablando con el backend corriendo en local.
- [ ] Base de datos: definir el esquema real y conectar el backend a ella.
- [ ] Panel de Streamlit: formulario básico de configuración de un chatbot.
- [ ] Probar todo el flujo de punta a punta: configurar en Streamlit → pegar el widget en una página HTML de prueba → chatear → ver el log en la base de datos.

## Notas para Claude Code

- Este proyecto usa **Nemotron 3 / DeepSeek vía NVIDIA NIM** como modelo de asistencia de código (conectado a través de un proxy llamado Free Claude Code), no el modelo real de Anthropic. Ten esto en cuenta si el modelo alguna vez "alucina" ser otra cosa o inventa comandos que no existen — verificar siempre con `/help` dentro de la sesión.
- Prioriza avanzar en el orden de la lista de "Próximos pasos" de arriba, un punto a la vez, en vez de intentar construir todo de golpe.
- Cuando falte una decisión (por ejemplo, Neon vs Supabase, o si se incluye Groq en el fallback), pregunta en vez de asumir.
