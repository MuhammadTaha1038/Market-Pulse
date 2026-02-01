# Backend API Reference & Setup Guide

## How to Run Backend

```bash
# Navigate to backend directory
cd "Data-main\sp-incb-market-pulse-master\src\main"

# Run the server
python handler.py
```

**Backend URL**: `http://127.0.0.1:3334`

---

## Backend File Structure

```
sp-incb-market-pulse-master/
├── src/main/
│   ├── handler.py                          # Main FastAPI app
│   ├── storage_config.py                   # Storage configuration (JSON/S3/Oracle)
│   ├── db_config.py                        # Database configuration
│   │
│   ├── services/                           # Business logic services
│   │   ├── manual_color_service.py         # Manual color processing
│   │   ├── ranking_engine.py               # Sorting logic (DATE>RANK>PX)
│   │   ├── output_service.py               # Output file generation
│   │   └── column_config_service.py        # Column configuration
│   │
│   ├── routers/                            # API endpoints
│   │   ├── manual_color.py                 # Manual color APIs (NEW)
│   │   ├── dashboard.py                    # Dashboard APIs
│   │   ├── manual_colors.py                # Manual colors page
│   │   └── admin.py                        # Admin APIs
│   │
│   ├── rules.py                            # Rules engine APIs
│   ├── rules_service.py                    # Rules business logic
│   ├── cron_jobs.py                        # Cron job APIs
│   ├── cron_service.py                     # Automation logic
│   ├── manual_upload.py                    # Manual upload APIs (Admin panel)
│   ├── manual_upload_service.py            # Upload service
│   ├── backup_restore.py                   # Backup APIs
│   ├── backup_service.py                   # Backup logic
│   ├── column_config.py                    # Column config APIs
│   ├── email_router.py                     # Email APIs
│   ├── unified_logs.py                     # Logging & revert APIs
│   ├── logging_service.py                  # Unified logging
│   ├── revert_service.py                   # Revert operations
│   │
│   ├── models/                             # Data models
│   │   └── color.py                        # Color data models
│   │
│   └── data/                               # Data storage (JSON files)
│       ├── rules.json                      # Rules data
│       ├── cron_jobs.json                  # Cron jobs data
│       ├── unified_logs.json               # Logs data
│       ├── backup_history.json             # Backup history
│       └── manual_color_sessions/          # Manual color sessions
```

---

## API Endpoints & Data Structures

### 1. Manual Color Processing (Color Page)

#### 1.1 Import Excel File
```
POST /api/manual-color/import
Content-Type: multipart/form-data
```

**Request:**
```
FormData:
- file: Excel file (.xlsx, .xls)
- user_id: 1 (integer)
```

**Response:**
```json
{
  "success": true,
  "session_id": "manual_color_1_20260201_233000",
  "filename": "colors.xlsx",
  "rows_imported": 100,
  "rows_valid": 98,
  "parsing_errors": ["Row 5: Invalid date format"],
  "sorted_preview": [
    {
      "row_id": 0,
      "message_id": "TEST001",
      "cusip": "961644AC4",
      "ticker": "BESXP15",
      "date": "2026-07-19T00:00:00",
      "rank": 1,
      "px": 100.5,
      "bid": 100.2,
      "mid": 101.3,
      "ask": 102.2,
      "source": "MANUAL",
      "bias": "BWC_COVER",
      "is_parent": true,
      "parent_id": null,
      "child_count": 1,
      "color": "GREEN"
    }
  ],
  "statistics": {
    "total_rows": 98,
    "parent_rows": 45,
    "child_rows": 53,
    "unique_cusips": 45
  },
  "duration_seconds": 1.5
}
```

#### 1.2 Get Preview
```
GET /api/manual-color/preview/{session_id}
```

**Response:**
```json
{
  "success": true,
  "session_id": "manual_color_1_20260201_233000",
  "data": [ /* same as sorted_preview */ ],
  "applied_rules": [1, 3],
  "deleted_rows": [5, 12],
  "statistics": {
    "total_rows": 85,
    "parent_rows": 42,
    "child_rows": 43
  }
}
```

#### 1.3 Delete Rows
```
POST /api/manual-color/delete-rows
Content-Type: application/json
```

**Request:**
```json
{
  "session_id": "manual_color_1_20260201_233000",
  "row_ids": [5, 12, 23]
}
```

**Response:**
```json
{
  "success": true,
  "deleted_count": 3,
  "remaining_rows": 95,
  "data": [ /* updated preview */ ]
}
```

#### 1.4 Apply Rules
```
POST /api/manual-color/apply-rules
Content-Type: application/json
```

**Request:**
```json
{
  "session_id": "manual_color_1_20260201_233000",
  "rule_ids": [1, 3, 5]
}
```

**Response:**
```json
{
  "success": true,
  "rules_applied": 3,
  "excluded_count": 15,
  "remaining_rows": 83,
  "data": [ /* filtered preview */ ],
  "rules_info": [
    {"id": 1, "name": "Exclude TEST symbols"},
    {"id": 3, "name": "Exclude invalid prices"}
  ]
}
```

#### 1.5 Save Manual Colors
```
POST /api/manual-color/save
Content-Type: application/json
```

**Request:**
```json
{
  "session_id": "manual_color_1_20260201_233000",
  "user_id": 1
}
```

**Response:**
```json
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

---

### 2. Rules Management

#### 2.1 Get All Rules
```
GET /api/rules
```

**Response:**
```json
{
  "rules": [
    {
      "id": 1,
      "name": "Exclude TEST symbols",
      "is_active": true,
      "conditions": [
        {
          "field": "TICKER",
          "operator": "contains",
          "value": "TEST",
          "logic_operator": "AND"
        }
      ],
      "created_at": "2026-01-20T10:30:00",
      "updated_at": "2026-01-25T15:45:00"
    }
  ],
  "count": 1
}
```

#### 2.2 Create Rule
```
POST /api/rules
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Exclude low prices",
  "market_data": {
    "market_symbols": ["CL", "NG"],
    "delivery_months": ["MAR 2026", "APR 2026"]
  },
  "conditions": [
    {
      "field": "PX",
      "operator": "<",
      "value": 50,
      "logic_operator": "AND"
    }
  ],
  "triggered_actions": {
    "color": "RED",
    "email_notifications": ["admin@example.com"],
    "email_subject": "Low Price Alert",
    "email_body": "Price below threshold"
  },
  "priority": 1,
  "is_active": true,
  "user_id": 1
}
```

**Response:**
```json
{
  "message": "Rule created successfully",
  "rule": {
    "id": 2,
    "name": "Exclude low prices",
    "is_active": true,
    "conditions": [ /* same as request */ ],
    "created_at": "2026-02-01T16:16:00.357611",
    "updated_at": "2026-02-01T16:16:00.357622"
  }
}
```

#### 2.3 Update Rule
```
PUT /api/rules/{id}
Content-Type: application/json
```

**Request:** Same structure as Create Rule

**Response:**
```json
{
  "message": "Rule updated successfully",
  "rule": { /* updated rule object */ }
}
```

#### 2.4 Delete Rule
```
DELETE /api/rules/{id}
```

**Response:**
```json
{
  "message": "Rule deleted successfully"
}
```

---

### 3. Automation & Cron Jobs

#### 3.1 Get All Cron Jobs
```
GET /api/cron/jobs
```

**Response:**
```json
{
  "jobs": [
    {
      "id": 1,
      "name": "Daily Market Processing",
      "schedule": "0 9 * * *",
      "is_active": true,
      "created_at": "2026-01-15T10:00:00",
      "last_run": "2026-02-01T09:00:00",
      "next_run": "2026-02-02T09:00:00+05:00"
    }
  ],
  "count": 1
}
```

#### 3.2 Create Cron Job
```
POST /api/cron/jobs
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Evening Cleanup",
  "schedule": "0 18 * * *",
  "is_active": true
}
```

**Response:**
```json
{
  "message": "Job created and scheduled successfully",
  "job": {
    "id": 2,
    "name": "Evening Cleanup",
    "schedule": "0 18 * * *",
    "is_active": true
  }
}
```

#### 3.3 Trigger Automation (with Override)
```
POST /api/cron/jobs/{id}/trigger?override=true
POST /api/cron/jobs/{id}/trigger?override=false
```

**Response:**
```json
{
  "message": "Job triggered successfully with override (next scheduled run cancelled)",
  "job": {
    "id": 1,
    "name": "Daily Market Processing",
    "schedule": "0 9 * * *",
    "is_active": true,
    "last_run": "2026-02-01T16:15:31.668570"
  },
  "override": true
}
```

---

### 4. Audit Logs & Revert

#### 4.1 Get Last 4 Rules Changes
```
GET /api/logs/rules
```

**Response:**
```json
{
  "logs": [
    {
      "log_id": 5,
      "module": "rules",
      "action": "delete",
      "description": "Deleted rule: Test Logging Rule",
      "performed_by": "admin",
      "performed_at": "2026-02-01T16:16:55.396272",
      "entity_id": 2,
      "entity_name": "Test Logging Rule",
      "can_revert": true,
      "revert_data": {
        "action": "restore",
        "rule_data": { /* full rule snapshot */ }
      },
      "reverted_at": null,
      "reverted_by": null,
      "metadata": {
        "conditions_count": 1
      }
    }
  ],
  "count": 4,
  "module": "rules"
}
```

#### 4.2 Get Log Statistics
```
GET /api/logs/stats
```

**Response:**
```json
{
  "total_logs": 25,
  "by_module": {
    "rules": 15,
    "cron": 8,
    "presets": 2
  },
  "revertable_count": 20
}
```

#### 4.3 Revert a Change
```
POST /api/logs/{log_id}/revert
Content-Type: application/json
```

**Request:**
```json
{
  "reverted_by": "admin"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reverted: Restored rule Test Logging Rule to previous state",
  "log_entry": { /* updated log with reverted_at timestamp */ }
}
```

---

## Common Data Structures

### Rule Condition
```json
{
  "field": "PX",           // Column name
  "operator": ">",         // Available: >, <, >=, <=, ==, !=, contains, starts_with, ends_with
  "value": 100,            // Value to compare
  "logic_operator": "AND"  // AND or OR
}
```

### Cron Schedule Format
```
"0 9 * * *"   - Every day at 9:00 AM
"30 18 * * *" - Every day at 6:30 PM
"0 */4 * * *" - Every 4 hours
"0 9 * * 1"   - Every Monday at 9:00 AM
```

### Color Row Data
```json
{
  "row_id": 0,
  "message_id": "MSG123",
  "cusip": "961644AC4",
  "ticker": "BESXP15",
  "date": "2026-07-19T00:00:00",
  "rank": 1,
  "px": 100.5,
  "bid": 100.2,
  "mid": 101.3,
  "ask": 102.2,
  "source": "MANUAL",
  "bias": "BWC_COVER",
  "is_parent": true,
  "parent_id": null,
  "child_count": 2,
  "color": "GREEN"
}
```

---

## Frontend Pages Mapping

| Page | Frontend Route | APIs Used |
|------|---------------|-----------|
| Manual Color Processing | `/manual-color` | `/api/manual-color/*` |
| Color Selection (Automated) | `/color-type` | `/api/cron/jobs/{id}/trigger` |
| Settings - Rules | `/settings` | `/api/rules/*` |
| Settings - Cron Jobs | `/settings` | `/api/cron/jobs/*` |
| Settings - Logs | `/settings` | `/api/logs/*` |

---

## Quick Integration Example

```typescript
// Import manual colors
const formData = new FormData();
formData.append('file', file);
formData.append('user_id', '1');

const importRes = await fetch('http://127.0.0.1:3334/api/manual-color/import', {
  method: 'POST',
  body: formData
});
const { session_id, sorted_preview } = await importRes.json();

// Delete rows
await fetch('http://127.0.0.1:3334/api/manual-color/delete-rows', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id, row_ids: [1, 5] })
});

// Apply rules
await fetch('http://127.0.0.1:3334/api/manual-color/apply-rules', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id, rule_ids: [1, 3] })
});

// Save
await fetch('http://127.0.0.1:3334/api/manual-color/save', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ session_id, user_id: 1 })
});
```
