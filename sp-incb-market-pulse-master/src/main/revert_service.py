"""
Revert Service - Handle log reversions
Applies revert operations for rules, presets, backup/restore
"""

import logging_service
import rules_service
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def revert_rules_operation(revert_data: Dict, entity_id: int) -> Dict:
    """
    Revert a rules operation
    
    Args:
        revert_data: Revert instructions
        entity_id: ID of the affected entity
    
    Returns:
        Result of revert operation
    """
    action = revert_data.get('action')
    
    if action == 'delete':
        # Original action was CREATE → revert by deleting
        rules_service.delete_rule(revert_data['rule_id'])
        return {"message": f"Reverted: Deleted rule ID {revert_data['rule_id']}"}
    
    elif action == 'restore':
        # Original action was DELETE or UPDATE → revert by restoring
        rule_data = revert_data.get('rule_data', {})
        rule_id = rule_data.get('id', entity_id)
        
        # Check if rule exists (UPDATE case) or needs recreation (DELETE case)
        existing_rule = next((r for r in rules_service.load_rules() if r['id'] == rule_id), None)
        
        if existing_rule:
            # UPDATE case: restore previous state
            rules_service.update_rule(
                rule_id,
                name=rule_data['name'],
                conditions=rule_data['conditions'],
                is_active=rule_data['is_active']
            )
            return {"message": f"Reverted: Restored rule {rule_data['name']} to previous state"}
        else:
            # DELETE case: recreate the rule
            rules = rules_service.load_rules()
            rules.append(rule_data)
            rules_service.save_rules(rules)
            return {"message": f"Reverted: Restored deleted rule {rule_data['name']}"}
    
    else:
        raise ValueError(f"Unknown revert action: {action}")


def revert_backup_operation(revert_data: Dict, entity_id: int) -> Dict:
    """
    Revert a backup/restore operation
    
    Args:
        revert_data: Revert instructions
        entity_id: ID of the affected entity
    
    Returns:
        Result of revert operation
    """
    # This will be implemented when backup service is updated
    action = revert_data.get('action')
    
    if action == 'restore':
        import backup_restore
        snapshot_id = revert_data.get('snapshot_id')
        return backup_restore.restore_snapshot(snapshot_id)
    
    raise ValueError(f"Unknown backup revert action: {action}")



def apply_revert(log_id: int, reverted_by: str = "admin") -> Dict:
    """
    Apply a revert operation from a log entry
    
    Args:
        log_id: ID of the log to revert
        reverted_by: User performing the revert
    
    Returns:
        Result of the revert operation
    """
    # Get the log entry and mark as reverted
    result = logging_service.revert_log(log_id, reverted_by)
    
    log_entry = result['log_entry']
    revert_data = log_entry.get('revert_data', {})
    module = log_entry.get('module')
    entity_id = log_entry.get('entity_id')
    
    # Apply module-specific revert logic
    if module == 'rules':
        operation_result = revert_rules_operation(revert_data, entity_id)
    elif module == 'backup' or module == 'restore':
        operation_result = revert_backup_operation(revert_data, entity_id)
    else:
        raise ValueError(f"Revert not supported for module: {module}")
    
    logger.info(f"↩️ Revert applied for log {log_id}: {operation_result.get('message')}")
    
    return {
        "success": True,
        "message": operation_result.get('message'),
        "log_entry": log_entry
    }
