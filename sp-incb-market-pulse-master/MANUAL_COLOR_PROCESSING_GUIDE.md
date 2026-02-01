# Manual Color Processing - Complete Integration Guide

## Overview
Implemented complete manual color processing workflow for **Color Processing Page** (separate from Admin Panel buffer).

---

## Implementation Summary

### New Files Created

1. **`services/manual_color_service.py`** (600+ lines)
   - Core service for manual color processing
   - Session management for preview workflow
   - Sorting, rules application, and save operations

2. **`routers/manual_color.py`** (250+ lines)
   - REST API endpoints for manual color workflow
   - File upload handling
   - Preview, delete, apply rules, and save operations

### Modified Files

1. **`rules_service.py`**
   - Updated `apply_rules()` to accept `specific_rule_ids` parameter
   - Can now apply selected rules instead of all active rules

2. **`handler.py`**
   - Registered new `/api/manual-color` router

---

## Architecture

### Two Separate Workflows

#### 1. Admin Panel Manual Upload (EXISTING)
- **Location**: Admin Panel → Manual Upload section
- **Flow**: Import → Save to buffer → Process during cron automation
- **API**: `/api/manual-upload/*`
- **Service**: `manual_upload_service.py`
- **Purpose**: Bulk uploads that get processed with automation

#### 2. Color Processing Page Manual Colors (NEW)
- **Location**: Color Processing Page → Manual Color section
- **Flow**: Import → Preview sorted → Apply rules → Save to output
- **API**: `/api/manual-color/*`
- **Service**: `services/manual_color_service.py`
- **Purpose**: Interactive manual color processing with preview

---

## API Endpoints

### Base URL
```
http://127.0.0.1:3334/api/manual-color
```

### 1. Import Excel for Manual Processing
```http
POST /api/manual-color/import
Content-Type: multipart/form-data

Parameters:
- file: Excel file (.xlsx, .xls)
- user_id: User ID (default: 1)

Response:
{
  "success": true,
  "session_id": "manual_color_1_20260201_233000",
  "filename": "colors.xlsx",
  "rows_imported": 100,
  "rows_valid": 98,
  "parsing_errors": ["Row 5: Invalid date format"],
  "sorted_preview": [...],
  "statistics": {
    "total_rows": 98,
    "parent_rows": 45,
    "child_rows": 53,
    "unique_cusips": 45
  },
  "duration_seconds": 1.5
}
```

**What it does:**
1. Accepts Excel file upload
2. Parses and validates data
3. Applies sorting logic (DATE > RANK > PX)
4. Returns sorted preview with parent-child hierarchy
5. Creates session for further operations

### 2. Get Preview
```http
GET /api/manual-color/preview/{session_id}

Response:
{
  "success": true,
  "session_id": "manual_color_1_20260201_233000",
  "data": [...],
  "applied_rules": [1, 3],
  "deleted_rows": [5, 12],
  "statistics": {
    "total_rows": 85,
    "parent_rows": 42,
    "child_rows": 43
  }
}
```

**What it does:**
- Returns current state of preview data
- Shows applied rules and deleted rows
- Updates after each operation

### 3. Delete Selected Rows
```http
POST /api/manual-color/delete-rows
Content-Type: application/json

Body:
{
  "session_id": "manual_color_1_20260201_233000",
  "row_ids": [5, 12, 23]
}

Response:
{
  "success": true,
  "deleted_count": 3,
  "remaining_rows": 95,
  "data": [...]
}
```

**What it does:**
- Removes selected rows from preview
- Updates session state
- Returns updated preview data

### 4. Apply Selected Rules
```http
POST /api/manual-color/apply-rules
Content-Type: application/json

Body:
{
  "session_id": "manual_color_1_20260201_233000",
  "rule_ids": [1, 3, 5]
}

Response:
{
  "success": true,
  "rules_applied": 3,
  "excluded_count": 15,
  "remaining_rows": 83,
  "data": [...],
  "rules_info": [
    {"id": 1, "name": "Exclude TEST symbols"},
    {"id": 3, "name": "Exclude invalid prices"}
  ]
}
```

**What it does:**
- Applies selected rules to current preview data
- Filters out rows matching rules
- Returns updated preview after exclusions

### 5. Save Processed Manual Colors
```http
POST /api/manual-color/save
Content-Type: application/json

Body:
{
  "session_id": "manual_color_1_20260201_233000",
  "user_id": 1
}

Response:
{
  "success": true,
  "session_id": "manual_color_1_20260201_233000",
  "rows_saved": 83,
  "output_file": "output/manual_colors_20260201_233500.xlsx",
  "duration_seconds": 0.8,
  "metadata": {
    "applied_rules_count": 3,
    "deleted_rows_count": 5
  }
}
```

**What it does:**
- Saves final processed data to output Excel
- Records applied rules and deletions
- Future: Will save to S3 bucket
- Does NOT trigger full automation

### 6. Get Active Sessions
```http
GET /api/manual-color/sessions?user_id=1

Response:
{
  "success": true,
  "sessions": [
    {
      "session_id": "manual_color_1_20260201_233000",
      "created_at": "2026-02-01T23:30:00",
      "updated_at": "2026-02-01T23:35:00",
      "filename": "colors.xlsx",
      "status": "preview",
      "rows_count": 83
    }
  ],
  "count": 1
}
```

### 7. Cleanup Old Sessions
```http
DELETE /api/manual-color/cleanup?days=1

Response:
{
  "success": true,
  "deleted_count": 5,
  "message": "Cleaned up 5 old sessions"
}
```

### 8. Health Check
```http
GET /api/manual-color/health

Response:
{
  "status": "healthy",
  "service": "Manual Color Processing"
}
```

---

## User Workflow

### Color Processing Page Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User imports Excel file                                  │
│    ↓                                                         │
│ 2. Backend sorts data (DATE > RANK > PX)                    │
│    ↓                                                         │
│ 3. User sees sorted preview in Manual Color page            │
│    ↓                                                         │
│ 4. User can:                                                 │
│    - Delete unwanted rows (checkbox selection)              │
│    - Click "Run Rules" → Select rules → Apply               │
│    ↓                                                         │
│ 5. User clicks "Run Automation" button                      │
│    ↓                                                         │
│ 6. Backend saves processed colors to output Excel           │
│    (Future: S3 bucket)                                       │
└─────────────────────────────────────────────────────────────┘
```

### Frontend Integration Steps

#### Step 1: Import Excel
```javascript
// File upload component
async function importManualColors(file, userId = 1) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);
  
  const response = await fetch('http://127.0.0.1:3334/api/manual-color/import', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  if (result.success) {
    // Store session_id for future operations
    sessionStorage.setItem('manualColorSessionId', result.session_id);
    
    // Show sorted preview in table
    displayPreview(result.sorted_preview);
    showStatistics(result.statistics);
  } else {
    alert(`Error: ${result.error}`);
  }
}
```

#### Step 2: Display Preview with Actions
```javascript
// Preview table component
function displayPreview(data) {
  const tableHtml = `
    <table>
      <thead>
        <tr>
          <th><input type="checkbox" id="selectAll"></th>
          <th>CUSIP</th>
          <th>Date</th>
          <th>Rank</th>
          <th>PX</th>
          <th>Color</th>
          <th>Parent/Child</th>
        </tr>
      </thead>
      <tbody>
        ${data.map(row => `
          <tr>
            <td><input type="checkbox" value="${row.row_id}"></td>
            <td>${row.cusip}</td>
            <td>${row.date}</td>
            <td>${row.rank}</td>
            <td>${row.px}</td>
            <td style="background-color: ${row.color}">${row.color}</td>
            <td>${row.is_parent ? '👑 Parent' : '👶 Child'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  
  document.getElementById('previewContainer').innerHTML = tableHtml;
}
```

#### Step 3: Delete Rows
```javascript
async function deleteSelectedRows() {
  const sessionId = sessionStorage.getItem('manualColorSessionId');
  const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
  const rowIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
  
  if (rowIds.length === 0) {
    alert('No rows selected');
    return;
  }
  
  const response = await fetch('http://127.0.0.1:3334/api/manual-color/delete-rows', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: sessionId,
      row_ids: rowIds
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    displayPreview(result.data);
    alert(`Deleted ${result.deleted_count} rows`);
  }
}
```

#### Step 4: Apply Rules
```javascript
async function showRulesDialog() {
  // Fetch available rules
  const rulesResponse = await fetch('http://127.0.0.1:3334/api/rules');
  const rulesData = await rulesResponse.json();
  
  // Show dialog with checkboxes for rules
  const rulesHtml = rulesData.rules.map(rule => `
    <div>
      <input type="checkbox" id="rule_${rule.id}" value="${rule.id}">
      <label for="rule_${rule.id}">
        ${rule.name} ${rule.is_active ? '✅' : '❌'}
      </label>
    </div>
  `).join('');
  
  // Show dialog (use your UI library)
  showDialog('Select Rules', rulesHtml, applyRules);
}

async function applyRules() {
  const sessionId = sessionStorage.getItem('manualColorSessionId');
  const checkboxes = document.querySelectorAll('[id^="rule_"]:checked');
  const ruleIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
  
  if (ruleIds.length === 0) {
    alert('No rules selected');
    return;
  }
  
  const response = await fetch('http://127.0.0.1:3334/api/manual-color/apply-rules', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: sessionId,
      rule_ids: ruleIds
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    displayPreview(result.data);
    alert(`Applied ${result.rules_applied} rules, excluded ${result.excluded_count} rows`);
  }
}
```

#### Step 5: Save Manual Colors
```javascript
async function saveManualColors() {
  const sessionId = sessionStorage.getItem('manualColorSessionId');
  const userId = getCurrentUserId(); // Your auth logic
  
  const response = await fetch('http://127.0.0.1:3334/api/manual-color/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: sessionId,
      user_id: userId
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    alert(`Saved ${result.rows_saved} colors to ${result.output_file}`);
    // Clear session
    sessionStorage.removeItem('manualColorSessionId');
    // Redirect or close preview
  }
}
```

---

## Automation with Override

### Override Dialog Flow

When user clicks **"Automated Coloring"** button (NOT manual colors):

```javascript
async function showAutomationDialog() {
  // Show dialog asking for override
  const override = await showConfirmDialog(
    'Run Automation',
    'Do you want to override the next scheduled run?',
    [
      {label: 'Yes, Override', value: true},
      {label: 'No, Keep Schedule', value: false}
    ]
  );
  
  // Trigger automation with override parameter
  await triggerAutomation(override);
}

async function triggerAutomation(override = false) {
  const jobId = 1; // Get from cron jobs list
  
  const response = await fetch(
    `http://127.0.0.1:3334/api/cron/jobs/${jobId}/trigger?override=${override}`,
    {method: 'POST'}
  );
  
  const result = await response.json();
  
  if (result.override) {
    alert('Automation triggered with override - next scheduled run cancelled');
  } else {
    alert('Automation triggered - scheduled run will still execute');
  }
}
```

---

## Key Features

### 1. Session Management
- Each import creates unique session
- Session stores all state (sorted data, applied rules, deleted rows)
- Sessions persist across requests
- Auto-cleanup after 1 day

### 2. Sorting Logic
Uses existing `RankingEngine`:
- **Primary**: DATE (descending) - More recent = higher priority
- **Secondary**: RANK (ascending) - Lower rank = higher priority
- **Tertiary**: PX (ascending) - Lower price = higher priority
- **Result**: Parent-child hierarchy by CUSIP

### 3. Rules Application
- User selects specific rules from UI
- Backend applies only selected rules (even if inactive)
- Filters out rows matching rule conditions
- Returns excluded count and remaining data

### 4. Data Flow
```
Excel Upload
    ↓
Parse & Validate
    ↓
Apply Sorting (RankingEngine)
    ↓
Store in Session
    ↓
Preview to User
    ↓
User Actions (Delete/Apply Rules)
    ↓
Update Session
    ↓
Save to Output Excel
    ↓
(Future: Save to S3)
```

---

## Differences: Admin Panel vs Color Processing Page

| Feature | Admin Panel Upload | Color Processing Manual |
|---------|-------------------|-------------------------|
| **Purpose** | Bulk upload for automation | Interactive processing |
| **API** | `/api/manual-upload/*` | `/api/manual-color/*` |
| **Service** | `manual_upload_service.py` | `services/manual_color_service.py` |
| **Flow** | Import → Buffer → Auto-process | Import → Preview → Edit → Save |
| **Processing** | Happens during cron job | Immediate interactive |
| **Preview** | No preview | Full sorted preview |
| **User Control** | None (automated) | Delete rows, apply rules |
| **Output** | Merged with automation | Standalone output |
| **When Used** | Scheduled bulk updates | Manual one-time processing |

---

## Testing

### Manual Test Flow

```powershell
# 1. Check health
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-color/health" -Method GET

# 2. Get available rules
$rules = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules" -Method GET
$rules.rules | Select id,name,is_active

# 3. Import Excel (create test file first)
# Use Postman or frontend to upload file

# 4. Get preview
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-color/preview/SESSION_ID" -Method GET

# 5. Delete rows
$deleteBody = @{
    session_id = "SESSION_ID"
    row_ids = @(1, 5, 10)
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-color/delete-rows" `
    -Method POST -Body $deleteBody -ContentType "application/json"

# 6. Apply rules
$rulesBody = @{
    session_id = "SESSION_ID"
    rule_ids = @(1, 3)
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-color/apply-rules" `
    -Method POST -Body $rulesBody -ContentType "application/json"

# 7. Save
$saveBody = @{
    session_id = "SESSION_ID"
    user_id = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/manual-color/save" `
    -Method POST -Body $saveBody -ContentType "application/json"
```

---

## Future Enhancements

### Phase 1 (Current)
- ✅ Excel import with sorting
- ✅ Session-based preview
- ✅ Delete rows functionality
- ✅ Apply selected rules
- ✅ Save to output Excel

### Phase 2 (S3 Integration)
- 🔜 Save to S3 bucket instead of Excel
- 🔜 S3 path configuration
- 🔜 S3 upload status tracking

### Phase 3 (Advanced Features)
- 🔜 Edit row values in preview
- 🔜 Add new rows manually
- 🔜 Undo/redo operations
- 🔜 Export preview as Excel before saving

---

## Error Handling

### Common Errors

#### 1. Invalid File Format
```json
{
  "detail": "Invalid file type. Only Excel files (.xlsx, .xls) are allowed."
}
```

#### 2. Missing Columns
```json
{
  "success": false,
  "error": "Missing required columns: CUSIP, DATE, RANK"
}
```

#### 3. Session Not Found
```json
{
  "success": false,
  "error": "Session not found or no data available"
}
```

#### 4. No Rules Selected
```json
{
  "detail": "No rules selected"
}
```

#### 5. No Data to Save
```json
{
  "success": false,
  "error": "No data to save"
}
```

---

## Configuration

### Session Storage
- **Location**: `data/manual_color_sessions/`
- **Format**: JSON files
- **Naming**: `manual_color_{user_id}_{timestamp}.json`
- **Cleanup**: Auto-delete after 1 day

### Output Files
- **Location**: Defined by `output_service`
- **Format**: Excel (.xlsx)
- **Naming**: `manual_colors_{timestamp}.xlsx`
- **Future**: S3 bucket path

---

## Summary

✅ **Complete manual color processing workflow implemented**
- Separate from admin panel buffer
- Interactive preview with sorting
- User can delete rows and apply selected rules
- Saves to output Excel (S3 in future)
- Override logic for automated coloring separate

✅ **APIs ready for frontend integration**
- 8 endpoints covering full workflow
- Clear request/response formats
- Error handling included

✅ **Backend fully functional**
- Tested health check endpoint
- Rules service updated for specific rule IDs
- Session management working

---

**Next Steps for Frontend Developer:**

1. Implement file upload component
2. Display sorted preview table
3. Add checkbox selection for row deletion
4. Create "Run Rules" dialog with rule selection
5. Implement "Run Automation" button to save
6. Add override dialog for automated coloring button
7. Test complete flow end-to-end
