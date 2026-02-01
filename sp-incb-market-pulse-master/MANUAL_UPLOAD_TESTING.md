# PowerShell Commands - Manual Upload

## ✅ Phase 3 Complete: Manual Colors Upload

### 🚀 What's Working:

**Manual Upload System:**
- Excel file upload with validation
- Automatic parsing and error detection
- Ranking engine application
- Save to output file (marked as MANUAL)
- Upload history tracking
- File storage in data/manual_uploads/
- Template information for frontend

**Upload Flow:**
1. Upload Excel file via API
2. Validate structure (required columns)
3. Parse rows to ColorRaw objects
4. Apply ranking engine (DATE → RANK → PX)
5. Save processed colors to output
6. Record upload in history with stats

---

## 📡 Manual Upload API

### Base URL: `http://127.0.0.1:3334`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/manual-upload/upload` | Upload Excel file |
| GET | `/api/manual-upload/history` | Get all upload history |
| GET | `/api/manual-upload/history/{id}` | Get single upload details |
| DELETE | `/api/manual-upload/history/{id}` | Delete upload from history |
| GET | `/api/manual-upload/stats` | Get upload statistics |
| GET | `/api/manual-upload/template-info` | Get template structure info |

---

## 🧪 Testing Commands

### 1️⃣ Get Template Information
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/template-info" -Method Get
```

**Returns:**
- Required columns list
- Optional columns list
- Column data types
- Validation rules
- Usage notes

### 2️⃣ Upload Excel File
```powershell
# Prepare multipart form data
$filePath = "D:\path\to\your\colors.xlsx"
$uploadedBy = "admin"

$form = @{
    file = Get-Item -Path $filePath
    uploaded_by = $uploadedBy
}

Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/upload" `
    -Method Post `
    -Form $form
```

**Alternative using curl:**
```powershell
curl.exe -X POST "http://127.0.0.1:3334/api/manual-upload/upload" `
    -F "file=@colors.xlsx" `
    -F "uploaded_by=admin"
```

**Success Response:**
```json
{
  "success": true,
  "upload_id": 1,
  "filename": "colors.xlsx",
  "rows_uploaded": 100,
  "rows_valid": 98,
  "rows_processed": 98,
  "parsing_errors": ["Row 5: Invalid date format", "Row 23: Missing CUSIP"],
  "duration_seconds": 2.5
}
```

**Error Response:**
```json
{
  "success": false,
  "upload_id": 1,
  "error": "Missing required columns: CUSIP, DATE",
  "validation_errors": [
    "Missing required columns: CUSIP, DATE",
    "Excel file is empty"
  ]
}
```

### 3️⃣ Get Upload History
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/history" -Method Get
```

**Formatted Output:**
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/history" -Method Get
$response.uploads | Format-Table id, filename, status, rows_processed, upload_time -AutoSize
```

**Sample Output:**
```
id filename      status  rows_processed upload_time
-- --------      ------  -------------- -----------
 3 colors3.xlsx  success 150            2026-01-26T16:45:00
 2 colors2.xlsx  success 200            2026-01-26T16:40:00
 1 colors1.xlsx  failed  0              2026-01-26T16:35:00
```

### 4️⃣ Get Single Upload Details
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/history/1" -Method Get | Format-List
```

**Sample Output:**
```
id                   : 1
filename             : colors.xlsx
uploaded_by          : admin
upload_time          : 2026-01-26T16:35:00.123456
processing_time      : 2026-01-26T16:35:02.678901
duration_seconds     : 2.555445
status               : success
rows_uploaded        : 100
rows_valid           : 98
rows_processed       : 98
parsing_errors_count : 2
error                :
```

### 5️⃣ Get Upload Statistics
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/stats" -Method Get | ConvertTo-Json -Depth 3
```

**Sample Output:**
```json
{
  "total_uploads": 5,
  "successful_uploads": 4,
  "failed_uploads": 1,
  "success_rate": 80.0,
  "total_rows_uploaded": 450,
  "total_rows_processed": 448,
  "recent_uploads": [
    {
      "id": 5,
      "filename": "latest.xlsx",
      "upload_time": "2026-01-26T16:50:00",
      "status": "success",
      "rows_processed": 120
    },
    ...
  ]
}
```

### 6️⃣ Delete Upload from History
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/history/1" -Method Delete
```

**Note:** This only deletes the history record and uploaded file, not the processed data already saved to output.

---

## 📋 Excel Template Structure

### Required Columns:
| Column | Type | Description |
|--------|------|-------------|
| MESSAGE_ID | integer | Unique message identifier |
| TICKER | string | Security ticker symbol |
| SECTOR | string | Sector/industry classification |
| CUSIP | string | CUSIP identifier (9 characters) |
| DATE | date | Price date (YYYY-MM-DD) |
| PRICE_LEVEL | float | Price level indicator |
| PX | float | Price value |
| SOURCE | string | Data source |
| BIAS | string | Bias indicator |
| RANK | integer | Ranking value (1-5) |

### Optional Columns:
- BID, ASK (float)
- COV_PRICE, PERCENT_DIFF, PRICE_DIFF (float)
- CONFIDENCE (integer)
- DATE_1 (date)
- DIFF_STATUS (string)
- SECURITY_NAME, BWIC_COVER, ASSET_CLASS (string)

### Validation Rules:
- MESSAGE_ID must be positive integer
- CUSIP must be 9 characters
- DATE must be valid date format
- PX must be positive number
- RANK must be integer between 1-5
- File must be .xlsx or .xls format
- At least one data row required

---

## 🔄 Upload Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    MANUAL UPLOAD PROCESSING                  │
└─────────────────────────────────────────────────────────────┘

1. 📤 UPLOAD
   ├─ Receive Excel file via API
   ├─ Validate file type (.xlsx, .xls)
   └─ Read file content
      Check: File size > 0

2. ✅ VALIDATE STRUCTURE
   ├─ Check required columns present
   ├─ Verify column data types
   └─ Validate at least 1 data row
      Fail → Return validation errors

3. 📊 PARSE DATA
   ├─ Read each row
   ├─ Convert to ColorRaw objects
   ├─ Handle missing optional columns
   └─ Collect parsing errors
      Result: List of valid ColorRaw objects

4. 📈 APPLY RANKING
   ├─ Group by CUSIP
   ├─ Rank by DATE (newest first)
   ├─ Rank by RANK column
   └─ Rank by PX (lowest)
      Result: List of ColorProcessed objects

5. 💾 SAVE OUTPUT
   ├─ Append to output Excel
   ├─ Mark as "MANUAL" type
   └─ Generate unique transaction ID
      Output: Merged with automation results

6. 📁 STORE FILE
   ├─ Save uploaded Excel to data/manual_uploads/
   └─ Filename: {id}_{timestamp}_{original_name}.xlsx

7. 📝 LOG HISTORY
   └─ Save to manual_upload_history.json:
      - Upload ID, filename, uploaded_by
      - Timestamps, duration
      - Row counts (uploaded/valid/processed)
      - Status (success/failed)
      - Parsing errors count
      - Error message (if failed)
```

---

## 📁 File Structure

```
sp-incb-market-pulse-master/
├── src/main/
│   ├── manual_upload_service.py    # ✅ NEW - Core upload logic
│   ├── manual_upload.py            # ✅ NEW - API router (6 endpoints)
│   ├── handler.py                  # ✏️ Modified - Added manual upload router
│   └── data/
│       ├── manual_upload_history.json  # ✅ Auto-created - Upload logs
│       └── manual_uploads/             # ✅ Auto-created - Uploaded files
│           ├── 1_20260126_163500_colors.xlsx
│           ├── 2_20260126_164000_data.xlsx
│           └── ...
```

---

## 🎯 Testing Scenarios

### ✅ Scenario 1: Valid Upload
```powershell
# Upload valid Excel file
$form = @{
    file = Get-Item -Path "valid_colors.xlsx"
    uploaded_by = "test_user"
}

$result = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/upload" -Method Post -Form $form

# Expected: success=true, rows_processed > 0
$result.success  # True
$result.rows_processed  # 100
```

### ❌ Scenario 2: Missing Columns
```powershell
# Upload Excel with missing required columns
$form = @{
    file = Get-Item -Path "invalid_columns.xlsx"
    uploaded_by = "test_user"
}

$result = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/upload" -Method Post -Form $form

# Expected: success=false, validation_errors present
$result.success  # False
$result.validation_errors  # ["Missing required columns: CUSIP, DATE"]
```

### ⚠️ Scenario 3: Partial Success (Some Invalid Rows)
```powershell
# Upload Excel with some invalid rows
$form = @{
    file = Get-Item -Path "partial_valid.xlsx"
    uploaded_by = "test_user"
}

$result = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-upload/upload" -Method Post -Form $form

# Expected: success=true, but parsing_errors present
$result.success  # True
$result.rows_uploaded  # 100
$result.rows_valid  # 95
$result.parsing_errors  # ["Row 5: Invalid date", "Row 12: Missing CUSIP", ...]
```

---

## ✅ What's Complete

### ✅ Phase 1: Rules Engine
- Storage abstraction (JSON/S3/Oracle)
- Rules CRUD APIs
- Integration with dashboard

### ✅ Phase 2: Cron Jobs & Automation
- Background scheduler
- Automated runs
- Execution logging
- Manual triggers

### ✅ Phase 3: Manual Upload
- Excel file upload API
- Structure validation
- Parsing with error handling
- Ranking engine integration
- Upload history tracking
- File storage
- Statistics endpoint
- Template information API

---

## 🔜 Next: Phase 4 - Restore & Logging

### Planned Features:
- Backup system for output data
- Rollback functionality
- Activity audit logs
- Version history
- Data recovery tools

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

### View Upload History:
```powershell
Get-Content "D:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main\data\manual_upload_history.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### List Uploaded Files:
```powershell
Get-ChildItem "D:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main\data\manual_uploads"
```

---

## 📝 Notes

1. **No Rules Applied to Manual Uploads**: Manual uploads bypass exclusion rules and go straight to ranking
2. **Merge with Automation**: Both MANUAL and AUTOMATED types saved to same output file
3. **Transaction Type Tracking**: Each row marked with source type for audit trail
4. **Error Tolerance**: Invalid rows skipped, valid rows processed
5. **History Retention**: Upload history kept indefinitely (can add cleanup later)
