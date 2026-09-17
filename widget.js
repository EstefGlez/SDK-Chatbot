/**
 * Widget de chat embebible.
 * Uso en cualquier sitio web:
 * <script src="https://tudominio.com/widget.js"
 *         data-chatbot-id="ID_UNICO"
 *         data-api-url="https://tudominio.com"></script>
 *
 * REGLA DE ORO: este archivo nunca debe contener API keys ni nombres de
 * modelos de IA. Solo conoce el chatbot_id público.
 */
(function () {
  // Lee la configuración desde el propio <script> que cargó este archivo
  const scriptTag = document.currentScript;
  const chatbotId = scriptTag.getAttribute("data-chatbot-id");
  const apiUrl = scriptTag.getAttribute("data-api-url") || new URL(scriptTag.src).origin;

  if (!chatbotId) {
    console.error("[chat-widget] Falta data-chatbot-id en el <script>.");
    return;
  }

  // Sesión persistente simple (memoria de conversación corta)
  const SESSION_KEY = "chat_widget_session_" + chatbotId;
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, sessionId);
  }

  // --- Estilos mínimos, inyectados dinámicamente ---
  const style = document.createElement("style");
  style.textContent = `
    #cw-bubble { position: fixed; bottom: 20px; right: 20px; width: 56px; height: 56px;
      border-radius: 50%; background: #2563eb; color: white; display: flex;
      align-items: center; justify-content: center; cursor: pointer; z-index: 999999;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2); font-size: 24px; }
    #cw-window { position: fixed; bottom: 88px; right: 20px; width: 320px; height: 420px;
      background: white; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.25);
      display: none; flex-direction: column; z-index: 999999; overflow: hidden;
      font-family: system-ui, sans-serif; }
    #cw-window.open { display: flex; }
    #cw-header { background: #2563eb; color: white; padding: 12px; font-weight: 600; }
    #cw-messages { flex: 1; padding: 12px; overflow-y: auto; font-size: 14px; }
    #cw-msg { margin-bottom: 8px; padding: 8px 12px; border-radius: 8px; max-width: 80%; }
    .cw-user { background: #2563eb; color: white; margin-left: auto; }
    .cw-bot { background: #f1f5f9; color: #1e293b; }
    #cw-inputRow { display: flex; border-top: 1px solid #e2e8f0; }
    #cw-input { flex: 1; border: none; padding: 10px; font-size: 14px; outline: none; }
    #cw-send { border: none; background: #2563eb; color: white; padding: 0 16px; cursor: pointer; }
  `;
  document.head.appendChild(style);

  // --- Estructura HTML del widget ---
  const bubble = document.createElement("div");
  bubble.id = "cw-bubble";
  bubble.textContent = "💬";

  const chatWindow = document.createElement("div");
  chatWindow.id = "cw-window";
  chatWindow.innerHTML = `
    <div id="cw-header">Chat</div>
    <div id="cw-messages"></div>
    <div id="cw-inputRow">
      <input id="cw-input" type="text" placeholder="Escribe un mensaje..." />
      <button id="cw-send">Enviar</button>
    </div>
  `;

  document.body.appendChild(bubble);
  document.body.appendChild(chatWindow);

  bubble.addEventListener("click", () => chatWindow.classList.toggle("open"));

  const messagesEl = chatWindow.querySelector("#cw-messages");
  const inputEl = chatWindow.querySelector("#cw-input");
  const sendBtn = chatWindow.querySelector("#cw-send");

  function appendMessage(text, role) {
    const div = document.createElement("div");
    div.id = "cw-msg";
    div.className = role === "user" ? "cw-user" : "cw-bot";
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;
    appendMessage(text, "user");
    inputEl.value = "";

    try {
      const res = await fetch(apiUrl + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chatbot_id: chatbotId, message: text, session_id: sessionId }),
      });
      const data = await res.json();
      appendMessage(data.reply || "(sin respuesta)", "bot");
    } catch (err) {
      appendMessage("Hubo un error de conexión. Intenta de nuevo.", "bot");
      console.error("[chat-widget]", err);
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();
