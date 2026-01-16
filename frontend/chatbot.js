(function () {
  // =====================================================
  // 0. KONFIGURACJA
  // =====================================================
  const API_BASE = "https://vet-assistant-chatbot.onrender.com";

  // =====================================================
  // 1. TWORZENIE HTML (POZYCJONOWANIE FIXED)
  // =====================================================
  if (!document.getElementById("vet-chat-toggle")) {
    document.body.insertAdjacentHTML(
      "beforeend",
      `
      <!-- TOGGLE -->
      <button
        id="vet-chat-toggle"
        style="
          position: fixed;
          bottom: 20px;
          right: 20px;
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
          z-index: 100000;
        "
      >🐾</button>

      <!-- OKNO CZATU -->
      <div
        id="vet-chat-window"
        style="
          position: fixed;
          bottom: 90px;
          right: 20px;
          width: 340px;
          background: #ffffff;
          border-radius: 12px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.25);
          overflow: hidden;
          font-family: Arial, sans-serif;
          display: none;
          z-index: 99999;
        "
      >
        <div style="
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

        <div style="
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
    `
    );
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
  // 3. TOGGLE (OTWÓRZ / ZAMKNIJ)
  // =====================================================
  toggle.addEventListener("click", () => {
    const isOpen = windowChat.style.display === "block";

    if (isOpen) {
      windowChat.style.display = "none";
    } else {
      windowChat.style.display = "block";

      if (!conversationStarted) {
        conversationStarted = true;
        startConversation();
      }
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
    } catch {
      replaceLastBot("Nie mogę teraz rozpocząć rozmowy.");
    }
  }

  // =====================================================
  // 6. WYSYŁANIE WIADOMOŚCI
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
    } catch {
      replaceLastBot("Problem z połączeniem.");
    } finally {
      isSending = false;
    }
  }

  // =====================================================
  // 7. UI
  // =====================================================
  function appendUser(text) {
    messages.innerHTML += `<div style="
      background:#e3f2fd;
      padding:8px;
      border-radius:8px;
      margin-bottom:6px;
      text-align:right;
    ">${escapeHtml(text)}</div>`;
    scrollDown();
  }

  function appendBot(text) {
    messages.innerHTML += `<div style="
      background:#f2f2f2;
      padding:8px;
      border-radius:8px;
      margin-bottom:6px;
    ">${escapeHtml(text)}</div>`;
    scrollDown();
  }

  function replaceLastBot(text) {
    const bots = messages.querySelectorAll("div");
    bots[bots.length - 1].innerHTML = escapeHtml(text);
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
