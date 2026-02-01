# Rules Engine - Testing Guide

## 🎉 Phase 1 Complete: Rules Engine Implemented!

### ✅ What's Been Created:

**Core Files:**
- `storage_interface.py` - Abstraction for JSON/S3/Oracle
- `json_storage.py` - JSON file implementation (active now)
- `storage_config.py` - Configuration switch point
- `rules_service.py` - Core business logic
- `rules.py` - FastAPI API endpoints

**Integration:**
- Rules integrated with dashboard.py (exclusion applied before ranking)
- Router registered in handler.py

**Storage:**
- Rules stored in: `data/rules.json`
- Using JSON files (no credentials needed)
- Ready to switch to S3/Oracle later (just change config!)

---

## 🚀 Server Status

```
✅ Server Running: http://127.0.0.1:3334
✅ Storage: JSON (data/ folder)
✅ Rules Engine: Active
```

---

## 📡 API Endpoints

### Base URL: `http://127.0.0.1:3334`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rules` | Get all rules |
| GET | `/api/rules/active` | Get active rules only |
| GET | `/api/rules/{id}` | Get single rule |
| POST | `/api/rules` | Create new rule |
| PUT | `/api/rules/{id}` | Update rule |
| DELETE | `/api/rules/{id}` | Delete rule |
| POST | `/api/rules/{id}/toggle` | Activate/deactivate rule |
| POST | `/api/rules/test` | Test rule without saving |
| GET | `/api/rules/operators/list` | Get supported operators |

---

## 🧪 Testing the APIs

### 1. Get All Rules (Empty initially)
```powershell
curl http://127.0.0.1:3334/api/rules
```

**Expected Response:**
```json
{
  "rules": [],
  "count": 0
}
```

### 2. Create First Rule: "Remove DZ Bank Securities"
```powershell
curl -X POST http://127.0.0.1:3334/api/rules `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Remove DZ Bank Securities",
    "is_active": true,
    "conditions": [
      {
        "type": "where",
        "column": "BWIC_COVER",
        "operator": "equals",
        "value": "DZ Bank"
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "message": "Rule created successfully",
  "rule": {
    "id": 1,
    "name": "Remove DZ Bank Securities",
    "is_active": true,
    "conditions": [...],
    "created_at": "2026-01-26T15:40:00",
    "updated_at": "2026-01-26T15:40:00"
  }
}
```

### 3. Create Second Rule: "Remove Performance Trust"
```powershell
curl -X POST http://127.0.0.1:3334/api/rules `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Remove Performance Trust Offers",
    "is_active": true,
    "conditions": [
      {
        "type": "where",
        "column": "SECURITY_NAME",
        "operator": "contains",
        "value": "Performance Trust"
      }
    ]
  }'
```

### 4. Create Complex Rule: Multiple Conditions
```powershell
curl -X POST http://127.0.0.1:3334/api/rules `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Remove Low Price Bank Securities",
    "is_active": true,
    "conditions": [
      {
        "type": "where",
        "column": "BWIC_COVER",
        "operator": "starts_with",
        "value": "Bank"
      },
      {
        "type": "and",
        "column": "PX",
        "operator": "less_than",
        "value": "50"
      }
    ]
  }'
```

### 5. Get All Rules
```powershell
curl http://127.0.0.1:3334/api/rules
```

### 6. Get Active Rules Only
```powershell
curl http://127.0.0.1:3334/api/rules/active
```

### 7. Toggle Rule (Deactivate)
```powershell
curl -X POST http://127.0.0.1:3334/api/rules/1/toggle
```

### 8. Update Rule
```powershell
curl -X PUT http://127.0.0.1:3334/api/rules/1 `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Updated Rule Name",
    "is_active": false
  }'
```

### 9. Delete Rule
```powershell
curl -X DELETE http://127.0.0.1:3334/api/rules/1
```

### 10. Get Supported Operators
```powershell
curl http://127.0.0.1:3334/api/rules/operators/list
```

**Response:**
```json
{
  "operators": [
    {"value": "equals", "label": "is equal to", "type": "string"},
    {"value": "not_equals", "label": "is not equal to", "type": "string"},
    {"value": "contains", "label": "contains", "type": "string"},
    {"value": "not_contains", "label": "does not contain", "type": "string"},
    {"value": "starts_with", "label": "starts with", "type": "string"},
    {"value": "ends_with", "label": "ends with", "type": "string"},
    {"value": "greater_than", "label": "is greater than", "type": "numeric"},
    {"value": "less_than", "label": "is less than", "type": "numeric"},
    {"value": "greater_or_equal", "label": "is greater than or equal to", "type": "numeric"},
    {"value": "less_or_equal", "label": "is less than or equal to", "type": "numeric"}
  ]
}
```

---

## 🔍 Testing Rule Application

### Test Dashboard API (with rules applied)
```powershell
curl http://127.0.0.1:3334/api/dashboard/colors
```

**What happens:**
1. Fetches raw colors from database
2. ✅ **Applies active rules** (excludes matching rows)
3. Runs ranking engine (DATE → RANK → PX)
4. Returns processed colors

**Console Output:**
```
📋 Active rules: 2/2
📊 Original: 5213 rows
📊 Excluded: 145 rows
📊 Remaining: 5068 rows
✅ Rules applied: 2 active rules
```

---

## 📁 File Structure Created

```
sp-incb-market-pulse-master/
├── src/main/
│   ├── storage_interface.py     # ✅ NEW
│   ├── json_storage.py          # ✅ NEW
│   ├── storage_config.py        # ✅ NEW
│   ├── rules_service.py         # ✅ NEW
│   ├── rules.py                 # ✅ NEW (router)
│   ├── handler.py               # ✏️ Modified (added rules router)
│   └── routers/
│       └── dashboard.py         # ✏️ Modified (added rules integration)
└── data/
    └── rules.json               # ✅ Auto-created (storage)
```

---

## 🔄 How Rules Work

### Rule Evaluation Logic:

1. **Fetch Data** → Load colors from database
2. **Apply Rules** → Check each row against active rules
3. **Exclusion** → If ANY rule matches, row is excluded
4. **Ranking** → Remaining rows go to ranking engine

### Condition Types:

- **WHERE** - First condition (always present)
- **AND** - All conditions must match
- **OR** - Any condition can match

### Operators:

**String Operators:**
- `equals` - Exact match (case-insensitive)
- `not_equals` - Not equal
- `contains` - Contains substring
- `not_contains` - Doesn't contain
- `starts_with` - Starts with
- `ends_with` - Ends with

**Numeric Operators:**
- `greater_than` - >
- `less_than` - <
- `greater_or_equal` - >=
- `less_or_equal` - <=

---

## 🎯 Next Steps

### ✅ Completed: Phase 1 - Rules Engine
- Storage abstraction layer
- JSON file storage
- Rules CRUD APIs
- Integration with dashboard
- 10 operators supported

### 🔜 Next: Phase 2 - Cron Jobs
- Background scheduler
- Automated runs
- Execution logs
- Manual triggers

---

## 🚦 Ready for Client Demo!

**What Works Now:**
1. ✅ Create exclusion rules
2. ✅ Activate/deactivate rules
3. ✅ Rules automatically applied to dashboard data
4. ✅ Multiple conditions per rule
5. ✅ 10 different operators
6. ✅ Test rules before saving
7. ✅ All data stored in JSON (no credentials needed)

**When S3/Oracle Credentials Ready:**
- Just update `storage_config.py` (1 line change)
- Add credentials to `.env`
- All rules logic works the same!

---

## 📖 API Documentation

Full API docs available at:
```
http://127.0.0.1:3334/docs
```

Interactive Swagger UI with all endpoints!
