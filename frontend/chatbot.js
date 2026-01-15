const toggle = document.getElementById("vet-chat-toggle");
const windowChat = document.getElementById("vet-chat-window");
const sendBtn = document.getElementById("vet-send");
const input = document.getElementById("vet-input");
const messages = document.getElementById("vet-chat-messages");

toggle.addEventListener("click", () => {
  windowChat.style.display =
    windowChat.style.display === "block" ? "none" : "block";
});

sendBtn.addEventListener("click", sendMessage);

input.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;

  messages.innerHTML += `<div class="user">${text}</div>`;
  input.value = "";
  messages.scrollTop = messages.scrollHeight;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await response.json();
    messages.innerHTML += `<div class="bot">${data.reply}</div>`;
    messages.scrollTop = messages.scrollHeight;

  } catch (error) {
    messages.innerHTML += `
      <div class="bot">
        W tej chwili nie mogę się połączyć.
        Proszę spróbować ponownie później lub skontaktować się z gabinetem.
      </div>`;
  }
}
