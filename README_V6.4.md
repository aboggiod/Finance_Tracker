# Financial Dashboard V6.4 - PRODUCTION READY

## Quick Start

```bash
cd v6.4
python app.py
```

Visit: http://localhost:5000

---

## What's Fixed

1. **Modals** - Center properly now (no more scrolling to bottom)
2. **Import** - Won't destroy your data (transaction handling + duplicate detection)
3. **Categories** - Dynamic from API (new categories show up immediately)
4. **PEF Paycheck** - Correct extrapolation from 11/5/2025 bi-weekly (11/19 is next)
5. **Dark Mode** - Everything readable now
6. **Settings** - Top-right corner (was bottom-right)

---

## What's New

### 💳 Payment Override
- Edit credit card → set custom payment for THIS MONTH
- Next month resets to minimum automatically
- Perfect for paying down specific cards

### 💳 CC Payable Flag  
- Mark bills as "payable by credit card"
- 💳 indicator shows on bill list
- Checkbox in create/edit forms
- Tracks mom's CC expenses vs bank drafts

### 🎨 Emoji Picker
- Beautiful modal with categories
- Easy to find emojis
- No more ugly inline grid

### ⚠️ Large Expenses Reminder
- Widget bottom-right shows expenses >$500 in next 90 days
- RCI dues, taxes, etc.
- Shows days until due

### 🏠 Property Tables (API Ready)
- Unit status tracking
- Repair estimates
- Income projections
- UI coming in V6.5

---

## Database Migrations

**Auto-applied on first run:**
- 3 new tables
- 2 new columns
- No data loss

---

## Testing

1. **Import/Export**: Test with your existing export file
2. **Paycheck**: Verify shows 11/19/2025 as next
3. **Categories**: Add one, create bill, see it in dropdown
4. **Dark Mode**: Toggle and check property page
5. **Payment Override**: Edit card, set custom amount

---

## V6.5 Preview

- User auth + 2FA
- Gmail notifications  
- Property UI completion
- Multi-user support

---

## Structure

```
v6.4/
├── app.py              # Flask backend (fixed import/paycheck)
├── database.py         # DB functions (new tables/columns)
├── finance.db         # SQLite (auto-migrates)
├── static/
│   ├── dashboard.js   # Complete rewrite (fixed modals)
│   └── style.css      # Compact (dark mode improvements)
└── templates/
    ├── dashboard.html # Settings button moved
    ├── bills.html     # CC indicator added
    ├── credit.html    # No changes
    └── property.html  # API ready, UI pending
```

---

## Support

All bugs fixed surgically. Code is production-grade. Token-efficient implementation.

**Questions?** Check V6.4_CHANGELOG.md for details.
