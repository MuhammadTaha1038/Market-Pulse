# Settings Page - Unified Logs System

## Problem
User reported that each section (Rules, Cron Jobs, Manual Upload, Email/Restore, Presets) has different logs, and Settings page should show the recent 2 logs from each section instead of mock data.

## Solution Overview

### Backend - Unified Logs API
Created `/api/logs/recent` endpoint that aggregates logs from all sources:
- Rules logs (rule creation, deletion, updates)
- Cron job execution logs  
- Manual upload logs
- Backup/restore activity logs
- (Presets logs - to be implemented)

### Frontend - Logs Display
Each section in Settings page shows its own recent logs:
- **Rules Section**: Show last 2 rule operations
- **Cron Jobs Section**: Show last 2 job executions
- **Manual Colors Section**: Show last 2 uploads
- **Restore & Email Section**: Show last 2 activities
- **Presets Section**: Show last 2 preset operations

## Implementation

### 1. Backend - Log Sources

#### Rules Logs
- Storage: Not currently saved to JSON (rules_service.py doesn't have log storage)
- **Action**: Need to add logging when rules are created/updated/deleted
- Format: `{"action": "Rule created", "details": "Rule name", "timestamp": "...", "user": "admin"}`

#### Cron Job Logs  
- Storage: `data/cron_logs.json`
- API: `/api/cron/logs`
- Format: `{"job_id": 1, "job_name": "...", "status": "success", "execution_time": "...", "duration_seconds": 2.5}`

#### Manual Upload Logs
- Storage: `data/manual_upload_history.json`
- API: `/api/manual-upload/history`
- Format: `{"id": 1, "filename": "...", "status": "success", "upload_time": "...", "rows_processed": 5213}`

#### Backup/Restore Logs
- Storage: `data/activity_logs.json`
- API: `/api/backup/activity-logs`
- Format: `{"action": "Backup created", "details": "...", "timestamp": "...", "user": "admin"}`

### 2. Dynamic Column Configuration

#### New API Endpoints
Created `/api/config/*` endpoints for managing column configuration:
- `GET /api/config/columns` - Get all columns
- `GET /api/config/columns/required` - Get required vs optional columns
- `POST /api/config/columns` - Add new column
- `PUT /api/config/columns/{id}` - Update column
- `DELETE /api/config/columns/{id}` - Delete column

#### Manual Upload Validation
Updated `manual_upload_service.py` to use dynamic column config:
- Instead of hardcoded required columns list
- Now calls `column_config.get_required_columns()` 
- Template info endpoint returns dynamic columns

## Next Steps

### Immediate (Required by User)
1. ✅ Add column config API
2. ✅ Update manual upload to use dynamic columns
3. ⏳ Add Rules logging (save rule operations to JSON)
4. ⏳ Create unified logs API endpoint
5. ⏳ Update frontend to call logs APIs per section
6. ⏳ Show recent 2 logs in each section

### Rules Logging Implementation Needed
```python
# In rules_service.py, add:
def save_rule_log(action: str, rule_name: str, user: str = "admin"):
    logs = get_rule_logs()
    log_entry = {
        "id": len(logs) + 1,
        "action": action,
        "rule_name": rule_name,
        "timestamp": datetime.now().isoformat(),
        "user": user
    }
    logs.insert(0, log_entry)
    storage.save("rule_logs", {"logs": logs})
```

### Frontend Updates Needed
1. Create LogsService to fetch logs from each API
2. Update settings.ts to have separate log arrays per section
3. Update settings.html to show logs using *ngFor with limit 2
4. Call log APIs in ngOnInit()

## Files Modified
- `column_config.py` (NEW) - Column config API router
- `handler.py` - Added column config router
- `manual_upload_service.py` - Use dynamic column config
- `manual_upload.py` - Template info uses dynamic columns

## Files To Create
- `logs_aggregator.py` - Unified logs API
- `logs.service.ts` - Frontend logs service

## Testing
```powershell
# Test column config API
curl.exe -X GET "http://127.0.0.1:3334/api/config/columns/required"

# Expected response:
{
  "required_columns": ["MESSAGE_ID", "TICKER", "CUSIP", ...],
  "optional_columns": ["BID", "ASK", ...]
}

# Test manual upload with dynamic validation
curl.exe -X POST "http://127.0.0.1:3334/api/manual-upload/upload" `
  -F "file=@test.xlsx" `
  -F "uploaded_by=admin"
```

## Column Configuration Benefits
1. **Future-proof**: Admin can add/remove columns without code changes
2. **Consistent**: All services use same column definitions
3. **Maintainable**: Single source of truth (column_config.json)
4. **Flexible**: Can change Oracle table structure without deployment
