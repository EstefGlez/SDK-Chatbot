# SDK-Chatbot: Chatbot IA Embebible para Sitios Web

Un plataforma que permite a dueños de sitios web agregar un chatbot de IA a sus sitios mediante un simple fragmento de JavaScript. El sistema incluye un backend API (FastAPI), un panel de administración (Streamlit) y un widget de JavaScript vanilla, todo diseñado para ser fácil de instalar, configurable sin programar y económico de operar.

## Arquitectura

El proyecto sigue una arquitectura de tres capas independientes:

1. **Widget de chat (JavaScript vanilla)**  
   Se ejecuta en el navegador del visitante. Sólo conoce un `chatbot_id` público y se comunica con el backend mediante llamadas HTTP.

2. **Backend API (Python + FastAPI)**  
   El cerebro del sistema: recibe mensajes, resuelve la configuración del chatbot, llama a proveedores de IA con fallback automático, y guarda logs en base de datos.

3. **Panel de administración (Streamlit)**  
   Interfaz donde el dueño del sitio configura su chatbot (elige modelo, API key, prompt de sistema, ve historial). Protegido con login y accesible en una URL separada.

### Seguridad

- El widget **nunca** expone API keys ni configuración sensible.
- Las API keys se almacenan encriptadas en la base de datos.
- CORS restringido a dominios autorizados (pendiente de implementar completamente).

## Tecnologías

| Componente          | Tecnología                                   |
|---------------------|----------------------------------------------|
| Widget embebible    | JavaScript vanilla (ES6)                     |
| Backend             | Python 3.9+, FastAPI, Uvicorn                |
| Panel de admin      | Streamlit                                    |
| Base de datos       | PostgreSQL (Neon o Supabase)                 |
| Proveedores de IA   | NVIDIA NIM (DeepSeek, Nemotron), Groq, Gemini|
| Despliegue backend  | Render (o similar)                           |
| Despliegue admin    | Streamlit Community Cloud (o similar)        |

## Estructura de archivos

```
SDK-Chatbot/
├── widget.js                 # Widget JavaScript para embed
├── test.html                 # Página de prueba para el widget
├── .env.example              # Ejemplo de variables de entorno
├── .gitignore
├── requirements.txt          # Dependencias del backend
├── contexto.md               # Detalles de arquitectura y planes
├── README.md                 # Este archivo
│
├── admin.py                  # Endpoints FastAPI para administración
├── app.py                    # Aplicación Streamlit (panel de admin)
├── chat.py                   # Endpoints FastAPI para chat
└── main.py                   # Punto de entrada del backend (uvicorn)
```

## Variables de entorno

Cree un archivo `.env` basado en `.env.example`:

```env
# InsForge (PostgreSQL) - usado para almacenar configuración y logs
INS_FORGE_BASE_URL=https://su-proyecto.supabase.co
INS_FORGE_ANON_KEY=su_anon_key_aqui

# Proveedores de IA (obtener claves de los respetivos servicios)
DEEPSEEK_API_KEY=su_clave_deepseek
NEMOTRON_API_KEY=su_clave_nemotron  # opcional
GEMINI_API_KEY=su_clave_gemini
# GROQ_API_KEY=su_clave_groq      # si se decide incluir Groq
```

## Instalación y ejecución local

### Prerrequisitos

- Python 3.9+
- pip
- Cuenta en un proveedor de PostgreSQL (Neon, Supabase, etc.)
- Claves de API para al menos un proveedor de IA (DeepSeek vía NVIDIA NIM recomendado para iniciar)

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/EstefGlez/SDK-Chatbot.git
   cd SDK-Chatbot
   ```

2. **Crear entorno virtual e instalar dependencias**
   ```bash
   python -m venv venv
   source venv/bin/activate  # en Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**
   Copie `.env.example` a `.env` y complete los valores.

4. **Ejecutar el backend**
   ```bash
   uvicorn main:app --reload
   ```
   El backend estará disponible en `http://localhost:8000`.

5. **Ejecutar el panel de administración (en otra terminal)**
   ```bash
   streamlit run app.py
   ```
   El panel estará disponible en `http://localhost:8501`.

6. **Probar el widget**
   Abra `test.html` en un navegador y verá el widget funcionando contra el backend local.

## Uso en producción

1. Despliegue el backend en un servicio como Render (usando `main:app`).
2. Despliegue el panel de administración en Streamlit Community Cloud o similar.
3. Hospede `widget.js` en un CDN o sirvalo desde su dominio.
4. En el sitio del cliente, inserte:
   ```html
   <script src="https://su-dominio.com/widget.js" data-chatbot-id="ID_DEL_CHATBOT"></script>
   ```
   donde `ID_DEL_CHATBOT` es el UUID generado en el panel de administración al crear un chatbot.

## Próximos pasos

- [ ] Implementar encriptación de API keys en la base de datos.
- [ ] Añadir restricciones de CORS por dominio registrado.
- [ ] Integrar Groq como proveedor de respaldo.
- [ ] Mejorar el widget con temas personalizables y animaciones.
- [ ] Añadir métricas y dashboard de uso en el panel de admin.
- [ ] Soportar múltiples sesiones por usuario y memoria de conversación a largo plazo.

## Licencia

Este proyecto está bajo la licencia MIT - vea el archivo `LICENSE` para más detalles.

## Créditos

Desarrollado por Estefano González usando Claude y Claude Code como herramientas de asistencia.