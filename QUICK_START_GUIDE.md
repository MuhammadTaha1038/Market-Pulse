# Quick Start Guide - Color Processing System

## 🚀 Start the System

### 1. Start Backend
```powershell
cd "d:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main"
python handler.py
```
✅ Backend: `http://127.0.0.1:3334`

### 2. Start Frontend
```powershell
cd "d:\SKILL\watsapp project\fast api project\Data-main\market-pulse-main"
npm start
```
✅ Frontend: `http://localhost:4200`

---

## 🎯 Features & How to Use

### Feature 1: Dashboard Automation with Rules
**Location**: Dashboard → Right Panel

**"Refresh Colors Now" Button** (Gray)
- Triggers full automation
- Applies ranking engine
- Applies all exclusion rules
- Saves to output
- Auto-refreshes table

**Steps:**
1. Navigate to Dashboard
2. Click "Refresh Colors Now"
3. Toast: "Automation Started"
4. Wait for processing
5. Toast: "Automation Complete - Processed X colors"
6. Table refreshes automatically

---

### Feature 2: Override Processing (No Rules)
**Location**: Dashboard → Right Panel

**"Override & Run" Button** (Dark Gray)
- Processes ALL data
- Bypasses exclusion rules
- Emergency processing mode

**Steps:**
1. Navigate to Dashboard
2. Click "Override & Run"
3. Toast: "Override Mode - Running without rules"
4. Wait for processing
5. Toast: "Override Complete - Processed X colors"
6. Table shows all data (no exclusions)

---

### Feature 3: Manual Color Processing
**Location**: Manual Color Page (`/color-type`)

**Complete Workflow:**

#### Step 1: Import Excel
1. Click "Import via Excel" button
2. Select Excel file (.xlsx or .xls)
3. File uploads and processes
4. Toast: "Upload Successful - Imported X rows"
5. Preview table shows sorted data
6. Statistics banner appears

#### Step 2: Delete Rows (Optional)
1. Select rows using checkboxes
2. Click "Delete Selected" button (red)
3. Toast: "Rows Deleted - X remaining"
4. Table updates immediately

#### Step 3: Apply Rules (Optional)
1. Click "Select Rules" dropdown
2. Choose one or more rules
3. Click "Apply Rules" button
4. Toast: "Rules Applied - Excluded X rows"
5. Table shows filtered data

#### Step 4: Save to Output
1. Review final preview
2. Click "Run Automation" button (white with play icon)
3. Toast: "Save Successful - Saved X rows"
4. Session clears
5. Data saved to output file

---

## 📊 UI Elements Guide

### Dashboard Buttons
- **Refresh Colors Now** - Automation with rules
- **Override & Run** - Automation without rules
- **Import Sample** - Navigate to manual color page
- **Rules & Presets** - Navigate to settings
- **Cron Jobs & Time** - Navigate to cron settings

### Manual Color Page Buttons
- **Import via Excel** - Upload file dialog
- **Delete Selected** - Remove selected rows (red)
- **Select Rules** - Multi-select dropdown
- **Apply Rules** - Execute selected rules
- **Filters** - Apply presets (existing feature)
- **Run Automation** - Save to output (white)

### Statistics Banner
Shows in blue box after import:
- **File**: Uploaded filename
- **Total Rows**: All imported rows
- **Valid Rows**: Rows passing validation
- **Deleted Rows**: Manually deleted count
- **Rules Applied Count**: Number of rules executed

---

## 🔍 Testing Quick Checks

### Check 1: Backend Running
```powershell
curl "http://127.0.0.1:3334/api/manual-color/health"
```
Expected: `{"status": "healthy", "service": "Manual Color Processing"}`

### Check 2: Frontend Loaded
Open: `http://localhost:4200`
Expected: Login or Dashboard page

### Check 3: API Docs
Open: `http://127.0.0.1:3334/docs`
Expected: FastAPI Swagger UI with all endpoints

### Check 4: Dashboard Data
```powershell
curl "http://127.0.0.1:3334/api/dashboard/colors?skip=0&limit=5" | ConvertFrom-Json
```
Expected: Array of color records

---

## ⚠️ Common Issues & Quick Fixes

### Issue: "Failed to upload file"
- ✅ Check backend is running
- ✅ Verify file is .xlsx or .xls
- ✅ Check file size < 10MB

### Issue: "No active session"
- ✅ Import a file first
- ✅ Session is temporary (lost on page refresh)

### Issue: Toast notifications not showing
- ✅ Check browser console for errors
- ✅ Clear browser cache
- ✅ Refresh page

### Issue: Table not updating
- ✅ Check network tab for API responses
- ✅ Look for HTTP error codes
- ✅ Review browser console logs

### Issue: Rules not applying
- ✅ Verify rules exist: `http://127.0.0.1:3334/api/rules`
- ✅ Check rule conditions match your data
- ✅ Review backend logs

---

## 📁 File Locations

### Backend Files
```
sp-incb-market-pulse-master/src/main/
├── routers/
│   ├── manual_color.py           - Manual color API
│   ├── dashboard.py               - Dashboard API
│   └── cron_jobs.py               - Automation API
├── services/
│   ├── manual_color_service.py   - Manual processing logic
│   └── cron_service.py            - Automation logic
└── data/
    ├── output_colors.xlsx         - Processed output file
    └── temp_uploads/              - Temporary upload storage
```

### Frontend Files
```
market-pulse-main/src/app/
├── components/
│   ├── home/
│   │   ├── home.ts                - Dashboard component
│   │   └── home.html              - Dashboard template
│   └── manual-color/
│       ├── manual-color.ts        - Manual color component
│       └── manual-color.html      - Manual color template
└── services/
    ├── manual-color.service.ts    - Manual color API service
    └── automation.service.ts      - Automation API service
```

---

## 🧪 Quick Test Workflow

### Test 1: Dashboard Automation (2 minutes)
1. Start backend & frontend
2. Navigate to dashboard
3. Click "Refresh Colors Now"
4. Wait for toast notifications
5. Verify table refreshes
✅ PASS if automation completes and data loads

### Test 2: Manual Processing (5 minutes)
1. Prepare test Excel file (50 rows)
2. Navigate to manual color page
3. Import Excel file
4. Verify preview shows sorted data
5. Select 5 rows and delete
6. Select 1-2 rules and apply
7. Click "Run Automation" to save
8. Verify success toast
✅ PASS if all steps complete without errors

### Test 3: Error Handling (3 minutes)
1. Try uploading .txt file → Should reject
2. Try deleting without selection → Should warn
3. Try applying rules without selection → Should warn
4. Stop backend and try operation → Should show error
✅ PASS if all errors handled gracefully

---

## 📞 Getting Help

**Full Testing Guide**: `COLOR_PROCESSING_TESTING_GUIDE.md`
**Implementation Summary**: `INTEGRATION_COMPLETE_SUMMARY.md`
**API Documentation**: `http://127.0.0.1:3334/docs`

**Check Backend Logs**: Console where `python handler.py` is running
**Check Frontend Logs**: Browser Developer Console (F12)

---

## ✅ System Status

All features integrated and ready for testing:
- ✅ Automated processing with rules (Dashboard)
- ✅ Override processing without rules (Dashboard)
- ✅ Manual color workflow (Import → Preview → Delete → Apply Rules → Save)
- ✅ Error handling and validation
- ✅ Toast notifications
- ✅ Loading states
- ✅ Statistics tracking

**Start testing now!** 🎉
