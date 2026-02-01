# Milestone 2: Backend Implementation Plan

**Project:** Market Pulse - Backend Logic (Python/FastAPI)  
**Date:** January 26, 2026  
**Timeline:** Remaining 10-12 days (Milestone 1 complete)  
**Focus:** Backend ONLY - No frontend, No database creation

---

## 🎯 Current Status

### ✅ Milestone 1 - COMPLETED
- [x] Oracle database connection ready (via `db_config.py`)
- [x] Data fetching from Excel (fallback mode working)
- [x] Ranking Engine: DATE → RANK → PRICE sorting ✓
- [x] Dashboard API: `/api/dashboard/colors` working ✓
- [x] Output Excel: `Processed_Colors_Output.xlsx` ✓

### ⏳ Milestone 2 - TO BE IMPLEMENTED
- [ ] S3 Integration (user permissions + data storage)
- [ ] Security Search API
- [ ] Exclusion Rules Engine
- [ ] Cron Jobs Automation
- [ ] Restore & Email functionality
- [ ] Manual Colors upload

---

## 📋 Requirements Summary

### **Backend Must Provide:**

1. **S3 Integration**
   - User → Asset Class mapping (stored in S3)
   - Save processed data to S3
   - User permissions checking

2. **Security Search**
   - Search by Message ID / CUSIP
   - Excel upload with identifiers
   - Return filtered results

3. **Rules Engine**
   - Define exclusion filters (e.g., "Remove DZ Bank")
   - Apply automatically in automation
   - Apply manually when requested
   - Active/Inactive toggle

4. **Cron Jobs**
   - Schedule automation runs
   - Override logic (run now + cancel next OR run now + keep next)
   - Track execution status (success/error/override/skipped)
   - Logs with status

5. **Manual Colors**
   - Upload Excel with colors
   - Store for next automation run
   - Download sample template

6. **Restore & Email**
   - Track all automation runs
   - Remove Data (rollback)
   - Send Email (manual trigger)

7. **Logging**
   - Log all actions (rules, cron, restore)
   - Show last 4 changes
   - Revert option (where applicable)

---

## 🚀 Implementation Plan

### **PHASE 1: S3 Integration & User Mapping** (2-3 days)

#### What Oracle DB provides:
- Raw color data (columns: DATE, RANK, PX, CUSIP, TICKER, etc.)

#### What S3 provides:
- User permissions: `user_permissions.json`
- Processed data storage: `processed_colors/`

#### Files to Create/Modify:

**1. `src/main/s3_service.py`** (NEW)
```python
"""
S3 integration service
- Get user permissions from S3
- Save processed data to S3
- Download/upload files
"""

import boto3
import json
from typing import Dict, List
import os

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'market-pulse-data')
    
    def get_user_permissions(self, username: str) -> Dict:
        """
        Get user's allowed asset classes from S3
        Returns: {"username": "user@company.com", "asset_classes": ["US CLO", "EU CLO"]}
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key='permissions/user_permissions.json'
            )
            permissions = json.loads(response['Body'].read())
            
            # Find user's permissions
            user_perm = next(
                (u for u in permissions['users'] if u['username'] == username),
                None
            )
            return user_perm
        except Exception as e:
            print(f"Error loading permissions: {e}")
            return None
    
    def save_processed_data(self, data: str, filename: str) -> str:
        """
        Save processed Excel/CSV to S3
        Returns: S3 URL
        """
        key = f"processed_colors/{filename}"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        return f"s3://{self.bucket_name}/{key}"
    
    def upload_file(self, file_path: str, s3_key: str) -> str:
        """Upload local file to S3"""
        self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
        return f"s3://{self.bucket_name}/{s3_key}"
    
    def download_file(self, s3_key: str, local_path: str):
        """Download file from S3 to local"""
        self.s3_client.download_file(self.bucket_name, s3_key, local_path)

s3_service = S3Service()
```

**2. `src/main/user_service.py`** (NEW)
```python
"""
User permission service
"""

from s3_service import s3_service
from typing import List

def get_user_asset_classes(username: str) -> List[str]:
    """
    Get asset classes user has access to
    Example: ["US CLO", "EU CLO"]
    """
    permissions = s3_service.get_user_permissions(username)
    if permissions:
        return permissions.get('asset_classes', [])
    return []

def filter_data_by_user(data: list, username: str, asset_class_column: str = 'ASSET_CLASS') -> list:
    """
    Filter data based on user's allowed asset classes
    """
    allowed_classes = get_user_asset_classes(username)
    if not allowed_classes:
        return []  # User has no permissions
    
    # Filter data
    filtered = [
        row for row in data 
        if row.get(asset_class_column) in allowed_classes
    ]
    return filtered
```

**3. Modify `src/main/dashboard.py`**
```python
# Add user filtering to existing API

@router.get("/colors")
async def get_colors(username: str = "default"):  # Get from auth header in production
    # 1. Load data
    raw_data = database_service.load_data()
    
    # 2. 🆕 Filter by user permissions
    from user_service import filter_data_by_user
    user_data = filter_data_by_user(raw_data, username)
    
    # 3. Apply rules (coming in Phase 2)
    # filtered_data = rules_service.apply_rules(user_data)
    
    # 4. Run ranking
    ranked_data = ranking_engine.rank_colors(user_data)
    
    return ranked_data
```

**4. Add to `requirements.txt`**
```
boto3==1.34.34
```

**5. Update `.env.example`**
```
# S3 Configuration
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=market-pulse-data
```

#### S3 Structure Expected:
```
s3://market-pulse-data/
├── permissions/
│   └── user_permissions.json  # User → Asset Class mapping
├── processed_colors/
│   ├── 2026-01-26_automated.xlsx
│   ├── 2026-01-26_manual.xlsx
│   └── ...
├── manual_imports/
│   └── user_uploaded_colors.xlsx
└── backups/
    └── ...
```

#### Example `user_permissions.json`:
```json
{
  "users": [
    {
      "username": "user_a@company.com",
      "asset_classes": ["US CLO"],
      "full_name": "User A"
    },
    {
      "username": "user_b@company.com",
      "asset_classes": ["EU CLO"],
      "full_name": "User B"
    },
    {
      "username": "admin@company.com",
      "asset_classes": ["US CLO", "EU CLO", "US RMBS"],
      "full_name": "Admin User"
    }
  ]
}
```

---

### **PHASE 2: Security Search API** (1 day)

**What it does:**
- Search colors by Message ID or CUSIP
- Upload Excel with IDs → fetch matching colors

#### Files to Create:

**1. `src/main/search_service.py`** (NEW)
```python
"""
Security search service
"""

from typing import List, Dict
from database_service import database_service

def search_by_identifier(
    identifier: str, 
    search_column: str = 'CUSIP'
) -> List[Dict]:
    """
    Search colors by identifier (CUSIP, Message ID, etc.)
    """
    all_data = database_service.load_data()
    
    # Search (case-insensitive)
    results = [
        row for row in all_data
        if str(row.get(search_column, '')).lower() == identifier.lower()
    ]
    
    return results

def search_multiple(
    identifiers: List[str],
    search_column: str = 'CUSIP'
) -> List[Dict]:
    """
    Search for multiple identifiers at once
    Used when Excel is uploaded
    """
    all_data = database_service.load_data()
    
    # Normalize identifiers
    id_set = {str(id).lower() for id in identifiers}
    
    # Filter
    results = [
        row for row in all_data
        if str(row.get(search_column, '')).lower() in id_set
    ]
    
    return results
```

**2. `src/main/search.py`** (NEW - FastAPI router)
```python
"""
Security Search API endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import pandas as pd
import io
from search_service import search_by_identifier, search_multiple

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.get("/by-identifier")
async def search_identifier(
    identifier: str,
    column: str = "CUSIP"
):
    """
    Search by single identifier
    Example: /api/search/by-identifier?identifier=12345&column=CUSIP
    """
    results = search_by_identifier(identifier, column)
    return {
        "identifier": identifier,
        "column": column,
        "count": len(results),
        "results": results
    }

@router.post("/bulk-search")
async def bulk_search(
    file: UploadFile = File(...),
    column: str = "CUSIP"
):
    """
    Upload Excel with identifiers, get all matching colors
    Excel should have a column matching the search column
    """
    try:
        # Read Excel
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Extract identifiers
        if column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Column '{column}' not found in Excel. Available: {list(df.columns)}"
            )
        
        identifiers = df[column].dropna().tolist()
        
        # Search
        results = search_multiple(identifiers, column)
        
        return {
            "identifiers_searched": len(identifiers),
            "matches_found": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sample-template")
async def download_sample():
    """
    Download sample Excel for bulk search
    """
    sample_data = {
        "CUSIP": ["12345", "67890", "ABCDE"],
        "Notes": ["Example 1", "Example 2", "Example 3"]
    }
    df = pd.DataFrame(sample_data)
    
    # Convert to Excel bytes
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=search_template.xlsx"}
    )
```

**3. Register router in `src/main/main.py`**
```python
from search import router as search_router

app.include_router(search_router)
```

---

### **PHASE 3: Rules Engine (Exclusion Logic)** (3-4 days)

**What it does:**
- Admin creates rules: "Remove all rows where BWIC_COVER = 'DZ Bank'"
- Rules stored in JSON file (no Oracle DB creation)
- Applied automatically in automation
- Can be applied manually

#### Files to Create:

**1. `data/rules.json`** (NEW - Storage file)
```json
{
  "rules": [
    {
      "id": 1,
      "name": "Remove DZ bank securities",
      "is_active": true,
      "conditions": [
        {
          "type": "where",
          "column": "BWIC_COVER",
          "operator": "equals",
          "value": "DZ Bank"
        }
      ],
      "created_at": "2026-01-26T10:00:00",
      "updated_at": "2026-01-26T10:00:00"
    },
    {
      "id": 2,
      "name": "Remove Performance Trust Offer",
      "is_active": true,
      "conditions": [
        {
          "type": "where",
          "column": "SECURITY_NAME",
          "operator": "contains",
          "value": "Performance Trust"
        }
      ],
      "created_at": "2026-01-26T11:00:00",
      "updated_at": "2026-01-26T11:00:00"
    }
  ]
}
```

**2. `src/main/rules_service.py`** (NEW)
```python
"""
Rules Engine - Exclusion Logic
"""

import json
import os
from typing import List, Dict
from datetime import datetime

RULES_FILE = "data/rules.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(RULES_FILE):
    with open(RULES_FILE, 'w') as f:
        json.dump({"rules": []}, f)

def load_rules() -> List[Dict]:
    """Load all rules from JSON file"""
    with open(RULES_FILE, 'r') as f:
        data = json.load(f)
    return data.get('rules', [])

def save_rules(rules: List[Dict]):
    """Save rules to JSON file"""
    with open(RULES_FILE, 'w') as f:
        json.dump({"rules": rules}, f, indent=2)

def get_active_rules() -> List[Dict]:
    """Get only active rules"""
    all_rules = load_rules()
    return [r for r in all_rules if r.get('is_active', True)]

def evaluate_condition(row: Dict, condition: Dict) -> bool:
    """
    Evaluate single condition against a row
    Supported operators: equals, not_equals, contains, not_contains, 
                         starts_with, ends_with, greater_than, less_than
    """
    column = condition['column']
    operator = condition['operator']
    value = condition['value']
    
    # Get row value
    row_value = str(row.get(column, ''))
    compare_value = str(value)
    
    # Apply operator
    if operator == 'equals':
        return row_value.lower() == compare_value.lower()
    elif operator == 'not_equals':
        return row_value.lower() != compare_value.lower()
    elif operator == 'contains':
        return compare_value.lower() in row_value.lower()
    elif operator == 'not_contains':
        return compare_value.lower() not in row_value.lower()
    elif operator == 'starts_with':
        return row_value.lower().startswith(compare_value.lower())
    elif operator == 'ends_with':
        return row_value.lower().endswith(compare_value.lower())
    elif operator == 'greater_than':
        try:
            return float(row_value) > float(compare_value)
        except:
            return False
    elif operator == 'less_than':
        try:
            return float(row_value) < float(compare_value)
        except:
            return False
    else:
        return False

def evaluate_rule(row: Dict, rule: Dict) -> bool:
    """
    Evaluate if a rule matches a row (should be excluded)
    Returns True if row should be EXCLUDED
    """
    conditions = rule.get('conditions', [])
    
    # For now, simple logic: ALL conditions must match (AND logic)
    for condition in conditions:
        condition_type = condition.get('type', 'where')
        
        if condition_type in ['where', 'and']:
            if not evaluate_condition(row, condition):
                return False  # One condition failed, don't exclude
        elif condition_type == 'or':
            # OR logic: if any OR condition matches, include this row
            # (implementation depends on complex requirements)
            pass
    
    return True  # All conditions matched, EXCLUDE this row

def apply_rules(data: List[Dict]) -> List[Dict]:
    """
    Apply all active rules to filter data
    Returns: Filtered data (excluded rows removed)
    """
    active_rules = get_active_rules()
    
    if not active_rules:
        return data  # No rules, return all data
    
    filtered_data = []
    excluded_count = 0
    
    for row in data:
        should_exclude = False
        
        # Check each rule
        for rule in active_rules:
            if evaluate_rule(row, rule):
                should_exclude = True
                excluded_count += 1
                break  # One rule matched, exclude this row
        
        if not should_exclude:
            filtered_data.append(row)
    
    print(f"Rules applied: {len(active_rules)} active rules")
    print(f"Excluded: {excluded_count} rows")
    print(f"Remaining: {len(filtered_data)} rows")
    
    return filtered_data

def create_rule(name: str, conditions: List[Dict], is_active: bool = True) -> Dict:
    """Create a new rule"""
    rules = load_rules()
    
    # Generate ID
    new_id = max([r.get('id', 0) for r in rules], default=0) + 1
    
    new_rule = {
        "id": new_id,
        "name": name,
        "is_active": is_active,
        "conditions": conditions,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    rules.append(new_rule)
    save_rules(rules)
    
    return new_rule

def update_rule(rule_id: int, name: str = None, conditions: List[Dict] = None, is_active: bool = None) -> Dict:
    """Update existing rule"""
    rules = load_rules()
    
    for rule in rules:
        if rule['id'] == rule_id:
            if name is not None:
                rule['name'] = name
            if conditions is not None:
                rule['conditions'] = conditions
            if is_active is not None:
                rule['is_active'] = is_active
            rule['updated_at'] = datetime.now().isoformat()
            
            save_rules(rules)
            return rule
    
    raise ValueError(f"Rule {rule_id} not found")

def delete_rule(rule_id: int):
    """Delete a rule"""
    rules = load_rules()
    rules = [r for r in rules if r['id'] != rule_id]
    save_rules(rules)

def toggle_rule(rule_id: int) -> Dict:
    """Toggle rule active status"""
    rules = load_rules()
    
    for rule in rules:
        if rule['id'] == rule_id:
            rule['is_active'] = not rule.get('is_active', True)
            rule['updated_at'] = datetime.now().isoformat()
            save_rules(rules)
            return rule
    
    raise ValueError(f"Rule {rule_id} not found")
```

**3. `src/main/rules.py`** (NEW - FastAPI router)
```python
"""
Rules API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
from pydantic import BaseModel
import rules_service

router = APIRouter(prefix="/api/rules", tags=["Rules"])

class RuleCondition(BaseModel):
    type: str  # 'where', 'and', 'or'
    column: str
    operator: str
    value: str

class RuleCreate(BaseModel):
    name: str
    conditions: List[Dict]
    is_active: bool = True

class RuleUpdate(BaseModel):
    name: str = None
    conditions: List[Dict] = None
    is_active: bool = None

@router.get("/")
async def get_all_rules():
    """Get all rules"""
    rules = rules_service.load_rules()
    return {"rules": rules, "count": len(rules)}

@router.get("/active")
async def get_active_rules():
    """Get only active rules"""
    rules = rules_service.get_active_rules()
    return {"rules": rules, "count": len(rules)}

@router.post("/")
async def create_rule(rule: RuleCreate):
    """Create new rule"""
    try:
        new_rule = rules_service.create_rule(
            name=rule.name,
            conditions=rule.conditions,
            is_active=rule.is_active
        )
        return {"message": "Rule created", "rule": new_rule}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{rule_id}")
async def update_rule(rule_id: int, rule: RuleUpdate):
    """Update existing rule"""
    try:
        updated = rules_service.update_rule(
            rule_id=rule_id,
            name=rule.name,
            conditions=rule.conditions,
            is_active=rule.is_active
        )
        return {"message": "Rule updated", "rule": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete rule"""
    try:
        rules_service.delete_rule(rule_id)
        return {"message": "Rule deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{rule_id}/toggle")
async def toggle_rule(rule_id: int):
    """Toggle rule active/inactive"""
    try:
        updated = rules_service.toggle_rule(rule_id)
        return {
            "message": f"Rule {'activated' if updated['is_active'] else 'deactivated'}",
            "rule": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**4. Integrate with existing APIs - Modify `src/main/dashboard.py`**
```python
@router.get("/colors")
async def get_colors(username: str = "default"):
    # 1. Load data
    raw_data = database_service.load_data()
    
    # 2. Filter by user permissions
    from user_service import filter_data_by_user
    user_data = filter_data_by_user(raw_data, username)
    
    # 3. 🆕 Apply exclusion rules
    from rules_service import apply_rules
    filtered_data = apply_rules(user_data)
    
    # 4. Run ranking
    ranked_data = ranking_engine.rank_colors(filtered_data)
    
    return ranked_data
```

**5. Register router in `src/main/main.py`**
```python
from rules import router as rules_router

app.include_router(rules_router)
```

---

### **PHASE 4: Cron Jobs & Automation** (3-4 days)

**What it does:**
- Schedule automated runs
- Override logic: run now + cancel next OR run now + keep next
- Track execution status
- Logs

#### Files to Create:

**1. `data/cron_jobs.json`** (NEW)
```json
{
  "jobs": [
    {
      "id": 1,
      "name": "US CLO N1800 Batch",
      "schedule_time": "18:30",
      "frequency": ["Mon", "Tue", "Wed", "Thu", "Fri"],
      "is_repeat": true,
      "is_active": true,
      "created_at": "2026-01-26T10:00:00"
    }
  ],
  "execution_logs": []
}
```

**2. `src/main/cron_service.py`** (NEW)
```python
"""
Cron Job Scheduler Service
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Import existing services
from database_service import database_service
from rules_service import apply_rules
from ranking_engine import rank_colors
from output_service import append_processed_colors

CRON_FILE = "data/cron_jobs.json"
scheduler = BackgroundScheduler()

# Day mapping
DAY_MAP = {
    "Mon": "mon", "Tue": "tue", "Wed": "wed",
    "Thu": "thu", "Fri": "fri", "Sat": "sat", "Sun": "sun"
}

def load_cron_data() -> Dict:
    """Load cron jobs and logs"""
    if not os.path.exists(CRON_FILE):
        return {"jobs": [], "execution_logs": []}
    
    with open(CRON_FILE, 'r') as f:
        return json.load(f)

def save_cron_data(data: Dict):
    """Save cron jobs and logs"""
    os.makedirs("data", exist_ok=True)
    with open(CRON_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def execute_automation(job_id: int, override_type: str = None):
    """
    Execute the automation process
    This is the main logic that runs when cron triggers
    """
    start_time = datetime.now()
    
    try:
        # 1. Load data from Oracle (or Excel fallback)
        print(f"[Job {job_id}] Loading data...")
        raw_data = database_service.load_data()
        
        # 2. Apply exclusion rules
        print(f"[Job {job_id}] Applying rules...")
        filtered_data = apply_rules(raw_data)
        
        # 3. Run ranking engine
        print(f"[Job {job_id}] Running ranking...")
        ranked_data = rank_colors(filtered_data)
        
        # 4. Save to output Excel
        print(f"[Job {job_id}] Saving output...")
        append_processed_colors(ranked_data, processing_type="AUTOMATED")
        
        # 5. Log execution
        duration = (datetime.now() - start_time).total_seconds()
        log_execution(
            job_id=job_id,
            status="success",
            rows_processed=len(ranked_data),
            duration=duration,
            override_type=override_type
        )
        
        print(f"[Job {job_id}] ✅ Completed: {len(ranked_data)} rows in {duration:.2f}s")
        
        # 6. TODO: Send email notification (Phase 5)
        
        return {"status": "success", "rows": len(ranked_data)}
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        log_execution(
            job_id=job_id,
            status="error",
            rows_processed=0,
            duration=duration,
            error_message=str(e)
        )
        print(f"[Job {job_id}] ❌ Error: {e}")
        return {"status": "error", "message": str(e)}

def log_execution(
    job_id: int,
    status: str,
    rows_processed: int,
    duration: float,
    override_type: str = None,
    error_message: str = None
):
    """Log execution in cron_jobs.json"""
    data = load_cron_data()
    
    log_entry = {
        "job_id": job_id,
        "execution_time": datetime.now().isoformat(),
        "status": status,  # success, error, override, skipped
        "rows_processed": rows_processed,
        "duration_seconds": duration,
        "override_type": override_type,
        "error_message": error_message
    }
    
    data['execution_logs'].append(log_entry)
    save_cron_data(data)

def register_job(job: Dict):
    """Register a job with APScheduler"""
    if not job.get('is_active', True):
        return
    
    job_id = job['id']
    schedule_time = job['schedule_time']  # "18:30"
    frequency = job.get('frequency', [])  # ["Mon", "Tue", ...]
    
    if not frequency:
        return  # No days selected
    
    hour, minute = schedule_time.split(":")
    days = ','.join([DAY_MAP[day] for day in frequency if day in DAY_MAP])
    
    trigger = CronTrigger(
        hour=int(hour),
        minute=int(minute),
        day_of_week=days
    )
    
    scheduler.add_job(
        func=execute_automation,
        trigger=trigger,
        id=f"job_{job_id}",
        args=[job_id],
        replace_existing=True,
        name=job['name']
    )
    
    print(f"✅ Registered: {job['name']} at {schedule_time} on {frequency}")

def start_scheduler():
    """Start the background scheduler and load all jobs"""
    if scheduler.running:
        return
    
    # Load and register all active jobs
    data = load_cron_data()
    for job in data['jobs']:
        if job.get('is_active', True):
            register_job(job)
    
    scheduler.start()
    print(f"🚀 Scheduler started with {len(scheduler.get_jobs())} jobs")

def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()

def create_job(name: str, schedule_time: str, frequency: List[str], is_repeat: bool = True) -> Dict:
    """Create new cron job"""
    data = load_cron_data()
    
    new_id = max([j.get('id', 0) for j in data['jobs']], default=0) + 1
    
    new_job = {
        "id": new_id,
        "name": name,
        "schedule_time": schedule_time,
        "frequency": frequency,
        "is_repeat": is_repeat,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    data['jobs'].append(new_job)
    save_cron_data(data)
    
    # Register with scheduler
    register_job(new_job)
    
    return new_job

def update_job(job_id: int, **kwargs) -> Dict:
    """Update cron job"""
    data = load_cron_data()
    
    for job in data['jobs']:
        if job['id'] == job_id:
            job.update(kwargs)
            job['updated_at'] = datetime.now().isoformat()
            save_cron_data(data)
            
            # Re-register with scheduler
            register_job(job)
            
            return job
    
    raise ValueError(f"Job {job_id} not found")

def delete_job(job_id: int):
    """Delete cron job"""
    data = load_cron_data()
    data['jobs'] = [j for j in data['jobs'] if j['id'] != job_id]
    save_cron_data(data)
    
    # Remove from scheduler
    try:
        scheduler.remove_job(f"job_{job_id}")
    except:
        pass

def toggle_job(job_id: int) -> Dict:
    """Toggle job active status"""
    data = load_cron_data()
    
    for job in data['jobs']:
        if job['id'] == job_id:
            job['is_active'] = not job.get('is_active', True)
            save_cron_data(data)
            
            if job['is_active']:
                register_job(job)
            else:
                try:
                    scheduler.remove_job(f"job_{job_id}")
                except:
                    pass
            
            return job
    
    raise ValueError(f"Job {job_id} not found")

def run_job_now(job_id: int, override_next: bool = False):
    """
    Run job immediately
    override_next: If True, cancel next scheduled run
    """
    # Execute now
    result = execute_automation(job_id, override_type="manual_override")
    
    # If override_next, skip next scheduled run
    if override_next:
        # This can be implemented by tracking override state
        # and checking it in execute_automation
        pass
    
    return result

def get_execution_logs(job_id: int = None, limit: int = 50) -> List[Dict]:
    """Get execution logs"""
    data = load_cron_data()
    logs = data['execution_logs']
    
    if job_id:
        logs = [l for l in logs if l['job_id'] == job_id]
    
    # Sort by time, newest first
    logs = sorted(logs, key=lambda x: x['execution_time'], reverse=True)
    
    return logs[:limit]
```

**3. `src/main/cron_jobs.py`** (NEW - FastAPI router)
```python
"""
Cron Jobs API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
import cron_service

router = APIRouter(prefix="/api/cron", tags=["Cron Jobs"])

class JobCreate(BaseModel):
    name: str
    schedule_time: str  # "18:30"
    frequency: List[str]  # ["Mon", "Tue", ...]
    is_repeat: bool = True

class JobUpdate(BaseModel):
    name: str = None
    schedule_time: str = None
    frequency: List[str] = None
    is_repeat: bool = None
    is_active: bool = None

@router.get("/jobs")
async def get_all_jobs():
    """Get all cron jobs"""
    data = cron_service.load_cron_data()
    return {"jobs": data['jobs'], "count": len(data['jobs'])}

@router.post("/jobs")
async def create_job(job: JobCreate):
    """Create new cron job"""
    try:
        new_job = cron_service.create_job(
            name=job.name,
            schedule_time=job.schedule_time,
            frequency=job.frequency,
            is_repeat=job.is_repeat
        )
        return {"message": "Job created", "job": new_job}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/jobs/{job_id}")
async def update_job(job_id: int, job: JobUpdate):
    """Update cron job"""
    try:
        updated = cron_service.update_job(job_id, **job.dict(exclude_none=True))
        return {"message": "Job updated", "job": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int):
    """Delete cron job"""
    cron_service.delete_job(job_id)
    return {"message": "Job deleted"}

@router.post("/jobs/{job_id}/toggle")
async def toggle_job(job_id: int):
    """Toggle job active/inactive"""
    try:
        updated = cron_service.toggle_job(job_id)
        return {"message": "Job toggled", "job": updated}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/jobs/{job_id}/run-now")
async def run_now(job_id: int, override_next: bool = False):
    """
    Run job immediately
    override_next: If true, cancels next scheduled run
    """
    result = cron_service.run_job_now(job_id, override_next)
    return {"message": "Job executed", "result": result}

@router.get("/logs")
async def get_logs(job_id: int = None, limit: int = 50):
    """Get execution logs"""
    logs = cron_service.get_execution_logs(job_id, limit)
    return {"logs": logs, "count": len(logs)}
```

**4. Modify `src/main/main.py` to start scheduler**
```python
from cron_service import start_scheduler, stop_scheduler
from cron_jobs import router as cron_router

app.include_router(cron_router)

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    print("✅ Cron scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
    print("🛑 Cron scheduler stopped")
```

---

### **PHASE 5: Manual Colors Upload** (1 day)

**What it does:**
- User uploads Excel with colors
- Stored for next automation run
- Download sample template

#### Files to Create:

**1. `src/main/manual_upload_service.py`** (NEW)
```python
"""
Manual colors upload service
"""

import pandas as pd
import os
from datetime import datetime
from typing import List, Dict

MANUAL_COLORS_DIR = "data/manual_colors"
os.makedirs(MANUAL_COLORS_DIR, exist_ok=True)

def save_manual_colors(df: pd.DataFrame) -> str:
    """
    Save uploaded manual colors
    Returns: filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"manual_colors_{timestamp}.xlsx"
    filepath = os.path.join(MANUAL_COLORS_DIR, filename)
    
    df.to_excel(filepath, index=False)
    
    return filename

def get_manual_colors() -> List[Dict]:
    """
    Load all manual colors from stored files
    Returns: List of color dictionaries
    """
    all_colors = []
    
    if not os.path.exists(MANUAL_COLORS_DIR):
        return all_colors
    
    # Load all Excel files in directory
    for filename in os.listdir(MANUAL_COLORS_DIR):
        if filename.endswith('.xlsx'):
            filepath = os.path.join(MANUAL_COLORS_DIR, filename)
            df = pd.read_excel(filepath)
            colors = df.to_dict('records')
            all_colors.extend(colors)
    
    return all_colors

def clear_manual_colors():
    """Clear all manual color files"""
    if os.path.exists(MANUAL_COLORS_DIR):
        for filename in os.listdir(MANUAL_COLORS_DIR):
            filepath = os.path.join(MANUAL_COLORS_DIR, filename)
            os.remove(filepath)
```

**2. Modify `src/main/database_service.py` to include manual colors**
```python
def load_data(self) -> List[Dict]:
    """Load data from Oracle (or Excel fallback) + manual colors"""
    
    # Existing logic (Oracle or Excel)
    if self.oracle_enabled and self._test_oracle_available():
        data = self._load_data_from_oracle()
    else:
        data = self._load_data_from_excel()
    
    # 🆕 Add manual colors
    from manual_upload_service import get_manual_colors
    manual_colors = get_manual_colors()
    
    if manual_colors:
        print(f"Adding {len(manual_colors)} manual colors")
        data.extend(manual_colors)
    
    return data
```

**3. Update `src/main/manual_colors.py` router**
```python
@router.post("/upload-excel")
async def upload_manual_colors(file: UploadFile = File(...)):
    """
    Upload Excel with manual colors
    These will be included in next automation run
    """
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns
        required_cols = ['DATE', 'RANK', 'PX', 'CUSIP']  # Adjust as needed
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {missing}"
            )
        
        # Save
        from manual_upload_service import save_manual_colors
        filename = save_manual_colors(df)
        
        return {
            "message": "Manual colors uploaded",
            "filename": filename,
            "rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/clear")
async def clear_manual_colors():
    """Clear all manual colors"""
    from manual_upload_service import clear_manual_colors
    clear_manual_colors()
    return {"message": "Manual colors cleared"}

@router.get("/sample-template")
async def download_sample():
    """Download sample Excel template"""
    # Create sample template with correct columns
    sample_data = {
        'DATE': ['2026-01-26', '2026-01-26'],
        'RANK': [1, 2],
        'PX': [100.5, 99.8],
        'CUSIP': ['12345ABC', '67890DEF'],
        'TICKER': ['SAMPLE1', 'SAMPLE2'],
        'BIAS': ['BUY', 'SELL']
    }
    df = pd.DataFrame(sample_data)
    
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=manual_colors_template.xlsx"}
    )
```

---

### **PHASE 6: Restore & Email** (2 days)

**What it does:**
- Track automation runs
- Remove Data (rollback)
- Send Email manually
- Email automation after cron jobs

#### Files to Create:

**1. `data/restore_logs.json`** (NEW)
```json
{
  "runs": [
    {
      "id": 1,
      "name": "US CLO N1800 Batch",
      "run_date": "2026-01-26",
      "run_time": "18:30",
      "process_type": "Automated",
      "status": "success",
      "rows_processed": 5213,
      "output_file": "Processed_Colors_Output.xlsx",
      "backup_file": "backups/backup_20260126_1830.xlsx"
    }
  ]
}
```

**2. `src/main/restore_service.py`** (NEW)
```python
"""
Restore & Email service
"""

import json
import os
import shutil
from datetime import datetime
from typing import List, Dict

RESTORE_FILE = "data/restore_logs.json"
BACKUPS_DIR = "data/backups"
OUTPUT_FILE = "Processed_Colors_Output.xlsx"

os.makedirs(BACKUPS_DIR, exist_ok=True)

def load_restore_data() -> Dict:
    """Load restore logs"""
    if not os.path.exists(RESTORE_FILE):
        return {"runs": []}
    with open(RESTORE_FILE, 'r') as f:
        return json.load(f)

def save_restore_data(data: Dict):
    """Save restore logs"""
    with open(RESTORE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def create_backup() -> str:
    """
    Create backup of current output file
    Returns: backup filename
    """
    if not os.path.exists(OUTPUT_FILE):
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.xlsx"
    backup_path = os.path.join(BACKUPS_DIR, backup_filename)
    
    shutil.copy2(OUTPUT_FILE, backup_path)
    
    return backup_filename

def log_run(
    name: str,
    process_type: str,
    status: str,
    rows_processed: int,
    backup_file: str = None
):
    """Log automation run"""
    data = load_restore_data()
    
    new_id = max([r.get('id', 0) for r in data['runs']], default=0) + 1
    
    run_entry = {
        "id": new_id,
        "name": name,
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "run_time": datetime.now().strftime("%H:%M"),
        "process_type": process_type,
        "status": status,
        "rows_processed": rows_processed,
        "output_file": OUTPUT_FILE,
        "backup_file": backup_file
    }
    
    data['runs'].append(run_entry)
    save_restore_data(data)

def restore_backup(run_id: int) -> bool:
    """
    Restore from backup (rollback)
    """
    data = load_restore_data()
    
    # Find run
    run = next((r for r in data['runs'] if r['id'] == run_id), None)
    if not run:
        raise ValueError(f"Run {run_id} not found")
    
    backup_file = run.get('backup_file')
    if not backup_file:
        raise ValueError("No backup available for this run")
    
    backup_path = os.path.join(BACKUPS_DIR, backup_file)
    if not os.path.exists(backup_path):
        raise ValueError(f"Backup file not found: {backup_file}")
    
    # Create backup of current before restoring
    current_backup = create_backup()
    
    # Restore
    shutil.copy2(backup_path, OUTPUT_FILE)
    
    print(f"✅ Restored from {backup_file}")
    return True

def get_all_runs() -> List[Dict]:
    """Get all automation runs"""
    data = load_restore_data()
    return sorted(data['runs'], key=lambda x: x['run_date'], reverse=True)
```

**3. `src/main/email_service.py`** (NEW)
```python
"""
Email notification service
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    attachment_path: str = None
) -> bool:
    """
    Send email via SMTP
    """
    # SMTP configuration from environment
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', smtp_user)
    
    if not smtp_user or not smtp_password:
        print("❌ Email not configured (missing SMTP credentials)")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(attachment_path)}'
                )
                msg.attach(part)
        
        # Send
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {to_emails}")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def send_automation_report(
    job_name: str,
    rows_processed: int,
    duration: float,
    status: str
):
    """
    Send email after automation run
    """
    to_emails = os.getenv('NOTIFICATION_EMAILS', '').split(',')
    if not to_emails or not to_emails[0]:
        return
    
    subject = f"Market Pulse - {job_name} - {status.upper()}"
    
    body = f"""
    <html>
    <body>
        <h2>Market Pulse Automation Report</h2>
        <p><strong>Job:</strong> {job_name}</p>
        <p><strong>Status:</strong> {status}</p>
        <p><strong>Rows Processed:</strong> {rows_processed:,}</p>
        <p><strong>Duration:</strong> {duration:.2f} seconds</p>
        <p><strong>Time:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Output file attached.</p>
    </body>
    </html>
    """
    
    send_email(
        to_emails=to_emails,
        subject=subject,
        body=body,
        attachment_path="Processed_Colors_Output.xlsx"
    )
```

**4. `src/main/restore.py`** (NEW - FastAPI router)
```python
"""
Restore & Email API endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List
import restore_service
import email_service

router = APIRouter(prefix="/api/restore", tags=["Restore & Email"])

@router.get("/runs")
async def get_all_runs():
    """Get all automation runs"""
    runs = restore_service.get_all_runs()
    return {"runs": runs, "count": len(runs)}

@router.post("/rollback/{run_id}")
async def rollback_run(run_id: int):
    """Rollback (remove data) from specific run"""
    try:
        restore_service.restore_backup(run_id)
        return {"message": "Data restored successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/send-email/{run_id}")
async def resend_email(run_id: int):
    """Manually send email for specific run"""
    runs = restore_service.get_all_runs()
    run = next((r for r in runs if r['id'] == run_id), None)
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Send email
    success = email_service.send_automation_report(
        job_name=run['name'],
        rows_processed=run['rows_processed'],
        duration=0,
        status=run['status']
    )
    
    if success:
        return {"message": "Email sent"}
    else:
        raise HTTPException(status_code=500, detail="Email failed")
```

**5. Integrate email with cron jobs - Modify `src/main/cron_service.py`**
```python
def execute_automation(job_id: int, override_type: str = None):
    """Execute automation + send email"""
    # ... existing logic ...
    
    # After successful processing
    if status == "success":
        # Send email notification
        from email_service import send_automation_report
        send_automation_report(
            job_name=job['name'],
            rows_processed=len(ranked_data),
            duration=duration,
            status="success"
        )
        
        # Log run for restore
        from restore_service import log_run, create_backup
        backup_file = create_backup()
        log_run(
            name=job['name'],
            process_type="Automated",
            status="success",
            rows_processed=len(ranked_data),
            backup_file=backup_file
        )
```

**6. Update `.env.example`**
```
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@marketpulse.com
NOTIFICATION_EMAILS=admin@company.com,team@company.com
```

---

## 📊 Summary

### **Total APIs Created:**

| Phase | APIs | Endpoints |
|-------|------|-----------|
| Phase 1: S3 Integration | User service | N/A (internal) |
| Phase 2: Security Search | 3 | `/search/by-identifier`, `/search/bulk-search`, `/search/sample-template` |
| Phase 3: Rules Engine | 6 | `/rules` (GET/POST/PUT/DELETE), `/rules/{id}/toggle`, `/rules/active` |
| Phase 4: Cron Jobs | 7 | `/cron/jobs` (CRUD), `/cron/jobs/{id}/run-now`, `/cron/logs` |
| Phase 5: Manual Colors | 3 | `/manual-colors/upload`, `/clear`, `/sample-template` |
| Phase 6: Restore & Email | 3 | `/restore/runs`, `/restore/rollback/{id}`, `/restore/send-email/{id}` |

**Total: ~22 new API endpoints**

### **Files Structure:**

```
sp-incb-market-pulse-master/
├── data/                          # 🆕 Local storage (no Oracle DB)
│   ├── rules.json                 # Rules storage
│   ├── cron_jobs.json             # Cron jobs + logs
│   ├── restore_logs.json          # Automation runs
│   ├── manual_colors/             # Uploaded colors
│   └── backups/                   # Output backups
├── src/main/
│   ├── s3_service.py              # 🆕 S3 integration
│   ├── user_service.py            # 🆕 User permissions
│   ├── search_service.py          # 🆕 Security search
│   ├── search.py                  # 🆕 Search router
│   ├── rules_service.py           # 🆕 Rules logic
│   ├── rules.py                   # 🆕 Rules router
│   ├── cron_service.py            # 🆕 Cron scheduler
│   ├── cron_jobs.py               # 🆕 Cron router
│   ├── manual_upload_service.py   # 🆕 Manual colors
│   ├── restore_service.py         # 🆕 Restore logic
│   ├── email_service.py           # 🆕 Email sending
│   ├── restore.py                 # 🆕 Restore router
│   ├── database_service.py        # ✏️ Modified (add manual colors)
│   ├── dashboard.py               # ✏️ Modified (add rules + user filter)
│   └── main.py                    # ✏️ Modified (register routers, start scheduler)
├── requirements.txt               # ✏️ Add boto3, apscheduler
└── .env                           # ✏️ Add S3, SMTP config
```

### **Dependencies to Add:**

```txt
boto3==1.34.34           # AWS S3
apscheduler==3.10.4      # Cron scheduler
```

### **Environment Variables:**

```bash
# S3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=market-pulse-data

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
NOTIFICATION_EMAILS=admin@company.com

# Oracle (for future)
ORACLE_ENABLED=False  # Will be True when Oracle is configured
```

### **Estimated Timeline:**

| Phase | Days |
|-------|------|
| Phase 1: S3 Integration | 2-3 days |
| Phase 2: Security Search | 1 day |
| Phase 3: Rules Engine | 3-4 days |
| Phase 4: Cron Jobs | 3-4 days |
| Phase 5: Manual Colors | 1 day |
| Phase 6: Restore & Email | 2 days |
| **Total** | **12-15 days** |

---

## 🚦 Next Steps

**Ready to start?** I can begin implementing:

1. **Phase 1 (S3 Integration)** - Get user permissions working
2. **Phase 2 (Security Search)** - Quick win, simple search APIs
3. **Phase 3 (Rules Engine)** - Core business logic
4. **Then continue** through Phases 4-6

**Which phase should I start with?** Or would you like me to begin with Phase 1 right away? 🚀
