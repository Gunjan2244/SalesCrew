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

// Cart, Wishlist, and Product Display State
let cartItems = [];
let wishlistItems = [];
let allDisplayedProducts = [];
let currentDisplayProducts = null;
let currentMessageElement = null;

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
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
const chatbox = document.getElementById("chatbox");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const voiceBtn = document.getElementById("voiceBtn");
const voiceIcon = document.getElementById("voiceIcon");

// Voice recognition setup
let recognition = null;
let isRecording = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    isRecording = true;
    voiceBtn.classList.add('voice-recording', 'bg-red-500', 'border-red-500');
    voiceBtn.classList.remove('bg-white', 'border-gray-200');
    voiceIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>';
    input.placeholder = 'Listening...';
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    input.value = transcript;
  };

  recognition.onend = () => {
    isRecording = false;
    voiceBtn.classList.remove('voice-recording', 'bg-red-500', 'border-red-500');
    voiceBtn.classList.add('bg-white', 'border-gray-200');
    voiceIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>';
    input.placeholder = 'Type your message...';
  };

  recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    isRecording = false;
    voiceBtn.classList.remove('voice-recording', 'bg-red-500', 'border-red-500');
    voiceBtn.classList.add('bg-white', 'border-gray-200');
    input.placeholder = 'Type your message...';
  };
} else {
  voiceBtn.style.display = 'none';
}

if (voiceBtn) {
  voiceBtn.onclick = () => {
    if (!recognition) return;
    
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
    }
  };
}

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

function showProductDisplay(products, messageElement) {
  if (!products || products.length === 0) return;
  
  currentDisplayProducts = products;
  currentMessageElement = messageElement;
  
  // Add to all displayed products
  allDisplayedProducts.push(...products);
  updateProductStack();
  
  const displayLayer = document.getElementById('productDisplayLayer');
  const displayContent = document.getElementById('productDisplayContent');
  
  displayContent.innerHTML = `
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-2xl font-bold text-gray-900">Recommended Products</h3>
      <button onclick="closeProductDisplay()" class="p-2 hover:bg-white/20 rounded-lg transition">
        <svg class="w-6 h-6 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      ${products.map(p => createLargeProductCard(p)).join('')}
    </div>
  `;
  
  displayLayer.classList.remove('hidden');
  setTimeout(() => {
    displayLayer.classList.add('active');
  }, 10);
}

function closeProductDisplay() {
  const displayLayer = document.getElementById('productDisplayLayer');
  displayLayer.classList.remove('active');
  
  setTimeout(() => {
    displayLayer.classList.add('hidden');
    
    // Attach products to the message as small boxes
    if (currentMessageElement && currentDisplayProducts) {
      attachProductsToMessage(currentMessageElement, currentDisplayProducts);
    }
    
    currentDisplayProducts = null;
    currentMessageElement = null;
  }, 300);
}

function attachProductsToMessage(messageElement, products) {
  const compactContainer = document.createElement('div');
  compactContainer.className = 'mt-3 flex gap-2 overflow-x-auto pb-2';
  compactContainer.style.scrollbarWidth = 'thin';
  
  compactContainer.innerHTML = products.map(product => {
    const imageUrl = productImages[product.id] || 'https://placehold.co/100x100?text=No+Image';
    const firstItem = product.items && product.items.length > 0 ? product.items[0] : null;
    const price = firstItem ? `₹${firstItem.price}` : 'N/A';
    
    return `
      <div onclick='openProductModal(${JSON.stringify(product).replace(/'/g, "&apos;")})' 
           class="flex-shrink-0 w-32 bg-white rounded-lg border border-gray-200 overflow-hidden cursor-pointer hover:shadow-md transition">
        <img src="${imageUrl}" alt="${product.name}" class="w-full h-24 object-cover" />
        <div class="p-2">
          <p class="text-xs font-medium text-gray-900 line-clamp-1">${product.name}</p>
          <p class="text-xs font-bold text-gray-900 mt-1">${price}</p>
        </div>
      </div>
    `;
  }).join('');
  
  // Find the message bubble and append after it
  const messageBubble = messageElement.querySelector('.bot-message-bubble');
  if (messageBubble) {
    messageBubble.parentElement.appendChild(compactContainer);
  }
}

function createLargeProductCard(product) {
  const imageUrl = productImages[product.id] || 'https://placehold.co/500x700?text=No+Image';
  const firstItem = product.items && product.items.length > 0 ? product.items[0] : null;
  const price = firstItem ? `₹${firstItem.price}` : 'Price varies';

  return `
    <div class="product-card-display cursor-pointer" onclick='openProductModal(${JSON.stringify(product).replace(/'/g, "&apos;")})'>
      <div class="product-image-container">
        <img 
          src="${imageUrl}" 
          alt="${product.name}" 
          class="product-image"
          loading="lazy"
        />
        <div class="product-overlay">
          <div class="product-overlay-content">
            <span class="product-category">${product.category || 'General'}</span>
            <h3 class="product-name">${product.name}</h3>
            <p class="product-price">${price}</p>
            <div class="product-actions">
              <button onclick='event.stopPropagation(); addToCart(${JSON.stringify(product).replace(/'/g, "&apos;")})' 
                      class="action-btn action-btn-cart">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
                </svg>
                Add to Cart
              </button>
              <button onclick='event.stopPropagation(); addToWishlist(${JSON.stringify(product).replace(/'/g, "&apos;")})' 
                      class="action-btn action-btn-wishlist">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function updateProductStack() {
  const stackContainer = document.getElementById('productStack');
  const stackCount = document.getElementById('stackCount');
  
  if (!stackContainer) return;
  
  // Get unique products (last 5)
  const uniqueProducts = Array.from(new Map(allDisplayedProducts.map(p => [p.id, p])).values()).slice(-5);
  
  stackContainer.innerHTML = uniqueProducts.map((product, index) => {
    const imageUrl = productImages[product.id] || 'https://placehold.co/80x80?text=No+Image';
    return `
      <div class="stack-item" style="--stack-index: ${index}">
        <img src="${imageUrl}" alt="${product.name}" class="w-full h-full object-cover" />
      </div>
    `;
  }).join('');
  
  if (stackCount) {
    stackCount.textContent = allDisplayedProducts.length;
  }
  
  stackContainer.style.display = allDisplayedProducts.length > 0 ? 'block' : 'none';
}

function openProductStackView() {
  const modal = document.getElementById('productStackModal');
  const modalContent = document.getElementById('stackModalContent');
  
  // Get unique products
  const uniqueProducts = Array.from(new Map(allDisplayedProducts.map(p => [p.id, p])).values());
  
  modalContent.innerHTML = `
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-2xl font-bold text-gray-900">All Viewed Products (${uniqueProducts.length})</h3>
      <button onclick="closeProductStackView()" class="p-2 hover:bg-gray-100 rounded-lg transition">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[70vh] overflow-y-auto">
      ${uniqueProducts.map(p => createCompactProductCard(p)).join('')}
    </div>
  `;
  
  modal.classList.remove('hidden');
}

function closeProductStackView() {
  const modal = document.getElementById('productStackModal');
  modal.classList.add('hidden');
}

function createCompactProductCard(product) {
  const imageUrl = productImages[product.id] || 'https://placehold.co/200x200?text=No+Image';
  const firstItem = product.items && product.items.length > 0 ? product.items[0] : null;
  const price = firstItem ? `₹${firstItem.price}` : 'N/A';
  
  return `
    <div onclick='openProductModal(${JSON.stringify(product).replace(/'/g, "&apos;")})' 
         class="bg-white rounded-xl border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg transition">
      <img src="${imageUrl}" alt="${product.name}" class="w-full h-40 object-cover" />
      <div class="p-4">
        <h4 class="font-semibold text-gray-900 text-sm mb-1 line-clamp-1">${product.name}</h4>
        <p class="text-xs text-gray-500 mb-2">${product.category || 'General'}</p>
        <p class="text-lg font-bold text-gray-900">${price}</p>
      </div>
    </div>
  `;
}

function addToCart(product) {
  const existingItem = cartItems.find(item => item.id === product.id);
  if (!existingItem) {
    cartItems.push({ ...product, quantity: 1 });
    updateCartDisplay();
    showNotification('Added to cart!', 'success');
    
    ws.send(JSON.stringify({
      action: 'add_to_cart',
      product_id: product.id,
      product_name: product.name
    }));
  } else {
    existingItem.quantity++;
    updateCartDisplay();
    showNotification('Quantity updated!', 'success');
  }
}

function addToWishlist(product) {
  const existingItem = wishlistItems.find(item => item.id === product.id);
  if (!existingItem) {
    wishlistItems.push(product);
    updateWishlistDisplay();
    showNotification('Added to wishlist!', 'success');
  } else {
    showNotification('Already in wishlist!', 'info');
  }
}

function removeFromCart(productId) {
  cartItems = cartItems.filter(item => item.id !== productId);
  updateCartDisplay();
  showNotification('Removed from cart', 'info');
}

function removeFromWishlist(productId) {
  wishlistItems = wishlistItems.filter(item => item.id !== productId);
  updateWishlistDisplay();
  showNotification('Removed from wishlist', 'info');
}

function updateCartDisplay() {
  const cartBadge = document.getElementById('cartBadge');
  const cartCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);
  if (cartBadge) {
    cartBadge.textContent = cartCount;
    cartBadge.style.display = cartCount > 0 ? 'flex' : 'none';
  }
}

function updateWishlistDisplay() {
  const wishlistBadge = document.getElementById('wishlistBadge');
  if (wishlistBadge) {
    wishlistBadge.textContent = wishlistItems.length;
    wishlistBadge.style.display = wishlistItems.length > 0 ? 'flex' : 'none';
  }
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `fixed top-20 right-4 z-50 px-4 py-3 rounded-lg shadow-lg animate-slideIn ${
    type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
  } text-white text-sm font-medium`;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('animate-slideOut');
    setTimeout(() => notification.remove(), 300);
  }, 2000);
}

function openProductModal(product) {
  const modal = document.getElementById('productModal');
  const modalContent = document.getElementById('modalProductContent');
  const imageUrl = productImages[product.id] || 'https://placehold.co/600x600?text=No+Image';
  const firstItem = product.items && product.items.length > 0 ? product.items[0] : null;
  const price = firstItem ? `₹${firstItem.price}` : 'Price varies';
  
  modalContent.innerHTML = `
    <div class="relative">
      <button onclick="closeProductModal()" class="absolute top-4 right-4 z-10 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>
      
      <div class="grid md:grid-cols-2 gap-8">
        <div class="relative aspect-square overflow-hidden rounded-2xl bg-gray-100">
          <img src="${imageUrl}" alt="${product.name}" class="w-full h-full object-cover" />
        </div>
        
        <div class="flex flex-col">
          <div class="flex-1">
            <p class="text-sm text-gray-500 uppercase tracking-wide mb-2">${product.category || 'General'}</p>
            <h2 class="text-3xl font-bold text-gray-900 mb-4">${product.name}</h2>
            <p class="text-4xl font-bold text-gray-900 mb-6">${price}</p>
            <p class="text-gray-600 leading-relaxed mb-6">${product.description || 'No description available.'}</p>
            
            ${product.features ? `
              <div class="mb-6">
                <h3 class="font-semibold text-gray-900 mb-3">Features:</h3>
                <p class="text-gray-600 text-sm">${product.features}</p>
              </div>
            ` : ''}
          </div>
          
          <div class="flex gap-3 pt-6 border-t">
            <button onclick='addToCartFromModal(${JSON.stringify(product).replace(/'/g, "&apos;")})' 
                    class="flex-1 bg-gray-900 hover:bg-black text-white px-6 py-4 rounded-xl transition font-semibold flex items-center justify-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
              </svg>
              Add to Cart
            </button>
            <button onclick='addToWishlistFromModal(${JSON.stringify(product).replace(/'/g, "&apos;")})' 
                    class="bg-white border-2 border-gray-900 hover:bg-gray-50 text-gray-900 px-6 py-4 rounded-xl transition font-semibold flex items-center justify-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
              </svg>
              Wishlist
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeProductModal() {
  const modal = document.getElementById('productModal');
  modal.classList.add('hidden');
  document.body.style.overflow = 'auto';
}

function addToCartFromModal(product) {
  addToCart(product);
  closeProductModal();
}

function addToWishlistFromModal(product) {
  addToWishlist(product);
}

function toggleCart() {
  const cartPanel = document.getElementById('cartPanel');
  const wishlistPanel = document.getElementById('wishlistPanel');
  wishlistPanel.classList.add('translate-x-full');
  cartPanel.classList.toggle('translate-x-full');
  updateCartPanel();
}

function toggleWishlist() {
  const cartPanel = document.getElementById('cartPanel');
  const wishlistPanel = document.getElementById('wishlistPanel');
  cartPanel.classList.add('translate-x-full');
  wishlistPanel.classList.toggle('translate-x-full');
  updateWishlistPanel();
}

function updateCartPanel() {
  const cartItemsContainer = document.getElementById('cartItems');
  const cartTotal = document.getElementById('cartTotal');
  
  if (cartItems.length === 0) {
    cartItemsContainer.innerHTML = `
      <div class="text-center py-12">
        <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
        </svg>
        <p class="text-gray-500">Your cart is empty</p>
      </div>
    `;
    cartTotal.textContent = '₹0';
    return;
  }
  
  let total = 0;
  cartItemsContainer.innerHTML = cartItems.map(item => {
    const imageUrl = productImages[item.id] || 'https://placehold.co/80x80?text=No+Image';
    const firstItem = item.items && item.items.length > 0 ? item.items[0] : null;
    const price = firstItem ? firstItem.price : 0;
    const itemTotal = price * item.quantity;
    total += itemTotal;
    
    return `
      <div class="flex gap-4 p-4 bg-gray-50 rounded-xl">
        <img src="${imageUrl}" alt="${item.name}" class="w-20 h-20 object-cover rounded-lg" />
        <div class="flex-1">
          <h4 class="font-semibold text-gray-900 text-sm mb-1">${item.name}</h4>
          <p class="text-xs text-gray-500 mb-2">${item.category || 'General'}</p>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <button onclick="decreaseQuantity(${item.id})" class="w-6 h-6 flex items-center justify-center bg-white rounded border hover:bg-gray-100">-</button>
              <span class="text-sm font-medium">${item.quantity}</span>
              <button onclick="increaseQuantity(${item.id})" class="w-6 h-6 flex items-center justify-center bg-white rounded border hover:bg-gray-100">+</button>
            </div>
            <p class="text-sm font-bold">₹${itemTotal}</p>
          </div>
        </div>
        <button onclick="removeFromCart(${item.id})" class="text-gray-400 hover:text-red-500">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    `;
  }).join('');
  
  cartTotal.textContent = `₹${total}`;
}

function updateWishlistPanel() {
  const wishlistItemsContainer = document.getElementById('wishlistItems');
  
  if (wishlistItems.length === 0) {
    wishlistItemsContainer.innerHTML = `
      <div class="text-center py-12">
        <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
        </svg>
        <p class="text-gray-500">Your wishlist is empty</p>
      </div>
    `;
    return;
  }
  
  wishlistItemsContainer.innerHTML = wishlistItems.map(item => {
    const imageUrl = productImages[item.id] || 'https://placehold.co/80x80?text=No+Image';
    const firstItem = item.items && item.items.length > 0 ? item.items[0] : null;
    const price = firstItem ? `₹${firstItem.price}` : 'Price varies';
    
    return `
      <div class="flex gap-4 p-4 bg-gray-50 rounded-xl">
        <img src="${imageUrl}" alt="${item.name}" class="w-20 h-20 object-cover rounded-lg cursor-pointer" onclick='openProductModal(${JSON.stringify(item).replace(/'/g, "&apos;")})' />
        <div class="flex-1">
          <h4 class="font-semibold text-gray-900 text-sm mb-1">${item.name}</h4>
          <p class="text-xs text-gray-500 mb-2">${item.category || 'General'}</p>
          <p class="text-sm font-bold mb-2">${price}</p>
          <button onclick='moveToCart(${JSON.stringify(item).replace(/'/g, "&apos;")})' class="text-xs bg-gray-900 text-white px-3 py-1.5 rounded-lg hover:bg-black transition">
            Move to Cart
          </button>
        </div>
        <button onclick="removeFromWishlist(${item.id})" class="text-gray-400 hover:text-red-500">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    `;
  }).join('');
}

function increaseQuantity(productId) {
  const item = cartItems.find(item => item.id === productId);
  if (item) {
    item.quantity++;
    updateCartDisplay();
    updateCartPanel();
  }
}

function decreaseQuantity(productId) {
  const item = cartItems.find(item => item.id === productId);
  if (item && item.quantity > 1) {
    item.quantity--;
    updateCartDisplay();
    updateCartPanel();
  }
}

function moveToCart(product) {
  removeFromWishlist(product.id);
  addToCart(product);
  updateWishlistPanel();
}

async function appendMessage(sender, text, agent = null, productIds = []) {
  const div = document.createElement("div");
  div.classList.add("message-container", "mb-4");
  
  if (sender === "user") {
    div.classList.add("user-message");
    div.innerHTML = `
      <div class="flex justify-end">
        <div class="user-message-bubble p-4 rounded-2xl max-w-[85%] sm:max-w-[70%] text-right shadow-md">
          <p class="text-sm text-white">${text}</p>
        </div>
      </div>
    `;
  } else {
    div.classList.add("bot-message");
    const agentIcon = getAgentIcon(agent);
    const agentLabel = agent ? agent : "Assistant";
    
    div.innerHTML = `
      <div class="flex gap-2 sm:gap-3">
        <div class="flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 bg-gray-100 rounded-lg flex items-center justify-center">
          ${agentIcon}
        </div>
        <div class="flex-1">
          <div class="bot-message-bubble p-4 rounded-2xl shadow-sm max-w-[85%] sm:max-w-[90%]">
            <p class="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">${agentLabel}</p>
            <p class="text-sm text-gray-800 leading-relaxed">${text.replace(/\n/g, '<br>')}</p>
          </div>
        </div>
      </div>
    `;
    
    // Load and display products if available
    if (productIds && productIds.length > 0) {
      const products = await loadProductDetails(productIds);
      if (products.length > 0) {
        showProductDisplay(products, div);
      }
    }
  }
  
  chatbox.appendChild(div);
  chatbox.scrollTop = chatbox.scrollHeight;
}

function getAgentIcon(agent) {
  if (!agent) return '<svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>';
  
  const icons = {
    'Recommendation Agent': '<svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>',
    'Sales Specialist': '<svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
    'Shopping Cart Specialist': '<svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>',
    'Financial Transactions Expert': '<svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-900" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"></path></svg>'
  };
  
  return icons[agent] || '<svg class="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>';
}