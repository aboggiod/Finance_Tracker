# Financial Dashboard V5.0 - Full CRUD + Enhanced Checkpoints

## 🎯 Major Features

### Full CRUD Operations
- **Create**: Add new bills, credit accounts, loans, and property transactions via modals
- **Read**: Enhanced displays with better date formatting
- **Update**: Edit any item with modern modal interface (from V4.5)
- **Delete**: Remove any item with confirmation dialogs

### Enhanced Checkpoint Breakdown
- Shows full financial math for each checkpoint:
  - Current available balance
  - Paychecks arriving during period (with dates)
  - Bills due during period (with dates)
  - How much Drew can cover
  - How much Mom needs to add
- Fixed paycheck display to show only paychecks for THAT specific period
- Added due dates to bills in checkpoint dropdowns

### One-Time Expenses
- New "One-time" frequency option for bills
- Uses date picker instead of due_day for one-time items
- Automatically shows in appropriate checkpoint based on date

### Past Due Instance Management
- Track multiple past due instances for the same bill
- Example: Rent can be past due for Oct, Nov, and upcoming in Dec
- Manage via edit modal with dedicated "Manage Past Due" button
- Past due instances shown separately on dashboard in red
- Total past due amount calculated and displayed

## 🔧 Technical Updates

### Database Changes
- Added `past_due_instances` table
- Fixed timedelta import (`from datetime import *`)
- Added delete functions for all entities
- Added past due management functions

### New Routes
**Create:**
- POST `/api/bill` - Create new bill
- POST `/api/credit` - Create credit account/loan
- POST `/api/property` - Create property transaction

**Delete:**
- DELETE `/api/bill/<id>` - Delete bill
- DELETE `/api/credit/<id>` - Delete credit account
- DELETE `/api/property/<id>` - Delete property transaction
- DELETE `/api/income/<id>` - Delete income record

**Past Due:**
- GET `/api/bill/<id>/past-due` - Get past due instances
- POST `/api/bill/<id>/past-due` - Add past due instance
- DELETE `/api/past-due/<id>` - Delete past due instance

### UI Updates
- Balance update button now small pencil icon (not giant button)
- Add buttons on all major sections (+ Add Bill, + Add Account, etc.)
- Delete buttons (🗑️) on every item with confirmation
- Past due management button (⚠️) in bill edit modal
- Date pickers throughout for better UX

### JavaScript Updates
- `createBill()` - Modal for creating bills with frequency toggle
- `createCreditAccount()` - Modal for creating accounts
- `createPropertyTransaction()` - Modal for property transactions
- `managePastDue()` - Modal for managing past due instances
- `toggleBillDateFields()` - Switch between due_day and due_date based on frequency

## 📋 Files Modified
- `database.py` - New table, delete functions, past due functions
- `app.py` - New routes, updated checkpoint logic
- `dashboard.js` - Create functions, past due management
- `style.css` - Icon button styling
- `dashboard.html` - Enhanced checkpoints, balance button, past due display
- `credit.html` - Add/delete buttons
- `bills.html` - Add/delete buttons
- `property.html` - Add/delete buttons

## 🚀 Installation
1. Extract zip file
2. Replace your financial-dashboard folder
3. Run `python app.py`
4. Database will auto-initialize with new table

## ✨ Key Features Summary
- ✅ Full CRUD everywhere
- ✅ One-time expense support
- ✅ Multiple past due instances per bill
- ✅ Enhanced checkpoint breakdown with full math
- ✅ Paychecks show dates and only for relevant period
- ✅ Bills in checkpoints show due dates
- ✅ Modern modal-based interface
- ✅ Confirmation dialogs for deletions
- ✅ Small pencil icon for balance update

## 🔜 Not Yet Included
- Plaid integration (planned for V6)
