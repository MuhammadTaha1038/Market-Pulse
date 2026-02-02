# MarketPulse API Documentation

**Version**: 1.2  
**Last Updated**: January 26, 2026  
**Base URL**: `http://127.0.0.1:3334/api`

## Table of Contents
1. [Configuration APIs](#configuration-apis)
2. [Rules APIs](#rules-apis)
3. [Cron Jobs APIs](#cron-jobs-apis)
4. [Manual Upload APIs](#manual-upload-apis)
5. [Dashboard APIs](#dashboard-apis)
6. [Backup & Restore APIs](#backup--restore-apis)

---

## Configuration APIs

### Get All Columns
Retrieve all available column names from the system.

**Endpoint**: `GET /api/config/columns`

**Response**:
```json
{
  "columns": [
    "Bwic Cover",
    "Security Name",
    "Issuer",
    "Cusip",
    "Price",
    "Yield",
    "Maturity",
    "Coupon"
  ]
}
```

---

### Get Required Columns
Get validation configuration for required and optional columns.

**Endpoint**: `GET /api/config/columns/required`

**Response**:
```json
{
  "required": ["Bwic Cover", "Cusip", "Security Name"],
  "optional": ["Price", "Yield", "Maturity", "Coupon"]
}
```

**Usage**: Use this endpoint to validate file uploads and configure rule column dropdowns.

---

### Update Column Configuration
Update the required and optional column lists.

**Endpoint**: `PUT /api/config/columns`

**Request Body**:
```json
{
  "required": ["Bwic Cover", "Cusip"],
  "optional": ["Price", "Yield"]
}
```

**Response**:
```json
{
  "message": "Column configuration updated successfully",
  "required": ["Bwic Cover", "Cusip"],
  "optional": ["Price", "Yield"]
}
```

---

## Rules APIs

### Get All Rules
Retrieve all exclusion rules.

**Endpoint**: `GET /api/rules`

**Response**:
```json
{
  "rules": [
    {
      "id": 1,
      "name": "Exclude JPMC",
      "conditions": [
        {
          "type": "where",
          "column": "Bwic Cover",
          "operator": "is equal to",
          "value": "JPMC"
        }
      ],
      "is_active": true,
      "created_at": "2026-01-26T10:00:00",
      "updated_at": "2026-01-26T10:00:00"
    }
  ]
}
```

**Rule Condition Types**:
- `where`: First condition in the rule
- `and`: AND logical operator
- `or`: OR logical operator

**Operators**:
- `is equal to`: Exact match (case-insensitive)
- `is not equal to`: Not equal
- `contains`: Substring match
- `does not contain`: Does not contain substring
- `starts with`: Starts with value
- `ends with`: Ends with value
- `is greater than`: Numeric comparison (>)
- `is less than`: Numeric comparison (<)

---

### Get Single Rule
Retrieve a specific rule by ID.

**Endpoint**: `GET /api/rules/{rule_id}`

**Response**: Same format as individual rule in "Get All Rules"

---

### Create Rule
Create a new exclusion rule.

**Endpoint**: `POST /api/rules`

**Request Body**:
```json
{
  "name": "Exclude JPMC",
  "conditions": [
    {
      "type": "where",
      "column": "Bwic Cover",
      "operator": "is equal to",
      "value": "JPMC"
    },
    {
      "type": "and",
      "column": "Price",
      "operator": "is greater than",
      "value": "100"
    }
  ],
  "is_active": true
}
```

**Response**:
```json
{
  "message": "Rule created successfully",
  "rule": {
    "id": 1,
    "name": "Exclude JPMC",
    "conditions": [...],
    "is_active": true,
    "created_at": "2026-01-26T10:00:00",
    "updated_at": "2026-01-26T10:00:00"
  }
}
```

---

### Update Rule
Update an existing rule.

**Endpoint**: `PUT /api/rules/{rule_id}`

**Request Body**: Same as Create Rule

**Response**:
```json
{
  "message": "Rule updated successfully",
  "rule": {...}
}
```

---

### Delete Rule
Delete a rule permanently.

**Endpoint**: `DELETE /api/rules/{rule_id}`

**Response**:
```json
{
  "message": "Rule deleted successfully"
}
```

---

### Get Rule Operation Logs
Retrieve operation history for rules (create/update/delete).

**Endpoint**: `GET /api/rules/logs?limit=10`

**Query Parameters**:
- `limit` (int, optional): Maximum logs to return (default: 50)

**Response**:
```json
{
  "logs": [
    {
      "id": 1,
      "action": "created",
      "rule_name": "Exclude JPMC",
      "details": "Rule created with 2 conditions",
      "user": "admin",
      "timestamp": "2026-01-26T10:00:00"
    }
  ],
  "count": 1
}
```

---

## Cron Jobs APIs

For detailed cron job documentation including timezone configuration, execution flow, and all endpoints, see:
**[API_CRON_JOBS.md](./API_CRON_JOBS.md)**

### Quick Reference

**Key Endpoints**:
- `GET /api/cron/jobs` - List all jobs
- `POST /api/cron/jobs` - Create job
- `PUT /api/cron/jobs/{id}` - Update job
- `DELETE /api/cron/jobs/{id}` - Delete job
- `GET /api/cron/logs` - Execution history
- `POST /api/cron/jobs/{id}/trigger` - Manual trigger

---

## Manual Upload APIs

### Upload Colors File
Upload an Excel file for manual color processing. Files are buffered and processed during the next scheduled cron job run.

**Endpoint**: `POST /api/manual-upload`

**Request**: Multipart form data
- `file`: Excel file (.xlsx)

**Response**:
```json
{
  "message": "File uploaded successfully",
  "upload": {
    "id": 1,
    "filename": "colors.xlsx",
    "upload_time": "2026-01-26T10:00:00",
    "uploaded_by": "admin",
    "status": "pending",
    "rows_uploaded": 5213,
    "processing_type": "MANUAL",
    "message": "File uploaded and buffered. Will be processed in next scheduled automation run."
  }
}
```

**Important Workflow Change**:
- Files are **NOT** processed immediately upon upload
- Files are saved to a buffer directory
- Processing occurs during the next scheduled cron job run
- This ensures consistent processing with rules and ranking

**Response Fields**:
- `status` (string): Will be "pending" after upload (changes to "success" or "failed" after processing)
- `rows_uploaded` (int): Number of rows in the uploaded file
- `message` (string): Information about buffer status

**Validation**:
- File must be .xlsx format
- Must contain all required columns (from `/api/config/columns/required`)
- Column names are case-insensitive

**Error Responses**:
- `400 Bad Request`: Invalid file format or missing required columns
- `422 Unprocessable Entity`: File validation error

---

### Get Upload History
Retrieve manual upload history.

**Endpoint**: `GET /api/manual-upload/history?limit=10`

**Query Parameters**:
- `limit` (int, optional): Maximum records to return (default: 50)

**Response**:
```json
{
  "uploads": [
    {
      "id": 1,
      "filename": "colors.xlsx",
      "upload_time": "2026-01-26T10:00:00",
      "uploaded_by": "admin",
      "status": "success",
      "rows_uploaded": 5213,
      "rows_processed": 5213,
      "processing_type": "MANUAL",
      "processing_time": "2026-01-26T11:00:00",
      "duration_seconds": 45.2
    },
    {
      "id": 2,
      "filename": "colors2.xlsx",
      "upload_time": "2026-01-26T12:00:00",
      "uploaded_by": "admin",
      "status": "pending",
      "rows_uploaded": 3000,
      "processing_type": "MANUAL",
      "message": "File buffered and will be processed in next scheduled run"
    }
  ],
  "count": 2
}
```

**Status Values**:
- `pending`: File buffered, waiting for next cron run
- `success`: File processed successfully during cron run
- `failed`: Validation or processing error occurred

---

## Dashboard APIs

### Get Processed Colors
Retrieve processed colors for dashboard display.

**Endpoint**: `GET /api/dashboard/colors?processing_type=AUTOMATED&cusip=123456789`

**Query Parameters**:
- `processing_type` (string, optional): Filter by type ("AUTOMATED" or "MANUAL")
- `cusip` (string, optional): Filter by specific CUSIP

**Response**:
```json
{
  "colors": [
    {
      "bwic_cover": "BAML",
      "security_name": "ABC Corp Bond",
      "issuer": "ABC Corp",
      "cusip": "123456789",
      "price": 101.5,
      "yield": 4.25,
      "rank": 1,
      "is_parent": true,
      "parent_cusip": "123456789",
      "parent_message_id": "MSG001",
      "children_count": 5,
      "processing_type": "AUTOMATED",
      "processed_at": "2026-01-26T10:00:00"
    }
  ],
  "count": 1
}
```

**Field Descriptions**:
- `rank`: Ranking within CUSIP group (1 = parent/best)
- `is_parent`: Whether this is the parent record
- `children_count`: Number of child records (parent only)
- `parent_message_id`: Message ID of parent (children only)
- `processing_type`: "AUTOMATED" (cron) or "MANUAL" (upload)

---

## Backup & Restore APIs

### Get Backup History
Retrieve backup history.

**Endpoint**: `GET /api/backup/history`

**Response**:
```json
{
  "backups": [
    {
      "id": 1,
      "timestamp": "2026-01-26T10:00:00",
      "type": "manual",
      "description": "Pre-update backup",
      "size_bytes": 1024000,
      "status": "completed"
    }
  ],
  "count": 1
}
```

---

### Create Backup
Create a new backup of current data.

**Endpoint**: `POST /api/backup`

**Request Body**:
```json
{
  "description": "Manual backup before changes"
}
```

**Response**:
```json
{
  "message": "Backup created successfully",
  "backup_id": 1,
  "timestamp": "2026-01-26T10:00:00"
}
```

---

### Restore from Backup
Restore data from a specific backup.

**Endpoint**: `POST /api/backup/restore/{backup_id}`

**Response**:
```json
{
  "message": "Backup restored successfully",
  "restored_from": "2026-01-26T10:00:00"
}
```

---

### Get Activity Logs
Retrieve backup/restore activity history.

**Endpoint**: `GET /api/backup/activity-logs?limit=10`

**Query Parameters**:
- `limit` (int, optional): Maximum logs to return (default: 50)

**Response**:
```json
{
  "logs": [
    {
      "id": 1,
      "action": "backup_created",
      "details": "Manual backup",
      "user": "admin",
      "timestamp": "2026-01-26T10:00:00"
    }
  ],
  "count": 1
}
```

---

## Common Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

---

## Authentication

**Current Version**: No authentication required  
**Future**: JWT-based authentication will be added

---

## Rate Limiting

**Current Version**: No rate limiting  
**Future**: Rate limiting may be implemented for production

---

## CORS Configuration

**Current Version**: Allows all origins (`*`)  
**Production**: Should be configured to specific frontend domain

---

## Data Flow Architecture

```
┌─────────────┐
│   Oracle    │ (Future)
│  Database   │
└──────┬──────┘
       │ OR
┌──────▼──────┐
│ Excel File  │ (Current)
│ Color.xlsx  │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│  Rules      │ ───► │   Ranking    │
│  Engine     │      │   Engine     │
└─────────────┘      └───────┬──────┘
                             │
                             ▼
                     ┌──────────────┐
                     │ Output File  │
                     │ (S3/Excel)   │
                     └───────┬──────┘
                             │
                             ▼
                     ┌──────────────┐
                     │  Dashboard   │
                     │   Display    │
                     └──────────────┘
```

**Processing Types**:
1. **Automated (Cron)**: Scheduled runs via cron jobs
2. **Manual Upload**: User-initiated file upload

---

## Column Configuration

**Important**: Column names are dynamically configurable via `/api/config/columns` API.

**Usage**:
- Rules UI fetches columns from this API to populate dropdowns
- Manual upload validation uses required columns from this API
- Both frontend and backend use the same column configuration

**Default Columns**:
- Required: Bwic Cover, Cusip, Security Name
- Optional: Price, Yield, Maturity, Coupon

---

## Version History

### v1.3 (2026-02-01)
- **BREAKING CHANGE**: Manual uploads now buffered instead of processed immediately
- Manual upload files are saved to buffer and processed during next scheduled cron run
- Added buffered file processing to cron automation workflow
- Upload history now shows "pending" status for buffered files
- Cron execution logs now include manual_files_processed and manual_files_failed counts
- Updated API documentation to reflect new workflow

### v1.2 (2026-01-26)
- Added centralized column configuration API
- Rules UI now uses dynamic column names from API
- Manual upload validation uses configurable columns
- Created ConfigService in frontend for column management
- NaN value handling in dashboard for robust data display

### v1.1 (2026-01-26)
- Added cron job execution logging with auto-incrementing IDs
- Added timezone support to APScheduler
- Fixed timestamp mapping in logs display
- Enhanced log details with processing statistics

### v1.0 (Initial Release)
- Core APIs for rules, cron jobs, manual upload
- Dashboard data retrieval
- Backup and restore functionality
- JSON file storage (S3 placeholder)

---

## Support & Contact

For API integration support or questions, contact the development team.

**Server**: http://127.0.0.1:3334  
**Health Check**: `GET /health` (if implemented)  
**API Prefix**: `/api`
