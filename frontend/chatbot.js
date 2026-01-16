(function () {
  // =====================================================
  // 0. KONFIGURACJA
  // =====================================================
  const API_BASE = "https://vet-assistant-chatbot.onrender.com";

  // =====================================================
  // 1. TWORZENIE HTML WIDGETU (JEŚLI NIE ISTNIEJE)
  // =====================================================
  if (!document.getElementById("vet-chat-widget")) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
      <div id="vet-chat-widget" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 99999;
      ">
        <button
          id="vet-chat-toggle"
          style="
            width: 56px;
            height: 56px;
            border-radius: 50%;
            border: none;
            background: #2e7d32;
            color: #fff;
            font-size: 26px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
            padding: 0;
          "
        >🐾</button>

        <div id="vet-chat-window" style="
          display:none;
          width: 340px;
          margin-top: 10px;
          background: #ffffff;
          border-radius: 12px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.25);
          overflow: hidden;
          font-family: Arial, sans-serif;
        ">
          <div class="header" style="
            background: #2e7d32;
            color: white;
            padding: 12px;
            font-weight: bold;
          ">
            Asystent Gabinetu Weterynaryjnego
          </div>

          <div id="vet-chat-messages" style="
            height: 260px;
            padding: 10px;
            overflow-y: auto;
            font-size: 14px;
          "></div>

          <div class="input-area" style="
            display: flex;
            border-top: 1px solid #ddd;
          ">
            <input
              type="text"
              id="vet-input"
              placeholder="W czym mogę pomóc?"
              autocomplete="off"
              style="
                flex: 1;
                border: none;
                padding: 10px;
                outline: none;
              "
            />
            <button
              id="vet-send"
              style="
                border: none;
                background: #2e7d32;
                color: white;
                padding: 10px 14px;
                cursor: pointer;
              "
            >Wyślij</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(wrapper);
  }

  // =====================================================
  // 2. REFERENCJE
  // =====================================================
  const toggle = document.getElementById("vet-chat-toggle");
  const windowChat = document.getElementById("vet-chat-window");
  const sendBtn = document.getElementById("vet-send");
  const input = document.getElementById("vet-input");
  const messages = document.getElementById("vet-chat-messages");

  let conversationStarted = false;
  let isSending = false;

  // =====================================================
  // 3. TOGGLE OKNA
  // =====================================================
  toggle.addEventListener("click", () => {
    const isOpen = windowChat.style.display === "block";
    windowChat.style.display = isOpen ? "none" : "block";

    if (!conversationStarted && !isOpen) {
      conversationStarted = true;
      startConversation();
    }
  });

  // =====================================================
  // 4. WYSYŁANIE
  // =====================================================
  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  // =====================================================
  // 5. START ROZMOWY
  // =====================================================
  async function startConversation() {
    appendBot("…");

    try {
      const response = await fetch(API_BASE + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "__start__" })
      });

      const data = await response.json();
      replaceLastBot(data.reply);

    } catch (error) {
      replaceLastBot(
        "Nie mogę teraz rozpocząć rozmowy. Spróbuj ponownie za chwilę."
      );
    }
  }

  // =====================================================
  // 6. WYSŁANIE WIADOMOŚCI
  // =====================================================
  async function sendMessage() {
    if (isSending) return;

    const text = input.value.trim();
    if (!text) return;

    isSending = true;
    input.value = "";

    appendUser(text);
    appendBot("…");

    try {
      const response = await fetch(API_BASE + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      const data = await response.json();
      replaceLastBot(data.reply);

    } catch (error) {
      replaceLastBot(
        "W tej chwili nie mogę się połączyć. Spróbuj ponownie później lub skontaktuj się z gabinetem."
      );
    } finally {
      isSending = false;
    }
  }

  // =====================================================
  // 7. POMOCNICZE
  // =====================================================
  function appendUser(text) {
    messages.innerHTML += `<div class="user" style="
      background:#e3f2fd;
      padding:8px;
      border-radius:8px;
      margin-bottom:6px;
      text-align:right;
    ">${escapeHtml(text)}</div>`;
    scrollDown();
  }

  function appendBot(text) {
    messages.innerHTML += `<div class="bot" style="
      background:#f2f2f2;
      padding:8px;
      border-radius:8px;
      margin-bottom:6px;
    ">${escapeHtml(text)}</div>`;
    scrollDown();
  }

  function replaceLastBot(text) {
    const botMessages = messages.querySelectorAll(".bot");
    if (botMessages.length > 0) {
      botMessages[botMessages.length - 1].innerHTML = escapeHtml(text);
    }
    scrollDown();
  }

  function scrollDown() {
    messages.scrollTop = messages.scrollHeight;
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
})();
