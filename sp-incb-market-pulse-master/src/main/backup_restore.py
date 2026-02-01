#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backup & Restore Router - APIs for data backup, restore, and audit logging
"""
from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
import logging
import sys
import os

# Import backup service
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backup_service import (
    create_backup,
    restore_from_backup,
    delete_backup,
    get_backup_history,
    get_backup_by_id,
    get_activity_logs,
    get_system_stats,
    cleanup_old_backups,
    log_activity
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["Backup & Restore"])


# Response Models
class BackupItem(BaseModel):
    id: int
    backup_type: str
    filename: Optional[str] = None
    created_at: str
    created_by: str
    status: str
    description: Optional[str] = None
    file_size_mb: Optional[float] = None
    row_count: Optional[int] = None
    checksum: Optional[str] = None
    error: Optional[str] = None


class BackupHistoryResponse(BaseModel):
    backups: List[BackupItem]
    count: int


class ActivityLogItem(BaseModel):
    timestamp: str
    action: str
    details: str
    user: str
    metadata: dict


class ActivityLogsResponse(BaseModel):
    logs: List[ActivityLogItem]
    count: int


class SystemStatsResponse(BaseModel):
    output_file: dict
    backups: dict
    activity: dict


# API Endpoints

@router.post("/create", response_model=dict)
async def create_manual_backup(
    description: str = Form("Manual backup"),
    created_by: str = Form("admin")
):
    """
    Create manual backup of output file
    
    Creates a snapshot of the current processed colors file
    """
    try:
        logger.info(f"📦 Creating manual backup by {created_by}")
        
        backup = create_backup(
            backup_type="manual",
            description=description,
            created_by=created_by
        )
        
        return {
            "message": "Backup created successfully" if backup["status"] == "success" else "Backup failed",
            "backup": BackupItem(**backup)
        }
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=BackupHistoryResponse)
async def get_history(limit: int = 50):
    """
    Get backup history
    
    Returns list of all backups with their status and statistics
    """
    try:
        history = get_backup_history()
        
        # Limit results
        history = history[:limit]
        
        return BackupHistoryResponse(
            backups=[BackupItem(**backup) for backup in history],
            count=len(history)
        )
    except Exception as e:
        logger.error(f"Error fetching backup history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{backup_id}", response_model=BackupItem)
async def get_backup_details(backup_id: int):
    """Get details of a specific backup"""
    try:
        backup = get_backup_by_id(backup_id)
        
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"Backup with ID {backup_id} not found"
            )
        
        return BackupItem(**backup)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{backup_id}", response_model=dict)
async def restore_backup(
    backup_id: int,
    restored_by: str = Form("admin")
):
    """
    Restore output file from backup
    
    WARNING: This will replace the current output file with the backup.
    A pre-restore backup of the current file will be created automatically.
    """
    try:
        logger.warning(f"⚠️ Restore requested for backup {backup_id} by {restored_by}")
        
        result = restore_from_backup(backup_id, restored_by)
        
        if result["success"]:
            return {
                "message": "Restore completed successfully",
                "result": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Restore failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{backup_id}", response_model=dict)
async def delete_backup_item(
    backup_id: int,
    deleted_by: str = "admin"
):
    """
    Delete backup file and history entry
    
    This permanently removes the backup file from storage
    """
    try:
        backup = get_backup_by_id(backup_id)
        
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"Backup with ID {backup_id} not found"
            )
        
        success = delete_backup(backup_id, deleted_by)
        
        if success:
            return {
                "message": "Backup deleted successfully",
                "backup_id": backup_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete backup")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs", response_model=ActivityLogsResponse)
async def get_activity(limit: int = 100):
    """
    Get activity audit logs
    
    Returns history of all backup/restore activities with timestamps and users
    """
    try:
        logs = get_activity_logs()
        
        # Limit results
        logs = logs[:limit]
        
        return ActivityLogsResponse(
            logs=[ActivityLogItem(**log) for log in logs],
            count=len(logs)
        )
    except Exception as e:
        logger.error(f"Error fetching activity logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=SystemStatsResponse)
async def get_stats():
    """
    Get system statistics
    
    Returns overall stats about output file, backups, and activity
    """
    try:
        stats = get_system_stats()
        return SystemStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup", response_model=dict)
async def cleanup_backups(keep_count: int = 10):
    """
    Clean up old backups
    
    Keeps only the most recent backups, deletes older ones to save storage space
    
    Args:
        keep_count: Number of recent backups to keep (default: 10)
    """
    try:
        if keep_count < 1:
            raise HTTPException(status_code=400, detail="keep_count must be at least 1")
        
        logger.info(f"🧹 Cleaning up backups, keeping {keep_count} most recent")
        
        result = cleanup_old_backups(keep_count)
        
        return {
            "message": result["message"],
            "deleted_count": result["deleted_count"],
            "kept_count": result["kept_count"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-activity", response_model=dict)
async def log_custom_activity(
    action: str = Form(...),
    details: str = Form(...),
    user: str = Form("admin")
):
    """
    Log custom activity (for manual audit trail entries)
    
    Useful for logging important administrative actions
    """
    try:
        log_activity(action, details, user)
        
        return {
            "message": "Activity logged successfully",
            "action": action,
            "user": user
        }
        
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{backup_id}", response_model=dict)
async def verify_backup(backup_id: int):
    """
    Verify backup file integrity
    
    Checks if backup file exists and validates checksum
    """
    try:
        backup = get_backup_by_id(backup_id)
        
        if not backup:
            raise HTTPException(
                status_code=404,
                detail=f"Backup with ID {backup_id} not found"
            )
        
        if backup["status"] != "success":
            return {
                "backup_id": backup_id,
                "valid": False,
                "error": "Backup creation failed originally"
            }
        
        file_path = backup.get("file_path")
        
        if not file_path:
            return {
                "backup_id": backup_id,
                "valid": False,
                "error": "Backup file path not found"
            }
        
        import os
        from backup_service import calculate_file_checksum
        
        if not os.path.exists(file_path):
            return {
                "backup_id": backup_id,
                "valid": False,
                "error": "Backup file does not exist"
            }
        
        current_checksum = calculate_file_checksum(file_path)
        original_checksum = backup.get("checksum", "")
        
        if current_checksum == original_checksum:
            return {
                "backup_id": backup_id,
                "valid": True,
                "message": "Backup file is valid and intact",
                "checksum": current_checksum
            }
        else:
            return {
                "backup_id": backup_id,
                "valid": False,
                "error": "Checksum mismatch - file may be corrupted",
                "current_checksum": current_checksum,
                "original_checksum": original_checksum
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
