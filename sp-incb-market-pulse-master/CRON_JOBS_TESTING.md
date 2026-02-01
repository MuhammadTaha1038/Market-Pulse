# PowerShell Commands - Cron Jobs & Automation

## ✅ Phase 2 Complete: Cron Jobs & Automation

### 🚀 What's Working:

**Cron Jobs:**
- Create scheduled automation jobs (cron expressions)
- Manual trigger support
- Active/inactive toggle
- Execution logging with detailed stats
- 10 preset schedule examples

**Automation Flow:**
1. Fetch raw colors from database (Excel)
2. Apply exclusion rules (from Phase 1)
3. Apply ranking engine (DATE → RANK → PX)
4. Save processed colors to output file
5. Log execution with stats

---

## 📡 Cron Jobs API

### Base URL: `http://127.0.0.1:3334`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cron/jobs` | Get all cron jobs |
| GET | `/api/cron/jobs/active` | Get active jobs only |
| GET | `/api/cron/jobs/{id}` | Get single job |
| POST | `/api/cron/jobs` | Create new cron job |
| PUT | `/api/cron/jobs/{id}` | Update cron job |
| DELETE | `/api/cron/jobs/{id}` | Delete cron job |
| POST | `/api/cron/jobs/{id}/toggle` | Activate/deactivate job |
| POST | `/api/cron/jobs/{id}/trigger` | Manually trigger job execution |
| GET | `/api/cron/logs` | Get execution logs (all jobs) |
| GET | `/api/cron/logs/{id}` | Get logs for specific job |
| GET | `/api/cron/schedule-examples` | Get cron expression presets |

---

## 🧪 Testing Commands

### 1️⃣ Get All Cron Jobs
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs" -Method Get
```

**Formatted Output:**
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs" -Method Get
$response.jobs | Format-Table id, name, schedule, is_active -AutoSize
```

### 2️⃣ Create Cron Job - Daily at 9 AM
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Daily Morning Run","schedule":"0 9 * * *","is_active":true}'
```

### 3️⃣ Create Cron Job - Every 4 Hours
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Every 4 Hours","schedule":"0 */4 * * *","is_active":true}'
```

### 4️⃣ Create Cron Job - Weekdays at 9 AM
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Weekday Morning","schedule":"0 9 * * 1-5","is_active":true}'
```

### 5️⃣ Get Active Jobs Only
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs/active" -Method Get
```

### 6️⃣ Get Single Job by ID
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs/1" -Method Get
```

### 7️⃣ Manually Trigger Job (Run Now)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs/1/trigger" -Method Post
```

**What Happens:**
- Job runs immediately in background
- Fetches colors from database
- Applies active rules (exclusion)
- Runs ranking engine
- Saves processed colors to Excel
- Creates execution log

### 8️⃣ Get Execution Logs
```powershell
$logs = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/logs" -Method Get
$logs.logs[0] | Format-List
```

**Sample Log Output:**
```
job_id           : 1
job_name         : Daily Morning Run
triggered_by     : manual
start_time       : 2026-01-26T16:15:58.597971
end_time         : 2026-01-26T16:16:33.615516
status           : success
duration_seconds : 35.017545
original_count   : 5213
excluded_count   : 0
processed_count  : 5213
rules_applied    : 2
error            :
```

### 9️⃣ Get Logs for Specific Job
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/logs/1" -Method Get
```

### 🔟 Toggle Job (Activate/Deactivate)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs/1/toggle" -Method Post
```

### 1️⃣1️⃣ Update Job
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs/1" -Method Put `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Updated Job Name","schedule":"0 10 * * *","is_active":true}'
```

### 1️⃣2️⃣ Delete Job
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/jobs/1" -Method Delete
```

### 1️⃣3️⃣ Get Schedule Examples
```powershell
$examples = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/cron/schedule-examples" -Method Get
$examples.examples | Format-Table expression, description, frequency -AutoSize
```

**Output:**
```
expression   description                     frequency
----------   -----------                     ---------
0 9 * * *    Every day at 9:00 AM            Daily
0 9 * * 1-5  Weekdays (Mon-Fri) at 9:00 AM   Weekdays
0 */6 * * *  Every 6 hours                   Every 6 hours
0 */4 * * *  Every 4 hours                   Every 4 hours
0 0,12 * * * Twice daily (midnight and noon) Twice daily
0 0 * * 0    Every Sunday at midnight        Weekly
0 0 1 * *    First day of every month        Monthly
*/30 * * * * Every 30 minutes                Every 30 minutes
0 8-17 * * 1-5 Every hour 8 AM-5 PM weekdays Business hours
0 10,14,16 * * * Three times daily           Custom
```

---

## 📅 Cron Expression Guide

### Format: `minute hour day month day_of_week`

| Field | Values | Special |
|-------|--------|---------|
| Minute | 0-59 | `*/5` = every 5 minutes |
| Hour | 0-23 | `*/4` = every 4 hours |
| Day | 1-31 | `*` = every day |
| Month | 1-12 | `*` = every month |
| Day of Week | 0-6 (Sun=0) | `1-5` = Mon-Fri |

### Common Examples:

```
0 9 * * *       = Every day at 9:00 AM
0 */6 * * *     = Every 6 hours
0 9 * * 1-5     = Weekdays at 9:00 AM
0 0 * * 0       = Every Sunday at midnight
*/30 * * * *    = Every 30 minutes
0 0,12 * * *    = Twice daily (midnight and noon)
0 8-17 * * 1-5  = Every hour 8 AM-5 PM on weekdays
```

---

## 📁 File Structure

```
sp-incb-market-pulse-master/
├── src/main/
│   ├── cron_service.py          # ✅ NEW - Core scheduler logic
│   ├── cron_jobs.py             # ✅ NEW - API router (11 endpoints)
│   ├── handler.py               # ✏️ Modified - Added cron router
│   └── data/
│       ├── cron_jobs.json       # ✅ Auto-created - Job definitions
│       └── cron_logs.json       # ✅ Auto-created - Execution logs
```

---

## 🔄 Automation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTOMATED COLOR PROCESSING                │
└─────────────────────────────────────────────────────────────┘

1. ⏰ TRIGGER
   ├─ Scheduled (cron expression)
   └─ Manual (API trigger)

2. 📥 FETCH DATA
   └─ Load raw colors from Excel (Color today.xlsx)
      Result: 5213 records

3. 🔍 APPLY RULES (Phase 1)
   ├─ Get active exclusion rules
   ├─ Filter rows matching conditions
   └─ Log excluded count
      Result: 5213 records (0 excluded with 2 rules)

4. 📊 APPLY RANKING (Existing)
   ├─ Group by CUSIP
   ├─ Rank by DATE (newest)
   ├─ Rank by RANK column
   └─ Rank by PX (lowest)
      Result: 5213 processed colors

5. 💾 SAVE OUTPUT
   ├─ Append to output Excel
   ├─ Mark as "AUTOMATED" type
   └─ Generate unique transaction ID
      Result: Saved to excel file

6. 📝 LOG EXECUTION
   └─ Save to cron_logs.json:
      - Job ID, name, trigger type
      - Start/end time, duration
      - Original/excluded/processed counts
      - Rules applied count
      - Status (success/failed)
      - Error message (if failed)
```

---

## ✅ Test Results

### Jobs Created:
- ✅ Job #1: Daily Morning Run (0 9 * * *)
- ✅ Job #2: Every 4 Hours (0 */4 * * *)

### Manual Trigger Test:
```
Job ID: 1 (Daily Morning Run)
Status: ✅ SUCCESS
Duration: 35.02 seconds
Original: 5213 records
Excluded: 0 records
Processed: 5213 records
Rules Applied: 2 active rules
```

### Storage:
- 📁 `data/cron_jobs.json` - 2 jobs stored
- 📁 `data/cron_logs.json` - Execution history
- 🔄 APScheduler running in background

---

## 🎯 What's Complete

### ✅ Phase 1: Rules Engine
- Storage abstraction (JSON/S3/Oracle)
- Rules CRUD APIs
- 10 condition operators
- Integration with dashboard

### ✅ Phase 2: Cron Jobs & Automation
- Background scheduler (APScheduler)
- Cron job CRUD APIs
- Manual trigger support
- Execution logging
- Full automation flow (fetch → rules → ranking → save)
- Storage-agnostic (uses JSON now, ready for S3/Oracle)

---

## 🔜 Next Steps

### Phase 3: Manual Colors Upload
- Excel file upload API
- Merge with automation results
- Validation and error handling
- History tracking

### Phase 4: Restore & Logging
- Backup system
- Rollback functionality
- Activity audit logs
- Version history

---

## 🚀 Server Commands

### Start Server:
```powershell
cd "D:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main"
python handler.py
```

### API Documentation:
```
http://127.0.0.1:3334/docs
```

### View Stored Data:
```powershell
# Cron Jobs
Get-Content "D:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main\data\cron_jobs.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10

# Execution Logs
Get-Content "D:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main\data\cron_logs.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```
