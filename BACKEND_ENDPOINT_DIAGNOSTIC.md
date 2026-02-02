# Backend Endpoint Diagnostic Test

## Quick Test: Is the Manual Color Router Working?

### Test 1: Check if endpoint is registered

**PowerShell Command**:
```powershell
curl "http://127.0.0.1:3334/docs"
```

**Expected**: FastAPI Swagger UI should open showing all endpoints including:
- `POST /api/manual-color/import`
- `GET /api/manual-color/preview/{session_id}`
- `POST /api/manual-color/delete-rows`
- `POST /api/manual-color/apply-rules`
- `POST /api/manual-color/save`

**If you DON'T see these**, the router is not properly loaded!

---

### Test 2: Test Import Endpoint Directly

**PowerShell Script**:
```powershell
# Create a test Excel file with PowerShell
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$workbook = $excel.Workbooks.Add()
$worksheet = $workbook.Worksheets.Item(1)

# Add headers
$worksheet.Cells.Item(1,1) = "MARKET"
$worksheet.Cells.Item(1,2) = "DATE"
$worksheet.Cells.Item(1,3) = "CLONAME"
$worksheet.Cells.Item(1,4) = "CLO"

# Add sample data
$worksheet.Cells.Item(2,1) = "US"
$worksheet.Cells.Item(2,2) = "2024-01-15"
$worksheet.Cells.Item(2,3) = "Test CLO"
$worksheet.Cells.Item(2,4) = "123456"

# Save
$testFile = "$env:TEMP\test_manual_colors.xlsx"
$workbook.SaveAs($testFile)
$workbook.Close()
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel)

Write-Host "✅ Test file created: $testFile"

# Test the API endpoint
curl -X POST "http://127.0.0.1:3334/api/manual-color/import" `
  -F "file=@$testFile" `
  -F "user_id=1" `
  --verbose

# Clean up
Remove-Item $testFile
```

**Expected Response**:
```json
{
  "success": true,
  "session_id": "manual_color_1_20260202...",
  "filename": "test_manual_colors.xlsx",
  "rows_imported": 1,
  "rows_valid": 1,
  "parsing_errors": [],
  "sorted_preview": [...],
  "statistics": {
    "total_rows": 1,
    "valid_rows": 1,
    "invalid_rows": 0
  }
}
```

**Backend Terminal Should Show**:
```
INFO: POST /api/manual-color/import HTTP/1.1" 200 OK
📂 Importing manual colors from: test_manual_colors.xlsx
✅ Read 1 rows from Excel
🔄 Applying sorting logic...
✅ Sorted 1 colors
💾 Session created: manual_color_1_...
```

---

### Test 3: Simpler curl test (if Test 2 fails)

If Excel COM doesn't work, use a CSV test:

**PowerShell**:
```powershell
# Create test CSV
$csvContent = @"
MARKET,DATE,CLONAME,CLO
US,2024-01-15,Test CLO,123456
EU,2024-01-16,Another CLO,789012
"@

$testFile = "$env:TEMP\test_manual_colors.csv"
$csvContent | Out-File -FilePath $testFile -Encoding utf8

# Convert CSV to XLSX manually or use CSV directly
# Note: Backend expects .xlsx, so this might fail
curl -X POST "http://127.0.0.1:3334/api/manual-color/import" `
  -F "file=@$testFile" `
  -F "user_id=1"

Remove-Item $testFile
```

---

## Frontend Debugging

### Check 1: Service Injection
Open browser console on Manual Color page and run:
```javascript
// Check if service is available
angular.element(document.querySelector('app-manual-color')).componentInstance
```

Should show the component with `manualColorService` injected.

---

### Check 2: Manual Import Test
Open browser console and run:
```javascript
// Get component instance
const comp = angular.element(document.querySelector('app-manual-color')).componentInstance;

// Check if method exists
console.log('uploadFile method:', comp.uploadFile);
console.log('manualColorService:', comp.manualColorService);

// Try manual file upload (you'll need a File object)
// This is just to test if the method is callable
```

---

### Check 3: Network Tab Analysis
1. Open F12 → Network tab
2. Click "Import via Excel" button
3. Select a file
4. **Look for**:
   - Request URL: Should be `http://localhost:3334/api/manual-color/import`
   - Request Method: POST
   - Request Headers: Content-Type should include `multipart/form-data`
   - Form Data: Should show `file` and `user_id`

**If no request appears**: File upload is not triggering the service call

**If request appears but fails**:
- Check Status Code (400, 404, 500, etc.)
- Check Response body for error message
- Check backend terminal for error details

---

## Common Issues and Fixes

### Issue 1: Endpoint returns 404 Not Found
**Cause**: Router not loaded or wrong URL

**Fix**:
1. Check `handler.py` has: `app.include_router(manual_color_router)`
2. Verify prefix in `manual_color.py`: `router = APIRouter(prefix="/api/manual-color")`
3. Restart backend server

---

### Issue 2: Endpoint returns 500 Internal Server Error
**Cause**: Backend code error

**Fix**:
1. Check backend terminal for full error stack trace
2. Common causes:
   - File path issues
   - Missing directories (data/manual_color_sessions/)
   - Import errors in service
   - Database connection issues

---

### Issue 3: Request never reaches backend (CORS or preflight)
**Cause**: CORS policy blocking request

**Check Backend Terminal For**:
```
INFO: OPTIONS /api/manual-color/import HTTP/1.1" 200 OK
```

If you see OPTIONS but not POST, it's a CORS issue.

**Fix**: Verify CORS middleware in `handler.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Issue 4: FormData not constructed properly
**Cause**: File not being appended correctly

**Fix in manual-color.service.ts**:
```typescript
const formData = new FormData();
formData.append('file', file, file.name);  // ← Add filename
formData.append('user_id', userId.toString());

// Debug: Log FormData contents
for (let [key, value] of (formData as any).entries()) {
  console.log(key, value);
}
```

---

## Immediate Action Plan

1. **Run Test 1**: Open `http://127.0.0.1:3334/docs` and verify endpoints exist
2. **Run Test 2** or **Test 3**: Test endpoint directly with curl
3. **If curl works**: Issue is in frontend
4. **If curl fails**: Issue is in backend

**Report back with**:
- Screenshot of `/docs` page showing manual-color endpoints
- Curl test result
- Browser console logs (F12 → Console)
- Network tab screenshot (F12 → Network)
- Backend terminal output during test

---

**Next Diagnostic Steps** (based on results):
- If backend works with curl but not from frontend → Check Angular HTTP interceptors
- If backend fails with curl → Check backend service implementation
- If no logs at all → Check if backend is even running
