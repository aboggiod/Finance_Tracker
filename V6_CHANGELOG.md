# Financial Dashboard V6 - Major Feature Release

## 🚀 Overview
V6 combines V5.5 checkpoint flexibility with comprehensive settings management, recurring income, batch operations, and quality-of-life improvements.

## 🎯 Major Features

### 1. Settings System
- **User Settings Table**: Configurable income, cushion, checkpoints
- **Settings Modal**: Easy configuration from any page
- **No More Hardcoding**: All values now user-configurable
- Settings persist across sessions

### 2. Checkpoint System Overhaul
- **Three Modes**:
  - **1-10-20**: Traditional 1st, 10th, 20th of month
  - **NYS Payroll**: Bi-weekly Wednesdays (ITS2 PEF admin schedule)
  - **Custom**: Any days you want (e.g., 5, 15, 25)
- **Variable Count**: Show 1-10 checkpoints (was fixed at 3)
- **Future-Proof**: Easy to add new checkpoint modes

### 3. Recurring Income Management
- **Auto-Generation**: Set up recurring income sources
- **Frequencies**: Weekly, bi-weekly, monthly
- **Smart Tracking**: Automatically shows in upcoming checkpoints
- **Examples**: 
  - Drew's Paycheck: $941.17 bi-weekly
  - Mom's Contribution: Monthly support

### 4. Custom Categories
- **Add/Edit/Delete**: Manage your own categories
- **Emoji Support**: Visual organization
- **Default Categories**: Housing 🏠, Utilities 💡, Phone 📱, etc.
- **Sort Order**: Organized display

### 5. Quick Actions (Batch Operations)
- **Mark Period Paid**: Batch mark bills for a checkpoint
- **Clear Paid Bills**: Archive old paid one-time bills
- **Reset Monthly**: Reset all monthly bills to pending
- **One-Click Operations**: Save time on routine tasks

### 6. Search & Filter
- **Bills Page**: Search across all bills instantly
- **Credit Page**: Filter 20+ credit accounts easily
- **Real-Time**: Instant filtering as you type
- **No Page Reload**: Smooth, responsive experience

### 7. Notes Visibility
- **Bills Notes**: Now visible in edit modals
- **Credit Notes**: Track special instructions
- **Example**: "This card is for gas only"
- **Already in DB**: Just surfaced in UI

### 8. Dark Mode
- **Toggle Switch**: Easy on/off
- **Full Theme**: Complete dark UI
- **Persistent**: Remembers your preference
- **Eye-Friendly**: Reduces strain at night

### 9. Export Data (CSV)
- **Bills Export**: Download all bills data
- **Credit Export**: Export credit accounts
- **Income Export**: Export income records
- **Backup Ready**: Keep local copies

### 10. Balance Display Cleanup
- **Simplified**: Shows "Available Balance" only
- **No Math**: Cushion calculated behind scenes
- **Hover Details**: See actual/cushion on hover
- **Cleaner UI**: Less visual clutter

## 🔧 Technical Changes

### Database Schema
```sql
-- New tables
user_settings (monthly_income, cushion_amount, checkpoint_mode, etc.)
recurring_income (source, amount, frequency, start_date)
categories (name, emoji, type, sort_order)
```

### API Routes Added
- `/api/settings` - GET/PUT user settings
- `/api/recurring-income` - CRUD for recurring income
- `/api/categories` - CRUD for categories
- `/api/batch/*` - Batch operations
- `/api/export/<type>` - CSV exports

### Files Modified
- `database.py` - New tables, functions for V6 features
- `app.py` - Modular checkpoints, new API routes
- `dashboard.js` - Settings modal, batch ops, search
- `style.css` - Dark mode, new components
- `dashboard.html` - Settings button, quick actions
- `bills.html` - Search bar, searchable rows
- `credit.html` - Search functionality

## 📋 NYS Payroll Dates (2025)
- Jan: 1, 15, 29
- Feb: 12, 26
- Mar: 12, 26
- Apr: 9, 23
- May: 7, 21
- Jun: 4, 18
- (Full calendar integrated)

## ✨ User Benefits
- **Flexibility**: Configure everything to your needs
- **Efficiency**: Batch operations save time
- **Visibility**: See notes, search instantly
- **Comfort**: Dark mode for night use
- **Control**: Export your data anytime
- **Automation**: Recurring income tracks itself

## 🚀 Installation
1. Extract V6 zip file
2. Replace your financial-dashboard folder
3. Run: `python app.py`
4. Database auto-migrates with new tables
5. Access Settings via ⚙️ button

## 💡 Quick Start
1. Click ⚙️ Settings button
2. Set your monthly income (default: $1,882.34)
3. Adjust cushion if needed (default: $500)
4. Choose checkpoint mode (1-10-20, NYS, or Custom)
5. Set up recurring income sources
6. Try dark mode!

## 🎉 V6 Summary
- ✅ Complete checkpoint flexibility
- ✅ No more hardcoded values
- ✅ Recurring income automation
- ✅ Custom categories
- ✅ Batch operations
- ✅ Search everything
- ✅ Dark mode
- ✅ Export data
- ✅ Notes visible
- ✅ Clean balance display

## Notes
- All existing data preserved
- Settings default to previous hardcoded values
- Dark mode preference persists
- Export creates standard CSV files
- Search is case-insensitive
- Categories can't be deleted if in use
