const API_URL = window.location.origin;
let currentUser = null;
let currentTheme = 'dark';

async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Request failed');
    }
    
    return response.json();
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    
    if (currentUser) {
        apiRequest('/api/settings/theme', {
            method: 'POST',
            body: JSON.stringify({ theme: currentTheme })
        });
    }
}

async function login(username, password) {
    try {
        const data = await apiRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        currentUser = data.user;
        currentTheme = data.user.theme;
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        if (data.user.first_login) {
            showChangePasswordModal();
        } else {
            window.location.href = '/dashboard';
        }
    } catch (error) {
        alert(error.message);
    }
}

async function register(username, email, password) {
    try {
        await apiRequest('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        
        alert('Registration successful! Please login.');
        window.location.href = '/login';
    } catch (error) {
        alert(error.message);
    }
}

async function logout() {
    try {
        await apiRequest('/api/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        alert(error.message);
    }
}

async function loadVehicles() {
    try {
        const vehicles = await apiRequest('/api/vehicles');
        displayVehicles(vehicles);
    } catch (error) {
        console.error('Failed to load vehicles:', error);
    }
}

function displayVehicles(vehicles) {
    const container = document.getElementById('vehicles-container');
    container.innerHTML = vehicles.map(v => `
        <div class="vehicle-card ${v.status === 'sold' ? 'sold' : ''}" onclick="viewVehicle(${v.id})">
            ${v.photo ? `<img src="${v.photo}" class="vehicle-photo" alt="${v.make} ${v.model}">` : ''}
            <h3>${v.year} ${v.make} ${v.model}</h3>
            <p>${v.vin || 'No VIN'}</p>
            <p>Odometer: ${v.odometer.toLocaleString()} miles</p>
        </div>
    `).join('');
}

async function addVehicle(vehicleData) {
    try {
        await apiRequest('/api/vehicles', {
            method: 'POST',
            body: JSON.stringify(vehicleData)
        });
        
        loadVehicles();
        closeModal('vehicle-modal');
    } catch (error) {
        alert(error.message);
    }
}

async function loadServiceRecords(vehicleId) {
    try {
        const records = await apiRequest(`/api/vehicles/${vehicleId}/service-records`);
        displayServiceRecords(records);
    } catch (error) {
        console.error('Failed to load service records:', error);
    }
}

function displayServiceRecords(records) {
    const tbody = document.getElementById('service-records-tbody');
    tbody.innerHTML = records.map(r => `
        <tr oncontextmenu="showContextMenu(event, 'service', ${r.id})">
            <td>${new Date(r.date).toLocaleDateString()}</td>
            <td>${r.odometer.toLocaleString()}</td>
            <td>${r.description}</td>
            <td>$${r.cost.toFixed(2)}</td>
            <td>${r.category || 'N/A'}</td>
            <td>${r.notes || ''}</td>
        </tr>
    `).join('');
}

async function loadFuelRecords(vehicleId) {
    try {
        const records = await apiRequest(`/api/vehicles/${vehicleId}/fuel-records`);
        displayFuelRecords(records);
        calculateFuelStats(records);
    } catch (error) {
        console.error('Failed to load fuel records:', error);
    }
}

function displayFuelRecords(records) {
    const tbody = document.getElementById('fuel-records-tbody');
    tbody.innerHTML = records.map(r => `
        <tr>
            <td>${new Date(r.date).toLocaleDateString()}</td>
            <td>${r.odometer.toLocaleString()}</td>
            <td>${r.fuel_amount.toFixed(2)}</td>
            <td>$${r.cost.toFixed(2)}</td>
            <td>${r.distance || 'N/A'}</td>
            <td>${r.fuel_economy ? r.fuel_economy.toFixed(2) : 'N/A'} ${r.unit}</td>
        </tr>
    `).join('');
}

function calculateFuelStats(records) {
    const totalCost = records.reduce((sum, r) => sum + r.cost, 0);
    const avgEconomy = records.filter(r => r.fuel_economy).reduce((sum, r, _, arr) => 
        sum + r.fuel_economy / arr.length, 0);
    
    document.getElementById('total-fuel-cost').textContent = `$${totalCost.toFixed(2)}`;
    document.getElementById('avg-fuel-economy').textContent = avgEconomy.toFixed(2);
}

async function loadReminders(vehicleId) {
    try {
        const reminders = await apiRequest(`/api/vehicles/${vehicleId}/reminders`);
        displayReminders(reminders);
    } catch (error) {
        console.error('Failed to load reminders:', error);
    }
}

function displayReminders(reminders) {
    const container = document.getElementById('reminders-container');
    container.innerHTML = reminders.map(r => `
        <div class="kanban-item urgency-${r.urgency}">
            <h4>${r.description}</h4>
            <p>${r.due_date ? `Due: ${new Date(r.due_date).toLocaleDateString()}` : ''}</p>
            <p>${r.due_odometer ? `At: ${r.due_odometer.toLocaleString()} miles` : ''}</p>
            <p>${r.notes || ''}</p>
        </div>
    `).join('');
}

async function loadTodos(vehicleId) {
    try {
        const todos = await apiRequest(`/api/vehicles/${vehicleId}/todos`);
        displayTodos(todos);
    } catch (error) {
        console.error('Failed to load todos:', error);
    }
}

function displayTodos(todos) {
    const statuses = ['planned', 'doing', 'testing', 'done'];
    statuses.forEach(status => {
        const column = document.getElementById(`todos-${status}`);
        const filtered = todos.filter(t => t.status === status);
        column.innerHTML = filtered.map(t => `
            <div class="kanban-item priority-${t.priority}" draggable="true" data-id="${t.id}">
                <h4>${t.description}</h4>
                <p>Cost: $${t.cost.toFixed(2)}</p>
                <p>${t.type || ''}</p>
                <small>${t.notes || ''}</small>
            </div>
        `).join('');
    });
}

function showContextMenu(event, type, id) {
    event.preventDefault();
    const menu = document.getElementById('context-menu');
    menu.style.left = `${event.pageX}px`;
    menu.style.top = `${event.pageY}px`;
    menu.classList.add('active');
    menu.dataset.type = type;
    menu.dataset.id = id;
}

document.addEventListener('click', () => {
    document.getElementById('context-menu')?.classList.remove('active');
});

function showModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

async function exportData(type, vehicleId) {
    window.location.href = `${API_URL}/api/export/${type}?vehicle_id=${vehicleId}`;
}

document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('theme') || 'dark';
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
});
