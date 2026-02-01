# PowerShell API Testing Commands

## ✅ Rules Engine - Working Commands

### 1️⃣ Get All Rules
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules" -Method Get
```

**Formatted Output:**
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules" -Method Get
$response.rules | Format-Table id, name, is_active -AutoSize
```

### 2️⃣ Create Rule - Simple
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Remove DZ Bank Securities","is_active":true,"conditions":[{"type":"where","column":"BWIC_COVER","operator":"equals","value":"DZ Bank"}]}'
```

### 3️⃣ Create Rule - Performance Trust
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Remove Performance Trust","is_active":true,"conditions":[{"type":"where","column":"SECURITY_NAME","operator":"contains","value":"Performance Trust"}]}'
```

### 4️⃣ Create Rule - Multiple Conditions
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Low Price Bank Securities","is_active":true,"conditions":[{"type":"where","column":"BWIC_COVER","operator":"starts_with","value":"Bank"},{"type":"and","column":"PX","operator":"less_than","value":"50"}]}'
```

### 5️⃣ Get Active Rules Only
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules/active" -Method Get
```

### 6️⃣ Get Single Rule by ID
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules/1" -Method Get
```

### 7️⃣ Toggle Rule (Activate/Deactivate)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules/1/toggle" -Method Post
```

### 8️⃣ Update Rule
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules/1" -Method Put `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name":"Updated Rule Name","is_active":false}'
```

### 9️⃣ Delete Rule
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules/1" -Method Delete
```

### 🔟 Get Supported Operators
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules/operators/list" -Method Get
```

**Formatted Output:**
```powershell
$ops = Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/rules/operators/list" -Method Get
$ops.operators | Format-Table value, label, type -AutoSize
```

---

## 📊 Dashboard API

### Get Colors (with rules applied)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/dashboard/colors?skip=0&limit=10" -Method Get
```

### Get Monthly Stats
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/dashboard/monthly-stats" -Method Get
```

### Get Next Run Time
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/dashboard/next-run" -Method Get
```

---

## 🔍 View Stored Rules (File)
```powershell
Get-Content "D:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main\data\rules.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 🚀 Start Server
```powershell
cd "D:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main"
python handler.py
```

---

## ⚠️ Important Notes

1. **Don't use `curl` in PowerShell** - It's an alias for `Invoke-WebRequest` with different syntax
2. **Use `Invoke-RestMethod`** - Better for JSON APIs
3. **Headers Syntax**: `-Headers @{"Content-Type"="application/json"}`
4. **JSON Body**: Use single quotes for the entire body string
5. **Server must be running**: Start with `python handler.py`

---

## ✅ Current Test Results

### Rules Created:
- ✅ Rule #1: Remove DZ Bank Securities
- ✅ Rule #2: Remove Performance Trust

### Operators Available:
| Operator | Label | Type |
|----------|-------|------|
| equals | is equal to | string |
| not_equals | is not equal to | string |
| contains | contains | string |
| not_contains | does not contain | string |
| starts_with | starts with | string |
| ends_with | ends with | string |
| greater_than | is greater than | numeric |
| less_than | is less than | numeric |
| greater_or_equal | is greater than or equal to | numeric |
| less_or_equal | is less than or equal to | numeric |

### Storage:
- 📁 Location: `data/rules.json`
- 💾 Format: JSON
- 🔄 Ready to switch to S3/Oracle later
