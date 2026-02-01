# Milestone 2: Admin Settings Implementation Plan

**Project:** Market Pulse - Admin Configuration System  
**Date:** January 2026  
**Phase:** Milestone 2 (Admin Features)  
**Prerequisites:** ✅ Milestone 1 Complete (Core ranking engine + APIs working)

---

## 🎯 Overview

This milestone implements the Admin Settings features that allow system administrators to:
1. **Rules Engine** - Define exclusion filters to remove data from auto-processing
2. **Presets** - Create reusable condition templates for quick data filtering
3. **Cron Jobs** - Schedule automated batch processing with calendar tracking
4. **Email & Restore** - Send reports, backup/restore data, and track changes

---

## 📊 Frontend Status Assessment

### ✅ COMPLETED (Frontend UI)
- Settings page fully designed ([settings.html](../market-pulse-main/src/app/components/settings/settings.html))
- All 4 sections implemented with UI:
  - Rules section with table + form builder
  - Presets section with condition builder
  - Cron Jobs section with calendar view
  - Email & Restore section with logs
- Component logic implemented ([settings.ts](../market-pulse-main/src/app/components/settings/settings.ts))
- Sidebar navigation configured ([app.menu.ts](../market-pulse-main/src/app/layout/component/app.menu.ts))

### ⏳ PENDING (Backend APIs)
- **0 out of 4 features** have backend implementation
- All frontend data is currently hardcoded mock data
- Need to create backend APIs + database schema
- Need to integrate with ranking engine

---

## 🚀 Implementation Strategy

### **Approach:** Incremental Phase Development
- Each phase is independent and deliverable
- Build → Test → Integrate → Next phase
- Database migrations planned for each phase
- API-first development (backend first, then connect frontend)

### **Development Order:**
1. **Phase 2.1:** Rules Engine (Most Critical - affects ranking)
2. **Phase 2.2:** Presets System (Extends Rules functionality)
3. **Phase 2.3:** Cron Jobs Scheduler (Automation layer)
4. **Phase 2.4:** Email & Restore (Reporting & safety)

---

## 📋 Phase 2.1: Rules Engine Implementation

### **Objective:** 
Allow admins to create exclusion filters that automatically remove specific data from the ranking process.

### **User Story:**
> As an admin, I want to define rules like "Remove all securities where Bwic Cover = 'DZ Bank'" so that unwanted data is automatically excluded from color ranking.

### **Frontend UI Reference:**
- Location: Settings page → Rules section
- Table showing existing rules (Name, Active status, Edit/Delete actions)
- Form builder with WHERE/AND/OR conditions
- Subgroup support for complex nested conditions

### **Database Schema:**

```sql
-- Rules table
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    conditions TEXT NOT NULL,  -- JSON structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'admin'
);

-- Rule execution logs
CREATE TABLE rule_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rows_excluded INTEGER,
    status TEXT,  -- 'success', 'error'
    error_message TEXT,
    FOREIGN KEY (rule_id) REFERENCES rules(id)
);
```

### **Condition JSON Structure:**

```json
{
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
    },
    {
      "type": "or",
      "column": "Security Name",
      "operator": "contains",
      "value": "Trust"
    },
    {
      "type": "subgroup",
      "logic": "and",
      "conditions": [
        {
          "type": "where",
          "column": "Issuer",
          "operator": "starts with",
          "value": "Bank"
        },
        {
          "type": "or",
          "column": "Yield",
          "operator": "is less than",
          "value": "5"
        }
      ]
    }
  ]
}
```

### **Supported Operators:**
- `is equal to`
- `is not equal to`
- `contains`
- `does not contain`
- `starts with`
- `ends with`
- `is greater than`
- `is less than`

### **Backend APIs:**

#### 1. **GET /api/rules** - Get all rules
```json
Response: {
  "rules": [
    {
      "id": 1,
      "name": "Remove DZ bank securities",
      "is_active": true,
      "conditions": {...},
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### 2. **POST /api/rules** - Create new rule
```json
Request: {
  "name": "Remove DZ bank securities",
  "is_active": true,
  "conditions": {...}
}
Response: {
  "id": 1,
  "message": "Rule created successfully"
}
```

#### 3. **PUT /api/rules/{rule_id}** - Update existing rule
```json
Request: {
  "name": "Updated rule name",
  "is_active": false,
  "conditions": {...}
}
Response: {
  "message": "Rule updated successfully"
}
```

#### 4. **DELETE /api/rules/{rule_id}** - Delete rule
```json
Response: {
  "message": "Rule deleted successfully"
}
```

#### 5. **POST /api/rules/{rule_id}/toggle** - Toggle active status
```json
Response: {
  "is_active": false,
  "message": "Rule deactivated"
}
```

#### 6. **GET /api/rules/execution-logs** - Get execution history
```json
Response: {
  "logs": [
    {
      "rule_name": "Remove DZ bank securities",
      "execution_time": "2024-01-15T18:30:00",
      "rows_excluded": 45,
      "status": "success"
    }
  ]
}
```

### **Core Logic Files to Create:**

#### 1. **`src/main/rules_service.py`**
- `apply_rules(data: List[ColorRaw]) -> List[ColorRaw]`
  - Load all active rules
  - Apply each rule sequentially
  - Log excluded rows
  - Return filtered data

- `evaluate_condition(row: ColorRaw, condition: dict) -> bool`
  - Parse condition JSON
  - Apply operator logic
  - Handle subgroups recursively

- `get_rule_by_id(rule_id: int) -> Rule`
- `create_rule(rule_data: dict) -> Rule`
- `update_rule(rule_id: int, rule_data: dict) -> Rule`
- `delete_rule(rule_id: int) -> bool`

#### 2. **`src/main/rules.py`** (FastAPI router)
- Define all 6 API endpoints
- Request/response models using Pydantic
- Error handling and validation

### **Integration Points:**

#### Modify: `src/main/dashboard.py`
```python
@router.get("/colors")
async def get_colors():
    # 1. Load data from Excel/Oracle
    raw_data = database_service.load_data()
    
    # 2. 🆕 Apply rules engine (NEW)
    from rules_service import apply_rules
    filtered_data = apply_rules(raw_data)
    
    # 3. Run ranking engine
    ranked_data = ranking_engine.rank_colors(filtered_data)
    
    return ranked_data
```

### **Testing Plan:**

1. **Unit Tests:**
   - Test each operator (equals, contains, greater than, etc.)
   - Test subgroup logic
   - Test rule activation/deactivation

2. **Integration Tests:**
   - Create rule → Apply to sample data → Verify exclusion
   - Test with "Color today.xlsx" (5,213 rows)
   - Verify parent-child relationships maintained

3. **Frontend Integration:**
   - Update `settings.ts` to call backend APIs
   - Replace mock data with real API calls
   - Test CRUD operations via UI

### **Estimated Time:**
- Database setup: 2 hours
- Backend APIs: 6 hours
- Rule evaluation logic: 8 hours
- Integration with ranking engine: 4 hours
- Frontend integration: 3 hours
- Testing: 5 hours
- **Total: ~28 hours (3-4 days)**

---

## 📋 Phase 2.2: Presets System Implementation

### **Objective:**
Create reusable condition templates that users can apply quickly without rebuilding complex rules.

### **User Story:**
> As an admin, I want to save frequently used filter combinations as presets like "Select 102 bank securities" so I can apply them quickly without recreating the conditions.

### **Frontend UI Reference:**
- Location: Settings page → Preset section
- List of saved presets with condition preview
- Form builder (similar to Rules)
- Activity logs showing preset usage

### **Key Difference from Rules:**
- **Rules:** Automatically applied to ALL ranking operations (exclusion)
- **Presets:** Manually applied by user when needed (selection/filtering)
- **Rules:** System-wide effect
- **Presets:** On-demand, temporary filtering

### **Database Schema:**

```sql
-- Presets table
CREATE TABLE presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    conditions TEXT NOT NULL,  -- JSON structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'admin'
);

-- Preset usage logs
CREATE TABLE preset_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preset_id INTEGER,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_by TEXT,
    rows_matched INTEGER,
    action_type TEXT,  -- 'filter', 'export', 'highlight'
    FOREIGN KEY (preset_id) REFERENCES presets(id)
);

-- Preset activity logs (for audit trail)
CREATE TABLE preset_activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    action_type TEXT,  -- 'created', 'updated', 'deleted', 'applied'
    performed_by TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preset_id INTEGER,
    FOREIGN KEY (preset_id) REFERENCES presets(id)
);
```

### **Condition JSON Structure:**
(Same as Rules - reuse the evaluation logic)

```json
{
  "conditions": [
    {
      "type": "where",
      "column": "Owner",
      "operator": "is equal to",
      "value": "Becalato"
    },
    {
      "type": "and",
      "column": "Pno",
      "operator": "is equal to",
      "value": "Becalato"
    }
  ]
}
```

### **Backend APIs:**

#### 1. **GET /api/presets** - Get all presets
```json
Response: {
  "presets": [
    {
      "id": 1,
      "name": "Select 102 bank securities",
      "conditions": {...},
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### 2. **POST /api/presets** - Create preset
```json
Request: {
  "name": "Select 102 bank securities",
  "conditions": {...}
}
Response: {
  "id": 1,
  "message": "Preset created successfully"
}
```

#### 3. **PUT /api/presets/{preset_id}** - Update preset
```json
Request: {
  "name": "Updated name",
  "conditions": {...}
}
Response: {
  "message": "Preset updated successfully"
}
```

#### 4. **DELETE /api/presets/{preset_id}** - Delete preset
```json
Response: {
  "message": "Preset deleted successfully"
}
```

#### 5. **POST /api/presets/{preset_id}/apply** - Apply preset to dataset
```json
Request: {
  "data": [...],  // Array of colors to filter
  "action": "filter"  // or 'export', 'highlight'
}
Response: {
  "filtered_data": [...],
  "matched_count": 102,
  "total_count": 5213
}
```

#### 6. **GET /api/presets/activity-logs** - Get preset activity history
```json
Response: {
  "logs": [
    {
      "description": "Preset added by Sharebank Sihasidara",
      "action_type": "created",
      "performed_at": "2024-11-02T10:30:00"
    }
  ]
}
```

### **Core Logic Files to Create:**

#### 1. **`src/main/presets_service.py`**
- `apply_preset(preset_id: int, data: List[ColorRaw]) -> List[ColorRaw]`
  - Load preset conditions
  - Reuse `evaluate_condition()` from rules_service
  - Return matching rows

- `get_preset_by_id(preset_id: int) -> Preset`
- `create_preset(preset_data: dict) -> Preset`
- `update_preset(preset_id: int, preset_data: dict) -> Preset`
- `delete_preset(preset_id: int) -> bool`
- `log_preset_activity(action: str, preset_id: int, user: str)`

#### 2. **`src/main/presets.py`** (FastAPI router)
- Define all 6 API endpoints
- Pydantic models
- Validation

### **Code Reuse Strategy:**

Since presets use the same condition evaluation logic as rules, extract common logic:

#### **`src/main/condition_evaluator.py`**
```python
def evaluate_conditions(row: dict, conditions: list) -> bool:
    """
    Shared logic for both Rules and Presets
    Evaluates a set of conditions against a data row
    """
    # Logic for WHERE/AND/OR
    # Logic for operators (equals, contains, etc.)
    # Logic for subgroups
    pass

def build_condition_query(conditions: list) -> str:
    """
    Convert JSON conditions to SQL-like query
    (Optional - for debugging/display)
    """
    pass
```

Then import in both `rules_service.py` and `presets_service.py`.

### **Frontend Integration:**

#### Modify: `src/app/components/settings/settings.ts`
```typescript
// Replace mock data
presets: Preset[] = [];  // Empty initially

ngOnInit() {
  this.loadPresets();  // Load from backend
}

loadPresets() {
  this.apiService.getPresets().subscribe(data => {
    this.presets = data.presets;
  });
}

savePreset() {
  this.apiService.createPreset({
    name: this.newPresetName,
    conditions: this.presetConditions
  }).subscribe(response => {
    this.loadPresets();  // Reload
    this.showToast('Preset saved!');
  });
}
```

### **Testing Plan:**

1. **Unit Tests:**
   - Reuse condition evaluation tests from Rules
   - Test preset application logic

2. **Integration Tests:**
   - Create preset → Apply to data → Verify filtering
   - Test activity logging

3. **Frontend Integration:**
   - CRUD operations via UI
   - Apply preset and verify data filtering

### **Estimated Time:**
- Database setup: 1 hour
- Backend APIs: 4 hours
- Reuse condition evaluator: 2 hours
- Frontend integration: 3 hours
- Testing: 3 hours
- **Total: ~13 hours (1-2 days)**

---

## 📋 Phase 2.3: Cron Jobs Scheduler Implementation

### **Objective:**
Schedule automated batch processing with calendar tracking and execution history.

### **User Story:**
> As an admin, I want to schedule "US CLO N1800 Batch" to run daily at 6:30 PM on weekdays so that color ranking happens automatically without manual intervention.

### **Frontend UI Reference:**
- Location: Settings page → Cron Jobs section
- Job list with name, time, frequency, repeat settings
- Calendar view showing scheduled runs with status indicators
- Colors: Green (success), Red (error), Blue (override), Yellow (not started)

### **Database Schema:**

```sql
-- Cron jobs configuration
CREATE TABLE cron_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    schedule_time TEXT NOT NULL,  -- "18:30" (24h format)
    frequency TEXT NOT NULL,  -- JSON: ["Mon", "Tue", "Wed", "Thu", "Fri"]
    is_repeat BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'admin'
);

-- Cron job execution history
CREATE TABLE cron_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,  -- 'success', 'error', 'skipped', 'override', 'not_started'
    rows_processed INTEGER,
    duration_seconds REAL,
    error_message TEXT,
    output_file TEXT,  -- Path to generated Excel file
    FOREIGN KEY (job_id) REFERENCES cron_jobs(id)
);

-- Cron job overrides (manual runs or skips)
CREATE TABLE cron_job_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    override_date DATE NOT NULL,
    override_type TEXT,  -- 'skip', 'run_now', 'reschedule'
    reason TEXT,
    performed_by TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES cron_jobs(id)
);
```

### **Frequency JSON Structure:**

```json
{
  "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],  // Weekdays only
  "timezone": "America/New_York"
}
```

### **Backend APIs:**

#### 1. **GET /api/cron-jobs** - Get all scheduled jobs
```json
Response: {
  "jobs": [
    {
      "id": 1,
      "name": "US CLO N1800 Batch",
      "schedule_time": "18:30",
      "frequency": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
      "is_repeat": true,
      "is_active": true,
      "next_run": "2024-01-16T18:30:00"
    }
  ]
}
```

#### 2. **POST /api/cron-jobs** - Create new job
```json
Request: {
  "name": "US CLO N1800 Batch",
  "description": "Daily color ranking for US CLO securities",
  "schedule_time": "18:30",
  "frequency": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri"]},
  "is_repeat": true,
  "is_active": true
}
Response: {
  "id": 1,
  "message": "Job created successfully",
  "next_run": "2024-01-16T18:30:00"
}
```

#### 3. **PUT /api/cron-jobs/{job_id}** - Update job
```json
Request: {
  "schedule_time": "19:00",
  "frequency": {"days": ["Mon", "Wed", "Fri"]}
}
Response: {
  "message": "Job updated successfully"
}
```

#### 4. **DELETE /api/cron-jobs/{job_id}** - Delete job
```json
Response: {
  "message": "Job deleted successfully"
}
```

#### 5. **POST /api/cron-jobs/{job_id}/toggle** - Activate/deactivate
```json
Response: {
  "is_active": false,
  "message": "Job deactivated"
}
```

#### 6. **POST /api/cron-jobs/{job_id}/run-now** - Manual trigger
```json
Response: {
  "message": "Job started",
  "execution_id": 123
}
```

#### 7. **GET /api/cron-jobs/execution-logs** - Execution history
```json
Request: {
  "job_id": 1,  // Optional filter
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
Response: {
  "logs": [
    {
      "job_name": "US CLO N1800 Batch",
      "execution_time": "2024-01-15T18:30:00",
      "status": "success",
      "rows_processed": 5213,
      "duration_seconds": 12.5,
      "output_file": "Processed_Colors_Output.xlsx"
    }
  ]
}
```

#### 8. **GET /api/cron-jobs/calendar** - Calendar view data
```json
Request: {
  "year": 2024,
  "month": 9  // September
}
Response: {
  "events": [
    {
      "date": "2024-09-09",
      "jobs": [
        {
          "job_name": "US CLO N1800 Batch",
          "time": "18:30",
          "status": "override",
          "reason": "Manual run by admin"
        }
      ]
    },
    {
      "date": "2024-09-24",
      "jobs": [
        {
          "job_name": "US CLO N1800 Batch",
          "time": "18:30",
          "status": "success",
          "rows_processed": 5213
        }
      ]
    }
  ]
}
```

### **Core Logic Files to Create:**

#### 1. **`src/main/cron_service.py`**
- `execute_job(job_id: int) -> dict`
  - Load data from database
  - Apply rules engine
  - Run ranking engine
  - Save to output Excel
  - Log execution

- `schedule_next_run(job_id: int) -> datetime`
  - Calculate next execution time based on frequency

- `get_calendar_events(year: int, month: int) -> list`
  - Return scheduled runs for calendar view

- CRUD operations for jobs

#### 2. **`src/main/cron_jobs.py`** (FastAPI router)
- Define all 8 API endpoints

#### 3. **`src/main/cron_scheduler.py`** (Background scheduler)
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

def register_job(job_id: int, schedule_time: str, frequency: list):
    """
    Register a job with APScheduler
    """
    hour, minute = schedule_time.split(":")
    days = frequency["days"]  # ["Mon", "Tue", ...]
    
    trigger = CronTrigger(
        hour=int(hour),
        minute=int(minute),
        day_of_week=','.join([day_map[d] for d in days])
    )
    
    scheduler.add_job(
        func=execute_job,
        trigger=trigger,
        id=f"job_{job_id}",
        args=[job_id],
        replace_existing=True
    )

def start_scheduler():
    """Call this on app startup"""
    scheduler.start()
    load_all_active_jobs()  # Register existing jobs
```

#### 4. **Modify: `src/main/main.py`** (FastAPI app)
```python
from cron_scheduler import start_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()  # 🆕 Initialize scheduler
```

### **Integration Points:**

Cron jobs execute the same flow as manual processing:
1. Load data
2. Apply rules
3. Run ranking
4. Save output

**Reuse existing code:**
- `database_service.load_data()`
- `rules_service.apply_rules()`
- `ranking_engine.rank_colors()`
- `output_service.append_processed_colors()`

### **Dependencies:**

```txt
# Add to requirements.txt
apscheduler==3.10.4  # For background job scheduling
```

### **Testing Plan:**

1. **Unit Tests:**
   - Test schedule calculation
   - Test frequency parsing

2. **Integration Tests:**
   - Create job → Wait for execution → Verify output
   - Test manual trigger
   - Test job activation/deactivation

3. **Frontend Integration:**
   - Create/edit/delete jobs via UI
   - Verify calendar view updates
   - Test manual run button

### **Estimated Time:**
- Database setup: 2 hours
- Backend APIs: 6 hours
- Scheduler integration: 8 hours
- Calendar logic: 4 hours
- Frontend integration: 4 hours
- Testing: 6 hours
- **Total: ~30 hours (3-4 days)**

---

## 📋 Phase 2.4: Email & Restore Implementation

### **Objective:**
Send automated email reports and provide backup/restore functionality with audit logging.

### **User Story:**
> As an admin, I want to send email reports after each batch processing and restore previous data versions if something goes wrong.

### **Frontend UI Reference:**
- Location: Settings page → Email & Restore section
- Two tabs: "Restore Data" and "Email & Restore Logs"
- Restore table showing batch history with Send Email / Remove Data actions
- Logs showing activity with Revert option

### **Database Schema:**

```sql
-- Data snapshots for restore
CREATE TABLE data_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_name TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    snapshot_time TEXT NOT NULL,
    process_type TEXT,  -- 'Automated', 'Manual'
    file_path TEXT NOT NULL,  -- Path to backed up Excel file
    row_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system'
);

-- Email configuration
CREATE TABLE email_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    smtp_host TEXT NOT NULL,
    smtp_port INTEGER DEFAULT 587,
    smtp_user TEXT NOT NULL,
    smtp_password TEXT NOT NULL,  -- Encrypted
    from_email TEXT NOT NULL,
    to_emails TEXT NOT NULL,  -- JSON array
    cc_emails TEXT,  -- JSON array
    subject_template TEXT,
    body_template TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email send logs
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    to_emails TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT,
    attachment_path TEXT,
    status TEXT,  -- 'sent', 'failed', 'pending'
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_by TEXT DEFAULT 'system'
);

-- Restore activity logs
CREATE TABLE restore_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,  -- 'snapshot_created', 'data_restored', 'data_removed', 'email_sent'
    description TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    snapshot_id INTEGER,
    can_revert BOOLEAN DEFAULT FALSE,
    reverted_at TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES data_snapshots(id)
);
```

### **Backend APIs:**

#### **Restore APIs:**

##### 1. **GET /api/restore/snapshots** - Get all data snapshots
```json
Response: {
  "snapshots": [
    {
      "id": 1,
      "snapshot_name": "US OLONI8000 Batch",
      "snapshot_date": "2005-11-22",
      "snapshot_time": "08:03 AM",
      "process_type": "Automated",
      "row_count": 5213,
      "file_path": "backups/2005-11-22_0803_automated.xlsx"
    }
  ]
}
```

##### 2. **POST /api/restore/create-snapshot** - Manual backup
```json
Request: {
  "snapshot_name": "Before manual cleanup",
  "process_type": "Manual"
}
Response: {
  "id": 1,
  "message": "Snapshot created successfully",
  "file_path": "backups/2024-01-15_1430_manual.xlsx"
}
```

##### 3. **POST /api/restore/{snapshot_id}/restore** - Restore data
```json
Response: {
  "message": "Data restored successfully",
  "rows_restored": 5213,
  "backup_created": "backups/pre_restore_2024-01-15.xlsx"
}
```

##### 4. **DELETE /api/restore/{snapshot_id}** - Remove snapshot
```json
Response: {
  "message": "Snapshot removed successfully"
}
```

##### 5. **GET /api/restore/logs** - Activity logs
```json
Response: {
  "logs": [
    {
      "description": "Email sent by Shusharak Shwazhan",
      "action_type": "email_sent",
      "performed_at": "2005-11-22T08:03:00",
      "can_revert": false
    },
    {
      "description": "Removed data by LUIS Sharma",
      "action_type": "data_removed",
      "performed_at": "2005-11-22T09:15:00",
      "can_revert": true,
      "snapshot_id": 3
    }
  ]
}
```

##### 6. **POST /api/restore/revert/{log_id}** - Revert action
```json
Response: {
  "message": "Action reverted successfully",
  "snapshot_restored": 3
}
```

#### **Email APIs:**

##### 7. **GET /api/email/config** - Get email settings
```json
Response: {
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "from_email": "noreply@marketpulse.com",
  "to_emails": ["admin@company.com", "team@company.com"],
  "subject_template": "Market Pulse - Daily Report {{date}}",
  "is_active": true
}
```

##### 8. **PUT /api/email/config** - Update email settings
```json
Request: {
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "user@gmail.com",
  "smtp_password": "app_password",
  "from_email": "noreply@marketpulse.com",
  "to_emails": ["admin@company.com"],
  "subject_template": "Market Pulse Report - {{date}}",
  "body_template": "Processing completed. {{row_count}} rows processed."
}
Response: {
  "message": "Email configuration updated"
}
```

##### 9. **POST /api/email/send-report** - Send manual email
```json
Request: {
  "to_emails": ["admin@company.com"],
  "subject": "Manual Report",
  "body": "Report attached",
  "attach_latest_output": true
}
Response: {
  "message": "Email sent successfully",
  "log_id": 123
}
```

##### 10. **POST /api/email/test** - Test email configuration
```json
Response: {
  "success": true,
  "message": "Test email sent to admin@company.com"
}
```

##### 11. **GET /api/email/logs** - Email send history
```json
Response: {
  "logs": [
    {
      "to_emails": ["admin@company.com"],
      "subject": "Market Pulse - Daily Report 2024-01-15",
      "status": "sent",
      "sent_at": "2024-01-15T18:35:00"
    }
  ]
}
```

### **Core Logic Files to Create:**

#### 1. **`src/main/restore_service.py`**
- `create_snapshot(name: str, process_type: str) -> dict`
  - Copy current Excel file to backup location
  - Save metadata to database

- `restore_snapshot(snapshot_id: int) -> dict`
  - Create pre-restore backup
  - Copy snapshot file back to main location
  - Log activity

- `get_snapshots() -> list`
- `delete_snapshot(snapshot_id: int) -> bool`
- `log_restore_activity(action: str, description: str, user: str)`
- `revert_action(log_id: int) -> dict`

#### 2. **`src/main/email_service.py`**
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_email(
    to_emails: list,
    subject: str,
    body: str,
    attachment_path: str = None
) -> bool:
    """
    Send email using configured SMTP settings
    """
    config = get_email_config()
    
    msg = MIMEMultipart()
    msg['From'] = config.from_email
    msg['To'] = ', '.join(to_emails)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    if attachment_path:
        attach_file(msg, attachment_path)
    
    try:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port)
        server.starttls()
        server.login(config.smtp_user, config.smtp_password)
        server.send_message(msg)
        server.quit()
        
        log_email_sent(to_emails, subject, 'sent')
        return True
    except Exception as e:
        log_email_sent(to_emails, subject, 'failed', str(e))
        return False

def attach_file(msg: MIMEMultipart, file_path: str):
    """Attach Excel file to email"""
    with open(file_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(file_path)}'
        )
        msg.attach(part)
```

#### 3. **`src/main/restore.py`** (FastAPI router)
- Define restore APIs (6 endpoints)

#### 4. **`src/main/email.py`** (FastAPI router)
- Define email APIs (5 endpoints)

### **Integration Points:**

#### Automatic Email After Cron Job:
```python
# In cron_service.py
def execute_job(job_id: int):
    # ... existing processing logic ...
    
    # 🆕 Send email after successful processing
    if email_config.is_active:
        send_email(
            to_emails=email_config.to_emails,
            subject=f"Market Pulse Report - {datetime.now().strftime('%Y-%m-%d')}",
            body=f"Processing completed. {row_count} rows processed.",
            attachment_path="Processed_Colors_Output.xlsx"
        )
```

#### Automatic Snapshot Before Processing:
```python
# In cron_service.py or dashboard.py
def execute_job(job_id: int):
    # 🆕 Create snapshot before processing
    create_snapshot(
        name=f"Pre-processing backup {datetime.now()}",
        process_type="Automated"
    )
    
    # ... existing processing logic ...
```

### **Dependencies:**

```txt
# Add to requirements.txt
# (No new dependencies - smtplib is built-in Python)
```

### **Security Considerations:**

1. **Encrypt SMTP password** in database:
```python
from cryptography.fernet import Fernet

def encrypt_password(password: str) -> str:
    key = os.getenv("ENCRYPTION_KEY")  # Store in environment
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    key = os.getenv("ENCRYPTION_KEY")
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()
```

2. **Validate email addresses**
3. **Rate limiting** on email sends (prevent spam)
4. **Backup retention policy** (auto-delete old snapshots)

### **Testing Plan:**

1. **Unit Tests:**
   - Test email sending (mock SMTP)
   - Test snapshot creation/restore
   - Test encryption/decryption

2. **Integration Tests:**
   - Create snapshot → Modify data → Restore → Verify
   - Configure email → Send test → Verify receipt
   - Test attachment handling

3. **Frontend Integration:**
   - Test email configuration form
   - Test restore data table
   - Test send email button
   - Test revert action

### **Estimated Time:**
- Database setup: 2 hours
- Backend APIs (11 endpoints): 8 hours
- Email service: 6 hours
- Restore service: 6 hours
- Encryption implementation: 2 hours
- Integration with cron: 2 hours
- Frontend integration: 4 hours
- Testing: 6 hours
- **Total: ~36 hours (4-5 days)**

---

## 📊 Milestone 2 Summary

### **Total Estimated Time:**
- Phase 2.1 (Rules): ~28 hours (3-4 days)
- Phase 2.2 (Presets): ~13 hours (1-2 days)
- Phase 2.3 (Cron Jobs): ~30 hours (3-4 days)
- Phase 2.4 (Email & Restore): ~36 hours (4-5 days)

**Grand Total: ~107 hours (13-16 days)**

### **Deliverables Checklist:**

#### Phase 2.1 - Rules Engine
- [ ] Database schema created
- [ ] 6 backend APIs implemented
- [ ] Rule evaluation logic working
- [ ] Integrated with ranking engine
- [ ] Frontend connected to backend
- [ ] Unit tests passing
- [ ] Integration tests passing

#### Phase 2.2 - Presets System
- [ ] Database schema created
- [ ] 6 backend APIs implemented
- [ ] Preset application logic working
- [ ] Activity logging functional
- [ ] Frontend connected to backend
- [ ] Unit tests passing
- [ ] Integration tests passing

#### Phase 2.3 - Cron Jobs
- [ ] Database schema created
- [ ] 8 backend APIs implemented
- [ ] APScheduler configured
- [ ] Jobs executing automatically
- [ ] Calendar view working
- [ ] Frontend connected to backend
- [ ] Unit tests passing
- [ ] Integration tests passing

#### Phase 2.4 - Email & Restore
- [ ] Database schema created
- [ ] 11 backend APIs implemented
- [ ] Email sending working
- [ ] Snapshot/restore functional
- [ ] Encryption implemented
- [ ] Frontend connected to backend
- [ ] Unit tests passing
- [ ] Integration tests passing

### **Risk Assessment:**

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Email SMTP blocked by firewall | High | Test early, document network requirements |
| Cron jobs not firing | High | Add monitoring, alerting, fallback mechanism |
| Large Excel files cause timeout | Medium | Implement async processing, progress updates |
| Database locking issues | Medium | Use connection pooling, transactions properly |
| Restore corrupts data | High | Always create pre-restore snapshot, validate data |

### **Testing Strategy:**

1. **Unit Testing (Each Phase):**
   - Test individual functions in isolation
   - Mock external dependencies (database, SMTP)
   - Aim for 80%+ code coverage

2. **Integration Testing:**
   - Test full workflow: Create → Execute → Verify
   - Test API endpoints with real database
   - Test frontend-backend integration

3. **End-to-End Testing:**
   - Test complete user workflows
   - Test with production-like data volume
   - Test error scenarios and recovery

4. **Performance Testing:**
   - Test with 5,213 row dataset
   - Measure API response times
   - Test concurrent users

### **Documentation Required:**

1. **API Documentation:**
   - Update README.md with all new endpoints
   - Add Swagger/OpenAPI definitions
   - Include request/response examples

2. **Database Schema:**
   - ER diagram showing relationships
   - Migration scripts
   - Backup/restore procedures

3. **Admin User Guide:**
   - How to create rules
   - How to schedule cron jobs
   - How to configure email
   - How to restore data

4. **Developer Guide:**
   - Code structure explanation
   - How to extend rules engine
   - How to add new operators
   - How to debug cron jobs

---

## 🚦 Getting Started

### **Prerequisites:**
- ✅ Milestone 1 completed
- ✅ Backend server running on port 3334
- ✅ Frontend Angular app accessible
- ✅ Database (SQLite) configured

### **Step 1: Create Database Schema**
```bash
cd sp-incb-market-pulse-master
python scripts/create_admin_schema.py  # You'll create this
```

### **Step 2: Install Dependencies**
```bash
pip install apscheduler==3.10.4
pip install cryptography  # For password encryption
```

### **Step 3: Start with Phase 2.1 (Rules)**
- Create `src/main/rules_service.py`
- Create `src/main/rules.py`
- Create database schema
- Test APIs with Postman/curl
- Connect frontend

### **Step 4: Progress Through Phases**
Follow the order: Rules → Presets → Cron → Email

---

## ❓ Questions to Clarify

Before starting implementation, please confirm:

1. **Email Configuration:**
   - Do you have SMTP server details?
   - Will you use Gmail, Office365, or custom SMTP?
   - Any email template preferences?

2. **Cron Jobs:**
   - What timezone should be used?
   - Should jobs run on holidays?
   - Max execution time limit?

3. **Data Backup:**
   - How many snapshots to retain? (e.g., last 30 days)
   - Where to store backup files? (local disk, S3, etc.)
   - Backup size limits?

4. **Rules Engine:**
   - Any specific operators needed beyond the list?
   - Should rules apply to parent colors only or children too?
   - Max number of conditions per rule?

5. **Security:**
   - Authentication required for Admin APIs?
   - Role-based access control needed?
   - Audit trail requirements?

---

## 📝 Next Steps

**Immediate action items:**

1. **Review this plan** - Confirm it matches your requirements
2. **Answer clarification questions** - Help me understand specifics
3. **Prioritize phases** - Confirm the order or request changes
4. **Approve to proceed** - I'll start with Phase 2.1 (Rules Engine)

**Once approved, I will:**
1. Create database migration script
2. Implement Phase 2.1 backend
3. Test APIs
4. Connect frontend
5. Move to next phase

---

**Ready to start? Let me know if you have any questions or need clarification on any part of this plan!** 🚀
