from database import *
from datetime import date, timedelta

def populate_initial_data():
    """Populate database with Drew's actual financial data"""
    
    print("Initializing database...")
    init_database()
    
    print("Setting initial Wells Fargo balance...")
    # Set initial balance (update this as needed)
    update_account_balance(0.00)
    
    print("Adding bills...")
    
    # Housing
    add_bill("Rent", "Housing", 1800.00, 1, "monthly", True)
    
    # Utilities
    add_bill("Spectrum", "Utilities", 85.00, 10, "monthly", True)
    add_bill("National Grid", "Utilities", 165.00, 30, "monthly", True)
    add_bill("Visible (Cell Phone)", "Utilities", 30.00, 2, "monthly", True)
    
    # Insurance
    add_bill("AVA Insurance", "Insurance", 105.00, 2, "monthly", True)
    add_bill("Building Insurance", "Insurance", 427.45, None, "bi-monthly", True, date(2025, 12, 5))
    add_bill("Renters Insurance", "Insurance", 52.00, 10, "monthly", True)
    add_bill("Auto Insurance", "Insurance", 3468.00, None, "semi-annual", True, date(2026, 4, 13))
    add_bill("Life Insurance", "Insurance", 874.80, None, "annual", True, date(2026, 7, 4))
    
    # Subscriptions
    add_bill("Apple Subscriptions", "Subscriptions", 32.46, 25, "monthly", True)
    add_bill("Planet Fitness", "Subscriptions", 27.00, 17, "monthly", True)
    add_bill("RCI Membership", "Subscriptions", 388.00, None, "triennial", True, date(2028, 3, 31))
    add_bill("RCI Maintenance Fees", "Subscriptions", 1150.00, None, "annual", True, date(2025, 12, 31))
    
    # Personal Expenses (split evenly across checkpoints)
    # Total: $1,195/month = Food ($500) + Gas ($120) + Weed ($150) + Vapes ($200) + Random subs ($125) + Claude ($100)
    # Split: $398.33 per checkpoint (1st, 10th, 20th)
    add_bill("Personal Expenses", "Personal", 398.33, 1, "monthly", False)
    add_bill("Personal Expenses", "Personal", 398.33, 10, "monthly", False)
    add_bill("Personal Expenses", "Personal", 398.34, 20, "monthly", False)  # Extra penny for rounding
    
    print("Adding credit accounts...")
    
    # Credit Cards
    credit_cards = [
        ("Credit One American Express", "credit_card", 297.00, 300.00, 30.00, 28.74, 15, 11),
        ("Credit One Visa", "credit_card", 622.00, 600.00, 30.00, 29.49, 15, 11),
        ("Milestone - 1", "credit_card", 698.00, 700.00, 47.00, 35.90, 3, 2),
        ("Indigo", "credit_card", 698.00, 700.00, 40.00, 35.90, 3, 2),
        ("Milestone - 2", "credit_card", 496.00, 500.00, 40.00, 29.90, 19, 18),
        ("Destiny", "credit_card", 562.00, 500.00, 40.00, 35.90, 5, 14),
        ("Imagine", "credit_card", 246.38, 400.00, 40.00, 36.00, 5, 2),
        ("Fortiva", "credit_card", 780.74, 800.00, 45.00, 36.00, 14, 11),
        ("Avant", "credit_card", 318.00, 300.00, 25.00, 35.99, 5, 1),
        ("Fit Mastercard", "credit_card", 304.02, 400.00, 45.00, 35.90, 7, 4),
        ("Amazon", "credit_card", 743.80, 750.00, 27.00, 10.00, 30, 23),
        ("Kohls", "credit_card", 218.13, 300.00, 29.00, 30.24, 16, 11),
        ("Target", "credit_card", 271.21, 400.00, 30.00, 28.95, 15, 13),
        ("Wards", "credit_card", 0.00, 900.00, 25.00, 25.99, 7, 5),
        ("Fingerhut", "credit_card", 538.56, 1000.00, 41.00, 35.99, 12, 11),
        ("Country Door", "credit_card", 0.00, 850.00, 20.00, 35.99, 7, 5),
        ("Firestone", "credit_card", 169.94, 700.00, 64.00, 34.99, 23, 18),
    ]
    
    for card in credit_cards:
        add_credit_account(*card)
    
    # Loans
    add_credit_account("21 Central Mortgage", "loan", 124156.49, None, 867.90, 4.25, None, 15)
    add_credit_account("Crescent Bay (Car)", "loan", 26551.79, None, 681.18, 22.60, None, 25)
    add_credit_account("Driveway (Car)", "loan", 26290.74, None, 839.11, 22.44, None, 25)
    
    print("Adding expected income (next 3 paychecks)...")
    
    # Calculate next 3 paycheck dates (bi-weekly on Wednesdays)
    today = date.today()
    # Find next Wednesday
    days_until_wednesday = (2 - today.weekday()) % 7
    if days_until_wednesday == 0:
        days_until_wednesday = 7
    
    next_paycheck = today + timedelta(days=days_until_wednesday)
    
    for i in range(3):
        paycheck_date = next_paycheck + timedelta(weeks=i*2)
        add_income("NYS ITS Paycheck", 941.17, paycheck_date, "expected")
    
    print("Adding tax obligations...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 2025 Property Tax
    cursor.execute('''
        INSERT INTO tax_obligations 
        (tax_type, amount_due, due_date, payment_plan, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("2025 Property Tax", 4461.47, date(2025, 12, 1), 0, "pending", 
          "1% interest monthly if not paid by 12/1"))
    
    # Back Taxes (to be negotiated into payment plan)
    cursor.execute('''
        INSERT INTO tax_obligations 
        (tax_type, amount_due, due_date, payment_plan, monthly_payment, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ("Back Taxes (2022-2024)", 38169.44, date(2026, 12, 1), 1, 1060.00, "pending",
          "Payment plan to be negotiated after 2025 taxes paid. Estimated 3-year plan at ~$1,060/month"))
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database populated successfully!")
    print("\nSummary:")
    print(f"- Bills added: {len(get_all_bills())}")
    print(f"- Credit accounts added: {len(get_all_credit_accounts())}")
    print(f"- Upcoming income entries: {len(get_upcoming_income(90))}")
    
    utilization = get_credit_utilization()
    if utilization:
        print(f"\n💳 Current Credit Utilization: {utilization['utilization_percent']}%")
        print(f"   Total Balance: ${utilization['total_balance']:,.2f}")
        print(f"   Total Limit: ${utilization['total_limit']:,.2f}")

if __name__ == '__main__':
    populate_initial_data()
