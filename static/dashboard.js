// ==================== V6.4 DASHBOARD.JS - COMPLETE REWRITE ====================

// PROPERLY FIXED MODAL SYSTEM
class Modal {
    constructor() {
        this.overlay = null;
        this.init();
    }

    init() {
        if (!document.getElementById('modal-overlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'modal-overlay';
            overlay.className = 'modal-overlay';
            overlay.innerHTML = `
                <div class="modal" id="modal-content">
                    <div class="modal-header">
                        <h3 id="modal-title"></h3>
                        <button class="modal-close" onclick="modal.close()">&times;</button>
                    </div>
                    <div class="modal-body" id="modal-body"></div>
                    <div class="modal-footer" id="modal-footer"></div>
                </div>
            `;
            document.body.appendChild(overlay);
            this.overlay = overlay;
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) this.close();
            });
        } else {
            this.overlay = document.getElementById('modal-overlay');
        }
    }

    open(title, body, footer = '') {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = body;
        document.getElementById('modal-footer').innerHTML = footer;
        this.overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// TOAST SYSTEM
class Toast {
    constructor() {
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
            this.container = container;
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icons = { success: '✓', error: '✕', info: 'ℹ' };
        toast.innerHTML = `
            <div class="toast-icon">${icons[type]}</div>
            <div class="toast-content"><div class="toast-message">${message}</div></div>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        this.container.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    success(msg) { this.show(msg, 'success'); }
    error(msg) { this.show(msg, 'error'); }
    info(msg) { this.show(msg, 'info'); }
}

// SPINNER
class Spinner {
    constructor() {
        if (!document.getElementById('spinner-overlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'spinner-overlay';
            overlay.className = 'spinner-overlay';
            overlay.innerHTML = '<div class="spinner"></div>';
            document.body.appendChild(overlay);
            this.overlay = overlay;
        } else {
            this.overlay = document.getElementById('spinner-overlay');
        }
    }
    show() { this.overlay.classList.add('active'); }
    hide() { this.overlay.classList.remove('active'); }
}

// GLOBALS
const modal = new Modal();
const toast = new Toast();
const spinner = new Spinner();

// AJAX HELPER
async function ajax(url, method = 'GET', data = null) {
    spinner.show();
    try {
        const options = { method, headers: { 'Content-Type': 'application/json' } };
        if (data && method !== 'GET') options.body = JSON.stringify(data);
        const response = await fetch(url, options);
        const result = await response.json();
        spinner.hide();
        if (result.success) {
            if (result.message) toast.success(result.message);
            return result;
        } else {
            toast.error(result.message || 'Error');
            return null;
        }
    } catch (error) {
        spinner.hide();
        toast.error('Network error: ' + error.message);
        return null;
    }
}

// EMOJI PICKER - FULL LIBRARY WITH SEARCH
let emojiTarget = null;
let emojiData = null;

async function loadEmojiData() {
    if (!emojiData) {
        const script = document.createElement('script');
        script.src = '/static/emojis.js';
        document.head.appendChild(script);
        await new Promise(resolve => script.onload = resolve);
        emojiData = EMOJI_DATA;
    }
}

function openEmojiPicker(inputId) {
    emojiTarget = inputId;
    
    // Load emoji data first
    if (!window.EMOJI_DATA) {
        const script = document.createElement('script');
        script.src = '/static/emojis.js';
        document.head.appendChild(script);
        script.onload = () => showEmojiPicker();
        return;
    }
    showEmojiPicker();
}

function showEmojiPicker() {
    const emojis = window.EMOJI_DATA;
    let html = '<div class="emoji-picker" style="max-height:500px;overflow-y:auto;">';
    html += '<input type="text" id="emoji-search-input" class="emoji-search" placeholder="Search emoji (money, house, food...)..." onkeyup="filterEmojis(this.value)">';
    html += '<div id="emoji-results"></div>';
    
    for (const [cat, list] of Object.entries(emojis)) {
        html += `<div class="emoji-category" data-category="${cat}"><h4>${cat}</h4><div class="emoji-grid">`;
        for (const e of list) {
            html += `<button type="button" class="emoji-btn" onclick="selectEmoji('${e}'); event.stopPropagation();">${e}</button>`;
        }
        html += '</div></div>';
    }
    html += '</div>';
    
    modal.open('Select Emoji', html, '<button class="btn btn-secondary" onclick="modal.close()">Cancel</button>');
}

function selectEmoji(emoji) {
    if (emojiTarget) {
        const input = document.getElementById(emojiTarget);
        if (input) input.value = emoji;
    }
    modal.close();
}

function filterEmojis(search) {
    const results = document.getElementById('emoji-results');
    const cats = document.querySelectorAll('.emoji-category');
    
    if (search.length < 2) {
        results.innerHTML = '';
        cats.forEach(cat => cat.style.display = 'block');
        return;
    }
    
    // Hide all categories
    cats.forEach(cat => cat.style.display = 'none');
    
    // Search and show results
    const found = window.searchEmojis ? window.searchEmojis(search) : null;
    if (found && found.length > 0) {
        let html = '<div class="emoji-category"><h4>Search Results</h4><div class="emoji-grid">';
        for (const e of found.slice(0, 50)) {
            html += `<button type="button" class="emoji-btn" onclick="selectEmoji('${e}'); event.stopPropagation();">${e}</button>`;
        }
        html += '</div></div>';
        results.innerHTML = html;
    } else {
        results.innerHTML = '<p style="padding:20px;text-align:center;color:#999;">No emojis found</p>';
    }
}

// CATEGORIES - DYNAMIC FROM API
let categories = [];
async function loadCategories() {
    const result = await fetch('/api/categories');
    const data = await result.json();
    if (data.success) categories = data.categories || [];
    return categories;
}

function getCategoryOptions() {
    if (categories.length === 0) {
        return `<option value="Housing">Housing</option>
                <option value="Utilities">Utilities</option>
                <option value="Other">Other</option>`;
    }
    return categories.map(c => `<option value="${c.name}">${c.emoji || ''} ${c.name}</option>`).join('');
}

// BILL CRUD
function createBill() {
    const body = `
        <form id="create-bill-form">
            <div class="form-row">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" required>
                </div>
                <div class="form-group">
                    <label>Emoji</label>
                    <div style="display:flex;gap:10px;">
                        <input type="text" id="new_bill_emoji" name="emoji" value="📄" 
                               style="width:60px;font-size:24px;text-align:center;" readonly>
                        <button type="button" class="btn btn-secondary" onclick="openEmojiPicker('new_bill_emoji')">Pick</button>
                    </div>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Category</label>
                    <select name="category" required>${getCategoryOptions()}</select>
                </div>
                <div class="form-group">
                    <label>Amount</label>
                    <input type="number" name="amount" step="0.01" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Frequency</label>
                    <select name="frequency" id="bill-frequency" onchange="toggleBillDateFields()" required>
                        <option value="monthly">Monthly</option>
                        <option value="one-time">One-time</option>
                        <option value="bi-monthly">Bi-monthly</option>
                        <option value="annual">Annual</option>
                    </select>
                </div>
                <div class="form-group" id="due-day-group">
                    <label>Due Day</label>
                    <input type="number" name="due_day" id="due-day-input" min="1" max="31">
                </div>
                <div class="form-group" id="due-date-group" style="display:none;">
                    <label>Due Date</label>
                    <input type="date" name="due_date" id="due-date-input">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Autopay</label>
                    <select name="autopay"><option value="0">No</option><option value="1">Yes</option></select>
                </div>
                <div class="form-group">
                    <label class="checkbox-group">
                        <input type="checkbox" name="payable_by_cc" value="1"> 💳 Payable by Credit Card
                    </label>
                </div>
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea name="notes"></textarea>
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="modal.close()">Cancel</button>
        <button class="btn btn-success" onclick="saveNewBill()">Create</button>
    `;
    modal.open('Create Bill', body, footer);
}

function toggleBillDateFields() {
    const freq = document.getElementById('bill-frequency').value;
    document.getElementById('due-day-group').style.display = freq === 'one-time' ? 'none' : 'block';
    document.getElementById('due-date-group').style.display = freq === 'one-time' ? 'block' : 'none';
}

async function saveNewBill() {
    const form = document.getElementById('create-bill-form');
    const data = Object.fromEntries(new FormData(form));
    data.autopay = data.autopay || '0';
    data.payable_by_cc = data.payable_by_cc ? '1' : '0';
    const result = await ajax('/api/bill', 'POST', data);
    if (result) {
        modal.close();
        setTimeout(() => location.reload(), 500);
    }
}

function editBill(id, name, emoji, amount, dueDay, frequency, autopay, status, notes, payableByCC) {
    const body = `
        <form id="edit-bill-form">
            <div class="form-row">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" value="${name}" required>
                </div>
                <div class="form-group">
                    <label>Emoji</label>
                    <div style="display:flex;gap:10px;">
                        <input type="text" id="edit_bill_emoji_${id}" name="emoji" value="${emoji}" 
                               style="width:60px;font-size:24px;text-align:center;" readonly>
                        <button type="button" class="btn btn-secondary" onclick="openEmojiPicker('edit_bill_emoji_${id}')">Pick</button>
                    </div>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Amount</label>
                    <input type="number" name="amount" value="${amount}" step="0.01" required>
                </div>
                <div class="form-group">
                    <label>Status</label>
                    <select name="status">
                        <option value="pending" ${status==='pending'?'selected':''}>Pending</option>
                        <option value="paid" ${status==='paid'?'selected':''}>Paid</option>
                        <option value="overdue" ${status==='overdue'?'selected':''}>Overdue</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Autopay</label>
                    <select name="autopay">
                        <option value="0" ${!autopay?'selected':''}>No</option>
                        <option value="1" ${autopay?'selected':''}>Yes</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="checkbox-group">
                        <input type="checkbox" name="payable_by_cc" value="1" ${payableByCC?'checked':''}> 
                        💳 Payable by Credit Card
                    </label>
                </div>
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea name="notes">${notes||''}</textarea>
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="modal.close()">Cancel</button>
        <button class="btn btn-success" onclick="updateBill(${id})">Save</button>
    `;
    modal.open('Edit Bill', body, footer);
}

async function updateBill(id) {
    const form = document.getElementById('edit-bill-form');
    const data = Object.fromEntries(new FormData(form));
    data.payable_by_cc = data.payable_by_cc ? '1' : '0';
    const result = await ajax(`/api/bill/${id}`, 'PUT', data);
    if (result) {
        modal.close();
        setTimeout(() => location.reload(), 500);
    }
}

async function confirmDelete(type, id, name) {
    if (confirm(`Delete ${name}?`)) {
        const url = type === 'bill' ? `/api/bill/${id}` : `/api/credit/${id}`;
        const result = await ajax(url, 'DELETE');
        if (result) setTimeout(() => location.reload(), 500);
    }
}

// CREDIT CARD CRUD WITH PAYMENT OVERRIDE
function createCreditAccount() {
    const body = `
        <form id="create-credit-form">
            <div class="form-row">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" required>
                </div>
                <div class="form-group">
                    <label>Emoji</label>
                    <div style="display:flex;gap:10px;">
                        <input type="text" id="new_credit_emoji" name="emoji" value="💳" 
                               style="width:60px;font-size:24px;text-align:center;" readonly>
                        <button type="button" class="btn btn-secondary" onclick="openEmojiPicker('new_credit_emoji')">Pick</button>
                    </div>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Type</label>
                    <select name="account_type">
                        <option value="credit_card">Credit Card</option>
                        <option value="loan">Loan</option>
                        <option value="line_of_credit">Line of Credit</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Balance</label>
                    <input type="number" name="current_balance" step="0.01" value="0" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Credit Limit</label>
                    <input type="number" name="credit_limit" step="0.01" required>
                </div>
                <div class="form-group">
                    <label>Minimum Payment</label>
                    <input type="number" name="minimum_payment" step="0.01" required>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>APR (%)</label>
                    <input type="number" name="apr" step="0.01">
                </div>
                <div class="form-group">
                    <label class="checkbox-group">
                        <input type="checkbox" name="payable_by_cc" value="1"> 💳 Payable by Credit Card
                    </label>
                </div>
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="modal.close()">Cancel</button>
        <button class="btn btn-success" onclick="saveNewCredit()">Create</button>
    `;
    modal.open('Create Credit Account', body, footer);
}

async function saveNewCredit() {
    const form = document.getElementById('create-credit-form');
    const data = Object.fromEntries(new FormData(form));
    data.payable_by_cc = data.payable_by_cc ? '1' : '0';
    const result = await ajax('/api/credit', 'POST', data);
    if (result) {
        modal.close();
        setTimeout(() => location.reload(), 500);
    }
}

function editCreditCard(id, name, emoji, balance, limit, minPay, apr) {
    fetch(`/api/credit/${id}/payment-override`)
        .then(r => r.json())
        .then(data => {
            const override = data.override;
            const body = `
                <form id="edit-credit-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Name</label>
                            <input type="text" name="name" value="${name}" required>
                        </div>
                        <div class="form-group">
                            <label>Emoji</label>
                            <div style="display:flex;gap:10px;">
                                <input type="text" id="edit_credit_emoji_${id}" name="emoji" value="${emoji}" 
                                       style="width:60px;font-size:24px;text-align:center;" readonly>
                                <button type="button" class="btn btn-secondary" onclick="openEmojiPicker('edit_credit_emoji_${id}')">Pick</button>
                            </div>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Balance</label>
                            <input type="number" name="current_balance" value="${balance}" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label>Limit</label>
                            <input type="number" name="credit_limit" value="${limit}" step="0.01" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Minimum Payment</label>
                            <input type="number" name="minimum_payment" value="${minPay}" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label>APR (%)</label>
                            <input type="number" name="apr" value="${apr||0}" step="0.01">
                        </div>
                    </div>
                    <div style="margin-top:20px;padding:15px;background:#fff3cd;border-radius:6px;">
                        <strong>💰 This Month's Payment Override</strong>
                        <div style="margin-top:10px;">
                            <input type="number" id="payment_override" value="${override?.override_amount||''}" 
                                   step="0.01" placeholder="Leave empty for minimum (${minPay})"
                                   style="width:100%;padding:8px;">
                            <small style="display:block;margin-top:5px;color:#666;">
                                Override resets next month. Leave empty to use minimum payment.
                            </small>
                        </div>
                    </div>
                </form>
            `;
            const footer = `
                <button class="btn btn-secondary" onclick="modal.close()">Cancel</button>
                <button class="btn btn-success" onclick="updateCreditCard(${id})">Save</button>
            `;
            modal.open('Edit Credit Account', body, footer);
        });
}

async function updateCreditCard(id) {
    const form = document.getElementById('edit-credit-form');
    const data = Object.fromEntries(new FormData(form));
    
    // Save card details
    const result = await ajax(`/api/credit/${id}`, 'PUT', data);
    
    // Save payment override
    const overrideAmt = document.getElementById('payment_override').value;
    if (overrideAmt) {
        await ajax(`/api/credit/${id}/payment-override`, 'POST', { override_amount: parseFloat(overrideAmt) });
    } else {
        await ajax(`/api/credit/${id}/payment-override`, 'DELETE');
    }
    
    if (result) {
        modal.close();
        setTimeout(() => location.reload(), 500);
    }
}

// SETTINGS
function openSettingsModal() {
    fetch('/api/settings')
        .then(r => r.json())
        .then(settings => {
            const body = `
                <form id="settings-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Monthly Income</label>
                            <input type="number" name="monthly_income" value="${settings.monthly_income}" step="0.01">
                        </div>
                        <div class="form-group">
                            <label>Cushion Amount</label>
                            <input type="number" name="cushion_amount" value="${settings.cushion_amount}" step="0.01">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Checkpoint Mode</label>
                        <select name="checkpoint_mode" onchange="toggleCheckpointSettings()">
                            <option value="1-10-20" ${settings.checkpoint_mode==='1-10-20'?'selected':''}>1st, 10th, 20th</option>
                            <option value="nys-payroll" ${settings.checkpoint_mode==='nys-payroll'?'selected':''}>NYS Payroll</option>
                            <option value="custom" ${settings.checkpoint_mode==='custom'?'selected':''}>Custom</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Checkpoints to Show</label>
                        <input type="number" name="checkpoint_count" value="${settings.checkpoint_count}" min="1" max="10">
                    </div>
                    <div class="form-group">
                        <label class="checkbox-group">
                            <input type="checkbox" name="dark_mode" ${settings.dark_mode?'checked':''}> Dark Mode
                        </label>
                    </div>
                </form>
            `;
            const footer = `
                <button class="btn btn-secondary" onclick="modal.close()">Cancel</button>
                <button class="btn btn-success" onclick="saveSettings()">Save</button>
            `;
            modal.open('Settings', body, footer);
        });
}

async function saveSettings() {
    const form = document.getElementById('settings-form');
    const data = Object.fromEntries(new FormData(form));
    data.dark_mode = data.dark_mode ? 1 : 0;
    const result = await ajax('/api/settings', 'PUT', data);
    if (result) {
        modal.close();
        setTimeout(() => location.reload(), 500);
    }
}

// RECURRING INCOME
function openRecurringIncomeModal() {
    fetch('/api/recurring-income')
        .then(r => r.json())
        .then(data => {
            const income = data.income || [];
            let rows = '';
            for (const inc of income) {
                rows += `<tr>
                    <td>${inc.source}</td>
                    <td>$${parseFloat(inc.amount).toFixed(2)}</td>
                    <td>${inc.frequency}</td>
                    <td>${inc.start_date}</td>
                    <td>
                        <button class="btn btn-danger" onclick="deleteRecurringIncome(${inc.id})">Delete</button>
                    </td>
                </tr>`;
            }
            const body = `
                <button class="add-button" onclick="addRecurringIncome()">+ Add Income</button>
                <table style="width:100%;margin-top:20px;">
                    <thead><tr><th>Source</th><th>Amount</th><th>Frequency</th><th>Start</th><th>Actions</th></tr></thead>
                    <tbody>${rows || '<tr><td colspan="5">No recurring income</td></tr>'}</tbody>
                </table>
            `;
            modal.open('Recurring Income', body, '<button class="btn btn-secondary" onclick="modal.close()">Close</button>');
        });
}

function addRecurringIncome() {
    const body = `
        <form id="income-form">
            <div class="form-group">
                <label>Source</label>
                <input type="text" name="source" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Amount</label>
                    <input type="number" name="amount" step="0.01" required>
                </div>
                <div class="form-group">
                    <label>Frequency</label>
                    <select name="frequency">
                        <option value="bi-weekly">Bi-Weekly</option>
                        <option value="monthly">Monthly</option>
                        <option value="weekly">Weekly</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Start Date</label>
                <input type="date" name="start_date" required>
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="openRecurringIncomeModal()">Back</button>
        <button class="btn btn-success" onclick="saveRecurringIncome()">Save</button>
    `;
    modal.open('Add Recurring Income', body, footer);
}

async function saveRecurringIncome() {
    const form = document.getElementById('income-form');
    const data = Object.fromEntries(new FormData(form));
    const result = await ajax('/api/recurring-income', 'POST', data);
    if (result) openRecurringIncomeModal();
}

async function deleteRecurringIncome(id) {
    if (confirm('Delete this income source?')) {
        const result = await ajax(`/api/recurring-income/${id}`, 'DELETE');
        if (result) openRecurringIncomeModal();
    }
}

// CATEGORIES
function openCategoriesModal() {
    fetch('/api/categories')
        .then(r => r.json())
        .then(data => {
            const cats = data.categories || [];
            let rows = '';
            for (const cat of cats) {
                rows += `<tr>
                    <td>${cat.emoji || ''} ${cat.name}</td>
                    <td>${cat.type}</td>
                    <td>
                        <button class="btn btn-danger" onclick="deleteCategory(${cat.id})">Delete</button>
                    </td>
                </tr>`;
            }
            const body = `
                <button class="add-button" onclick="addCategory()">+ Add Category</button>
                <table style="width:100%;margin-top:20px;">
                    <thead><tr><th>Name</th><th>Type</th><th>Actions</th></tr></thead>
                    <tbody>${rows || '<tr><td colspan="3">No categories</td></tr>'}</tbody>
                </table>
            `;
            modal.open('Categories', body, '<button class="btn btn-secondary" onclick="modal.close()">Close</button>');
        });
}

function addCategory() {
    const body = `
        <form id="category-form">
            <div class="form-row">
                <div class="form-group">
                    <label>Name</label>
                    <input type="text" name="name" required>
                </div>
                <div class="form-group">
                    <label>Emoji</label>
                    <div style="display:flex;gap:10px;">
                        <input type="text" id="new_cat_emoji" name="emoji" value="📁" 
                               style="width:60px;font-size:24px;text-align:center;" readonly>
                        <button type="button" class="btn btn-secondary" onclick="openEmojiPicker('new_cat_emoji')">Pick</button>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label>Type</label>
                <select name="type">
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                </select>
            </div>
        </form>
    `;
    const footer = `
        <button class="btn btn-secondary" onclick="openCategoriesModal()">Back</button>
        <button class="btn btn-success" onclick="saveCategory()">Save</button>
    `;
    modal.open('Add Category', body, footer);
}

async function saveCategory() {
    const form = document.getElementById('category-form');
    const data = Object.fromEntries(new FormData(form));
    const result = await ajax('/api/categories', 'POST', data);
    if (result) {
        await loadCategories();
        openCategoriesModal();
    }
}

async function deleteCategory(id) {
    if (confirm('Delete this category?')) {
        const result = await ajax(`/api/categories/${id}`, 'DELETE');
        if (result) {
            await loadCategories();
            openCategoriesModal();
        }
    }
}

// UTILITIES
async function updateBalance() {
    const newBalance = prompt('Enter new Wells Fargo balance:');
    if (newBalance !== null && !isNaN(newBalance)) {
        const result = await ajax('/api/balance', 'PUT', { balance: parseFloat(newBalance) });
        if (result) setTimeout(() => location.reload(), 500);
    }
}

async function resetMonthlyBills() {
    if (confirm('Reset all monthly bills to pending?')) {
        const result = await ajax('/api/batch/reset-monthly', 'POST');
        if (result) setTimeout(() => location.reload(), 500);
    }
}

async function clearPaidBills() {
    if (confirm('Clear all paid bills?')) {
        const result = await ajax('/api/batch/clear-paid', 'POST');
        if (result) setTimeout(() => location.reload(), 500);
    }
}

function exportFullDatabase() {
    window.location.href = '/api/export/full';
}

function importData() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        spinner.show();
        try {
            const response = await fetch('/api/import', { method: 'POST', body: formData });
            const result = await response.json();
            spinner.hide();
            if (result.success) {
                toast.success(result.message);
                setTimeout(() => location.reload(), 1000);
            } else {
                toast.error(result.message);
            }
        } catch (error) {
            spinner.hide();
            toast.error('Import failed: ' + error.message);
        }
    };
    input.click();
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    const btn = document.getElementById('darkModeBtn');
    if (btn) btn.innerHTML = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
    fetch('/api/settings', { method: 'PUT', headers: {'Content-Type':'application/json'}, 
        body: JSON.stringify({dark_mode: isDark ? 1 : 0}) });
}

// LARGE EXPENSES REMINDER WIDGET
function loadLargeExpenses() {
    fetch('/api/large-expenses')
        .then(r => r.json())
        .then(data => {
            if (data.success && data.expenses && data.expenses.length > 0) {
                const widget = document.createElement('div');
                widget.className = 'reminder-widget';
                widget.id = 'reminder-widget';
                let items = '';
                for (const exp of data.expenses) {
                    const daysText = exp.days_until === 0 ? 'Today!' : exp.days_until === 1 ? 'Tomorrow' : `in ${exp.days_until} days`;
                    items += `
                        <div class="reminder-item">
                            <div class="reminder-item-name">${exp.name}</div>
                            <div class="reminder-item-amount">$${parseFloat(exp.amount).toFixed(2)}</div>
                            <div class="reminder-item-days">Due ${daysText} (${exp.due_date})</div>
                        </div>
                    `;
                }
                widget.innerHTML = `
                    <div class="reminder-header">
                        ⚠️ Large Expenses (>$500)
                        <button class="reminder-close" onclick="document.getElementById('reminder-widget').remove()">×</button>
                    </div>
                    <div class="reminder-body">${items}</div>
                `;
                document.body.appendChild(widget);
            }
        });
}

// INIT
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    loadLargeExpenses();
    
    // Dark mode init
    const isDark = document.body.classList.contains('dark-mode');
    const btn = document.getElementById('darkModeBtn');
    if (btn) btn.innerHTML = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
    
    // Search functionality
    const searchBar = document.getElementById('searchBar');
    if (searchBar) {
        searchBar.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            document.querySelectorAll('.searchable-row').forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
});
