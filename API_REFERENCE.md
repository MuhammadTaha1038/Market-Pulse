# API Reference

## Base URL
```
http://127.0.0.1:3334/api
```

---

## 1. Dashboard APIs

### Get Monthly Statistics
```
GET /dashboard/monthly-stats
```
**Use:** Display monthly color count chart  
**Response:**
```json
{
  "stats": [
    {"month": "2026-01", "count": 245},
    {"month": "2026-02", "count": 189}
  ]
}
```

### Get Today's Colors (Security Search)
```
GET /dashboard/colors?skip=0&limit=50&cusip=XXX&ticker=YYY
```
**Use:** Security search, dashboard data grid  
**Query Parameters:**
- `skip` - Pagination offset (default: 0)
- `limit` - Records to return (default: 10, max: 500)
- `clo_id` - Filter by CLO for column visibility
- `cusip` - Filter by CUSIP
- `ticker` - Filter by ticker symbol
- `message_id` - Filter by message ID
- `asset_class` - Filter by sector
- `source` - Filter by source (TRACE, BLOOMBERG)
- `bias` - Filter by bias (BUY_BIAS, SELL_BIAS)
- `processing_type` - Filter by type (AUTOMATED, MANUAL)
- `date_from` - Start date (YYYY-MM-DD)
- `date_to` - End date (YYYY-MM-DD)

**Response:**
```json
{
  "colors": [
    {
      "message_id": 12345,
      "ticker": "AAPL",
      "cusip": "037833100",
      "date": "2026-02-02",
      "px": 150.25,
      "bias": "BUY_BIAS",
      "rank": 1,
      "is_parent": true,
      "children_count": 3
    }
  ],
  "total": 189,
  "page": 0,
  "page_size": 50
}
```

---

## 2. Manual Color Processing

### Upload Excel File
```
POST /manual-colors/upload
```
**Use:** Manual color upload workflow  
**Body:** `multipart/form-data` with Excel file  
**Response:**
```json
{
  "success": true,
  "colors_count": 50,
  "preview": [...first 10 colors...],
  "session_id": "uuid-here"
}
```

### Submit for Processing
```
POST /manual-colors/submit
```
**Use:** Final submission after preview  
**Body:**
```json
{
  "session_id": "uuid-here",
  "apply_rules": true
}
```

---

## 3. Automation

### Trigger Manual Run
```
POST /cron/trigger
```
**Use:** "Run Automation" button  
**Response:**
```json
{
  "success": true,
  "execution_id": 123,
  "colors_processed": 45,
  "duration_seconds": 12.5
}
```

### Get Cron Job Status
```
GET /cron/jobs
```
**Use:** View scheduled jobs  
**Response:**
```json
{
  "jobs": [
    {
      "id": "automation_job",
      "schedule": "0 8,10,12,14,16,18 * * *",
      "next_run": "2026-02-02T10:00:00",
      "enabled": true
    }
  ]
}
```

---

## 4. Rules Management

### Get All Rules
```
GET /rules
```

### Create Rule
```
POST /rules
```
**Body:**
```json
{
  "name": "Exclude Low Volume",
  "conditions": [
    {"field": "px", "operator": "less_than", "value": 10}
  ],
  "action": "exclude"
}
```

### Apply Preset
```
POST /presets/{preset_id}/apply
```
**Body:** Array of color objects

---

## 5. Admin APIs

### System Status
```
GET /admin/system-status
```
**Use:** Check Oracle/S3 connection status  
**Response:**
```json
{
  "success": true,
  "overall_status": "ready",
  "data_source": {
    "info": {"type": "Oracle", "host": "..."},
    "connection_test": {"status": "success"},
    "ready": true
  },
  "output_destination": {
    "info": {"type": "AWS S3", "bucket": "..."},
    "connection_test": {"status": "success"},
    "ready": true
  }
}
```

### CLO Column Mappings
```
GET /admin/clo-mappings
POST /admin/clo-mappings
PUT /admin/clo-mappings/{clo_id}
```
**Use:** Configure visible columns per CLO

---

## 6. Logs

### Get Unified Logs
```
GET /logs?level=INFO&limit=100&source=automation
```
**Query Parameters:**
- `level` - ERROR, WARNING, INFO
- `limit` - Number of logs (default: 100)
- `source` - Filter by source (automation, manual_upload, etc.)
- `date_from` / `date_to` - Date range

---

## Common Response Structure

### Success
```json
{
  "success": true,
  "message": "Operation completed",
  "data": {...}
}
```

### Error
```json
{
  "detail": "Error message here"
}
```

---

## Data Models

### ColorRaw (Input)
```json
{
  "message_id": 12345,
  "ticker": "AAPL",
  "sector": "MM-CLO",
  "cusip": "037833100",
  "date": "2026-02-02",
  "price_level": 100.5,
  "bid": 100.25,
  "ask": 100.75,
  "px": 100.5,
  "source": "TRACE",
  "bias": "BUY_BIAS"
}
```

### ColorProcessed (Output)
```json
{
  ...all ColorRaw fields...,
  "rank": 1,
  "cov_price": 99.8,
  "percent_diff": 0.7,
  "price_diff": 0.7,
  "confidence": 95,
  "date_1": "2026-02-01",
  "diff_status": "HIGHER",
  "is_parent": true,
  "parent_message_id": null,
  "children_count": 3,
  "processed_at": "2026-02-02T10:30:00",
  "processing_type": "AUTOMATED"
}
```

---

## Authentication
**Current:** None (demo mode)  
**Production:** Add JWT tokens to all requests
```
Authorization: Bearer <token>
```
