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
  userInfo.textContent = user.full_name;
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

// Product image mapping
const productImages = {
  1: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=400&fit=crop',
  2: 'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=400&fit=crop',
  3: 'https://images.unsplash.com/photo-1572804013427-4d7ca7268217?w=400&h=400&fit=crop',
  4: 'https://images.unsplash.com/photo-1542840410-3092f99611a3?w=400&h=400&fit=crop',
  5: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop',
  6: 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=400&fit=crop',
  7: 'https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?w=400&h=400&fit=crop',
  8: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop',
  9: 'https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=400&h=400&fit=crop',
  10: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=400&fit=crop',
  11: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&h=400&fit=crop',
  12: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400&h=400&fit=crop',
  13: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400&h=400&fit=crop',
  14: 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=400&h=400&fit=crop',
  15: 'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400&h=400&fit=crop',
  16: 'https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=400&h=400&fit=crop',
  17: 'https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=400&h=400&fit=crop',
  18: 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400&h=400&fit=crop',
  19: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop',
  20: 'https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=400&fit=crop'
};

// WebSocket connection
const ws = new WebSocket(`ws://${window.location.host}/ws`);
const chatbox = document.getElementById("chatbox");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

ws.onopen = () => {
  ws.send(JSON.stringify({ token }));
  console.log('WebSocket connected and authenticated');
};

ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    if (data.agent && data.message) {
      appendMessage("bot", data.message, data.agent, data.product_ids || []);
    } else {
      appendMessage("bot", event.data);
    }
  } catch (e) {
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
  if (e.key === "Enter") sendMessage();
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
  const imageUrl = productImages[product.id] || 'https://placehold.co/400x300?text=No+Image';
  const firstItem = product.items && product.items.length > 0 ? product.items[0] : null;
  const price = firstItem ? `₹${firstItem.price}` : 'Price varies';

  return `
    <div class="product-card bg-white rounded-2xl shadow-md overflow-hidden hover:shadow-2xl transition-all duration-300 cursor-pointer border border-gray-100">
      <div class="aspect-[4/3] overflow-hidden bg-gray-50 relative group">
        <img 
          src="${imageUrl}" 
          alt="${product.name}" 
          class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          loading="lazy"
          onerror="this.src='https://placehold.co/400x300?text=No+Image'"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
      </div>
      <div class="p-4">
        <h3 class="font-semibold text-gray-900 text-sm mb-1 line-clamp-1">${product.name}</h3>
        <p class="text-xs text-gray-500 mb-2 uppercase tracking-wide">${product.category || 'General'}</p>
        <div class="flex items-center justify-between">
          <p class="text-base font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">${price}</p>
          <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
          </svg>
        </div>
        <p class="text-xs text-gray-600 mt-2 line-clamp-2">${product.description || 'No description available.'}</p>
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
        <div class="bg-gradient-to-br from-purple-600 to-blue-600 p-4 rounded-2xl max-w-[80%] text-right shadow-lg">
          <p class="text-sm text-white">${text}</p>
        </div>
      </div>
    `;
  } else {
    div.classList.add("bot-message");
    const agentIcon = getAgentIcon(agent);
    const agentLabel = agent ? agent : "Assistant";
    
    let messageHtml = `
      <div class="flex gap-3">
        <div class="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center shadow-sm">
          ${agentIcon}
        </div>
        <div class="flex-1">
          <div class="bg-white p-4 rounded-2xl shadow-md border border-gray-100 max-w-[85%]">
            <p class="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">${agentLabel}</p>
            <p class="text-sm text-gray-800 leading-relaxed">${text.replace(/\n/g, '<br>')}</p>
          </div>
        </div>
      </div>
    `;
    
    if (productIds && productIds.length > 0) {
      const products = await loadProductDetails(productIds);
      if (products.length > 0) {
        const productCardsHtml = `
          <div class="ml-13 mt-3">
            <div class="product-grid">
              ${products.map(p => createProductCard(p)).join('')}
            </div>
          </div>
        `;
        messageHtml = messageHtml.replace('</div>', productCardsHtml + '</div>');
      }
    }
    
    div.innerHTML = messageHtml;
  }
  
  chatbox.appendChild(div);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function getAgentIcon(agent) {
  if (!agent) return '<svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>';
  
  const icons = {
    'Product Recommendation Agent': '<svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>',
    'Customer Support Agent': '<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>',
    'Order Processing Agent': '<svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path></svg>'
  };
  
  return icons[agent] || '<svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>';
}