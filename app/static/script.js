const ws = new WebSocket(`ws://${window.location.host}/ws`);
const chatbox = document.getElementById("chatbox");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

ws.onmessage = (event) => appendMessage("bot", event.data);

sendBtn.onclick = sendMessage;
input.addEventListener("keypress", (e) => e.key === "Enter" && sendMessage());

function sendMessage() {
  const msg = input.value.trim();
  if (!msg) return;
  appendMessage("user", msg);
  ws.send(msg);
  input.value = "";
}

function appendMessage(sender, text) {
  const div = document.createElement("div");
  div.classList.add("p-2", "rounded-xl", "max-w-[80%]");
  if (sender === "user") {
    div.classList.add("bg-blue-100", "self-end", "ml-auto");
    div.textContent = `You: ${text}`;
  } else {
    div.classList.add("bg-gray-100");
    div.textContent = text;
  }
  chatbox.appendChild(div);
  chatbox.scrollTop = chatbox.scrollHeight;
}
