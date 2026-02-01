# Milestone 2: Core Logic Implementation (Pre-Integration)

**Project:** Market Pulse - Backend Logic (Python/FastAPI)  
**Date:** January 26, 2026  
**Strategy:** Build core logic first, add S3/Oracle integration later  
**Timeline:** 8-10 days (core logic only)

---

## 🎯 Strategy: Separation of Concerns

### **Phase A: Core Logic (NOW - No Credentials Needed)**
Build all business logic using JSON file storage. Everything works standalone.

### **Phase B: Integration Layer (LATER - When Credentials Available)**
Swap JSON storage with S3/Oracle by updating configuration only.

---

## 📦 Architecture: Storage Abstraction

All services will use **storage interfaces**:

```python
# storage_interface.py
class StorageInterface:
    def save(self, key: str, data: dict): pass
    def load(self, key: str) -> dict: pass
    def delete(self, key: str): pass

# json_storage.py (Phase A - NOW)
class JSONStorage(StorageInterface):
    def save(self, key, data):
        with open(f"data/{key}.json", 'w') as f:
            json.dump(data, f)

# s3_storage.py (Phase B - LATER)
class S3Storage(StorageInterface):
    def save(self, key, data):
        self.s3_client.put_object(...)
```

**When credentials arrive:** Change one line in config:
```python
# storage = JSONStorage()  # Phase A
storage = S3Storage()      # Phase B - just change this!
```

---

## 🚀 Implementation Plan (Core Logic First)

### **PHASE 1: Rules Engine** (2-3 days)

#### What We're Building:
- Exclusion rules system ("Remove DZ Bank securities")
- Condition evaluation (WHERE/AND/OR)
- Apply rules to data
- CRUD APIs for rules

#### Storage: JSON file (`data/rules.json`)

#### Files to Create:

**1. `src/main/storage_interface.py`** (NEW - Abstraction layer)
```python
"""
Storage abstraction - allows swapping between JSON and S3
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class StorageInterface(ABC):
    """Base class for all storage implementations"""
    
    @abstractmethod
    def save(self, key: str, data: Any):
        """Save data"""
        pass
    
    @abstractmethod
    def load(self, key: str) -> Any:
        """Load data"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """Delete data"""
        pass
```

**2. `src/main/json_storage.py`** (NEW - JSON implementation)
```python
"""
JSON file storage implementation
Used for Phase A (before S3 credentials)
"""

import json
import os
from typing import Any
from storage_interface import StorageInterface

class JSONStorage(StorageInterface):
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def _get_path(self, key: str) -> str:
        return os.path.join(self.data_dir, f"{key}.json")
    
    def save(self, key: str, data: Any):
        """Save to JSON file"""
        with open(self._get_path(key), 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, key: str) -> Any:
        """Load from JSON file"""
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return json.load(f)
    
    def exists(self, key: str) -> bool:
        """Check if file exists"""
        return os.path.exists(self._get_path(key))
    
    def delete(self, key: str):
        """Delete JSON file"""
        path = self._get_path(key)
        if os.path.exists(path):
            os.remove(path)

# Default storage (will be configured later)
storage = JSONStorage()
```

**3. `src/main/storage_config.py`** (NEW - Configuration point)
```python
"""
Storage configuration - SINGLE POINT to switch between JSON and S3
When S3 credentials are ready, just change this file
"""

import os
from json_storage import JSONStorage
# from s3_storage import S3Storage  # Uncomment when ready

def get_storage():
    """
    Get storage implementation based on environment
    
    To switch to S3 later:
    1. Set environment variable: STORAGE_TYPE=s3
    2. Set S3 credentials in .env
    3. Uncomment S3Storage import above
    """
    storage_type = os.getenv('STORAGE_TYPE', 'json')
    
    if storage_type == 's3':
        # return S3Storage()  # Will implement in Phase B
        raise NotImplementedError("S3 storage not configured yet")
    else:
        return JSONStorage()

# Global storage instance
storage = get_storage()
```

**4. `src/main/rules_service.py`** (NEW - Rules logic)
```python
"""
Rules Engine - Core Business Logic
Works with ANY storage backend (JSON or S3)
"""

from typing import List, Dict
from datetime import datetime
from storage_config import storage

RULES_KEY = "rules"

def _ensure_rules_exist():
    """Initialize rules storage if doesn't exist"""
    if not storage.exists(RULES_KEY):
        storage.save(RULES_KEY, {"rules": []})

def load_rules() -> List[Dict]:
    """Load all rules"""
    _ensure_rules_exist()
    data = storage.load(RULES_KEY)
    return data.get('rules', [])

def save_rules(rules: List[Dict]):
    """Save rules"""
    storage.save(RULES_KEY, {"rules": rules})

def get_active_rules() -> List[Dict]:
    """Get only active rules"""
    all_rules = load_rules()
    return [r for r in all_rules if r.get('is_active', True)]

def evaluate_condition(row: Dict, condition: Dict) -> bool:
    """
    Evaluate single condition against a row
    
    Operators:
    - equals, not_equals
    - contains, not_contains
    - starts_with, ends_with
    - greater_than, less_than
    """
    column = condition['column']
    operator = condition['operator']
    value = condition['value']
    
    # Get row value (handle missing columns)
    row_value = str(row.get(column, ''))
    compare_value = str(value)
    
    # Operator logic
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
        except (ValueError, TypeError):
            return False
    
    elif operator == 'less_than':
        try:
            return float(row_value) < float(compare_value)
        except (ValueError, TypeError):
            return False
    
    return False

def evaluate_rule(row: Dict, rule: Dict) -> bool:
    """
    Evaluate if a rule matches a row
    Returns True if row should be EXCLUDED
    
    Logic:
    - WHERE/AND conditions: ALL must match (AND logic)
    - OR conditions: If any OR matches, evaluate separately
    - Subgroups: Nested evaluation
    """
    conditions = rule.get('conditions', [])
    
    if not conditions:
        return False
    
    # Simple implementation: All conditions must match (AND logic)
    # For OR logic and subgroups, we can extend this later
    for condition in conditions:
        condition_type = condition.get('type', 'where')
        
        if condition_type in ['where', 'and']:
            if not evaluate_condition(row, condition):
                return False  # One condition failed
        
        elif condition_type == 'or':
            # OR logic: needs special handling
            # For now, treat as AND (can enhance later)
            if not evaluate_condition(row, condition):
                return False
    
    return True  # All conditions matched -> EXCLUDE this row

def apply_rules(data: List[Dict]) -> Dict:
    """
    Apply all active rules to filter data
    
    Returns:
    {
        "filtered_data": [...],
        "excluded_count": 123,
        "rules_applied": 2
    }
    """
    active_rules = get_active_rules()
    
    if not active_rules:
        return {
            "filtered_data": data,
            "excluded_count": 0,
            "rules_applied": 0
        }
    
    filtered_data = []
    excluded_count = 0
    
    for row in data:
        should_exclude = False
        
        # Check each rule
        for rule in active_rules:
            if evaluate_rule(row, rule):
                should_exclude = True
                excluded_count += 1
                break  # One rule matched, exclude
        
        if not should_exclude:
            filtered_data.append(row)
    
    print(f"✅ Rules applied: {len(active_rules)} active rules")
    print(f"📊 Excluded: {excluded_count} rows")
    print(f"📊 Remaining: {len(filtered_data)} rows")
    
    return {
        "filtered_data": filtered_data,
        "excluded_count": excluded_count,
        "rules_applied": len(active_rules),
        "original_count": len(data)
    }

def create_rule(name: str, conditions: List[Dict], is_active: bool = True) -> Dict:
    """Create new rule"""
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

def update_rule(rule_id: int, **kwargs) -> Dict:
    """Update existing rule"""
    rules = load_rules()
    
    for rule in rules:
        if rule['id'] == rule_id:
            # Update fields
            for key, value in kwargs.items():
                if value is not None:
                    rule[key] = value
            
            rule['updated_at'] = datetime.now().isoformat()
            save_rules(rules)
            return rule
    
    raise ValueError(f"Rule {rule_id} not found")

def delete_rule(rule_id: int):
    """Delete rule"""
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

def get_rule_by_id(rule_id: int) -> Dict:
    """Get single rule by ID"""
    rules = load_rules()
    rule = next((r for r in rules if r['id'] == rule_id), None)
    if not rule:
        raise ValueError(f"Rule {rule_id} not found")
    return rule
```

**5. `src/main/rules.py`** (NEW - FastAPI router)
```python
"""
Rules API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
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
    name: Optional[str] = None
    conditions: Optional[List[Dict]] = None
    is_active: Optional[bool] = None

@router.get("")
async def get_all_rules():
    """Get all rules"""
    rules = rules_service.load_rules()
    return {
        "rules": rules,
        "count": len(rules)
    }

@router.get("/active")
async def get_active_rules():
    """Get only active rules"""
    rules = rules_service.get_active_rules()
    return {
        "rules": rules,
        "count": len(rules)
    }

@router.get("/{rule_id}")
async def get_rule(rule_id: int):
    """Get single rule by ID"""
    try:
        rule = rules_service.get_rule_by_id(rule_id)
        return {"rule": rule}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("")
async def create_rule(rule: RuleCreate):
    """Create new rule"""
    try:
        new_rule = rules_service.create_rule(
            name=rule.name,
            conditions=rule.conditions,
            is_active=rule.is_active
        )
        return {
            "message": "Rule created successfully",
            "rule": new_rule
        }
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
        return {
            "message": "Rule updated successfully",
            "rule": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete rule"""
    try:
        rules_service.delete_rule(rule_id)
        return {"message": "Rule deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{rule_id}/toggle")
async def toggle_rule(rule_id: int):
    """Toggle rule active/inactive"""
    try:
        updated = rules_service.toggle_rule(rule_id)
        status = "activated" if updated['is_active'] else "deactivated"
        return {
            "message": f"Rule {status}",
            "rule": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/test")
async def test_rule(rule: RuleCreate, test_data: List[Dict]):
    """
    Test a rule against sample data without saving
    Useful for previewing what will be excluded
    """
    try:
        # Create temporary rule
        temp_rule = {
            "id": -1,
            "name": rule.name,
            "is_active": True,
            "conditions": rule.conditions
        }
        
        # Test against data
        excluded = []
        included = []
        
        for row in test_data:
            if rules_service.evaluate_rule(row, temp_rule):
                excluded.append(row)
            else:
                included.append(row)
        
        return {
            "total_rows": len(test_data),
            "excluded_count": len(excluded),
            "included_count": len(included),
            "excluded_sample": excluded[:5],  # First 5 excluded
            "included_sample": included[:5]   # First 5 included
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**6. Register in `src/main/main.py`**
```python
# Add to imports
from rules import router as rules_router

# Add to app
app.include_router(rules_router)
```

**7. Integrate with Dashboard API - Modify `src/main/dashboard.py`**
```python
from rules_service import apply_rules

@router.get("/colors")
async def get_colors():
    """
    Get processed colors with rules applied
    """
    # 1. Load data
    raw_data = database_service.load_data()
    
    # 2. 🆕 Apply exclusion rules
    rules_result = apply_rules(raw_data)
    filtered_data = rules_result['filtered_data']
    
    # 3. Run ranking
    ranked_data = ranking_engine.rank_colors(filtered_data)
    
    # 4. Append to output
    output_service.append_processed_colors(ranked_data, processing_type="AUTOMATED")
    
    return {
        "data": ranked_data,
        "stats": {
            "original_count": rules_result['original_count'],
            "excluded_count": rules_result['excluded_count'],
            "rules_applied": rules_result['rules_applied'],
            "final_count": len(ranked_data)
        }
    }
```

---

### **PHASE 2: Cron Jobs & Automation** (3 days)

#### What We're Building:
- Schedule automated runs
- Background task execution
- Status tracking
- Run manually with override options

#### Storage: JSON file (`data/cron_jobs.json`)

#### Files to Create:

**1. `src/main/cron_service.py`** (NEW)
```python
"""
Cron Job Scheduler - Core Logic
Uses storage abstraction (works with JSON or S3)
"""

import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from storage_config import storage

# Import existing services
from database_service import database_service
from rules_service import apply_rules
from ranking_engine import rank_colors
from output_service import append_processed_colors

CRON_KEY = "cron_jobs"
LOGS_KEY = "cron_logs"

# Scheduler instance
scheduler = BackgroundScheduler()

# Day mapping for cron
DAY_MAP = {
    "Mon": "mon", "Tue": "tue", "Wed": "wed",
    "Thu": "thu", "Fri": "fri", "Sat": "sat", "Sun": "sun"
}

def _ensure_storage():
    """Initialize storage if needed"""
    if not storage.exists(CRON_KEY):
        storage.save(CRON_KEY, {"jobs": []})
    if not storage.exists(LOGS_KEY):
        storage.save(LOGS_KEY, {"logs": []})

def load_jobs() -> List[Dict]:
    """Load all cron jobs"""
    _ensure_storage()
    data = storage.load(CRON_KEY)
    return data.get('jobs', [])

def save_jobs(jobs: List[Dict]):
    """Save cron jobs"""
    storage.save(CRON_KEY, {"jobs": jobs})

def load_logs() -> List[Dict]:
    """Load execution logs"""
    _ensure_storage()
    data = storage.load(LOGS_KEY)
    return data.get('logs', [])

def save_logs(logs: List[Dict]):
    """Save execution logs"""
    storage.save(LOGS_KEY, {"logs": logs})

def execute_automation(job_id: int, override_type: Optional[str] = None):
    """
    Main automation execution logic
    This runs when cron triggers or manual run
    """
    start_time = datetime.now()
    
    # Get job details
    jobs = load_jobs()
    job = next((j for j in jobs if j['id'] == job_id), None)
    
    if not job:
        print(f"❌ Job {job_id} not found")
        return
    
    print(f"🚀 Starting automation: {job['name']}")
    
    try:
        # 1. Load data
        print(f"  📥 Loading data...")
        raw_data = database_service.load_data()
        print(f"  ✓ Loaded {len(raw_data)} rows")
        
        # 2. Apply rules
        print(f"  🔧 Applying rules...")
        rules_result = apply_rules(raw_data)
        filtered_data = rules_result['filtered_data']
        print(f"  ✓ Excluded {rules_result['excluded_count']} rows")
        
        # 3. Run ranking
        print(f"  📊 Running ranking...")
        ranked_data = rank_colors(filtered_data)
        print(f"  ✓ Ranked {len(ranked_data)} colors")
        
        # 4. Save output
        print(f"  💾 Saving output...")
        append_processed_colors(ranked_data, processing_type="AUTOMATED")
        print(f"  ✓ Saved to output file")
        
        # 5. Log execution
        duration = (datetime.now() - start_time).total_seconds()
        log_execution(
            job_id=job_id,
            job_name=job['name'],
            status="success",
            rows_processed=len(ranked_data),
            duration=duration,
            override_type=override_type
        )
        
        print(f"✅ Completed in {duration:.2f}s")
        
        return {
            "status": "success",
            "rows_processed": len(ranked_data),
            "duration": duration
        }
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"❌ Error: {e}")
        
        log_execution(
            job_id=job_id,
            job_name=job['name'],
            status="error",
            rows_processed=0,
            duration=duration,
            error_message=str(e)
        )
        
        return {
            "status": "error",
            "message": str(e)
        }

def log_execution(
    job_id: int,
    job_name: str,
    status: str,
    rows_processed: int,
    duration: float,
    override_type: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Add execution log"""
    logs = load_logs()
    
    log_entry = {
        "job_id": job_id,
        "job_name": job_name,
        "execution_time": datetime.now().isoformat(),
        "status": status,  # success, error, override, skipped
        "rows_processed": rows_processed,
        "duration_seconds": duration,
        "override_type": override_type,
        "error_message": error_message
    }
    
    logs.append(log_entry)
    
    # Keep only last 1000 logs
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    save_logs(logs)

def register_job(job: Dict):
    """Register job with APScheduler"""
    if not job.get('is_active', True):
        return
    
    job_id = job['id']
    schedule_time = job['schedule_time']  # "18:30"
    frequency = job.get('frequency', [])
    
    if not frequency:
        print(f"⚠️ Job {job['name']}: No frequency set")
        return
    
    try:
        hour, minute = schedule_time.split(":")
        days = ','.join([DAY_MAP[day] for day in frequency if day in DAY_MAP])
        
        if not days:
            print(f"⚠️ Job {job['name']}: No valid days")
            return
        
        trigger = CronTrigger(
            hour=int(hour),
            minute=int(minute),
            day_of_week=days,
            timezone='UTC'  # Will be configurable later
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
        
    except Exception as e:
        print(f"❌ Failed to register {job['name']}: {e}")

def start_scheduler():
    """Start APScheduler and load all jobs"""
    if scheduler.running:
        print("⚠️ Scheduler already running")
        return
    
    # Load and register all active jobs
    jobs = load_jobs()
    active_jobs = [j for j in jobs if j.get('is_active', True)]
    
    for job in active_jobs:
        register_job(job)
    
    scheduler.start()
    print(f"🚀 Scheduler started with {len(scheduler.get_jobs())} jobs")

def stop_scheduler():
    """Stop scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Scheduler stopped")

def create_job(
    name: str,
    schedule_time: str,
    frequency: List[str],
    is_repeat: bool = True,
    description: str = ""
) -> Dict:
    """Create new cron job"""
    jobs = load_jobs()
    
    new_id = max([j.get('id', 0) for j in jobs], default=0) + 1
    
    new_job = {
        "id": new_id,
        "name": name,
        "description": description,
        "schedule_time": schedule_time,
        "frequency": frequency,
        "is_repeat": is_repeat,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    jobs.append(new_job)
    save_jobs(jobs)
    
    # Register with scheduler
    register_job(new_job)
    
    return new_job

def update_job(job_id: int, **kwargs) -> Dict:
    """Update cron job"""
    jobs = load_jobs()
    
    for job in jobs:
        if job['id'] == job_id:
            # Update fields
            for key, value in kwargs.items():
                if value is not None:
                    job[key] = value
            
            job['updated_at'] = datetime.now().isoformat()
            save_jobs(jobs)
            
            # Re-register if active
            if job.get('is_active', True):
                register_job(job)
            else:
                # Remove from scheduler
                try:
                    scheduler.remove_job(f"job_{job_id}")
                except:
                    pass
            
            return job
    
    raise ValueError(f"Job {job_id} not found")

def delete_job(job_id: int):
    """Delete cron job"""
    jobs = load_jobs()
    jobs = [j for j in jobs if j['id'] != job_id]
    save_jobs(jobs)
    
    # Remove from scheduler
    try:
        scheduler.remove_job(f"job_{job_id}")
    except:
        pass

def toggle_job(job_id: int) -> Dict:
    """Toggle job active status"""
    jobs = load_jobs()
    
    for job in jobs:
        if job['id'] == job_id:
            job['is_active'] = not job.get('is_active', True)
            job['updated_at'] = datetime.now().isoformat()
            save_jobs(jobs)
            
            if job['is_active']:
                register_job(job)
            else:
                try:
                    scheduler.remove_job(f"job_{job_id}")
                except:
                    pass
            
            return job
    
    raise ValueError(f"Job {job_id} not found")

def run_job_now(job_id: int, cancel_next: bool = False) -> Dict:
    """
    Run job immediately
    
    Args:
        job_id: Job to run
        cancel_next: If True, skip next scheduled run (override mode)
    """
    # Execute now
    result = execute_automation(
        job_id=job_id,
        override_type="manual_override" if cancel_next else "manual_run"
    )
    
    # If cancel_next, we can implement skip logic here
    # For now, just log it
    if cancel_next:
        print(f"⚠️ Next scheduled run will be skipped")
        # TODO: Implement skip next run logic
    
    return result

def get_execution_logs(
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """Get execution logs with filters"""
    logs = load_logs()
    
    # Filter by job_id
    if job_id:
        logs = [l for l in logs if l['job_id'] == job_id]
    
    # Filter by status
    if status:
        logs = [l for l in logs if l['status'] == status]
    
    # Sort by time (newest first)
    logs = sorted(logs, key=lambda x: x['execution_time'], reverse=True)
    
    return logs[:limit]

def get_next_run_time(job: Dict) -> Optional[str]:
    """Calculate next run time for a job"""
    if not job.get('is_active', True):
        return None
    
    try:
        job_id = f"job_{job['id']}"
        scheduled_job = scheduler.get_job(job_id)
        if scheduled_job and scheduled_job.next_run_time:
            return scheduled_job.next_run_time.isoformat()
    except:
        pass
    
    return None
```

**2. `src/main/cron_jobs.py`** (NEW - FastAPI router)
```python
"""
Cron Jobs API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import cron_service

router = APIRouter(prefix="/api/cron", tags=["Cron Jobs"])

class JobCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    schedule_time: str  # "18:30"
    frequency: List[str]  # ["Mon", "Tue", "Wed"]
    is_repeat: bool = True

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_time: Optional[str] = None
    frequency: Optional[List[str]] = None
    is_repeat: Optional[bool] = None
    is_active: Optional[bool] = None

@router.get("/jobs")
async def get_all_jobs():
    """Get all cron jobs with next run times"""
    jobs = cron_service.load_jobs()
    
    # Add next run time to each job
    for job in jobs:
        job['next_run'] = cron_service.get_next_run_time(job)
    
    return {
        "jobs": jobs,
        "count": len(jobs)
    }

@router.get("/jobs/{job_id}")
async def get_job(job_id: int):
    """Get single job by ID"""
    jobs = cron_service.load_jobs()
    job = next((j for j in jobs if j['id'] == job_id), None)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job['next_run'] = cron_service.get_next_run_time(job)
    
    return {"job": job}

@router.post("/jobs")
async def create_job(job: JobCreate):
    """Create new cron job"""
    try:
        new_job = cron_service.create_job(
            name=job.name,
            description=job.description,
            schedule_time=job.schedule_time,
            frequency=job.frequency,
            is_repeat=job.is_repeat
        )
        return {
            "message": "Job created successfully",
            "job": new_job
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/jobs/{job_id}")
async def update_job(job_id: int, job: JobUpdate):
    """Update cron job"""
    try:
        updated = cron_service.update_job(
            job_id=job_id,
            **job.dict(exclude_none=True)
        )
        return {
            "message": "Job updated successfully",
            "job": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int):
    """Delete cron job"""
    try:
        cron_service.delete_job(job_id)
        return {"message": "Job deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/jobs/{job_id}/toggle")
async def toggle_job(job_id: int):
    """Toggle job active/inactive"""
    try:
        updated = cron_service.toggle_job(job_id)
        status = "activated" if updated['is_active'] else "deactivated"
        return {
            "message": f"Job {status}",
            "job": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/jobs/{job_id}/run-now")
async def run_now(
    job_id: int,
    cancel_next: bool = False
):
    """
    Run job immediately
    
    Args:
        cancel_next: If true, skip next scheduled run (override mode)
    """
    try:
        result = cron_service.run_job_now(job_id, cancel_next)
        return {
            "message": "Job executed",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/logs")
async def get_logs(
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    Get execution logs
    
    Args:
        job_id: Filter by job ID
        status: Filter by status (success, error, override)
        limit: Max number of logs to return
    """
    logs = cron_service.get_execution_logs(job_id, status, limit)
    return {
        "logs": logs,
        "count": len(logs)
    }

@router.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    is_running = cron_service.scheduler.running
    jobs_count = len(cron_service.scheduler.get_jobs()) if is_running else 0
    
    return {
        "running": is_running,
        "jobs_scheduled": jobs_count
    }
```

**3. Update `src/main/main.py`**
```python
from cron_service import start_scheduler, stop_scheduler
from cron_jobs import router as cron_router

app.include_router(cron_router)

@app.on_event("startup")
async def startup_event():
    """Start cron scheduler on app startup"""
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop cron scheduler on app shutdown"""
    stop_scheduler()
```

**4. Add to `requirements.txt`**
```
apscheduler==3.10.4
```

---

### **PHASE 3: Manual Colors Upload** (1 day)

Simple file upload and storage, merged with automated data.

**Files:** `src/main/manual_upload_service.py`, update `database_service.py`

(Similar to previous plan, but using local storage)

---

### **PHASE 4: Restore & Logging** (2 days)

Backup system and activity logs.

**Files:** `src/main/restore_service.py`, `src/main/restore.py`

(Using JSON storage for logs)

---

## 🔌 Integration Layer (Phase B - Later)

When S3/Oracle credentials arrive:

**1. Create `src/main/s3_storage.py`**
```python
"""
S3 Storage Implementation
Create this file when credentials are ready
"""

import boto3
import json
import os
from storage_interface import StorageInterface

class S3Storage(StorageInterface):
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
    
    def save(self, key: str, data: Any):
        """Save to S3"""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f"{key}.json",
            Body=json.dumps(data),
            ContentType='application/json'
        )
    
    def load(self, key: str) -> Any:
        """Load from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=f"{key}.json"
            )
            return json.loads(response['Body'].read())
        except:
            return None
    
    def exists(self, key: str) -> bool:
        """Check if exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=f"{key}.json"
            )
            return True
        except:
            return False
    
    def delete(self, key: str):
        """Delete from S3"""
        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=f"{key}.json"
        )
```

**2. Update `storage_config.py`** (ONE LINE CHANGE!)
```python
from s3_storage import S3Storage  # Uncomment this

def get_storage():
    storage_type = os.getenv('STORAGE_TYPE', 'json')
    
    if storage_type == 's3':
        return S3Storage()  # Change here!
    else:
        return JSONStorage()
```

**3. Update `.env`**
```
STORAGE_TYPE=s3  # Change from 'json' to 's3'
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=...
```

**That's it! No code changes needed. Just configuration.**

---

## 📊 Summary

### **Phase A (NOW - 8-10 days):**
- ✅ Phase 1: Rules Engine (JSON storage)
- ✅ Phase 2: Cron Jobs (JSON storage)
- ✅ Phase 3: Manual Colors (local files)
- ✅ Phase 4: Restore & Logging (JSON storage)

### **Phase B (LATER - 1 day):**
- Create `s3_storage.py`
- Update `storage_config.py` (1 line)
- Update `.env` file
- Done!

### **When Credentials Arrive:**
Only 3 files to touch:
1. Create `s3_storage.py`
2. Edit `storage_config.py` (uncomment 1 import)
3. Edit `.env` (add credentials)

**Ready to start Phase 1 (Rules Engine)?** 🚀
