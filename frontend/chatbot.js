(function () {
  // =====================================================
  // 1. TWORZENIE HTML WIDGETU (JEŚLI NIE ISTNIEJE)
  // =====================================================
  if (!document.getElementById("vet-chat-widget")) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
      <div id="vet-chat-widget">
        <button id="vet-chat-toggle">🐾</button>

        <div id="vet-chat-window" style="display:none;">
          <div class="header">Asystent Gabinetu Weterynaryjnego</div>

          <div id="vet-chat-messages"></div>

          <div class="input-area">
            <input
              type="text"
              id="vet-input"
              placeholder="W czym mogę pomóc?"
              autocomplete="off"
            />
            <button id="vet-send">Wyślij</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(wrapper);
  }

  // =====================================================
  // 2. REFERENCJE DO ELEMENTÓW
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
  // 4. OBSŁUGA WYSYŁANIA
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
      const response = await fetch("/chat", {
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
      const response = await fetch("/chat", {
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
  // 7. FUNKCJE POMOCNICZE (ZACHOWANE)
  // =====================================================
  function appendUser(text) {
    messages.innerHTML += `<div class="user">${escapeHtml(text)}</div>`;
    scrollDown();
  }

  function appendBot(text) {
    messages.innerHTML += `<div class="bot">${escapeHtml(text)}</div>`;
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
