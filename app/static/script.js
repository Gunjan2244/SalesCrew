// Check if user is authenticated
const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token) {
  window.location.href = '/login';
}

// Display user info
const userInfo = document.getElementById('userInfo');
const logoutBtn = document.getElementById('logoutBtn');

if (userInfo && user.full_name) {
  userInfo.textContent = `Welcome, ${user.full_name}`;
}

// Logout handler
if (logoutBtn) {
  logoutBtn.onclick = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  };
}

// WebSocket connection with authentication
const ws = new WebSocket(`ws://${window.location.host}/ws`);
const chatbox = document.getElementById("chatbox");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

ws.onopen = () => {
  // Send authentication token as first message
  ws.send(JSON.stringify({ token }));
  console.log('WebSocket connected and authenticated');
};

ws.onmessage = (event) => {
  appendMessage("bot", event.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  appendMessage("bot", "⚠️ Connection error. Please refresh the page.");
};

ws.onclose = () => {
  appendMessage("bot", "Connection closed. Please refresh to reconnect.");
};

sendBtn.onclick = sendMessage;
input.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    sendMessage();
  }
});

function sendMessage() {
  const msg = input.value.trim();
  if (!msg) return;
  
  appendMessage("user", msg);
  ws.send(msg);
  input.value = "";
}

function appendMessage(sender, text) {
  const div = document.createElement("div");
  div.classList.add("p-3", "rounded-xl", "max-w-[80%]", "mb-2");
  
  if (sender === "user") {
    div.classList.add("bg-blue-100", "self-end", "ml-auto", "text-right");
    div.textContent = `You: ${text}`;
  } else {
    div.classList.add("bg-gray-100");
    div.innerHTML = text.replace(/\n/g, '<br>');
  }
  
  chatbox.appendChild(div);
  chatbox.scrollTop = chatbox.scrollHeight;
}