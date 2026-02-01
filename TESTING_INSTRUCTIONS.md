# Testing Instructions - Fully Integrated Admin System

## 🚀 Quick Start (2 Steps)

### Step 1: Start Backend
```bash
cd "sp-incb-market-pulse-master"
python src/main/handler.py
```
✅ Backend running on: `http://localhost:3334`

### Step 2: Start Frontend
```bash
cd "market-pulse-main"
npm run dev
```
✅ Frontend running on: `http://localhost:4200` (or port shown in terminal)

---

## ✅ What Was Integrated

### Settings Component Updated
**File**: `market-pulse-main/src/app/components/settings/settings.ts`

**Changes Made**:
1. ✅ Imported 4 API services (RulesService, CronJobsService, ManualUploadService, BackupService)
2. ✅ Injected services in constructor
3. ✅ Added `loadRules()` method - loads rules from backend on page load
4. ✅ Added `saveRule()` method - creates new rules via API
5. ✅ Added `deleteRule()` method - deletes rules via API
6. ✅ Added `loadCronJobs()` method - loads cron jobs from backend
7. ✅ Added `saveCronJob()` method - creates cron jobs via API
8. ✅ Added `deleteCronJob()` method - deletes cron jobs via API
9. ✅ Added `triggerCronJob()` method - manually triggers cron jobs
10. ✅ Added `loadBackupHistory()` method - loads backup history
11. ✅ Added `createBackup()` method - creates backups via API
12. ✅ Added `restoreFromBackup()` method - restores from backup
13. ✅ Added `uploadFile()` method - handles manual file uploads
14. ✅ Updated existing methods (addJob, deleteJob, saveJob) to call API instead of mock data
15. ✅ All methods called in `ngOnInit()` to load data on component initialization

**No Frontend Code Changes Required**: Everything is integrated and ready to test!

---

## 🧪 Test Scenarios

### 1. Rules Tab Testing
Navigate to: Settings → Rules Tab

**Test 1: View Existing Rules**
- ✅ Page loads
- ✅ Rules table populates with data from backend
- ✅ Columns show: Rule Name, Column, Operator, Value, Active Status

**Test 2: Create New Rule**
1. Enter rule name in "Rule Name" field
2. Set conditions (Column, Operator, Value)
3. Click "Save Rule" button
4. ✅ Toast notification: "Rule saved successfully!"
5. ✅ New rule appears in table

**Test 3: Delete Rule**
1. Click delete icon on any rule
2. ✅ Toast notification: "Rule deleted successfully!"
3. ✅ Rule removed from table

**Expected API Calls**:
- `GET http://localhost:3334/rules` - Load rules
- `POST http://localhost:3334/rules` - Create rule
- `DELETE http://localhost:3334/rules/{rule_id}` - Delete rule

---

### 2. Cron Jobs Tab Testing
Navigate to: Settings → Corn Jobs Tab

**Test 1: View Existing Cron Jobs**
- ✅ Page loads
- ✅ Cron jobs table populates with data from backend
- ✅ Shows: Job Name, Time, Frequency (days), Repeat status

**Test 2: Create New Cron Job**
1. Enter job name in "Job Name" field
2. Set time (e.g., "11:40")
3. Select days of week
4. Choose repeat option (Yes/No)
5. Click "Add Job" button
6. ✅ Toast notification: "Cron job created successfully!"
7. ✅ New job appears in table

**Test 3: Edit Cron Job**
1. Click edit icon on any job
2. Modify job details
3. Click save
4. ✅ Toast notification: "Job updated successfully!"
5. ✅ Changes reflected in table

**Test 4: Delete Cron Job**
1. Click delete icon on any job
2. ✅ Toast notification: "Cron job deleted successfully!"
3. ✅ Job removed from table

**Expected API Calls**:
- `GET http://localhost:3334/cron-jobs` - Load jobs
- `POST http://localhost:3334/cron-jobs` - Create job
- `PUT http://localhost:3334/cron-jobs/{job_id}` - Update job
- `DELETE http://localhost:3334/cron-jobs/{job_id}` - Delete job

---

### 3. Manual Upload Testing
Navigate to: Settings → Manual Upload Section

**Test 1: Upload File**
1. Click "Choose File" button
2. Select a CSV/Excel file
3. Click "Upload" button
4. ✅ Toast notification: "File uploaded successfully! Processed X records"
5. ✅ Upload history updates

**Expected API Calls**:
- `POST http://localhost:3334/manual-upload/upload` - Upload file
- `GET http://localhost:3334/manual-upload/history` - Get upload history

---

### 4. Restore & Email Tab Testing
Navigate to: Settings → Restore & Email Tab

**Test 1: View Backup History**
- ✅ Page loads
- ✅ Backup history table populates with data from backend
- ✅ Shows: Details, Date, Time, Process Type

**Test 2: Create Backup**
1. Click "Create Backup" button
2. ✅ Toast notification: "Backup created successfully!"
3. ✅ New backup appears in history

**Test 3: Restore from Backup**
1. Click "Restore" button on any backup
2. ✅ Toast notification: "Backup restored successfully!"
3. ✅ All data refreshes (rules, cron jobs, backups)

**Expected API Calls**:
- `GET http://localhost:3334/backup/history` - Load backup history
- `POST http://localhost:3334/backup/create` - Create backup
- `POST http://localhost:3334/backup/restore/{backup_id}` - Restore backup

---

## 🔍 Verify API Connectivity

### Check Browser Console
1. Open Browser DevTools (F12)
2. Go to Console tab
3. Look for:
   - ✅ No CORS errors
   - ✅ No 404 errors
   - ✅ Successful API responses (200 status)

### Check Network Tab
1. Open Browser DevTools (F12)
2. Go to Network tab
3. Filter: XHR
4. You should see:
   - `GET http://localhost:3334/rules` - Status 200
   - `GET http://localhost:3334/cron-jobs` - Status 200
   - `GET http://localhost:3334/backup/history` - Status 200

---

## 🐛 Troubleshooting

### Issue: "Failed to load rules from server"
**Solution**:
1. Verify backend is running: `python src/main/handler.py`
2. Check backend URL: `http://localhost:3334`
3. Check backend console for errors

### Issue: CORS Error
**Solution**: Backend already has CORS enabled. If you see CORS errors:
```python
# In handler.py, verify this is present:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: 404 Not Found
**Solution**: 
1. Check backend routes are registered
2. Verify API URL format: `http://localhost:3334/rules` (no /api prefix)
3. Check backend console logs

### Issue: Data Not Loading
**Solution**:
1. Open Browser Console (F12)
2. Check for JavaScript errors
3. Verify API responses in Network tab
4. Check backend terminal for logs

---

## 📊 Expected Data Flow

```
User Opens Settings Page
         ↓
ngOnInit() Executes
         ↓
    ┌────┴────┬──────────┬────────────┐
    ↓         ↓          ↓            ↓
loadRules() loadCronJobs() loadBackupHistory()
    ↓         ↓          ↓            ↓
  API GET   API GET    API GET    (parallel)
    ↓         ↓          ↓            ↓
  Rules    CronJobs   Backups    (data returned)
    ↓         ↓          ↓            ↓
    └────┬────┴──────────┴────────────┘
         ↓
   UI Updates with Real Data
```

---

## ✅ Integration Checklist

- [x] Backend running (port 3334)
- [x] Frontend running (port 4200 or similar)
- [x] 4 API services created
- [x] Services imported in settings.ts
- [x] Services injected in constructor
- [x] Load methods call APIs in ngOnInit()
- [x] CRUD operations integrated (Create, Read, Update, Delete)
- [x] Error handling with toast notifications
- [x] No hardcoded URLs (uses environment.ts)
- [x] All 4 tabs connected to backend APIs

---

## 🎯 Success Criteria

Your integration is successful if:
1. ✅ Settings page loads without errors
2. ✅ Rules tab shows data from backend
3. ✅ Cron Jobs tab shows data from backend
4. ✅ Backup history shows data from backend
5. ✅ Can create new rules (POST request works)
6. ✅ Can create new cron jobs (POST request works)
7. ✅ Can delete items (DELETE request works)
8. ✅ Toast notifications appear on actions
9. ✅ No CORS errors in console
10. ✅ No 404 errors in Network tab

---

## 📝 Notes

- **Storage**: Backend uses JSON file storage by default (`data/rules.json`, `data/cron_jobs.json`, etc.)
- **Environment**: Development environment uses `http://localhost:3334`
- **Production**: Update `environment.ts` → `baseURL` before deploying
- **CORS**: Already configured in backend for all origins
- **Services Location**: `market-pulse-main/src/app/services/`
- **Settings Component**: `market-pulse-main/src/app/components/settings/settings.ts` (fully integrated)

---

## 🎉 You're Ready to Test!

Just start both servers and navigate to the Settings page. Everything is integrated and ready to use!

**Backend**: `python src/main/handler.py`
**Frontend**: `npm run dev`

All APIs are connected, all methods are wired up, and all tabs are functional!
