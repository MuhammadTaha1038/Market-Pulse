"""
Unified Logging Service
Standardized logging across all modules with revert functionality
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
UNIFIED_LOGS_FILE = os.path.join(DATA_DIR, 'unified_logs.json')


class LogEntry:
    """Standard log entry structure"""
    def __init__(
        self,
        log_id: int,
        module: str,  # 'rules', 'cron', 'restore', 'email'
        action: str,  # 'create', 'update', 'delete', 'toggle', 'restore', 'send', etc.
        description: str,
        performed_by: str,
        performed_at: str,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        can_revert: bool = False,
        revert_data: Optional[Dict] = None,  # Snapshot of data before change
        reverted_at: Optional[str] = None,
        reverted_by: Optional[str] = None,
        metadata: Optional[Dict] = None  # Additional module-specific data
    ):
        self.log_id = log_id
        self.module = module
        self.action = action
        self.description = description
        self.performed_by = performed_by
        self.performed_at = performed_at
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.can_revert = can_revert
        self.revert_data = revert_data or {}
        self.reverted_at = reverted_at
        self.reverted_by = reverted_by
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "log_id": self.log_id,
            "module": self.module,
            "action": self.action,
            "description": self.description,
            "performed_by": self.performed_by,
            "performed_at": self.performed_at,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "can_revert": self.can_revert,
            "revert_data": self.revert_data,
            "reverted_at": self.reverted_at,
            "reverted_by": self.reverted_by,
            "metadata": self.metadata
        }


def load_unified_logs() -> Dict:
    """Load all unified logs"""
    if not os.path.exists(UNIFIED_LOGS_FILE):
        return {"logs": [], "next_id": 1}
    
    try:
        with open(UNIFIED_LOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading unified logs: {e}")
        return {"logs": [], "next_id": 1}


def save_unified_logs(logs_data: Dict):
    """Save unified logs"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(UNIFIED_LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs_data, f, indent=2)


def add_log(
    module: str,
    action: str,
    description: str,
    performed_by: str = "admin",
    entity_id: Optional[int] = None,
    entity_name: Optional[str] = None,
    can_revert: bool = False,
    revert_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Add a log entry
    
    Args:
        module: Module name ('rules', 'cron', 'restore', 'email')
        action: Action performed ('create', 'update', 'delete', 'toggle', etc.)
        description: Human-readable description
        performed_by: User who performed the action
        entity_id: ID of the entity (rule_id, cron_id, etc.)
        entity_name: Name of the entity
        can_revert: Whether this action can be reverted
        revert_data: Data snapshot for reverting (full entity before change)
        metadata: Additional module-specific data
    
    Returns:
        Created log entry
    """
    logs_data = load_unified_logs()
    
    log_entry = LogEntry(
        log_id=logs_data['next_id'],
        module=module,
        action=action,
        description=description,
        performed_by=performed_by,
        performed_at=datetime.now().isoformat(),
        entity_id=entity_id,
        entity_name=entity_name,
        can_revert=can_revert,
        revert_data=revert_data,
        metadata=metadata
    )
    
    logs_data['logs'].insert(0, log_entry.to_dict())  # Most recent first
    logs_data['next_id'] += 1
    
    # Keep only last 500 logs (to prevent file from growing too large)
    logs_data['logs'] = logs_data['logs'][:500]
    
    save_unified_logs(logs_data)
    
    logger.info(f"📝 Log added: [{module}] {action} - {description}")
    
    return log_entry.to_dict()


def get_logs(
    module: Optional[str] = None,
    limit: int = 4,
    entity_id: Optional[int] = None
) -> List[Dict]:
    """
    Get log entries
    
    Args:
        module: Filter by module (None = all modules)
        limit: Number of logs to return (default 4 for "last 4 changes")
        entity_id: Filter by specific entity ID
    
    Returns:
        List of log entries (most recent first)
    """
    logs_data = load_unified_logs()
    logs = logs_data.get('logs', [])
    
    # Filter by module
    if module:
        logs = [log for log in logs if log.get('module') == module]
    
    # Filter by entity_id
    if entity_id is not None:
        logs = [log for log in logs if log.get('entity_id') == entity_id]
    
    # Return limited results
    return logs[:limit]


def get_log_by_id(log_id: int) -> Optional[Dict]:
    """Get single log entry by ID"""
    logs_data = load_unified_logs()
    logs = logs_data.get('logs', [])
    
    for log in logs:
        if log.get('log_id') == log_id:
            return log
    
    return None


def revert_log(log_id: int, reverted_by: str = "admin") -> Dict:
    """
    Revert a log entry (restore previous state)
    
    Args:
        log_id: ID of the log to revert
        reverted_by: User performing the revert
    
    Returns:
        Result with success status and restored data
    """
    logs_data = load_unified_logs()
    logs = logs_data.get('logs', [])
    
    # Find the log entry
    log_entry = None
    for log in logs:
        if log.get('log_id') == log_id:
            log_entry = log
            break
    
    if not log_entry:
        raise ValueError(f"Log entry {log_id} not found")
    
    if not log_entry.get('can_revert', False):
        raise ValueError(f"Log entry {log_id} cannot be reverted")
    
    if log_entry.get('reverted_at'):
        raise ValueError(f"Log entry {log_id} has already been reverted")
    
    # Get revert data
    revert_data = log_entry.get('revert_data', {})
    if not revert_data:
        raise ValueError(f"No revert data available for log {log_id}")
    
    # Mark as reverted
    log_entry['reverted_at'] = datetime.now().isoformat()
    log_entry['reverted_by'] = reverted_by
    
    save_unified_logs(logs_data)
    
    # Create a new log entry for the revert action
    add_log(
        module=log_entry['module'],
        action='revert',
        description=f"Reverted: {log_entry['description']}",
        performed_by=reverted_by,
        entity_id=log_entry.get('entity_id'),
        entity_name=log_entry.get('entity_name'),
        can_revert=False,
        metadata={
            'original_log_id': log_id,
            'original_action': log_entry['action']
        }
    )
    
    logger.info(f"↩️ Reverted log {log_id}: {log_entry['description']}")
    
    return {
        "success": True,
        "message": f"Successfully reverted: {log_entry['description']}",
        "revert_data": revert_data,
        "log_entry": log_entry
    }


def get_module_stats() -> Dict:
    """
    Get statistics about logs per module
    
    Returns:
        Dict with counts per module
    """
    logs_data = load_unified_logs()
    logs = logs_data.get('logs', [])
    
    stats = {}
    for log in logs:
        module = log.get('module', 'unknown')
        stats[module] = stats.get(module, 0) + 1
    
    return {
        "total_logs": len(logs),
        "by_module": stats,
        "revertable_count": len([log for log in logs if log.get('can_revert', False)])
    }


def cleanup_old_logs(days: int = 90):
    """
    Remove logs older than specified days
    
    Args:
        days: Number of days to keep (default 90)
    """
    from datetime import timedelta
    
    logs_data = load_unified_logs()
    logs = logs_data.get('logs', [])
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Keep only logs within date range
    filtered_logs = []
    for log in logs:
        try:
            log_date = datetime.fromisoformat(log.get('performed_at', ''))
            if log_date >= cutoff_date:
                filtered_logs.append(log)
        except:
            # Keep logs with invalid dates (safety)
            filtered_logs.append(log)
    
    removed_count = len(logs) - len(filtered_logs)
    
    if removed_count > 0:
        logs_data['logs'] = filtered_logs
        save_unified_logs(logs_data)
        logger.info(f"🧹 Cleaned up {removed_count} old log entries (>{days} days)")
    
    return removed_count
