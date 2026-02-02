# Presets and Rules Logs - API Documentation

## Overview
- **Presets**: Saved filter combinations for security search (no logs, no revert)
- **Rules Logs**: Operation history for rules with revert capability

---

## 1. Presets APIs

### GET /api/presets
Get all saved presets

**Response:**
```json
{
  "presets": [
    {
      "id": 1,
      "name": "Select 102 bank securities",
      "description": "Filter bank securities",
      "conditions": [
        {
          "column": "BWIC_COVER",
          "operator": "equals",
          "value": "Bank"
        }
      ],
      "created_at": "2026-02-02T...",
      "created_by": "admin",
      "updated_at": "2026-02-02T..."
    }
  ],
  "count": 1
}
```

### GET /api/presets/{preset_id}
Get single preset by ID

### POST /api/presets
Create new preset

**Request:**
```json
{
  "name": "Select 102 bank securities",
  "description": "Bank securities filter",
  "conditions": [
    {
      "column": "Bwic",
      "operator": "is eq",
      "value": "JPMC"
    }
  ]
}
```

**Response:**
```json
{
  "message": "Preset created successfully",
  "preset": { ... }
}
```

### PUT /api/presets/{preset_id}
Update existing preset

**Request:**
```json
{
  "name": "Updated preset name",
  "conditions": [ ... ],
  "description": "New description"
}
```

### DELETE /api/presets/{preset_id}
Delete preset

**Response:**
```json
{
  "message": "Preset deleted successfully"
}
```

### POST /api/presets/{preset_id}/apply
Apply preset filters to data

**Request:**
```json
{
  "data": [
    {"CUSIP": "123", "BWIC_COVER": "Bank", ...},
    {"CUSIP": "456", "BWIC_COVER": "Other", ...}
  ]
}
```

**Response:**
```json
{
  "total_rows": 100,
  "filtered_rows": 25,
  "data": [ ... ]
}
```

---

## 2. Rules Logs APIs

### GET /api/logs/rules
Get last 4 rule operation logs

**Query Parameters:**
- `limit` (optional): Number of logs to return (default: 4)

**Response:**
```json
{
  "logs": [
    {
      "log_id": 7,
      "module": "rules",
      "action": "delete",
      "description": "Deleted rule: testing rule1",
      "performed_by": "admin",
      "performed_at": "2026-02-01T16:24:29.013322",
      "entity_id": 1,
      "entity_name": "testing rule1",
      "can_revert": true,
      "revert_data": {
        "action": "restore",
        "rule_data": {
          "id": 1,
          "name": "testing rule1",
          "is_active": true,
          "conditions": [ ... ]
        }
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

### POST /api/logs/{log_id}/revert
Revert a rule operation (restore deleted rule, undo update)

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
  "message": "Successfully restored rule: testing rule1",
  "log_entry": { ... },
  "operation_result": {
    "message": "Restored deleted rule",
    "rule": { ... }
  }
}
```

---

## Frontend Integration

### 1. Presets Section
Display presets as filter templates:
```javascript
// Fetch all presets
const response = await fetch('http://127.0.0.1:3334/api/presets');
const data = await response.json();
// data.presets = array of preset objects
```

### 2. Rules Logs Section
Display with revert button:
```javascript
// Fetch rules logs
const response = await fetch('http://127.0.0.1:3334/api/logs/rules?limit=4');
const data = await response.json();
// data.logs = array of log objects with can_revert: true/false

// Revert a log entry
const revertResponse = await fetch(`http://127.0.0.1:3334/api/logs/${logId}/revert`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ reverted_by: 'admin' })
});
```

### UI Structure (from screenshot)
```
┌─────────────────────────────────────┐
│ Presets                             │
│ ─────────────────────────────────── │
│ [List of saved filter presets]      │
│                                     │
│ Preset Name input field             │
│ Where [Column] [Operator] [Value]   │
│ + Add Condition                     │
│ + Add Subgroup                      │
│ + Add Group                         │
│ ✗ Clear   💾 Save Preset            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Logs                                │
│ Recent rule operations              │
│ ─────────────────────────────────── │
│                                     │
│ Rule created                        │
│ Jan 26, 2026, 11:25 PM | testing... │
│ [↩️ Revert]  ← IF can_revert: true │
│                                     │
│ Rule deleted                        │
│ Jan 26, 2026, 09:29 PM | harsha...  │
│ [↩️ Revert]                        │
└─────────────────────────────────────┘
```

---

## Testing

### Test Presets:
```powershell
# Create preset
curl -X POST http://127.0.0.1:3334/api/presets `
  -H "Content-Type: application/json" `
  -d '{"name":"Select 102 bank securities","conditions":[{"column":"BWIC_COVER","operator":"equals","value":"Bank"}]}'

# Get all presets
curl http://127.0.0.1:3334/api/presets

# Apply preset
curl -X POST http://127.0.0.1:3334/api/presets/1/apply `
  -H "Content-Type: application/json" `
  -d '{"data":[{"BWIC_COVER":"Bank"},{"BWIC_COVER":"Other"}]}'
```

### Test Rules Logs:
```powershell
# Get rules logs
curl http://127.0.0.1:3334/api/logs/rules

# Revert a log
curl -X POST http://127.0.0.1:3334/api/logs/7/revert `
  -H "Content-Type: application/json" `
  -d '{"reverted_by":"admin"}'
```

---

## Implementation Status

✅ **Presets** - Complete
- Create/Read/Update/Delete presets
- Apply preset filters to data
- No logging (simple CRUD only)

✅ **Rules Logs** - Complete
- Get last 4 rule operations
- Revert capability for create/update/delete
- Detailed metadata for each operation
- Revert button data (`can_revert: true`)

---

## Key Differences

| Feature | Presets | Rules Logs |
|---------|---------|------------|
| Purpose | Save filter combinations | Track rule changes |
| Logging | ❌ No logs | ✅ Every operation logged |
| Revert | ❌ Not applicable | ✅ Revert delete/update |
| Storage | `presets.json` | `unified_logs.json` |
| Module | `presets` | `rules` |
