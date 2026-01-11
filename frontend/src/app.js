
const API_BASE_URL = '/api';

// Navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Remove active class from all links and pages
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        // Add active class to clicked link
        e.target.classList.add('active');
        
        // Show corresponding page
        const pageId = e.target.getAttribute('data-page');
        document.getElementById(pageId).classList.add('active');
        
        // Load inventory if inventory page is selected
        if (pageId === 'inventory') {
            loadInventory();
        }
    });
});

// Load products on page load
window.addEventListener('DOMContentLoaded', () => {
    loadProducts();
});

// Load products for dropdown
async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE_URL}/products`);
        if (!response.ok) throw new Error('Failed to load products');
        
        const products = await response.json();
        const select = document.getElementById('productSelect');
        
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} - $${product.price}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading products:', error);
        showMessage('orderMessage', 'Error loading products. Using mock data.', 'error');
        
        // Mock data fallback
        const mockProducts = [
            { id: 1, name: 'Laptop', price: 999 },
            { id: 2, name: 'Mouse', price: 29 },
            { id: 3, name: 'Keyboard', price: 79 },
            { id: 4, name: 'Monitor', price: 299 },
            { id: 5, name: 'Headphones', price: 149 }
        ];
        
        const select = document.getElementById('productSelect');
        mockProducts.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = `${product.name} - $${product.price}`;
            select.appendChild(option);
        });
    }
}

// Place Order Form Submit
document.getElementById('orderForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const orderData = {
        customerName: document.getElementById('customerName').value,
        customerEmail: document.getElementById('customerEmail').value,
        productId: parseInt(document.getElementById('productSelect').value),
        quantity: parseInt(document.getElementById('quantity').value)
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        if (!response.ok) throw new Error('Failed to place order');
        
        const result = await response.json();
        showMessage('orderMessage', `Order placed successfully! Order ID: ${result.orderId || result.id}`, 'success');
        document.getElementById('orderForm').reset();
        
    } catch (error) {
        console.error('Error placing order:', error);
        showMessage('orderMessage', 'Error placing order. Please try again.', 'error');
    }
});

// Track Order Button
document.getElementById('trackBtn').addEventListener('click', async () => {
    const orderId = document.getElementById('orderIdInput').value.trim();
    
    if (!orderId) {
        showMessage('trackMessage', 'Please enter an order ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${orderId}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Order not found');
            }
            throw new Error('Failed to fetch order');
        }
        
        const order = await response.json();
        displayOrderDetails(order);
        document.getElementById('trackMessage').style.display = 'none';
        
    } catch (error) {
        console.error('Error tracking order:', error);
        showMessage('trackMessage', error.message || 'Error tracking order. Please check the order ID.', 'error');
        document.getElementById('orderDetails').style.display = 'none';
    }
});

// Display Order Details
function displayOrderDetails(order) {
    document.getElementById('detailOrderId').textContent = order.id || order.orderId;
    document.getElementById('detailCustomer').textContent = order.customerName;
    document.getElementById('detailEmail').textContent = order.customerEmail;
    document.getElementById('detailProduct').textContent = order.productName || 'Product #' + order.productId;
    document.getElementById('detailQuantity').textContent = order.quantity;
    
    const statusBadge = document.getElementById('detailStatus');
    statusBadge.textContent = order.status || 'Pending';
    statusBadge.className = 'detail-value status-badge ' + (order.status || 'pending').toLowerCase();
    
    const createdDate = order.createdAt ? new Date(order.createdAt).toLocaleString() : new Date().toLocaleString();
    document.getElementById('detailCreated').textContent = createdDate;
    
    document.getElementById('orderDetails').style.display = 'block';
}

// Load Inventory
async function loadInventory() {
    try {
        const response = await fetch(`${API_BASE_URL}/inventory`);
        if (!response.ok) throw new Error('Failed to load inventory');
        
        const inventory = await response.json();
        displayInventory(inventory);
        
    } catch (error) {
        console.error('Error loading inventory:', error);
        showMessage('inventoryMessage', 'Error loading inventory. Showing mock data.', 'error');
        
        // Mock data fallback
        const mockInventory = [
            { id: 1, productName: 'Laptop', quantity: 45, price: 999 },
            { id: 2, productName: 'Mouse', quantity: 150, price: 29 },
            { id: 3, productName: 'Keyboard', quantity: 8, price: 79 },
            { id: 4, productName: 'Monitor', quantity: 30, price: 299 },
            { id: 5, productName: 'Headphones', quantity: 67, price: 149 }
        ];
        displayInventory(mockInventory);
    }
}

// Display Inventory
function displayInventory(inventory) {
    const container = document.getElementById('inventoryList');
    container.innerHTML = '';
    
    if (inventory.length === 0) {
        container.innerHTML = '<p>No inventory items available.</p>';
        return;
    }
    
    inventory.forEach(item => {
        const card = document.createElement('div');
        card.className = 'inventory-card';
        
        const stockClass = item.quantity < 10 ? 'low' : '';
        
        card.innerHTML = `
            <h3>${item.productName || item.name}</h3>
            <p>Product ID: ${item.id || item.productId}</p>
            <p>Price: $${item.price || 'N/A'}</p>
            <div class="inventory-stock ${stockClass}">
                Stock: ${item.quantity}
                ${item.quantity < 10 ? '<span style="color: var(--error-color); font-size: 0.875rem;"> (Low Stock!)</span>' : ''}
            </div>
        `;
        
        container.appendChild(card);
    });
}

// Refresh Inventory Button
document.getElementById('refreshInventory').addEventListener('click', () => {
    loadInventory();
});

// Utility function to show messages
function showMessage(elementId, text, type) {
    const messageEl = document.getElementById(elementId);
    messageEl.textContent = text;
    messageEl.className = `message ${type} show`;
    
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 5000);
}