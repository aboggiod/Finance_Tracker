from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import *
from datetime import date, datetime, timedelta
from calendar import monthrange
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

def calculate_checkpoints(count=None, mode=None, custom_days=None, start_date=None):
    """Calculate checkpoint dates based on mode (1-10-20, nys-payroll, custom)"""
    from datetime import timedelta
    import json
    
    # Get settings if not provided
    settings = get_settings()
    if not count:
        count = settings.get('checkpoint_count', 3)
    if not mode:
        mode = settings.get('checkpoint_mode', '1-10-20')
    
    today = date.today()
    checkpoints = []
    
    if mode == '1-10-20':
        # Original logic for 1/10/20 checkpoints
        checkpoint_days = [1, 10, 20]
        for month_offset in range(6):  # Generate more to ensure we have enough
            target_date = today + timedelta(days=month_offset * 30)
            year = target_date.year
            month = target_date.month
            
            for day in checkpoint_days:
                try:
                    checkpoint_date = date(year, month, day)
                    if checkpoint_date >= today:
                        checkpoints.append(checkpoint_date)
                except ValueError:
                    pass  # Invalid date (e.g., Feb 31)
    
    elif mode == 'nys-payroll':
        # NYS Admin payroll: bi-weekly Wednesdays
        # Start from 11/5/2025 (last confirmed paycheck) and extrapolate forward
        from datetime import timedelta
        
        # PEF Admin payroll base date: 11/5/2025 (Wednesday)
        base_date = date(2025, 11, 5)
        
        # Go backwards to find earlier paychecks if needed
        current = base_date
        while current > date(2025, 1, 1):
            current = current - timedelta(days=14)
        
        # Now go forward from earliest 2025 date
        while len(checkpoints) < count * 3:  # Generate extra
            if current >= today:
                checkpoints.append(current)
            current = current + timedelta(days=14)
    
    elif mode == 'custom':
        # Custom days from settings
        if not custom_days:
            custom_days = settings.get('custom_checkpoint_days')
        if custom_days:
            days = json.loads(custom_days) if isinstance(custom_days, str) else custom_days
            for month_offset in range(6):
                target_date = today + timedelta(days=month_offset * 30)
                year = target_date.year
                month = target_date.month
                
                for day in days:
                    try:
                        checkpoint_date = date(year, month, int(day))
                        if checkpoint_date >= today:
                            checkpoints.append(checkpoint_date)
                    except ValueError:
                        pass
    
    # Sort and return requested count
    checkpoints.sort()
    return checkpoints[:count]

def get_bills_for_period(start_date, end_date):
    """Get all bills due between start and end date"""
    bills = get_all_bills()
    period_bills = []
    
    # Get last day of the target month
    last_day_of_month = monthrange(end_date.year, end_date.month)[1]
    
    for bill in bills:
        if bill['status'] in ['pending', 'overdue']:
            # Handle MONTHLY recurring bills with due_day
            if bill['due_day'] and bill['frequency'] == 'monthly':
                # Cap due_day at last day of month (e.g., 31 becomes 30 for November)
                actual_due_day = min(bill['due_day'], last_day_of_month)
                bill_date = date(end_date.year, end_date.month, actual_due_day)
                if start_date <= bill_date <= end_date:
                    bill['calculated_due_date'] = bill_date
                    period_bills.append(bill)
            # Handle bills with explicit due_date (one-time or non-monthly recurring)
            elif bill['due_date']:
                bill_due = datetime.strptime(bill['due_date'], '%Y-%m-%d').date()
                if start_date <= bill_due <= end_date:
                    bill['calculated_due_date'] = bill_due
                    period_bills.append(bill)
    
    # Add credit card minimum payments (always monthly)
    credit_accounts = get_all_credit_accounts()
    for account in credit_accounts:
        if account['minimum_payment'] and account['payment_due_day']:
            # Cap payment day at last day of month
            actual_payment_day = min(account['payment_due_day'], last_day_of_month)
            payment_date = date(end_date.year, end_date.month, actual_payment_day)
            if start_date <= payment_date <= end_date:
                period_bills.append({
                    'name': f"{account['name']} - Min Payment",
                    'amount': account['minimum_payment'],
                    'category': 'Debt',
                    'calculated_due_date': payment_date,
                    'is_credit_payment': True
                })
    
    return sorted(period_bills, key=lambda x: x['calculated_due_date'])

def calculate_checkpoint_requirements():
    """Calculate money needed for each checkpoint with full breakdown"""
    checkpoints = calculate_checkpoints()
    today = date.today()
    account = get_account_balance()
    
    # Use recurring income if available, otherwise fall back to regular income
    recurring = get_recurring_income()
    if recurring:
        # Generate income from recurring sources for next 90 days
        end_date = today + timedelta(days=90)
        upcoming_income = generate_income_for_period(today, end_date)
        # Convert to expected format
        formatted_income = []
        for inc in upcoming_income:
            formatted_income.append({
                'source': inc['source'],
                'amount': inc['amount'],
                'date_expected': inc['date_expected'].strftime('%Y-%m-%d') if isinstance(inc['date_expected'], date) else inc['date_expected']
            })
        upcoming_income = formatted_income
    else:
        upcoming_income = get_upcoming_income(90)
    
    checkpoint_data = []
    
    for i, checkpoint in enumerate(checkpoints):
        # Get bills due BETWEEN this checkpoint and the NEXT checkpoint
        start = checkpoint
        if i + 1 < len(checkpoints):
            end = checkpoints[i + 1] - timedelta(days=1)
        else:
            end = checkpoint + timedelta(days=9)
        
        bills = get_bills_for_period(start, end)
        
        # Add past due instances to bills for this checkpoint
        past_due_instances = get_past_due_instances()
        for instance in past_due_instances:
            bills.append({
                'name': f"{instance['item_name']} - {instance['period']} (PAST DUE)",
                'amount': instance['amount'],
                'category': 'Past Due',
                'calculated_due_date': start,  # Show at start of period
                'is_past_due': True
            })
        
        total_bills = sum(bill['amount'] for bill in bills)
        
        # Get paychecks arriving DURING THIS PERIOD ONLY
        period_paychecks = []
        for inc in upcoming_income:
            inc_date = datetime.strptime(inc['date_expected'], '%Y-%m-%d').date()
            if start <= inc_date <= end:
                period_paychecks.append({
                    'source': inc['source'],
                    'amount': inc['amount'],
                    'date': inc_date
                })
        
        period_income = sum(p['amount'] for p in period_paychecks)
        
        # Simple math: Drew's paychecks cover part, Mom covers the rest
        mom_needs = max(0, total_bills - period_income)
        
        days_away = (checkpoint - today).days
        status = 'good' if mom_needs == 0 else 'warning' if mom_needs < 1000 else 'critical'
        
        checkpoint_data.append({
            'date': checkpoint,
            'deadline': checkpoint - timedelta(days=1),
            'days_away': days_away,
            'bills': bills,
            'total_bills': total_bills,
            'period_paychecks': period_paychecks,
            'period_income': period_income,
            'mom_needs': mom_needs,
            'status': status,
            'period_end': end
        })
    
    return checkpoint_data

@app.route('/')
def dashboard():
    """Main dashboard view"""
    account = get_account_balance()
    settings = get_settings()  # Get user settings for income/cushion
    overdue = get_overdue_bills()
    past_due_instances = get_past_due_instances()  # Get all past due instances
    checkpoints = calculate_checkpoint_requirements()
    upcoming_income = get_upcoming_income(30)
    recent_income = get_recent_income(30)
    utilization = get_credit_utilization()
    
    # Calculate total monthly obligations
    all_bills = get_all_bills()
    monthly_bills_total = sum(bill['amount'] for bill in all_bills if bill['frequency'] == 'monthly')
    credit_minimums = sum(acc['minimum_payment'] for acc in get_all_credit_accounts())
    total_monthly = monthly_bills_total + credit_minimums
    
    # Update account with available balance (minus cushion)
    if account:
        account['available'] = account['balance'] - settings['cushion_amount']
    
    # Calculate tax interest
    from datetime import datetime
    now = datetime.now()
    if now.year == 2025:
        months_passed = now.month - 1
        tax_interest = 3900 * 0.01 * months_passed
        tax_total = 3900 + tax_interest
    else:
        tax_interest = 0
        tax_total = 3900
    
    return render_template('dashboard.html',
                         account=account,
                         settings=settings,
                         overdue=overdue,
                         past_due_instances=past_due_instances,
                         checkpoints=checkpoints,
                         upcoming_income=upcoming_income,
                         recent_income=recent_income,
                         utilization=utilization,
                         total_monthly=total_monthly,
                         tax_interest=tax_interest,
                         tax_total=tax_total)

@app.route('/credit')
def credit_overview():
    """Credit accounts overview"""
    accounts = get_all_credit_accounts()
    utilization = get_credit_utilization()
    
    # Separate cards and loans
    cards = [acc for acc in accounts if acc['account_type'] == 'credit_card']
    loans = [acc for acc in accounts if acc['account_type'] == 'loan']
    
    # Calculate utilization for each card
    for card in cards:
        if card['credit_limit']:
            card['utilization'] = round((card['current_balance'] / card['credit_limit']) * 100, 1)
        else:
            card['utilization'] = 0
    
    # Sort cards by utilization (highest first)
    cards.sort(key=lambda x: x['utilization'], reverse=True)
    
    return render_template('credit.html',
                         cards=cards,
                         loans=loans,
                         utilization=utilization)

@app.route('/property')
def property_overview():
    """Investment property overview"""
    transactions = get_property_transactions(6)
    
    # Calculate totals
    income = sum(t['amount'] for t in transactions if t['transaction_type'] == 'income')
    expenses = sum(t['amount'] for t in transactions if t['transaction_type'] == 'expense')
    net = income - expenses
    
    return render_template('property.html',
                         transactions=transactions,
                         income=income,
                         expenses=expenses,
                         net=net)

@app.route('/bills')
def bills_list():
    """All bills list"""
    bills = get_all_bills()
    
    # Group by category
    categories = {}
    for bill in bills:
        cat = bill['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(bill)
    
    # Calculate summary stats
    total_bills = len(bills)
    total_amount = sum(bill['amount'] for bill in bills if bill['frequency'] == 'monthly')
    autopay_count = sum(1 for bill in bills if bill['autopay'])
    manual_count = total_bills - autopay_count
    
    return render_template('bills.html', 
                         categories=categories,
                         total_bills=total_bills,
                         total_amount=total_amount,
                         autopay_count=autopay_count,
                         manual_count=manual_count)

@app.route('/update-balance', methods=['POST'])
def update_balance():
    """Update Wells Fargo balance"""
    balance = float(request.form.get('balance', 0))
    update_account_balance(balance)
    return redirect(url_for('dashboard'))

@app.route('/mark-paid/<int:bill_id>', methods=['POST'])
def mark_paid(bill_id):
    """Mark a bill as paid"""
    payment_date = date.today()
    mark_bill_paid(bill_id, payment_date)
    return redirect(url_for('dashboard'))

@app.route('/mark-overdue/<int:bill_id>', methods=['POST'])
def mark_overdue_route(bill_id):
    """Mark a bill as overdue"""
    mark_bill_overdue(bill_id)
    return redirect(url_for('dashboard'))

@app.route('/update-bill/<int:bill_id>', methods=['POST'])
def update_bill_route(bill_id):
    """Update a bill"""
    name = request.form.get('name')
    amount = float(request.form.get('amount')) if request.form.get('amount') else None
    due_day = int(request.form.get('due_day')) if request.form.get('due_day') else None
    frequency = request.form.get('frequency')
    autopay = request.form.get('autopay') == '1'
    status = request.form.get('status')
    
    update_bill(bill_id, name, amount, due_day, frequency, autopay, status)
    return redirect(url_for('bills_list'))

@app.route('/add-income', methods=['POST'])
def add_income_route():
    """Add mom's contribution"""
    source = request.form.get('source', 'Mom Contribution')
    amount = float(request.form.get('amount'))
    date_received = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO income (source, amount, date_received, status)
        VALUES (?, ?, ?, 'received')
    ''', (source, amount, date_received))
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/update-credit/<int:account_id>', methods=['POST'])
def update_credit_route(account_id):
    """Update credit account"""
    balance = float(request.form.get('balance')) if request.form.get('balance') else None
    limit = float(request.form.get('limit')) if request.form.get('limit') else None
    min_payment = float(request.form.get('min_payment')) if request.form.get('min_payment') else None
    apr = float(request.form.get('apr')) if request.form.get('apr') else None
    cycle_close_day = int(request.form.get('cycle_close_day')) if request.form.get('cycle_close_day') else None
    payment_due_day = int(request.form.get('payment_due_day')) if request.form.get('payment_due_day') else None
    
    update_credit_account(account_id, balance, limit, min_payment, apr, cycle_close_day, payment_due_day)
    return redirect(url_for('credit_overview'))

@app.template_filter('currency')
def currency_filter(value):
    """Format value as currency"""
    return f"${value:,.2f}"

@app.template_filter('date_format')
def date_format_filter(value):
    """Format date nicely"""
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d').date()
    return value.strftime('%b %d, %Y')

# JSON API Routes
@app.route('/api/balance', methods=['POST'])
def api_update_balance():
    try:
        data = request.get_json()
        balance = float(data['balance'])
        update_account_balance(balance)
        return jsonify({'success': True, 'message': 'Balance updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/credit/<int:account_id>', methods=['PUT'])
def api_update_credit(account_id):
    try:
        data = request.get_json()
        name = data.get('name')
        emoji = data.get('emoji')
        balance = float(data.get('balance', 0))
        limit = float(data.get('limit', 0)) if data.get('limit') else None
        min_payment = float(data.get('min_payment', 0))
        apr = float(data.get('apr', 0))
        
        # Fix int() conversion - handle None and empty strings
        cycle_close_day = data.get('cycle_close_day')
        if cycle_close_day is not None and cycle_close_day != '':
            cycle_close_day = int(cycle_close_day)
        else:
            cycle_close_day = 0
            
        payment_due_day = data.get('payment_due_day')
        if payment_due_day is not None and payment_due_day != '':
            payment_due_day = int(payment_due_day)
        else:
            payment_due_day = 0
        
        update_credit_account(account_id, name, emoji, balance, limit, min_payment, apr, cycle_close_day, payment_due_day)
        return jsonify({'success': True, 'message': 'Credit account updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/bill/<int:bill_id>', methods=['PUT'])
def api_update_bill(bill_id):
    try:
        data = request.get_json()
        name = data.get('name')
        emoji = data.get('emoji')
        amount = float(data.get('amount', 0))
        due_day = int(data.get('due_day', 0)) if data.get('due_day') else None
        frequency = data.get('frequency')
        autopay = data.get('autopay') == '1'
        status = data.get('status')
        
        update_bill(bill_id, name, emoji, amount, due_day, frequency, autopay, status)
        return jsonify({'success': True, 'message': 'Bill updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/income', methods=['POST'])
def api_add_income():
    try:
        data = request.get_json()
        source = data.get('source', 'Mom Contribution')
        amount = float(data['amount'])
        date_received = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO income (source, amount, date_received, status)
            VALUES (?, ?, ?, 'received')
        ''', (source, amount, date_received))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Contribution recorded'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# DELETE ROUTES
@app.route('/api/bill/<int:bill_id>', methods=['DELETE'])
def api_delete_bill(bill_id):
    try:
        delete_bill(bill_id)
        return jsonify({'success': True, 'message': 'Bill deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/credit/<int:account_id>', methods=['DELETE'])
def api_delete_credit(account_id):
    try:
        delete_credit_account(account_id)
        return jsonify({'success': True, 'message': 'Account deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/property/<int:transaction_id>', methods=['DELETE'])
def api_delete_property(transaction_id):
    try:
        delete_property_transaction(transaction_id)
        return jsonify({'success': True, 'message': 'Transaction deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/income/<int:income_id>', methods=['DELETE'])
def api_delete_income(income_id):
    try:
        delete_income(income_id)
        return jsonify({'success': True, 'message': 'Income record deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# CREATE ROUTES
@app.route('/api/bill', methods=['POST'])
def api_create_bill():
    try:
        data = request.get_json()
        name = data['name']
        category = data['category']
        amount = float(data['amount'])
        frequency = data.get('frequency', 'monthly')
        
        # Handle one-time vs recurring
        if frequency == 'one-time':
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            due_day = None
        else:
            due_day = int(data.get('due_day', 1))
            due_date = None
        
        autopay = data.get('autopay', False)
        
        add_bill(name, category, amount, due_day, frequency, autopay, due_date)
        return jsonify({'success': True, 'message': 'Bill created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/credit', methods=['POST'])
def api_create_credit():
    try:
        data = request.get_json()
        name = data['name']
        account_type = data['account_type']
        balance = float(data.get('balance', 0))
        limit = float(data['limit']) if data.get('limit') else None
        min_payment = float(data.get('min_payment', 0))
        apr = float(data.get('apr', 0))
        cycle_close_day = int(data.get('cycle_close_day', 1))
        payment_due_day = int(data.get('payment_due_day', 1))
        
        add_credit_account(name, account_type, balance, limit, min_payment, apr, cycle_close_day, payment_due_day)
        return jsonify({'success': True, 'message': 'Account created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/property', methods=['POST'])
def api_create_property():
    try:
        data = request.get_json()
        transaction_type = data['transaction_type']
        description = data['description']
        amount = float(data['amount'])
        trans_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        category = data.get('category', '')
        
        add_property_transaction(transaction_type, description, amount, trans_date, category)
        return jsonify({'success': True, 'message': 'Transaction created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# PAST DUE ROUTES
@app.route('/api/bill/<int:bill_id>/past-due', methods=['GET'])
def api_get_bill_past_due(bill_id):
    try:
        instances = get_past_due_instances(bill_id=bill_id)
        return jsonify({'success': True, 'instances': instances})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/credit/<int:account_id>/past-due', methods=['GET'])
def api_get_credit_past_due(account_id):
    try:
        instances = get_past_due_instances(credit_account_id=account_id)
        return jsonify({'success': True, 'instances': instances})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/bill/<int:bill_id>/past-due', methods=['POST'])
def api_add_bill_past_due(bill_id):
    try:
        data = request.get_json()
        period = data['period']
        amount = float(data['amount'])
        
        add_past_due_instance(bill_id=bill_id, period=period, amount=amount)
        return jsonify({'success': True, 'message': 'Past due instance added'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/credit/<int:account_id>/past-due', methods=['POST'])
def api_add_credit_past_due(account_id):
    try:
        data = request.get_json()
        period = data['period']
        amount = float(data['amount'])
        
        add_past_due_instance(credit_account_id=account_id, period=period, amount=amount)
        return jsonify({'success': True, 'message': 'Past due instance added'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/past-due/<int:instance_id>', methods=['DELETE'])
def api_delete_past_due(instance_id):
    try:
        delete_past_due_instance(instance_id)
        return jsonify({'success': True, 'message': 'Past due instance deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== V6 API ROUTES ====================

@app.route('/api/settings', methods=['GET', 'PUT'])
def api_settings():
    if request.method == 'GET':
        settings = get_settings()
        return jsonify(settings)
    else:
        try:
            data = request.get_json()
            update_settings(data)
            return jsonify({'success': True, 'message': 'Settings updated'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/recurring-income', methods=['GET', 'POST'])
def api_recurring_income():
    if request.method == 'GET':
        income = get_recurring_income()
        return jsonify(income)
    else:
        try:
            data = request.get_json()
            income_id = add_recurring_income(
                data['source'],
                float(data['amount']),
                data['frequency'],
                data['start_date'],
                data.get('end_date'),
                data.get('day_of_month'),
                data.get('notes', '')
            )
            return jsonify({'success': True, 'id': income_id})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/recurring-income/<int:income_id>', methods=['PUT', 'DELETE'])
def api_recurring_income_item(income_id):
    if request.method == 'PUT':
        try:
            data = request.get_json()
            update_recurring_income(income_id, **data)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    else:
        try:
            delete_recurring_income(income_id)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/categories', methods=['GET', 'POST'])
def api_categories():
    if request.method == 'GET':
        categories = get_categories()
        return jsonify(categories)
    else:
        try:
            data = request.get_json()
            cat_id = add_category(
                data['name'],
                data.get('emoji', '📁'),
                data.get('type', 'expense')
            )
            return jsonify({'success': True, 'id': cat_id})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/categories/<int:cat_id>', methods=['PUT', 'DELETE'])
def api_category(cat_id):
    if request.method == 'PUT':
        try:
            data = request.get_json()
            update_category(cat_id, data.get('name'), data.get('emoji'))
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    else:
        try:
            if delete_category(cat_id):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'message': 'Category in use'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/api/batch/mark-period-paid', methods=['POST'])
def api_mark_period_paid():
    try:
        data = request.get_json()
        count = mark_bills_paid_for_period(data['start_date'], data['end_date'])
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/batch/clear-paid', methods=['POST'])
def api_clear_paid():
    try:
        data = request.get_json()
        count = clear_paid_bills(data.get('before_date'))
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/batch/reset-monthly', methods=['POST'])
def api_reset_monthly():
    try:
        count = reset_monthly_bills()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/export/<data_type>', methods=['GET'])
def api_export(data_type):
    import csv
    from io import StringIO
    from flask import Response
    
    try:
        output = StringIO()
        
        if data_type == 'full':
            # Export ENTIRE database - all tables
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if table_name == 'sqlite_sequence':
                    continue
                
                # Write table separator
                output.write(f"\n=== TABLE: {table_name} ===\n")
                
                # Get all data from table
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                if rows:
                    # Get column names
                    columns = [description[0] for description in cursor.description]
                    
                    # Write as CSV
                    writer = csv.writer(output)
                    writer.writerow(columns)
                    for row in rows:
                        writer.writerow(row)
                
            conn.close()
            
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=full_database_export.csv'}
            )
            
        elif data_type == 'bills':
            bills = get_all_bills()
            writer = csv.writer(output)
            writer.writerow(['Name', 'Emoji', 'Category', 'Amount', 'Due Day', 'Due Date', 'Frequency', 'Status', 'Autopay', 'Notes'])
            for bill in bills:
                writer.writerow([
                    bill['name'], bill.get('emoji', ''), bill['category'], bill['amount'],
                    bill['due_day'], bill.get('due_date', ''), bill['frequency'], bill['status'],
                    'Yes' if bill['autopay'] else 'No', bill.get('notes', '')
                ])
        elif data_type == 'credit':
            accounts = get_all_credit_accounts()
            writer = csv.writer(output)
            writer.writerow(['Name', 'Emoji', 'Type', 'Balance', 'Limit', 'Min Payment', 'APR', 'Cycle Day', 'Due Day', 'Utilization'])
            for acc in accounts:
                util = (acc['current_balance'] / acc['credit_limit'] * 100) if acc['credit_limit'] else 0
                writer.writerow([
                    acc['name'], acc.get('emoji', ''), acc['account_type'], acc['current_balance'],
                    acc['credit_limit'], acc['minimum_payment'], acc['apr'],
                    acc.get('cycle_close_day', ''), acc.get('payment_due_day', ''), f"{util:.1f}%"
                ])
        else:
            return jsonify({'success': False, 'message': 'Invalid export type'})
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={data_type}_export.csv'}
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/import', methods=['POST'])
def api_import():
    """Import CSV data with transaction handling and duplicate detection"""
    import csv
    from io import StringIO
    
    try:
        file = request.files['file']
        content = file.read().decode('utf-8')
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Begin transaction
        cursor.execute('BEGIN TRANSACTION')
        
        current_table = None
        columns = None
        imported_count = 0
        skipped_count = 0
        
        for line in content.split('\n'):
            if line.startswith('=== TABLE:'):
                current_table = line.replace('=== TABLE:', '').replace('===', '').strip()
                columns = None
            elif current_table and line.strip():
                if not columns:
                    columns = line.strip().split(',')
                else:
                    values = list(csv.reader(StringIO(line)))[0] if line.strip() else []
                    if not values:
                        continue
                    
                    # Handle each table with appropriate logic
                    if current_table == 'account_balance':
                        cursor.execute('''
                            INSERT OR REPLACE INTO account_balance (id, balance, cushion, last_updated)
                            VALUES (?, ?, ?, ?)
                        ''', values[:4])
                        imported_count += 1
                        
                    elif current_table == 'user_settings':
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_settings 
                            (id, monthly_income, cushion_amount, checkpoint_mode, checkpoint_count, 
                             custom_checkpoint_days, nys_payroll_start_date, dark_mode, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', values[:9])
                        imported_count += 1
                        
                    elif current_table in ['bills', 'credit_accounts', 'income', 'recurring_income', 
                                          'categories', 'past_due_instances', 'property_transactions',
                                          'tax_obligations', 'property_unit_status', 
                                          'property_repair_estimates', 'property_income_projections',
                                          'credit_payment_overrides']:
                        # Check for duplicates before inserting
                        if current_table == 'bills' and len(values) > 1:
                            # Check if bill with same name exists
                            cursor.execute('SELECT id FROM bills WHERE name = ?', (values[1],))
                            if cursor.fetchone():
                                skipped_count += 1
                                continue
                        
                        if current_table == 'categories' and len(values) > 1:
                            # Check if category with same name exists
                            cursor.execute('SELECT id FROM categories WHERE name = ?', (values[1],))
                            if cursor.fetchone():
                                skipped_count += 1
                                continue
                        
                        # Insert with IGNORE to skip duplicates
                        placeholders = ','.join(['?' for _ in values])
                        try:
                            cursor.execute(f"INSERT INTO {current_table} ({','.join(columns)}) VALUES ({placeholders})", values)
                            imported_count += 1
                        except sqlite3.IntegrityError:
                            # Duplicate or constraint violation, skip
                            skipped_count += 1
                            continue
        
        # Commit transaction
        conn.commit()
        conn.close()
        
        message = f'Import successful! {imported_count} records imported'
        if skipped_count > 0:
            message += f', {skipped_count} duplicates skipped'
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        # Rollback on error
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return jsonify({'success': False, 'message': f'Import failed: {str(e)}'})

# ==================== V6.4: CREDIT PAYMENT OVERRIDE ENDPOINTS ====================

@app.route('/api/credit/<int:credit_id>/payment-override', methods=['GET', 'POST', 'DELETE'])
def credit_payment_override(credit_id):
    """Manage credit payment override for current month"""
    from datetime import date
    today = date.today()
    month, year = today.month, today.year
    
    if request.method == 'GET':
        override = get_payment_override(credit_id, month, year)
        return jsonify({'success': True, 'override': override})
    
    elif request.method == 'POST':
        data = request.json
        override_amount = data.get('override_amount')
        if not override_amount:
            return jsonify({'success': False, 'message': 'Override amount required'})
        
        set_payment_override(credit_id, month, year, override_amount)
        return jsonify({'success': True, 'message': 'Payment override set'})
    
    elif request.method == 'DELETE':
        delete_payment_override(credit_id, month, year)
        return jsonify({'success': True, 'message': 'Payment override removed'})

# ==================== V6.4: PROPERTY UNIT STATUS ENDPOINTS ====================

@app.route('/api/property/units', methods=['GET', 'POST'])
def property_units():
    """Get all units or create new unit"""
    if request.method == 'GET':
        units = get_all_units()
        return jsonify({'success': True, 'units': units})
    
    elif request.method == 'POST':
        data = request.json
        unit_id = add_unit(
            unit_number=data.get('unit_number'),
            status=data.get('status', 'vacant'),
            monthly_rent=data.get('monthly_rent'),
            tenant_name=data.get('tenant_name'),
            lease_start=data.get('lease_start'),
            lease_end=data.get('lease_end'),
            notes=data.get('notes')
        )
        return jsonify({'success': True, 'message': 'Unit added', 'id': unit_id})

@app.route('/api/property/units/<int:unit_id>', methods=['PUT', 'DELETE'])
def property_unit(unit_id):
    """Update or delete unit"""
    if request.method == 'PUT':
        data = request.json
        update_unit(unit_id, **data)
        return jsonify({'success': True, 'message': 'Unit updated'})
    
    elif request.method == 'DELETE':
        delete_unit(unit_id)
        return jsonify({'success': True, 'message': 'Unit deleted'})

# ==================== V6.4: PROPERTY REPAIR ESTIMATES ENDPOINTS ====================

@app.route('/api/property/repairs', methods=['GET', 'POST'])
def property_repairs():
    """Get all repairs or create new repair"""
    if request.method == 'GET':
        repairs = get_all_repairs()
        return jsonify({'success': True, 'repairs': repairs})
    
    elif request.method == 'POST':
        data = request.json
        repair_id = add_repair(
            description=data.get('description'),
            estimated_cost=data.get('estimated_cost'),
            unit_number=data.get('unit_number'),
            contractor=data.get('contractor'),
            notes=data.get('notes')
        )
        return jsonify({'success': True, 'message': 'Repair added', 'id': repair_id})

@app.route('/api/property/repairs/<int:repair_id>', methods=['PUT', 'DELETE'])
def property_repair(repair_id):
    """Update or delete repair"""
    if request.method == 'PUT':
        data = request.json
        update_repair(repair_id, **data)
        return jsonify({'success': True, 'message': 'Repair updated'})
    
    elif request.method == 'DELETE':
        delete_repair(repair_id)
        return jsonify({'success': True, 'message': 'Repair deleted'})

# ==================== V6.4: PROPERTY INCOME PROJECTIONS ENDPOINTS ====================

@app.route('/api/property/projections', methods=['GET', 'POST'])
def property_projections():
    """Get all projections or create new projection"""
    if request.method == 'GET':
        projections = get_all_income_projections()
        return jsonify({'success': True, 'projections': projections})
    
    elif request.method == 'POST':
        data = request.json
        proj_id = add_income_projection(
            month=data.get('month'),
            year=data.get('year'),
            projected_income=data.get('projected_income'),
            actual_income=data.get('actual_income'),
            notes=data.get('notes')
        )
        return jsonify({'success': True, 'message': 'Projection added', 'id': proj_id})

@app.route('/api/property/projections/<int:month>/<int:year>', methods=['DELETE'])
def property_projection(month, year):
    """Delete projection"""
    delete_income_projection(month, year)
    return jsonify({'success': True, 'message': 'Projection deleted'})

# ==================== V6.4: LARGE EXPENSES REMINDER ====================

@app.route('/api/large-expenses')
def large_expenses():
    """Get upcoming expenses > $500 in next 90 days"""
    from datetime import timedelta
    today = date.today()
    end_date = today + timedelta(days=90)
    
    large_expenses = []
    
    # Check bills
    bills = get_all_bills()
    for bill in bills:
        if bill['amount'] > 500:
            # Calculate next due date
            if bill['frequency'] == 'annual':
                # Add annual bills if within window
                if bill.get('due_date'):
                    due = datetime.strptime(bill['due_date'], '%Y-%m-%d').date()
                    if today <= due <= end_date:
                        large_expenses.append({
                            'type': 'bill',
                            'name': f"{bill.get('emoji', '📄')} {bill['name']}",
                            'amount': bill['amount'],
                            'due_date': due.isoformat(),
                            'days_until': (due - today).days
                        })
    
    # Check taxes
    taxes = get_all_taxes()
    for tax in taxes:
        if tax['amount_due'] > 500 and tax['status'] != 'paid':
            due = datetime.strptime(tax['due_date'], '%Y-%m-%d').date()
            if today <= due <= end_date:
                large_expenses.append({
                    'type': 'tax',
                    'name': f"💰 {tax['tax_type']}",
                    'amount': tax['amount_due'],
                    'due_date': due.isoformat(),
                    'days_until': (due - today).days
                })
    
    # Sort by due date
    large_expenses.sort(key=lambda x: x['due_date'])
    
    return jsonify({'success': True, 'expenses': large_expenses})

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE_NAME):
        print("Database not found. Please run populate_data.py first!")
    else:
        init_database()  # Ensure V6 tables exist
        app.run(debug=True, host='0.0.0.0', port=5000)
