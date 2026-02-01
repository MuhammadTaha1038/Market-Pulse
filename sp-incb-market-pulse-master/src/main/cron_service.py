#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cron Service - Background job scheduler for automated color runs

This service manages scheduled automation runs:
- APScheduler for background jobs
- Storage-agnostic (works with JSON/S3/Oracle)
- Manual trigger support
- Execution logging
- Buffered manual file processing
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import sys
import os
import pytz

# Import storage
sys.path.insert(0, os.path.dirname(__file__))
from storage_config import storage

# Import services for automation
from services.database_service import DatabaseService
from services.ranking_engine import RankingEngine
from services.output_service import get_output_service
from rules_service import apply_rules
from models.color import ColorRaw
from manual_upload_service import get_buffered_files, process_buffered_file

logger = logging.getLogger(__name__)

# Get timezone (adjust this to your timezone)
TIMEZONE = pytz.timezone('Asia/Karachi')  # Change to your timezone

# Global scheduler instance with timezone
scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.start()

# Services
db_service = DatabaseService()
ranking_engine = RankingEngine()
output_service = get_output_service()


def get_all_jobs() -> List[Dict]:
    """Get all scheduled cron jobs"""
    try:
        jobs_data = storage.load("cron_jobs")
        if jobs_data is None:
            return []
        return jobs_data.get("jobs", [])
    except FileNotFoundError:
        return []


def get_job_by_id(job_id: int) -> Optional[Dict]:
    """Get single job by ID"""
    jobs = get_all_jobs()
    for job in jobs:
        if job["id"] == job_id:
            return job
    return None


def save_jobs(jobs: List[Dict]):
    """Save jobs to storage"""
    storage.save("cron_jobs", {"jobs": jobs})


def get_next_job_id() -> int:
    """Get next available job ID"""
    jobs = get_all_jobs()
    if not jobs:
        return 1
    return max(job["id"] for job in jobs) + 1


def get_execution_logs() -> List[Dict]:
    """Get execution history"""
    try:
        logs_data = storage.load("cron_logs")
        if logs_data is None:
            return []
        return logs_data.get("logs", [])
    except FileNotFoundError:
        return []


def save_execution_log(log_entry: Dict):
    """Save execution log entry"""
    logs = get_execution_logs()
    
    # Add auto-incrementing ID
    if logs:
        max_id = max(log.get("id", 0) for log in logs)
        log_entry["id"] = max_id + 1
    else:
        log_entry["id"] = 1
    
    logs.insert(0, log_entry)  # Most recent first
    
    # Keep only last 100 logs
    logs = logs[:100]
    
    storage.save("cron_logs", {"logs": logs})


def run_automation_task(job_id: int, job_name: str, triggered_by: str = "scheduled"):
    """
    Execute the automated color processing task
    
    This is the core automation logic:
    1. Process any buffered manual uploads
    2. Fetch raw colors from database
    3. Apply exclusion rules
    4. Apply ranking engine
    5. Save processed colors to output file
    """
    start_time = datetime.now()
    log_entry = {
        "job_id": job_id,
        "job_name": job_name,
        "triggered_by": triggered_by,
        "start_time": start_time.isoformat(),
        "status": "running"
    }
    
    manual_files_processed = 0
    manual_files_failed = 0
    
    try:
        logger.info(f"🚀 Starting automation task: {job_name} (ID: {job_id})")
        
        # Step 1: Process buffered manual uploads first
        buffered_files = get_buffered_files()
        if buffered_files:
            logger.info(f"📂 Found {len(buffered_files)} buffered manual uploads to process")
            for buffer_entry in buffered_files:
                try:
                    result = process_buffered_file(buffer_entry)
                    if result["success"]:
                        manual_files_processed += 1
                    else:
                        manual_files_failed += 1
                except Exception as e:
                    logger.error(f"❌ Failed to process buffered file: {e}")
                    manual_files_failed += 1
            
            logger.info(f"✅ Processed {manual_files_processed} manual uploads, {manual_files_failed} failed")
        else:
            logger.info("ℹ️ No buffered manual uploads to process")
        
        # Step 2: Fetch raw colors from database
        logger.info("📥 Fetching raw colors from database...")
        raw_colors = db_service.fetch_all_colors()
        original_count = len(raw_colors)
        logger.info(f"✅ Fetched {original_count} raw colors")
        
        # Step 3: Apply exclusion rules
        logger.info("🔍 Applying exclusion rules...")
        raw_colors_dict = [color.dict() for color in raw_colors]
        rules_result = apply_rules(raw_colors_dict)
        filtered_colors_dict = rules_result["filtered_data"]
        excluded_count = rules_result["excluded_count"]
        rules_applied = rules_result["rules_applied"]
        logger.info(f"✅ Rules applied: {rules_applied} active rules, excluded {excluded_count} rows")
        
        # Convert filtered dicts back to ColorRaw objects for ranking engine
        filtered_colors = [ColorRaw(**color_dict) for color_dict in filtered_colors_dict]
        
        # Step 4: Apply ranking engine
        logger.info("📊 Applying ranking engine...")
        processed_colors = ranking_engine.run_colors(filtered_colors)
        logger.info(f"✅ Ranked {len(processed_colors)} colors")
        
        # Step 5: Save to output file
        logger.info("💾 Saving processed colors to output...")
        output_service.append_processed_colors(processed_colors, processing_type="AUTOMATED")
        logger.info(f"✅ Saved {len(processed_colors)} processed colors")
        
        # Success
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_entry.update({
            "status": "success",
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "original_count": original_count,
            "excluded_count": excluded_count,
            "processed_count": len(processed_colors),
            "rules_applied": rules_applied,
            "manual_files_processed": manual_files_processed,
            "manual_files_failed": manual_files_failed
        })
        
        logger.info(f"✅ Automation task completed successfully in {duration:.2f}s")
        
        # Step 6: Send email report if enabled
        try:
            import email_service
            
            report_data = {
                "date": start_time.strftime("%Y-%m-%d"),
                "time": start_time.strftime("%H:%M:%S"),
                "total_processed": len(processed_colors),
                "total_excluded": excluded_count,
                "rules_applied": rules_applied,
                "duration": f"{duration:.2f}s",
                "manual_files_processed": manual_files_processed
            }
            
            email_result = email_service.send_report_email(report_data)
            if email_result.get("success"):
                logger.info("📧 Email report sent successfully")
                log_entry["email_sent"] = True
            else:
                logger.warning(f"⚠️ Email not sent: {email_result.get('message')}")
                log_entry["email_sent"] = False
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to send email report: {e}")
            log_entry["email_sent"] = False
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_entry.update({
            "status": "failed",
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "error": str(e),
            "manual_files_processed": manual_files_processed,
            "manual_files_failed": manual_files_failed
        })
        
        logger.error(f"❌ Automation task failed: {e}")
    
    # Save execution log
    save_execution_log(log_entry)


def create_job(name: str, schedule: str, is_active: bool = True) -> Dict:
    """
    Create new cron job
    
    Args:
        name: Job name/description
        schedule: Cron expression (e.g., "0 9 * * *" for 9 AM daily)
        is_active: Whether job is active
    """
    jobs = get_all_jobs()
    
    job_id = get_next_job_id()
    
    new_job = {
        "id": job_id,
        "name": name,
        "schedule": schedule,
        "is_active": is_active,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "last_run": None,
        "next_run": None
    }
    
    # Add to APScheduler if active
    if is_active:
        try:
            trigger = CronTrigger.from_crontab(schedule, timezone=TIMEZONE)
            scheduler.add_job(
                func=run_automation_task,
                trigger=trigger,
                args=[job_id, name],
                id=f"cron_job_{job_id}",
                replace_existing=True
            )
            
            # Get next run time
            apscheduler_job = scheduler.get_job(f"cron_job_{job_id}")
            if apscheduler_job and apscheduler_job.next_run_time:
                new_job["next_run"] = apscheduler_job.next_run_time.isoformat()
            
            logger.info(f"✅ Scheduled job: {name} with schedule: {schedule}")
        except Exception as e:
            logger.error(f"❌ Failed to schedule job: {e}")
            raise ValueError(f"Invalid cron schedule: {schedule}")
    
    jobs.append(new_job)
    save_jobs(jobs)
    
    return new_job


def update_job(job_id: int, name: Optional[str] = None, schedule: Optional[str] = None, 
               is_active: Optional[bool] = None) -> Dict:
    """Update existing cron job"""
    jobs = get_all_jobs()
    
    job = None
    for j in jobs:
        if j["id"] == job_id:
            job = j
            break
    
    if not job:
        raise ValueError(f"Job with ID {job_id} not found")
    
    # Update fields
    if name is not None:
        job["name"] = name
    if schedule is not None:
        job["schedule"] = schedule
    if is_active is not None:
        job["is_active"] = is_active
    
    job["updated_at"] = datetime.now().isoformat()
    
    # Update APScheduler
    scheduler.remove_job(f"cron_job_{job_id}", jobstore=None)
    
    if job["is_active"]:
        try:
            trigger = CronTrigger.from_crontab(job["schedule"], timezone=TIMEZONE)
            scheduler.add_job(
                func=run_automation_task,
                trigger=trigger,
                args=[job_id, job["name"]],
                id=f"cron_job_{job_id}",
                replace_existing=True
            )
            
            # Get next run time
            apscheduler_job = scheduler.get_job(f"cron_job_{job_id}")
            if apscheduler_job and apscheduler_job.next_run_time:
                job["next_run"] = apscheduler_job.next_run_time.isoformat()
        except Exception as e:
            logger.error(f"❌ Failed to reschedule job: {e}")
            raise ValueError(f"Invalid cron schedule: {job['schedule']}")
    else:
        job["next_run"] = None
    
    save_jobs(jobs)
    return job


def delete_job(job_id: int):
    """Delete cron job"""
    jobs = get_all_jobs()
    
    # Remove from APScheduler
    try:
        scheduler.remove_job(f"cron_job_{job_id}")
    except:
        pass
    
    # Remove from storage
    jobs = [j for j in jobs if j["id"] != job_id]
    save_jobs(jobs)


def toggle_job(job_id: int) -> Dict:
    """Toggle job active status"""
    job = get_job_by_id(job_id)
    if not job:
        raise ValueError(f"Job with ID {job_id} not found")
    
    new_status = not job["is_active"]
    return update_job(job_id, is_active=new_status)


def trigger_job_manually(job_id: int, override: bool = False) -> Dict:
    """
    Manually trigger a job execution
    
    Args:
        job_id: ID of the job to trigger
        override: If True, cancels next scheduled run
                 If False (default), keeps scheduled run
    
    Returns:
        Dict with status and job info
    """
    job = get_job_by_id(job_id)
    if not job:
        raise ValueError(f"Job with ID {job_id} not found")
    
    # Handle override logic
    override_message = ""
    if override and job["is_active"]:
        # Cancel next scheduled execution temporarily
        apscheduler_job_id = f"cron_job_{job_id}"
        existing_job = scheduler.get_job(apscheduler_job_id)
        
        if existing_job:
            # Remove the scheduled job temporarily
            scheduler.remove_job(apscheduler_job_id)
            override_message = " (next scheduled run cancelled)"
            logger.info(f"⚠️ Override: Cancelled next scheduled run for job {job_id}")
            
            # Re-add the job to scheduler after manual execution completes
            # This will restore normal scheduling after this one-time override
            def restore_schedule():
                """Restore the regular schedule after manual override execution"""
                import time
                time.sleep(10)  # Wait for manual execution to start
                if job["is_active"]:
                    try:
                        scheduler.add_job(
                            func=run_automation_task,
                            args=[job_id, job["name"], "scheduled"],
                            trigger='cron',
                            **parse_cron_schedule(job["schedule"]),
                            id=f"cron_job_{job_id}",
                            replace_existing=True
                        )
                        logger.info(f"✅ Schedule restored for job {job_id} after override")
                    except Exception as e:
                        logger.error(f"Failed to restore schedule for job {job_id}: {e}")
            
            # Schedule the restore in background
            import threading
            threading.Thread(target=restore_schedule, daemon=True).start()
    
    # Run immediately in background
    scheduler.add_job(
        func=run_automation_task,
        args=[job_id, job["name"], "manual_override" if override else "manual"],
        id=f"manual_trigger_{job_id}_{datetime.now().timestamp()}",
    )
    
    # Update last_run
    jobs = get_all_jobs()
    for j in jobs:
        if j["id"] == job_id:
            j["last_run"] = datetime.now().isoformat()
            break
    save_jobs(jobs)
    
    mode = f"with override{override_message}" if override else "without override (schedule maintained)"
    logger.info(f"🚀 Manually triggered job: {job['name']} - {mode}")
    
    return {
        "message": f"Job triggered successfully {mode}",
        "job": job,
        "override": override
    }


def get_next_run_time(job_id: int) -> Optional[str]:
    """Get next scheduled run time for a job"""
    apscheduler_job = scheduler.get_job(f"cron_job_{job_id}")
    if apscheduler_job and apscheduler_job.next_run_time:
        return apscheduler_job.next_run_time.isoformat()
    return None


def initialize_scheduler():
    """Initialize scheduler with stored jobs"""
    logger.info("🔧 Initializing cron scheduler...")
    
    jobs = get_all_jobs()
    active_count = 0
    
    for job in jobs:
        if job["is_active"]:
            try:
                trigger = CronTrigger.from_crontab(job["schedule"])
                scheduler.add_job(
                    func=run_automation_task,
                    trigger=trigger,
                    args=[job["id"], job["name"]],
                    id=f"cron_job_{job['id']}",
                    replace_existing=True
                )
                active_count += 1
                logger.info(f"✅ Loaded job: {job['name']} ({job['schedule']})")
            except Exception as e:
                logger.error(f"❌ Failed to load job {job['id']}: {e}")
    
    logger.info(f"✅ Scheduler initialized with {active_count} active jobs")


# Initialize on module load
initialize_scheduler()
