import sqlite3
from datetime import *
from typing import List, Dict, Optional

DATABASE_NAME = 'finance.db'

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with all tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Account balance tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_balance (
            id INTEGER PRIMARY KEY,
            balance REAL NOT NULL,
            cushion REAL DEFAULT 500.00,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Income sources
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            date_received DATE,
            date_expected DATE,
            status TEXT DEFAULT 'expected',
            notes TEXT
        )
    ''')
    
    # Bills and recurring expenses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '📄',
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            due_day INTEGER,
            due_date DATE,
            frequency TEXT DEFAULT 'monthly',
            autopay INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            last_paid_date DATE,
            notes TEXT
        )
    ''')
    
    # Credit accounts (cards and loans)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '💳',
            account_type TEXT NOT NULL,
            current_balance REAL NOT NULL,
            credit_limit REAL,
            minimum_payment REAL NOT NULL,
            apr REAL,
            cycle_close_day INTEGER,
            payment_due_day INTEGER,
            last_updated DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # User settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY,
            monthly_income REAL DEFAULT 1882.34,
            cushion_amount REAL DEFAULT 500.00,
            checkpoint_mode TEXT DEFAULT '1-10-20',
            checkpoint_count INTEGER DEFAULT 3,
            custom_checkpoint_days TEXT,
            nys_payroll_start_date DATE,
            dark_mode INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Recurring income
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recurring_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            day_of_month INTEGER,
            active INTEGER DEFAULT 1,
            notes TEXT
        )
    ''')
    
    # Categories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            emoji TEXT DEFAULT '📁',
            type TEXT DEFAULT 'expense',
            sort_order INTEGER DEFAULT 999
        )
    ''')
    
    # Property transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS property_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date DATE NOT NULL,
            category TEXT,
            notes TEXT
        )
    ''')
    
    # Tax obligations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tax_obligations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tax_type TEXT NOT NULL,
            amount_due REAL NOT NULL,
            due_date DATE NOT NULL,
            payment_plan INTEGER DEFAULT 0,
            monthly_payment REAL,
            status TEXT DEFAULT 'pending',
            notes TEXT
        )
    ''')
    
    # Payment history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER,
            credit_account_id INTEGER,
            amount REAL NOT NULL,
            payment_date DATE NOT NULL,
            notes TEXT,
            FOREIGN KEY (bill_id) REFERENCES bills (id),
            FOREIGN KEY (credit_account_id) REFERENCES credit_accounts (id)
        )
    ''')
    
    # Past due bill instances
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS past_due_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id INTEGER,
            credit_account_id INTEGER,
            period TEXT NOT NULL,
            amount REAL NOT NULL,
            created_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (bill_id) REFERENCES bills (id),
            FOREIGN KEY (credit_account_id) REFERENCES credit_accounts (id)
        )
    ''')
    
    # V6.4: Credit payment overrides
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_payment_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_account_id INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            override_amount REAL NOT NULL,
            created_date DATE DEFAULT CURRENT_DATE,
            UNIQUE(credit_account_id, month, year),
            FOREIGN KEY (credit_account_id) REFERENCES credit_accounts (id)
        )
    ''')
    
    # V6.4: Property unit status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS property_unit_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_number TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'vacant',
            monthly_rent REAL,
            tenant_name TEXT,
            lease_start DATE,
            lease_end DATE,
            notes TEXT
        )
    ''')
    
    # V6.4: Property repair estimates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS property_repair_estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_number TEXT,
            description TEXT NOT NULL,
            estimated_cost REAL,
            actual_cost REAL,
            contractor TEXT,
            status TEXT DEFAULT 'pending',
            date_created DATE DEFAULT CURRENT_DATE,
            date_completed DATE,
            notes TEXT
        )
    ''')
    
    # V6.4: Property income projections
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS property_income_projections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            projected_income REAL NOT NULL,
            actual_income REAL,
            notes TEXT,
            UNIQUE(month, year)
        )
    ''')
    
    # V6.4: Add payable_by_cc column to bills if not exists
    try:
        cursor.execute('ALTER TABLE bills ADD COLUMN payable_by_cc INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # V6.4: Add payable_by_cc column to credit_accounts if not exists
    try:
        cursor.execute('ALTER TABLE credit_accounts ADD COLUMN payable_by_cc INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Initialize default settings if not exists
    cursor.execute("SELECT COUNT(*) FROM user_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO user_settings (id, monthly_income, cushion_amount, checkpoint_mode, checkpoint_count)
            VALUES (1, 1882.34, 500.00, '1-10-20', 3)
        ''')
    
    # Initialize default categories if not exists
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ('Housing', '🏠', 'expense', 1),
            ('Utilities', '💡', 'expense', 2),
            ('Phone/Internet', '📱', 'expense', 3),
            ('Subscriptions', '📺', 'expense', 4),
            ('Insurance', '🛡️', 'expense', 5),
            ('Transportation', '🚗', 'expense', 6),
            ('Food', '🍔', 'expense', 7),
            ('Healthcare', '🏥', 'expense', 8),
            ('Personal', '👤', 'expense', 9),
            ('Other', '📌', 'expense', 10)
        ]
        for cat in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, emoji, type, sort_order)
                VALUES (?, ?, ?, ?)
            ''', cat)
    
    conn.commit()
    conn.close()

def get_account_balance():
    """Get current Wells Fargo account balance"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM account_balance WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'balance': result['balance'],
            'cushion': result['cushion'],
            'available': result['balance'] - result['cushion'],
            'last_updated': result['last_updated']
        }
    return None

def update_account_balance(balance: float):
    """Update Wells Fargo balance"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO account_balance (id, balance, cushion, last_updated)
        VALUES (1, ?, 500.00, ?)
    ''', (balance, datetime.now()))
    conn.commit()
    conn.close()

def get_all_bills():
    """Get all bills"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bills ORDER BY due_day')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_overdue_bills():
    """Get all overdue bills"""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today()
    cursor.execute('''
        SELECT * FROM bills 
        WHERE status = 'overdue' 
        OR (due_date IS NOT NULL AND due_date < ? AND status = 'pending')
        ORDER BY due_date
    ''', (today,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_upcoming_bills(days: int = 30):
    """Get bills due in next X days"""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today()
    cursor.execute('''
        SELECT * FROM bills 
        WHERE (due_date IS NOT NULL AND due_date >= ? AND status = 'pending')
        OR (due_day IS NOT NULL AND status = 'pending')
        ORDER BY due_date, due_day
    ''', (today,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_bill(name: str, category: str, amount: float, due_day: int = None, 
             frequency: str = 'monthly', autopay: bool = False, due_date: date = None):
    """Add a new bill"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bills (name, category, amount, due_day, frequency, autopay, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, category, amount, due_day, frequency, 1 if autopay else 0, due_date))
    conn.commit()
    conn.close()

def mark_bill_paid(bill_id: int, payment_date: date):
    """Mark a bill as paid"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE bills 
        SET status = 'paid', last_paid_date = ?
        WHERE id = ?
    ''', (payment_date, bill_id))
    conn.commit()
    conn.close()

def mark_bill_overdue(bill_id: int):
    """Mark a bill as overdue"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE bills 
        SET status = 'overdue'
        WHERE id = ?
    ''', (bill_id,))
    conn.commit()
    conn.close()

def update_bill(bill_id: int, name: str = None, emoji: str = None, amount: float = None, 
               due_day: int = None, frequency: str = None, 
               autopay: bool = None, status: str = None):
    """Update bill with multiple fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build dynamic UPDATE query
    updates = []
    values = []
    
    if name is not None:
        updates.append('name = ?')
        values.append(name)
    if emoji is not None:
        updates.append('emoji = ?')
        values.append(emoji)
    if amount is not None:
        updates.append('amount = ?')
        values.append(amount)
    if due_day is not None:
        updates.append('due_day = ?')
        values.append(due_day if due_day > 0 else None)
    if frequency is not None:
        updates.append('frequency = ?')
        values.append(frequency)
    if autopay is not None:
        updates.append('autopay = ?')
        values.append(1 if autopay else 0)
    if status is not None:
        updates.append('status = ?')
        values.append(status)
    
    if updates:
        values.append(bill_id)
        query = f"UPDATE bills SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()

def get_all_credit_accounts():
    """Get all credit accounts"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM credit_accounts ORDER BY name')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_credit_utilization():
    """Calculate overall credit utilization"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            SUM(current_balance) as total_balance,
            SUM(credit_limit) as total_limit
        FROM credit_accounts
        WHERE account_type = 'credit_card' AND credit_limit IS NOT NULL
    ''')
    result = cursor.fetchone()
    conn.close()
    
    if result and result['total_limit'] and result['total_limit'] > 0:
        utilization = (result['total_balance'] / result['total_limit']) * 100
        return {
            'utilization_percent': round(utilization, 1),
            'total_balance': result['total_balance'],
            'total_limit': result['total_limit']
        }
    return None

def add_credit_account(name: str, account_type: str, balance: float, 
                       limit: Optional[float], min_payment: float, apr: float,
                       cycle_close_day: int, payment_due_day: int):
    """Add a credit account"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO credit_accounts 
        (name, account_type, current_balance, credit_limit, minimum_payment, 
         apr, cycle_close_day, payment_due_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, account_type, balance, limit, min_payment, apr, cycle_close_day, payment_due_day))
    conn.commit()
    conn.close()

def update_credit_balance(account_id: int, new_balance: float):
    """Update credit account balance"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE credit_accounts 
        SET current_balance = ?, last_updated = ?
        WHERE id = ?
    ''', (new_balance, date.today(), account_id))
    conn.commit()
    conn.close()

def update_credit_account(account_id: int, name: str = None, emoji: str = None, 
                         balance: float = None, limit: float = None, 
                         min_payment: float = None, apr: float = None,
                         cycle_close_day: int = None, payment_due_day: int = None):
    """Update credit account with multiple fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build dynamic UPDATE query based on provided values
    updates = []
    values = []
    
    if name is not None:
        updates.append('name = ?')
        values.append(name)
    if emoji is not None:
        updates.append('emoji = ?')
        values.append(emoji)
    if balance is not None:
        updates.append('current_balance = ?')
        values.append(balance)
    if limit is not None:
        updates.append('credit_limit = ?')
        values.append(limit)
    if min_payment is not None:
        updates.append('minimum_payment = ?')
        values.append(min_payment)
    if apr is not None:
        updates.append('apr = ?')
        values.append(apr)
    if cycle_close_day is not None:
        updates.append('cycle_close_day = ?')
        values.append(cycle_close_day)
    if payment_due_day is not None:
        updates.append('payment_due_day = ?')
        values.append(payment_due_day)
    
    if updates:
        updates.append('last_updated = ?')
        values.append(date.today())
        values.append(account_id)
        
        query = f"UPDATE credit_accounts SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()

def get_upcoming_income(days: int = 30):
    """Get expected income in next X days"""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today()
    cursor.execute('''
        SELECT * FROM income 
        WHERE status = 'expected' AND date_expected >= ?
        ORDER BY date_expected
    ''', (today,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def get_recent_income(days: int = 30):
    """Get recently received income in last X days"""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_date = date.today() - timedelta(days=days)
    cursor.execute('''
        SELECT * FROM income 
        WHERE status = 'received' AND date_received >= ?
        ORDER BY date_received DESC
    ''', (cutoff_date,))
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_income(source: str, amount: float, date_expected: date, status: str = 'expected'):
    """Add expected or received income"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO income (source, amount, date_expected, status)
        VALUES (?, ?, ?, ?)
    ''', (source, amount, date_expected, status))
    conn.commit()
    conn.close()

def mark_income_received(income_id: int, date_received: date):
    """Mark income as received"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE income 
        SET status = 'received', date_received = ?
        WHERE id = ?
    ''', (date_received, income_id))
    conn.commit()
    conn.close()

def get_property_transactions(months: int = 3):
    """Get property transactions for last X months"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM property_transactions
        ORDER BY date DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_property_transaction(transaction_type: str, description: str, 
                            amount: float, date: date, category: str = None):
    """Add property transaction"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO property_transactions 
        (transaction_type, description, amount, date, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (transaction_type, description, amount, date, category))
    conn.commit()
    conn.close()

# DELETE FUNCTIONS
def delete_bill(bill_id: int):
    """Delete a bill"""
    conn = get_connection()
    cursor = conn.cursor()
    # Delete past due instances first
    cursor.execute('DELETE FROM past_due_instances WHERE bill_id = ?', (bill_id,))
    cursor.execute('DELETE FROM bills WHERE id = ?', (bill_id,))
    conn.commit()
    conn.close()

def delete_credit_account(account_id: int):
    """Delete a credit account"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM credit_accounts WHERE id = ?', (account_id,))
    conn.commit()
    conn.close()

def delete_property_transaction(transaction_id: int):
    """Delete a property transaction"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM property_transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()

def delete_income(income_id: int):
    """Delete an income record"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM income WHERE id = ?', (income_id,))
    conn.commit()
    conn.close()

# PAST DUE INSTANCE FUNCTIONS
def get_past_due_instances(bill_id: int = None, credit_account_id: int = None):
    """Get all past due instances, optionally for a specific bill or credit account"""
    conn = get_connection()
    cursor = conn.cursor()
    if bill_id:
        cursor.execute('''
            SELECT pdi.*, b.name as item_name, 'bill' as item_type
            FROM past_due_instances pdi
            JOIN bills b ON pdi.bill_id = b.id
            WHERE pdi.bill_id = ?
            ORDER BY pdi.period DESC
        ''', (bill_id,))
    elif credit_account_id:
        cursor.execute('''
            SELECT pdi.*, ca.name as item_name, 'credit' as item_type
            FROM past_due_instances pdi
            JOIN credit_accounts ca ON pdi.credit_account_id = ca.id
            WHERE pdi.credit_account_id = ?
            ORDER BY pdi.period DESC
        ''', (credit_account_id,))
    else:
        # Get all, from both bills and credit accounts
        cursor.execute('''
            SELECT pdi.id, pdi.bill_id, pdi.credit_account_id, pdi.period, pdi.amount, pdi.created_date,
                   COALESCE(b.name, ca.name) as item_name,
                   CASE WHEN pdi.bill_id IS NOT NULL THEN 'bill' ELSE 'credit' END as item_type
            FROM past_due_instances pdi
            LEFT JOIN bills b ON pdi.bill_id = b.id
            LEFT JOIN credit_accounts ca ON pdi.credit_account_id = ca.id
            ORDER BY pdi.period DESC
        ''')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_past_due_instance(bill_id: int = None, credit_account_id: int = None, period: str = None, amount: float = None):
    """Add a past due instance for bill or credit account"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO past_due_instances (bill_id, credit_account_id, period, amount)
        VALUES (?, ?, ?, ?)
    ''', (bill_id, credit_account_id, period, amount))
    conn.commit()
    conn.close()

def delete_past_due_instance(instance_id: int):
    """Delete a past due instance"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM past_due_instances WHERE id = ?', (instance_id,))
    conn.commit()
    conn.close()

# ==================== V6 NEW FUNCTIONS ====================

def get_settings():
    """Get user settings"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_settings WHERE id = 1')
    result = cursor.fetchone()
    conn.close()
    if result:
        return dict(result)
    return None

def update_settings(settings_data):
    """Update user settings"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in settings_data.items():
        if key in ['monthly_income', 'cushion_amount', 'checkpoint_mode', 'checkpoint_count', 
                   'custom_checkpoint_days', 'nys_payroll_start_date', 'dark_mode']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if fields:
        values.append(1)  # id
        query = f"UPDATE user_settings SET {', '.join(fields)}, last_updated = CURRENT_TIMESTAMP WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

# Recurring Income Functions
def get_recurring_income():
    """Get all recurring income sources"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recurring_income WHERE active = 1 ORDER BY source')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_recurring_income(source, amount, frequency, start_date, end_date=None, day_of_month=None, notes=''):
    """Add recurring income source"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO recurring_income (source, amount, frequency, start_date, end_date, day_of_month, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (source, amount, frequency, start_date, end_date, day_of_month, notes))
    income_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return income_id

def update_recurring_income(income_id, **kwargs):
    """Update recurring income"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ['source', 'amount', 'frequency', 'start_date', 'end_date', 'day_of_month', 'notes', 'active']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if fields:
        values.append(income_id)
        query = f"UPDATE recurring_income SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

def delete_recurring_income(income_id):
    """Delete (deactivate) recurring income"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE recurring_income SET active = 0 WHERE id = ?', (income_id,))
    conn.commit()
    conn.close()
    return True

def generate_income_for_period(start_date, end_date):
    """Generate expected income entries for a date range from recurring income"""
    from datetime import timedelta
    import calendar
    
    recurring = get_recurring_income()
    generated = []
    
    for income in recurring:
        freq = income['frequency']
        source_start = datetime.strptime(income['start_date'], '%Y-%m-%d').date() if isinstance(income['start_date'], str) else income['start_date']
        source_end = datetime.strptime(income['end_date'], '%Y-%m-%d').date() if income['end_date'] and isinstance(income['end_date'], str) else None
        
        current = start_date
        while current <= end_date:
            # Skip if before start or after end
            if current < source_start:
                current = current + timedelta(days=1)
                continue
            if source_end and current > source_end:
                break
                
            should_generate = False
            
            if freq == 'bi-weekly':
                # Calculate weeks since start
                days_diff = (current - source_start).days
                if days_diff % 14 == 0:
                    should_generate = True
            elif freq == 'monthly' and income['day_of_month']:
                # Monthly on specific day
                if current.day == income['day_of_month']:
                    should_generate = True
            elif freq == 'weekly':
                # Weekly on same weekday
                if current.weekday() == source_start.weekday():
                    should_generate = True
                    
            if should_generate:
                generated.append({
                    'source': income['source'],
                    'amount': income['amount'],
                    'date_expected': current,
                    'recurring_id': income['id']
                })
            
            current = current + timedelta(days=1)
    
    return generated

# Category Functions
def get_categories():
    """Get all categories"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY sort_order, name')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_category(name, emoji='📁', type='expense'):
    """Add new category"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(sort_order) FROM categories')
    max_order = cursor.fetchone()[0] or 0
    cursor.execute('''
        INSERT INTO categories (name, emoji, type, sort_order)
        VALUES (?, ?, ?, ?)
    ''', (name, emoji, type, max_order + 1))
    cat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return cat_id

def update_category(cat_id, name=None, emoji=None):
    """Update category"""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    if name:
        updates.append('name = ?')
        values.append(name)
    if emoji:
        updates.append('emoji = ?')
        values.append(emoji)
    
    if updates:
        values.append(cat_id)
        query = f"UPDATE categories SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

def delete_category(cat_id):
    """Delete category (only if not in use)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if in use
    cursor.execute('SELECT COUNT(*) FROM bills WHERE category = (SELECT name FROM categories WHERE id = ?)', (cat_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return False
    
    cursor.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
    conn.commit()
    conn.close()
    return True

# Batch Operations
def mark_bills_paid_for_period(start_date, end_date):
    """Mark all bills in a period as paid"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE bills 
        SET status = 'paid', last_paid_date = CURRENT_DATE
        WHERE status IN ('pending', 'overdue')
        AND ((due_date BETWEEN ? AND ?) OR 
             (due_day IS NOT NULL AND frequency = 'monthly'))
    ''', (start_date, end_date))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def clear_paid_bills(before_date=None):
    """Archive/clear old paid bills"""
    conn = get_connection()
    cursor = conn.cursor()
    if before_date:
        cursor.execute('''
            DELETE FROM bills 
            WHERE status = 'paid' 
            AND last_paid_date < ?
            AND frequency = 'one-time'
        ''', (before_date,))
    else:
        cursor.execute('''
            DELETE FROM bills 
            WHERE status = 'paid' 
            AND frequency = 'one-time'
        ''')
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

# ==================== V6.4: CREDIT PAYMENT OVERRIDES ====================

def get_payment_override(credit_account_id, month, year):
    """Get payment override for specific month/year"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM credit_payment_overrides
        WHERE credit_account_id = ? AND month = ? AND year = ?
    ''', (credit_account_id, month, year))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def set_payment_override(credit_account_id, month, year, override_amount):
    """Set or update payment override"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO credit_payment_overrides 
        (credit_account_id, month, year, override_amount)
        VALUES (?, ?, ?, ?)
    ''', (credit_account_id, month, year, override_amount))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def delete_payment_override(credit_account_id, month, year):
    """Delete payment override"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM credit_payment_overrides
        WHERE credit_account_id = ? AND month = ? AND year = ?
    ''', (credit_account_id, month, year))
    conn.commit()
    conn.close()

# ==================== V6.4: PROPERTY UNIT STATUS ====================

def get_all_units():
    """Get all property units"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM property_unit_status ORDER BY unit_number')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_unit(unit_number, status='vacant', monthly_rent=None, tenant_name=None, 
             lease_start=None, lease_end=None, notes=None):
    """Add new property unit"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO property_unit_status 
        (unit_number, status, monthly_rent, tenant_name, lease_start, lease_end, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (unit_number, status, monthly_rent, tenant_name, lease_start, lease_end, notes))
    conn.commit()
    unit_id = cursor.lastrowid
    conn.close()
    return unit_id

def update_unit(unit_id, **kwargs):
    """Update property unit"""
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed_fields = ['unit_number', 'status', 'monthly_rent', 'tenant_name', 
                     'lease_start', 'lease_end', 'notes']
    updates = []
    values = []
    
    for field in allowed_fields:
        if field in kwargs:
            updates.append(f'{field} = ?')
            values.append(kwargs[field])
    
    if updates:
        values.append(unit_id)
        query = f"UPDATE property_unit_status SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

def delete_unit(unit_id):
    """Delete property unit"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM property_unit_status WHERE id = ?', (unit_id,))
    conn.commit()
    conn.close()

# ==================== V6.4: PROPERTY REPAIR ESTIMATES ====================

def get_all_repairs():
    """Get all repair estimates"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM property_repair_estimates ORDER BY date_created DESC')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_repair(description, estimated_cost=None, unit_number=None, contractor=None, notes=None):
    """Add new repair estimate"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO property_repair_estimates 
        (unit_number, description, estimated_cost, contractor, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (unit_number, description, estimated_cost, contractor, notes))
    conn.commit()
    repair_id = cursor.lastrowid
    conn.close()
    return repair_id

def update_repair(repair_id, **kwargs):
    """Update repair estimate"""
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed_fields = ['unit_number', 'description', 'estimated_cost', 'actual_cost',
                     'contractor', 'status', 'date_completed', 'notes']
    updates = []
    values = []
    
    for field in allowed_fields:
        if field in kwargs:
            updates.append(f'{field} = ?')
            values.append(kwargs[field])
    
    if updates:
        values.append(repair_id)
        query = f"UPDATE property_repair_estimates SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    return True

def delete_repair(repair_id):
    """Delete repair estimate"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM property_repair_estimates WHERE id = ?', (repair_id,))
    conn.commit()
    conn.close()

# ==================== V6.4: PROPERTY INCOME PROJECTIONS ====================

def get_all_income_projections():
    """Get all income projections"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM property_income_projections ORDER BY year, month')
    results = cursor.fetchall()
    conn.close()
    return [dict(row) for row in results]

def add_income_projection(month, year, projected_income, actual_income=None, notes=None):
    """Add or update income projection"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO property_income_projections 
        (month, year, projected_income, actual_income, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (month, year, projected_income, actual_income, notes))
    conn.commit()
    proj_id = cursor.lastrowid
    conn.close()
    return proj_id

def delete_income_projection(month, year):
    """Delete income projection"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM property_income_projections 
        WHERE month = ? AND year = ?
    ''', (month, year))
    conn.commit()
    conn.close()

def reset_monthly_bills():
    """Reset all monthly bills to pending for new month"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE bills 
        SET status = 'pending'
        WHERE frequency = 'monthly'
        AND status = 'paid'
    ''')
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

if __name__ == '__main__':
    init_database()
    print("Database initialized successfully!")
