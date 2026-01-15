const toggle = document.getElementById("vet-chat-toggle");
const windowChat = document.getElementById("vet-chat-window");
const sendBtn = document.getElementById("vet-send");
const input = document.getElementById("vet-input");
const messages = document.getElementById("vet-chat-messages");

let conversationStarted = false;
let isSending = false;

// ====== TOGGLE OKNA ======
toggle.addEventListener("click", () => {
  const isOpen = windowChat.style.display === "block";
  windowChat.style.display = isOpen ? "none" : "block";

  if (!conversationStarted && !isOpen) {
    conversationStarted = true;
    startConversation();
  }
});

// ====== WYSYŁANIE ======
sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

// ====== START ROZMOWY ======
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

// ====== WYSŁANIE WIADOMOŚCI ======
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

// ====== POMOCNICZE ======
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
