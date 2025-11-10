# Financial Command Center

A lightweight Flask web application to manage your financial recovery plan.

## What's In The Box

- **Dashboard**: Real-time balance, checkpoint requirements, past due alerts
- **Credit Overview**: All credit accounts, utilization tracking, payoff strategy  
- **Property Tracker**: 21 Central income/expenses, unit status, projections
- **Bills Manager**: All bills organized by category

## Setup & Run

### First Time Setup
```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Initialize database (ALREADY DONE - your data is loaded!)
# python populate_data.py

# Run the app
python app.py
```

### Every Time After
```bash
python app.py
```

Then open your browser to: **http://localhost:5000**

## Your Data

The database (`finance.db`) is already populated with:
- ✅ All 19 bills
- ✅ All 20 credit accounts (17 cards + 3 loans)
- ✅ Next 3 paychecks scheduled
- ✅ Tax obligations ($4,461 + $38,169)
- ✅ Current credit utilization: **68.9%**

## Key Features

### Dashboard
- Wells Fargo balance (with $500 cushion calculation)
- Upcoming checkpoints (1st, 10th, 20th of month)
- Shows exactly what mom needs to transfer and when
- Past due alerts at the top
- Credit utilization snapshot
- Monthly obligation totals

### Checkpoint System
The app calculates three things:
1. Bills due from now until the checkpoint
2. Your paychecks that will arrive before then
3. **The gap** = how much mom needs to send

### Credit Overview
- All cards sorted by utilization (worst first)
- Overall utilization percentage
- Payoff strategy to get under 30%
- Update balances as you pay them down

### Property Tracking
- Current status of all 3 units
- Monthly obligations breakdown
- Projected income when fully rented (~$2,318/month net)

## Quick Actions

**Update Wells Fargo Balance:**
- Right on the dashboard, purple card at top
- Enter new balance, click "Update Balance"

**Record Mom's Contribution:**
- Dashboard → "Upcoming Income" card
- Click "+ Record mom's contribution"
- Enter amount and date

**Update Credit Card Balance:**
- Credit → scroll to bottom
- Select card, enter new balance
- Click "Update"

## File Structure
```
financial-dashboard/
├── app.py              # Main Flask app
├── database.py         # All database functions
├── populate_data.py    # Initial data loader
├── finance.db          # SQLite database (YOUR DATA)
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── credit.html
│   ├── property.html
│   └── bills.html
└── README.md          # This file
```

## Important Notes

1. **Backup the database!** Copy `finance.db` regularly
2. **Update balance daily** for accurate checkpoint calculations
3. **The $500 cushion** is hardcoded but can be changed in database.py
4. **Plaid integration** is NOT included yet - that's Phase 2
5. **This runs locally** - only accessible on your computer for now

## Next Steps (Future)

- [ ] Plaid integration for automatic Wells Fargo balance
- [ ] Bill payment tracking/history
- [ ] Mom's login (separate view, read-only)
- [ ] Mobile responsive improvements
- [ ] Email/text alerts for checkpoints
- [ ] Deploy to cloud for shared access

## Troubleshooting

**Port 5000 already in use?**
Change the port in app.py, last line: `app.run(debug=True, port=5001)`

**Database not found?**
Run: `python populate_data.py` to recreate it

**Can't install Flask?**
Make sure you're using: `pip install -r requirements.txt --break-system-packages`

---

**You've got this, Drew. One day at a time.** 💪
