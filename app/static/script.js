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

// Product image mapping (using placeholder images from Unsplash)
const productImages = {
  1: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop',  // Denim Jacket
  2: 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=400&fit=crop',  // Chinos
  3: 'https://images.unsplash.com/photo-1572804013427-4d7ca7268217?w=400&h=400&fit=crop',  // Summer Dress
  4: 'https://images.unsplash.com/photo-1542840410-3092f99611a3?w=400&h=400&fit=crop',  // Leather Boots
  5: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop',  // T-Shirt
  6: 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=400&fit=crop',  // Hoodie
  7: 'https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?w=400&h=400&fit=crop',  // Midi Skirt
  8: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop',  // Running Sneakers
  9: 'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=400&h=400&fit=crop',  // Scarf
  10: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=400&fit=crop', // Linen Shirt
  11: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop', // Knitted Sweater
  12: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400&h=400&fit=crop', // Formal Blazer
  13: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400&h=400&fit=crop', // Evening Gown
  14: 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&h=400&fit=crop', // Cargo Joggers
  15: 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop', // High Heels
  16: 'https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400&h=400&fit=crop', // Polo Shirt
  17: 'https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=400&h=400&fit=crop', // Wool Overcoat
  18: 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400&h=400&fit=crop', // Leggings
  19: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop', // Canvas Backpack
  20: 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=400&fit=crop'  // Wristwatch
};

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
  try {
    const data = JSON.parse(event.data);
    if (data.agent && data.message) {
      appendMessage("bot", data.message, data.agent, data.product_ids || []);
    } else {
      // Fallback for plain text messages
      appendMessage("bot", event.data);
    }
  } catch (e) {
    // Handle plain text messages
    appendMessage("bot", event.data);
  }
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

async function loadProductDetails(productIds) {
  const products = [];
  for (const id of productIds) {
    try {
      const response = await fetch(`/api/products/${id}`);
      if (response.ok) {
        const product = await response.json();
        products.push(product);
      }
    } catch (error) {
      console.error(`Error loading product ${id}:`, error);
    }
  }
  return products;
}

function createProductCard(product) {
  const imageUrl = productImages[product.id] || 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&h=400&fit=crop';
  
  // Get first item's price for display
  const firstItem = product.items && product.items.length > 0 ? product.items[0] : null;
  const price = firstItem ? `$${firstItem.price}` : 'Price varies';
  
  return `
    <div class="product-card bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer">
      <img src="${imageUrl}" alt="${product.name}" class="w-full h-48 object-cover" />
      <div class="p-4">
        <h3 class="font-semibold text-gray-800 text-sm mb-1">${product.name}</h3>
        <p class="text-xs text-gray-600 mb-2">${product.category}</p>
        <p class="text-sm font-bold text-blue-600">${price}</p>
        <p class="text-xs text-gray-500 mt-2 line-clamp-2">${product.description}</p>
      </div>
    </div>
  `;
}

async function appendMessage(sender, text, agent = null, productIds = []) {
  const div = document.createElement("div");
  div.classList.add("message-container", "mb-4");
  
  if (sender === "user") {
    div.classList.add("user-message");
    div.innerHTML = `
      <div class="flex justify-end">
        <div class="bg-blue-100 p-3 rounded-xl max-w-[80%] text-right">
          <p class="text-sm text-gray-800"><strong>You:</strong> ${text}</p>
        </div>
      </div>
    `;
  } else {
    div.classList.add("bot-message");
    const agentLabel = agent ? `🧠 ${agent}` : "Bot";
    
    let messageHtml = `
      <div class="bg-gray-100 p-3 rounded-xl max-w-[80%]">
        <p class="text-xs font-semibold text-gray-700 mb-1">${agentLabel}</p>
        <p class="text-sm text-gray-800">${text.replace(/\n/g, '<br>')}</p>
      </div>
    `;
    
    // Add product cards if product IDs are provided
    if (productIds && productIds.length > 0) {
      const products = await loadProductDetails(productIds);
      if (products.length > 0) {
        const productCardsHtml = `
          <div class="product-grid grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mt-3 max-w-full">
            ${products.map(p => createProductCard(p)).join('')}
          </div>
        `;
        messageHtml += productCardsHtml;
      }
    }
    
    div.innerHTML = messageHtml;
  }
  
  chatbox.appendChild(div);
  chatbox.scrollTop = chatbox.scrollHeight;
}