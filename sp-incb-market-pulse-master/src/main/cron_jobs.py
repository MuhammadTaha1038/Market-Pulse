#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cron Jobs Router - APIs for managing scheduled automation jobs
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging
import sys
import os

# Import cron service
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from cron_service import (
    get_all_jobs,
    get_job_by_id,
    create_job,
    update_job,
    delete_job,
    toggle_job,
    trigger_job_manually,
    get_execution_logs,
    get_next_run_time
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cron", tags=["Cron Jobs"])


# Request/Response Models
class CronJobCreate(BaseModel):
    name: str = Field(..., description="Job name/description")
    schedule: str = Field(..., description="Cron expression (e.g., '0 9 * * *' for 9 AM daily)")
    is_active: bool = Field(True, description="Whether job is active")


class CronJobUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Job name/description")
    schedule: Optional[str] = Field(None, description="Cron expression")
    is_active: Optional[bool] = Field(None, description="Whether job is active")


class CronJobResponse(BaseModel):
    id: int
    name: str
    schedule: str
    is_active: bool
    created_at: str
    updated_at: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None


class CronJobsListResponse(BaseModel):
    jobs: List[CronJobResponse]
    count: int


class ExecutionLogResponse(BaseModel):
    id: Optional[int] = None  # Optional for backward compatibility with old logs
    job_id: int
    job_name: str
    triggered_by: str
    start_time: str
    end_time: Optional[str] = None
    status: str
    duration_seconds: Optional[float] = None
    original_count: Optional[int] = None
    excluded_count: Optional[int] = None
    processed_count: Optional[int] = None
    rules_applied: Optional[int] = None
    error: Optional[str] = None


class ExecutionLogsResponse(BaseModel):
    logs: List[ExecutionLogResponse]
    count: int


class CronScheduleExamples(BaseModel):
    examples: List[dict]


# API Endpoints

@router.get("/jobs", response_model=CronJobsListResponse)
async def list_jobs():
    """
    Get all cron jobs
    
    Returns list of all scheduled automation jobs with their status
    """
    try:
        jobs = get_all_jobs()
        
        # Update next_run times from scheduler
        for job in jobs:
            if job["is_active"]:
                next_run = get_next_run_time(job["id"])
                if next_run:
                    job["next_run"] = next_run
        
        return CronJobsListResponse(
            jobs=[CronJobResponse(**job) for job in jobs],
            count=len(jobs)
        )
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/active", response_model=CronJobsListResponse)
async def list_active_jobs():
    """Get only active cron jobs"""
    try:
        jobs = get_all_jobs()
        active_jobs = [j for j in jobs if j["is_active"]]
        
        # Update next_run times
        for job in active_jobs:
            next_run = get_next_run_time(job["id"])
            if next_run:
                job["next_run"] = next_run
        
        return CronJobsListResponse(
            jobs=[CronJobResponse(**job) for job in active_jobs],
            count=len(active_jobs)
        )
    except Exception as e:
        logger.error(f"Error listing active jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=CronJobResponse)
async def get_job(job_id: int):
    """Get single cron job by ID"""
    try:
        job = get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        
        # Update next_run time
        if job["is_active"]:
            next_run = get_next_run_time(job_id)
            if next_run:
                job["next_run"] = next_run
        
        return CronJobResponse(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=dict)
async def create_cron_job(job_data: CronJobCreate):
    """
    Create new cron job
    
    Examples of cron schedules:
    - "0 9 * * *" - Every day at 9 AM
    - "0 */6 * * *" - Every 6 hours
    - "0 9 * * 1-5" - Weekdays at 9 AM
    - "0 0 * * 0" - Every Sunday at midnight
    """
    try:
        job = create_job(
            name=job_data.name,
            schedule=job_data.schedule,
            is_active=job_data.is_active
        )
        
        return {
            "message": "Cron job created successfully",
            "job": CronJobResponse(**job)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/jobs/{job_id}", response_model=dict)
async def update_cron_job(job_id: int, job_data: CronJobUpdate):
    """Update existing cron job"""
    try:
        job = update_job(
            job_id=job_id,
            name=job_data.name,
            schedule=job_data.schedule,
            is_active=job_data.is_active
        )
        
        return {
            "message": "Cron job updated successfully",
            "job": CronJobResponse(**job)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}", response_model=dict)
async def delete_cron_job(job_id: int):
    """Delete cron job"""
    try:
        job = get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        
        delete_job(job_id)
        
        return {
            "message": "Cron job deleted successfully",
            "job_id": job_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/toggle", response_model=dict)
async def toggle_cron_job(job_id: int):
    """Toggle job active/inactive status"""
    try:
        job = toggle_job(job_id)
        
        status = "activated" if job["is_active"] else "deactivated"
        
        return {
            "message": f"Cron job {status} successfully",
            "job": CronJobResponse(**job)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/trigger", response_model=dict)
async def trigger_job(job_id: int, override: bool = False):
    """
    Manually trigger a cron job execution
    
    Args:
        job_id: ID of the job to trigger
        override: If True, cancels next scheduled run and runs immediately
                 If False (default), runs now and keeps scheduled run
    
    Behavior:
        - override=True: Cancel next scheduled execution, run immediately only
        - override=False: Run immediately, next scheduled execution remains
    """
    try:
        result = trigger_job_manually(job_id, override=override)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error triggering job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=ExecutionLogsResponse)
async def get_logs(limit: int = 50):
    """
    Get execution logs
    
    Returns history of job executions with status, duration, and stats
    """
    try:
        logs = get_execution_logs()
        
        # Limit results
        logs = logs[:limit]
        
        return ExecutionLogsResponse(
            logs=[ExecutionLogResponse(**log) for log in logs],
            count=len(logs)
        )
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{job_id}", response_model=ExecutionLogsResponse)
async def get_job_logs(job_id: int, limit: int = 20):
    """Get execution logs for specific job"""
    try:
        all_logs = get_execution_logs()
        job_logs = [log for log in all_logs if log["job_id"] == job_id]
        
        # Limit results
        job_logs = job_logs[:limit]
        
        return ExecutionLogsResponse(
            logs=[ExecutionLogResponse(**log) for log in job_logs],
            count=len(job_logs)
        )
    except Exception as e:
        logger.error(f"Error fetching logs for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule-examples", response_model=CronScheduleExamples)
async def get_schedule_examples():
    """
    Get common cron schedule examples
    
    Helpful for frontend to show schedule presets
    """
    examples = [
        {
            "expression": "0 9 * * *",
            "description": "Every day at 9:00 AM",
            "frequency": "Daily"
        },
        {
            "expression": "0 9 * * 1-5",
            "description": "Weekdays (Mon-Fri) at 9:00 AM",
            "frequency": "Weekdays"
        },
        {
            "expression": "0 */6 * * *",
            "description": "Every 6 hours",
            "frequency": "Every 6 hours"
        },
        {
            "expression": "0 */4 * * *",
            "description": "Every 4 hours",
            "frequency": "Every 4 hours"
        },
        {
            "expression": "0 0,12 * * *",
            "description": "Twice daily (midnight and noon)",
            "frequency": "Twice daily"
        },
        {
            "expression": "0 0 * * 0",
            "description": "Every Sunday at midnight",
            "frequency": "Weekly"
        },
        {
            "expression": "0 0 1 * *",
            "description": "First day of every month at midnight",
            "frequency": "Monthly"
        },
        {
            "expression": "*/30 * * * *",
            "description": "Every 30 minutes",
            "frequency": "Every 30 minutes"
        },
        {
            "expression": "0 8-17 * * 1-5",
            "description": "Every hour from 8 AM to 5 PM on weekdays",
            "frequency": "Business hours"
        },
        {
            "expression": "0 10,14,16 * * *",
            "description": "Three times daily (10 AM, 2 PM, 4 PM)",
            "frequency": "Custom"
        }
    ]
    
    return CronScheduleExamples(examples=examples)
