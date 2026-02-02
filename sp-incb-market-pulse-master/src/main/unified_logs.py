"""
Unified Logs API Endpoints
Standardized logging across all modules with revert functionality
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging_service
import revert_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["Unified Logs"])


class LogResponse(BaseModel):
    """Log entry response"""
    log_id: int
    module: str
    action: str
    description: str
    performed_by: str
    performed_at: str
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    can_revert: bool = False
    reverted_at: Optional[str] = None
    reverted_by: Optional[str] = None
    metadata: Optional[Dict] = None


class RevertRequest(BaseModel):
    """Revert log request"""
    reverted_by: str = "admin"


@router.get("", response_model=Dict)
async def get_all_logs(
    module: Optional[str] = Query(None, description="Filter by module (rules, cron, restore, email)"),
    limit: int = Query(4, description="Number of logs to return (default: 4 for last 4 changes)")
):
    """
    Get unified logs across all modules
    
    Query Parameters:
        - module: Optional module filter (rules, cron, restore, email)
        - limit: Number of logs to return (default: 4)
    
    Returns:
        {
            "logs": [...],
            "count": 4,
            "module": "rules" (if filtered)
        }
    """
    try:
        logs = logging_service.get_logs(module=module, limit=limit)
        
        return {
            "logs": logs,
            "count": len(logs),
            "module": module,
            "showing": f"last {limit} changes" + (f" for {module}" if module else "")
        }
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=Dict)
async def get_rules_logs(limit: int = Query(4, description="Number of logs")):
    """
    Get last 4 changes for rules module
    
    Returns recent rule operations (create, update, delete, toggle)
    """
    try:
        logs = logging_service.get_logs(module='rules', limit=limit)
        return {
            "logs": logs,
            "count": len(logs),
            "module": "rules"
        }
    except Exception as e:
        logger.error(f"Error fetching rules logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/restore", response_model=Dict)
async def get_restore_logs(limit: int = Query(4, description="Number of logs")):
    """
    Get last 4 changes for restore/email module
    
    Returns recent backup/restore operations
    """
    try:
        logs = logging_service.get_logs(module='restore', limit=limit)
        return {
            "logs": logs,
            "count": len(logs),
            "module": "restore"
        }
    except Exception as e:
        logger.error(f"Error fetching restore logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cron", response_model=Dict)
async def get_cron_logs(limit: int = Query(4, description="Number of logs")):
    """
    Get last 4 changes for cron module
    
    Returns recent cron job operations (create, update, delete, toggle)
    Note: Cron execution logs are separate from operation logs
    """
    try:
        logs = logging_service.get_logs(module='cron', limit=limit)
        return {
            "logs": logs,
            "count": len(logs),
            "module": "cron"
        }
    except Exception as e:
        logger.error(f"Error fetching cron logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict)
async def get_log_stats():
    """
    Get logging statistics
    
    Returns:
        {
            "total_logs": 45,
            "by_module": {"rules": 20, "cron": 15, "restore": 10},
            "revertable_count": 30
        }
    """
    try:
        stats = logging_service.get_module_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching log stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{log_id}/revert", response_model=Dict)
async def revert_log_entry(log_id: int, request: RevertRequest):
    """
    Revert a log entry (undo the action)
    
    Applies revert logic based on the module:
    - Rules: Restore deleted rules, undo updates
    - Restore: Revert data restore operations
    - Cron: Not revertable (read-only logs)
    
    Args:
        log_id: ID of the log entry to revert
        request: Revert request with user info
    
    Returns:
        {
            "success": true,
            "message": "Successfully reverted...",
            "log_entry": {...}
        }
    """
    try:
        result = revert_service.apply_revert(log_id, reverted_by=request.reverted_by)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Error reverting log {log_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{log_id}", response_model=Dict)
async def get_log_by_id(log_id: int):
    """
    Get single log entry by ID
    
    Args:
        log_id: ID of the log entry
    
    Returns:
        Log entry details
    """
    try:
        log = logging_service.get_log_by_id(log_id)
        
        if not log:
            raise HTTPException(status_code=404, detail=f"Log entry {log_id} not found")
        
        return log
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching log {log_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup", response_model=Dict)
async def cleanup_old_logs(days: int = Query(90, description="Remove logs older than this many days")):
    """
    Cleanup old log entries
    
    Removes logs older than specified days (default: 90)
    
    Args:
        days: Number of days to keep
    
    Returns:
        {
            "removed_count": 50,
            "message": "Cleaned up 50 old log entries"
        }
    """
    try:
        removed_count = logging_service.cleanup_old_logs(days)
        
        return {
            "removed_count": removed_count,
            "message": f"Cleaned up {removed_count} old log entries (>{days} days)"
        }
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
