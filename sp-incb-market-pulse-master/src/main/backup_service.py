#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backup & Restore Service - Data backup, versioning, and rollback functionality

This service manages:
- Automatic backups of output data
- Manual backup creation
- Version history
- Rollback to previous versions
- Activity audit logging
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime
import logging
import os
import shutil
from pathlib import Path
import hashlib

from storage_config import storage

logger = logging.getLogger(__name__)

# Backup directory
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Output file path (the file we're backing up)
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "Color processed.xlsx")


def get_backup_history() -> List[Dict]:
    """Get backup history"""
    try:
        history_data = storage.load("backup_history")
        if history_data is None:
            return []
        return history_data.get("backups", [])
    except FileNotFoundError:
        return []


def save_backup_history(history: List[Dict]):
    """Save backup history"""
    storage.save("backup_history", {"backups": history})


def get_activity_logs() -> List[Dict]:
    """Get activity audit logs"""
    try:
        logs_data = storage.load("activity_logs")
        if logs_data is None:
            return []
        return logs_data.get("logs", [])
    except FileNotFoundError:
        return []


def save_activity_log(log_entry: Dict):
    """Save activity log entry"""
    logs = get_activity_logs()
    logs.insert(0, log_entry)
    
    # Keep only last 500 logs
    logs = logs[:500]
    
    storage.save("activity_logs", {"logs": logs})


def get_next_backup_id() -> int:
    """Get next available backup ID"""
    history = get_backup_history()
    if not history:
        return 1
    return max(backup["id"] for backup in history) + 1


def calculate_file_checksum(file_path: str) -> str:
    """Calculate MD5 checksum of file"""
    if not os.path.exists(file_path):
        return ""
    
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()


def get_file_stats(file_path: str) -> Dict:
    """Get file statistics"""
    if not os.path.exists(file_path):
        return {"exists": False}
    
    stats = os.stat(file_path)
    
    # Try to read Excel and count rows
    try:
        df = pd.read_excel(file_path)
        row_count = len(df)
    except:
        row_count = 0
    
    return {
        "exists": True,
        "size_bytes": stats.st_size,
        "size_mb": round(stats.st_size / (1024 * 1024), 2),
        "modified_time": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "row_count": row_count
    }


def create_backup(
    backup_type: str = "manual",
    description: str = "",
    created_by: str = "system"
) -> Dict:
    """
    Create backup of output file
    
    Args:
        backup_type: "manual", "automatic", or "pre-restore"
        description: Optional description
        created_by: User who created backup
        
    Returns:
        Backup info dict
    """
    backup_id = get_next_backup_id()
    timestamp = datetime.now()
    
    try:
        logger.info(f"🔄 Creating backup (ID: {backup_id}, type: {backup_type})")
        
        # Check if output file exists
        if not os.path.exists(OUTPUT_FILE):
            error_msg = "Output file does not exist"
            logger.error(f"❌ {error_msg}")
            
            backup_entry = {
                "id": backup_id,
                "backup_type": backup_type,
                "created_at": timestamp.isoformat(),
                "created_by": created_by,
                "status": "failed",
                "error": error_msg,
                "description": description
            }
            
            history = get_backup_history()
            history.insert(0, backup_entry)
            save_backup_history(history)
            
            return backup_entry
        
        # Get file stats before backup
        file_stats = get_file_stats(OUTPUT_FILE)
        checksum = calculate_file_checksum(OUTPUT_FILE)
        
        # Create backup filename
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{backup_id}_{timestamp_str}.xlsx"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Copy file
        shutil.copy2(OUTPUT_FILE, backup_path)
        logger.info(f"📁 Backup saved: {backup_filename}")
        
        # Create backup entry
        backup_entry = {
            "id": backup_id,
            "backup_type": backup_type,
            "filename": backup_filename,
            "file_path": backup_path,
            "created_at": timestamp.isoformat(),
            "created_by": created_by,
            "status": "success",
            "description": description,
            "file_size_bytes": file_stats["size_bytes"],
            "file_size_mb": file_stats["size_mb"],
            "row_count": file_stats["row_count"],
            "checksum": checksum
        }
        
        # Save to history
        history = get_backup_history()
        history.insert(0, backup_entry)
        save_backup_history(history)
        
        # Log activity
        log_activity(
            action="backup_created",
            details=f"Backup {backup_id} created ({backup_type})",
            user=created_by,
            metadata={
                "backup_id": backup_id,
                "backup_type": backup_type,
                "row_count": file_stats["row_count"]
            }
        )
        
        logger.info(f"✅ Backup created successfully (ID: {backup_id})")
        return backup_entry
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Backup failed: {error_msg}")
        
        backup_entry = {
            "id": backup_id,
            "backup_type": backup_type,
            "created_at": timestamp.isoformat(),
            "created_by": created_by,
            "status": "failed",
            "error": error_msg,
            "description": description
        }
        
        history = get_backup_history()
        history.insert(0, backup_entry)
        save_backup_history(history)
        
        return backup_entry


def restore_from_backup(backup_id: int, restored_by: str = "admin") -> Dict:
    """
    Restore output file from backup
    
    Steps:
    1. Find backup by ID
    2. Create pre-restore backup of current file
    3. Replace current file with backup
    4. Verify restoration
    """
    timestamp = datetime.now()
    
    try:
        logger.info(f"🔄 Starting restore from backup {backup_id}")
        
        # Find backup
        history = get_backup_history()
        backup = None
        for b in history:
            if b["id"] == backup_id:
                backup = b
                break
        
        if not backup:
            raise ValueError(f"Backup with ID {backup_id} not found")
        
        if backup["status"] != "success":
            raise ValueError(f"Cannot restore from failed backup")
        
        backup_path = backup["file_path"]
        
        if not os.path.exists(backup_path):
            raise ValueError(f"Backup file not found: {backup_path}")
        
        # Step 1: Create pre-restore backup of current file
        logger.info("📦 Creating pre-restore backup...")
        pre_restore_backup = create_backup(
            backup_type="pre-restore",
            description=f"Auto backup before restore from backup {backup_id}",
            created_by=restored_by
        )
        
        if pre_restore_backup["status"] != "success":
            raise ValueError("Failed to create pre-restore backup")
        
        # Step 2: Replace current file with backup
        logger.info(f"🔄 Restoring from backup {backup_id}...")
        shutil.copy2(backup_path, OUTPUT_FILE)
        
        # Step 3: Verify
        restored_checksum = calculate_file_checksum(OUTPUT_FILE)
        if restored_checksum != backup["checksum"]:
            logger.warning("⚠️ Checksum mismatch after restore")
        
        restored_stats = get_file_stats(OUTPUT_FILE)
        
        # Log activity
        log_activity(
            action="restore_completed",
            details=f"Restored from backup {backup_id}",
            user=restored_by,
            metadata={
                "backup_id": backup_id,
                "pre_restore_backup_id": pre_restore_backup["id"],
                "row_count": restored_stats["row_count"]
            }
        )
        
        logger.info(f"✅ Restore completed successfully")
        
        return {
            "success": True,
            "backup_id": backup_id,
            "pre_restore_backup_id": pre_restore_backup["id"],
            "restored_at": timestamp.isoformat(),
            "restored_by": restored_by,
            "row_count": restored_stats["row_count"],
            "file_size_mb": restored_stats["size_mb"]
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Restore failed: {error_msg}")
        
        # Log failed restore
        log_activity(
            action="restore_failed",
            details=f"Failed to restore from backup {backup_id}: {error_msg}",
            user=restored_by,
            metadata={"backup_id": backup_id, "error": error_msg}
        )
        
        return {
            "success": False,
            "backup_id": backup_id,
            "error": error_msg
        }


def delete_backup(backup_id: int, deleted_by: str = "admin") -> bool:
    """Delete backup file and history entry"""
    history = get_backup_history()
    
    # Find backup
    backup = None
    for b in history:
        if b["id"] == backup_id:
            backup = b
            break
    
    if not backup:
        return False
    
    # Delete file if exists
    if "file_path" in backup and os.path.exists(backup["file_path"]):
        try:
            os.remove(backup["file_path"])
            logger.info(f"🗑️ Deleted backup file: {backup['file_path']}")
        except Exception as e:
            logger.warning(f"Failed to delete backup file: {e}")
    
    # Remove from history
    history = [b for b in history if b["id"] != backup_id]
    save_backup_history(history)
    
    # Log activity
    log_activity(
        action="backup_deleted",
        details=f"Backup {backup_id} deleted",
        user=deleted_by,
        metadata={"backup_id": backup_id}
    )
    
    return True


def get_backup_by_id(backup_id: int) -> Optional[Dict]:
    """Get single backup by ID"""
    history = get_backup_history()
    for backup in history:
        if backup["id"] == backup_id:
            return backup
    return None


def log_activity(action: str, details: str, user: str = "system", metadata: Optional[Dict] = None):
    """
    Log activity for audit trail
    
    Args:
        action: Action type (e.g., "backup_created", "restore_completed")
        details: Human-readable description
        user: User who performed action
        metadata: Additional data
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
        "user": user,
        "metadata": metadata or {}
    }
    
    save_activity_log(log_entry)
    logger.info(f"📝 Activity logged: {action} by {user}")


def get_system_stats() -> Dict:
    """Get overall system statistics"""
    history = get_backup_history()
    activity_logs = get_activity_logs()
    
    successful_backups = [b for b in history if b["status"] == "success"]
    failed_backups = [b for b in history if b["status"] == "failed"]
    
    # Output file stats
    output_stats = get_file_stats(OUTPUT_FILE)
    
    # Backup storage usage
    total_backup_size = sum(b.get("file_size_bytes", 0) for b in successful_backups)
    
    return {
        "output_file": {
            "exists": output_stats.get("exists", False),
            "path": OUTPUT_FILE,
            "size_mb": output_stats.get("size_mb", 0),
            "row_count": output_stats.get("row_count", 0),
            "last_modified": output_stats.get("modified_time", None)
        },
        "backups": {
            "total_count": len(history),
            "successful_count": len(successful_backups),
            "failed_count": len(failed_backups),
            "total_size_mb": round(total_backup_size / (1024 * 1024), 2)
        },
        "activity": {
            "total_logs": len(activity_logs),
            "recent_actions": [log["action"] for log in activity_logs[:10]]
        }
    }


def cleanup_old_backups(keep_count: int = 10) -> Dict:
    """
    Clean up old backups, keeping only the most recent ones
    
    Args:
        keep_count: Number of backups to keep
        
    Returns:
        Cleanup statistics
    """
    history = get_backup_history()
    successful_backups = [b for b in history if b["status"] == "success"]
    
    if len(successful_backups) <= keep_count:
        return {
            "deleted_count": 0,
            "kept_count": len(successful_backups),
            "message": f"No cleanup needed, only {len(successful_backups)} backups exist"
        }
    
    # Sort by creation time (most recent first)
    successful_backups.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Keep recent ones, delete old ones
    to_keep = successful_backups[:keep_count]
    to_delete = successful_backups[keep_count:]
    
    deleted_count = 0
    for backup in to_delete:
        if delete_backup(backup["id"], deleted_by="system"):
            deleted_count += 1
    
    log_activity(
        action="backups_cleaned",
        details=f"Cleaned up {deleted_count} old backups, kept {len(to_keep)}",
        user="system",
        metadata={"deleted_count": deleted_count, "kept_count": len(to_keep)}
    )
    
    return {
        "deleted_count": deleted_count,
        "kept_count": len(to_keep),
        "message": f"Cleaned up {deleted_count} old backups"
    }
