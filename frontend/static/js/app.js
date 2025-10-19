const API_URL = window.location.origin;
let editingServiceRecordId = null;
let editingFuelRecordId = null;
let editingReminderId = null;
let editingVehicleId = null;
let currentUser = null;
let currentTheme = 'dark';
let userSettings = null;

function setSelectedVehicle(vehicleId) {
    localStorage.setItem('selectedVehicleId', vehicleId);
}

function getSelectedVehicle() {
    return localStorage.getItem('selectedVehicleId');
}

function clearSelectedVehicle() {
    localStorage.removeItem('selectedVehicleId');
}

async function loadUserSettings() {
    try {
        const settings = await apiRequest('/api/settings');
        userSettings = settings;
        localStorage.setItem('userSettings', JSON.stringify(settings));
        return settings;
    } catch (error) {
        const cached = localStorage.getItem('userSettings');
        if (cached) {
            userSettings = JSON.parse(cached);
            return userSettings;
        }
        return { currency: 'GBP', unit_system: 'imperial', language: 'en' };
    }
}

function getCurrencySymbol(currency) {
    const symbols = {
        'USD': '$',
        'GBP': '£',
        'RON': 'lei',
        'EUR': '€'
    };
    return symbols[currency] || currency;
}

function formatCurrency(amount, currency = null) {
    if (!currency) {
        const settings = JSON.parse(localStorage.getItem('userSettings') || '{"currency":"GBP"}');
        currency = settings.currency || 'GBP';
    }
    
    const numAmount = parseFloat(amount) || 0;
    const symbol = getCurrencySymbol(currency);
    
    if (currency === 'RON') {
        return `${numAmount.toFixed(2)} ${symbol}`;
    } else {
        return `${symbol}${numAmount.toFixed(2)}`;
    }
}

function formatDate(dateString) {
    const settings = JSON.parse(localStorage.getItem('userSettings') || '{"language":"en"}');
    const lang = settings.language || 'en';
    const locale = lang === 'ro' ? 'ro-RO' : 'en-GB';
    return new Date(dateString).toLocaleDateString(locale);
}

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            }
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text);
            throw new Error('Server returned non-JSON response');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    
    if (currentUser) {
        apiRequest('/api/settings/theme', {
            method: 'POST',
            body: JSON.stringify({ theme: currentTheme })
        }).catch(err => console.error('Failed to save theme:', err));
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
        localStorage.setItem('userSettings', JSON.stringify(data.user));
        
        if (data.user.must_change_credentials) {
            window.location.href = '/first-login';
        } else if (data.user.first_login) {
            alert('Welcome! Please review your settings.');
            window.location.href = '/dashboard';
        } else {
            window.location.href = '/dashboard';
        }
    } catch (error) {
        alert('Login failed: ' + error.message);
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
        alert('Registration failed: ' + error.message);
    }
}

async function logout() {
    try {
        await apiRequest('/api/auth/logout', { method: 'POST' });
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = '/login';
    } catch (error) {
        alert('Logout failed: ' + error.message);
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
    if (!container) return;
    
    const settings = JSON.parse(localStorage.getItem('userSettings') || '{"unit_system":"imperial"}');
    const unitLabel = settings.unit_system === 'metric' ? 'km' : 'miles';
    
    container.innerHTML = vehicles.map(v => `
        <div class="vehicle-card ${v.status === 'sold' ? 'sold' : ''}" onclick="viewVehicle(${v.id})">
            ${v.photo ? `<img src="${v.photo}" class="vehicle-photo" alt="${v.make} ${v.model}">` : ''}
            <h3>${v.year} ${v.make} ${v.model}</h3>
            <p>${v.vin || 'No VIN'}</p>
            <p>Odometer: ${v.odometer.toLocaleString()} ${unitLabel}</p>
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
        closeModal('add-vehicle-modal');
        document.getElementById('add-vehicle-form').reset();
        const photoPreview = document.getElementById('photo-preview');
        if (photoPreview) photoPreview.innerHTML = '';
    } catch (error) {
        alert('Failed to add vehicle: ' + error.message);
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
    if (!tbody) return;
    
    const settings = JSON.parse(localStorage.getItem('userSettings') || '{"currency":"GBP"}');
    const vehicleId = getSelectedVehicle();
    
    tbody.innerHTML = records.map(r => `
        <tr>
            <td>${formatDate(r.date)}</td>
            <td>${r.odometer.toLocaleString()}</td>
            <td>${r.description}</td>
            <td>${r.category || 'N/A'}</td>
            <td>${formatCurrency(r.cost, settings.currency)}</td>
            <td>${r.notes || ''}</td>
            <td>${r.document_path ? `<a href="/api/attachments/download?path=${encodeURIComponent(r.document_path)}" class="btn" style="padding: 5px 10px; font-size: 12px;">Download</a>` : 'None'}</td>
            <td>
                <button onclick="editServiceRecord(${vehicleId}, ${r.id})" class="btn" style="padding: 5px 10px; font-size: 12px; margin-right: 5px;">Edit</button>
                <button onclick="deleteServiceRecord(${vehicleId}, ${r.id})" class="btn" style="padding: 5px 10px; font-size: 12px; background: #dc3545;">Delete</button>
            </td>
        </tr>
    `).join('');
}
function displayFuelRecords(records) {
    const tbody = document.getElementById('fuel-records-tbody');
    if (!tbody) return;
    
    const settings = JSON.parse(localStorage.getItem('userSettings') || '{"currency":"GBP"}');
    const vehicleId = getSelectedVehicle();
    
    tbody.innerHTML = records.map(r => `
        <tr>
            <td>${formatDate(r.date)}</td>
            <td>${r.odometer.toLocaleString()}</td>
            <td>${r.fuel_amount.toFixed(2)}</td>
            <td>${formatCurrency(r.cost, settings.currency)}</td>
            <td>${r.distance || 'N/A'}</td>
            <td>${r.fuel_economy ? r.fuel_economy.toFixed(2) : 'N/A'} ${r.unit}</td>
            <td>${r.notes && r.notes.startsWith('attachment:') ? `<a href="/api/attachments/download?path=${encodeURIComponent(r.notes.replace('attachment:', ''))}" class="btn" style="padding: 5px 10px; font-size: 12px;">Download</a>` : 'None'}</td>
            <td>
                <button onclick="editFuelRecord(${vehicleId}, ${r.id})" class="btn" style="padding: 5px 10px; font-size: 12px; margin-right: 5px;">Edit</button>
                <button onclick="deleteFuelRecord(${vehicleId}, ${r.id})" class="btn" style="padding: 5px 10px; font-size: 12px; background: #dc3545;">Delete</button>
            </td>
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


function calculateFuelStats(records) {
    const totalCost = records.reduce((sum, r) => sum + r.cost, 0);
    const avgEconomy = records.filter(r => r.fuel_economy).reduce((sum, r, _, arr) => 
        sum + r.fuel_economy / arr.length, 0);
    
    const settings = JSON.parse(localStorage.getItem('userSettings') || '{"currency":"GBP"}');
    
    const totalCostEl = document.getElementById('total-fuel-cost');
    const avgEconomyEl = document.getElementById('avg-fuel-economy');
    
    if (totalCostEl) totalCostEl.textContent = formatCurrency(totalCost, settings.currency);
    if (avgEconomyEl) avgEconomyEl.textContent = avgEconomy.toFixed(2);
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
    if (!container) return;
    
    const vehicleId = getSelectedVehicle();
    
    container.innerHTML = reminders.map(r => `
        <div class="kanban-item urgency-${r.urgency}">
            <h4>${r.description}</h4>
            <p>${r.due_date ? `Due: ${formatDate(r.due_date)}` : ''}</p>
            <p>${r.due_odometer ? `At: ${r.due_odometer.toLocaleString()}` : ''}</p>
            <p>${r.notes || ''}</p>
            <div style="margin-top: 10px;">
                <button onclick="editReminder(${vehicleId}, ${r.id})" class="btn" style="padding: 5px 10px; font-size: 12px; margin-right: 5px;">Edit</button>
                <button onclick="deleteReminder(${vehicleId}, ${r.id})" class="btn" style="padding: 5px 10px; font-size: 12px; background: #dc3545;">Delete</button>
            </div>
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
        if (!column) return;
        
        const filtered = todos.filter(t => t.status === status);
        const settings = JSON.parse(localStorage.getItem('userSettings') || '{"currency":"GBP"}');
        
        column.innerHTML = filtered.map(t => `
            <div class="kanban-item priority-${t.priority}" draggable="true" data-id="${t.id}">
                <h4>${t.description}</h4>
                <p>Cost: ${formatCurrency(t.cost, settings.currency)}</p>
                <p>${t.type || ''}</p>
                <small>${t.notes || ''}</small>
            </div>
        `).join('');
    });
}

function showContextMenu(event, type, id) {
    event.preventDefault();
    const menu = document.getElementById('context-menu');
    if (!menu) return;
    
    menu.style.left = `${event.pageX}px`;
    menu.style.top = `${event.pageY}px`;
    menu.classList.add('active');
    menu.dataset.type = type;
    menu.dataset.id = id;
}

document.addEventListener('click', () => {
    const menu = document.getElementById('context-menu');
    if (menu) menu.classList.remove('active');
});

function showModal(modalId) {
    resetEditMode();
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
    resetEditMode();
}

async function exportData(type, vehicleId) {
    window.location.href = `${API_URL}/api/export/${type}?vehicle_id=${vehicleId}`;
}

function exportAllVehicleData(vehicleId) {
    window.location.href = `${API_URL}/api/vehicles/${vehicleId}/export-all`;
}

function viewVehicle(vehicleId) {
    setSelectedVehicle(vehicleId);
    window.location.href = `/vehicle-detail?id=${vehicleId}`;
}

document.addEventListener('DOMContentLoaded', async () => {
    const theme = localStorage.getItem('theme') || 'dark';
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    
    await loadUserSettings();
    
    const vehicleSelect = document.getElementById('vehicle-select');
    if (vehicleSelect) {
        const selectedVehicleId = getSelectedVehicle();
        if (selectedVehicleId) {
            vehicleSelect.value = selectedVehicleId;
            vehicleSelect.dispatchEvent(new Event('change'));
        }
    }
});







async function editRecurringExpense(vehicleId, expenseId) {
    try {
        const expense = await apiRequest(`/api/vehicles/${vehicleId}/recurring-expenses/${expenseId}`);
        const expense_type = prompt('Expense Type:', expense.expense_type);
        if (!expense_type) return;
        const description = prompt('Description:', expense.description);
        if (!description) return;
        const amount = prompt('Amount:', expense.amount);
        if (!amount) return;
        const frequency = prompt('Frequency (monthly/yearly):', expense.frequency);
        const notes = prompt('Notes:', expense.notes || '');
        
        await apiRequest(`/api/vehicles/${vehicleId}/recurring-expenses/${expenseId}`, {
            method: 'PUT',
            body: JSON.stringify({ expense_type, description, amount: parseFloat(amount), frequency, notes })
        });
        alert('Tax/Expense updated successfully');
        location.reload();
    } catch (error) {
        alert('Failed to update tax/expense: ' + error.message);
    }
}

async function deleteRecurringExpense(vehicleId, expenseId) {
    if (!confirm('Are you sure you want to delete this tax/expense?')) return;
    try {
        await apiRequest(`/api/vehicles/${vehicleId}/recurring-expenses/${expenseId}`, { method: 'DELETE' });
        alert('Tax/Expense deleted successfully');
        location.reload();
    } catch (error) {
        alert('Failed to delete tax/expense: ' + error.message);
    }
}

async function editServiceRecord(vehicleId, recordId) {
    try {
        const record = await apiRequest(`/api/vehicles/${vehicleId}/service-records/${recordId}`);
        editingServiceRecordId = recordId;
        editingVehicleId = vehicleId;
        
        document.getElementById('service-date').value = record.date;
        document.getElementById('service-odometer').value = record.odometer;
        document.getElementById('service-description').value = record.description;
        document.getElementById('service-category').value = record.category || 'Maintenance';
        document.getElementById('service-cost').value = record.cost;
        document.getElementById('service-notes').value = record.notes || '';
        
        const modal = document.getElementById('add-service-modal');
        const modalTitle = modal.querySelector('h2');
        if (modalTitle) modalTitle.textContent = 'Edit Service Record';
        modal.style.display = 'block';
    } catch (error) {
        alert('Failed to load service record: ' + error.message);
    }
}

async function deleteServiceRecord(vehicleId, recordId) {
    if (!confirm('Are you sure you want to delete this service record?')) return;
    try {
        await apiRequest(`/api/vehicles/${vehicleId}/service-records/${recordId}`, { method: 'DELETE' });
        alert('Service record deleted successfully');
        await loadServiceRecords(vehicleId);
    } catch (error) {
        alert('Failed to delete service record: ' + error.message);
    }
}

async function editFuelRecord(vehicleId, recordId) {
    try {
        const record = await apiRequest(`/api/vehicles/${vehicleId}/fuel-records/${recordId}`);
        editingFuelRecordId = recordId;
        editingVehicleId = vehicleId;
        
        document.getElementById('fuel-date').value = record.date;
        document.getElementById('fuel-odometer').value = record.odometer;
        document.getElementById('fuel-amount').value = record.fuel_amount;
        document.getElementById('fuel-cost').value = record.cost;
        document.getElementById('fuel-notes').value = record.notes || '';
        
        const modal = document.getElementById('add-fuel-modal');
        const modalTitle = modal.querySelector('h2');
        if (modalTitle) modalTitle.textContent = 'Edit Fuel Record';
        modal.style.display = 'block';
    } catch (error) {
        alert('Failed to load fuel record: ' + error.message);
    }
}

async function deleteFuelRecord(vehicleId, recordId) {
    if (!confirm('Are you sure you want to delete this fuel record?')) return;
    try {
        await apiRequest(`/api/vehicles/${vehicleId}/fuel-records/${recordId}`, { method: 'DELETE' });
        alert('Fuel record deleted successfully');
        await loadFuelRecords(vehicleId);
    } catch (error) {
        alert('Failed to delete fuel record: ' + error.message);
    }
}

async function editReminder(vehicleId, reminderId) {
    try {
        const reminder = await apiRequest(`/api/vehicles/${vehicleId}/reminders/${reminderId}`);
        editingReminderId = reminderId;
        editingVehicleId = vehicleId;
        
        document.getElementById('reminder-description').value = reminder.description;
        document.getElementById('reminder-urgency').value = reminder.urgency;
        document.getElementById('reminder-date').value = reminder.due_date || '';
        document.getElementById('reminder-odometer').value = reminder.due_odometer || '';
        document.getElementById('reminder-notes').value = reminder.notes || '';
        
        const modal = document.getElementById('add-reminder-modal');
        const modalTitle = modal.querySelector('h2');
        if (modalTitle) modalTitle.textContent = 'Edit Reminder';
        modal.style.display = 'block';
    } catch (error) {
        alert('Failed to load reminder: ' + error.message);
    }
}

async function deleteReminder(vehicleId, reminderId) {
    if (!confirm('Are you sure you want to delete this reminder?')) return;
    try {
        await apiRequest(`/api/vehicles/${vehicleId}/reminders/${reminderId}`, { method: 'DELETE' });
        alert('Reminder deleted successfully');
        await loadTodos(vehicleId);
    } catch (error) {
        alert('Failed to delete reminder: ' + error.message);
    }
}

function resetEditMode() {
    editingServiceRecordId = null;
    editingFuelRecordId = null;
    editingReminderId = null;
    editingVehicleId = null;
    
    const serviceModal = document.getElementById('add-service-modal');
    if (serviceModal) {
        const serviceTitle = serviceModal.querySelector('h2');
        if (serviceTitle) serviceTitle.textContent = 'Add Service Record';
    }
    
    const fuelModal = document.getElementById('add-fuel-modal');
    if (fuelModal) {
        const fuelTitle = fuelModal.querySelector('h2');
        if (fuelTitle) fuelTitle.textContent = 'Add Fuel Record';
    }
    
    const reminderModal = document.getElementById('add-reminder-modal');
    if (reminderModal) {
        const reminderTitle = reminderModal.querySelector('h2');
        if (reminderTitle) reminderTitle.textContent = 'Add Reminder';
    }
}
