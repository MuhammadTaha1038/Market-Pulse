"""
Rules Engine - Core Business Logic
Works with ANY storage backend (JSON, S3, or Oracle)
"""

from typing import List, Dict, Optional
from datetime import datetime
from storage_config import storage
import logging
import logging_service

logger = logging.getLogger(__name__)

RULES_KEY = "rules"
RULE_LOGS_KEY = "rule_logs"


def _ensure_rules_exist():
    """Initialize rules storage if doesn't exist"""
    if not storage.exists(RULES_KEY):
        storage.save(RULES_KEY, {"rules": []})
        logger.info("✅ Rules storage initialized")


def _ensure_logs_exist():
    """Initialize rule logs storage if doesn't exist"""
    if not storage.exists(RULE_LOGS_KEY):
        storage.save(RULE_LOGS_KEY, {"logs": []})


def get_rule_logs() -> List[Dict]:
    """Get rule operation logs"""
    _ensure_logs_exist()
    data = storage.load(RULE_LOGS_KEY)
    return data.get('logs', [])


def save_rule_log(action: str, rule_name: str, details: str = "", user: str = "admin"):
    """Save rule operation log"""
    _ensure_logs_exist()
    logs = get_rule_logs()
    
    log_entry = {
        "id": len(logs) + 1,
        "action": action,
        "rule_name": rule_name,
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "user": user
    }
    
    logs.insert(0, log_entry)
    storage.save(RULE_LOGS_KEY, {"logs": logs})
    logger.info(f"📝 Rule log: {action} - {rule_name}")


def load_rules() -> List[Dict]:
    """Load all rules from storage"""
    _ensure_rules_exist()
    data = storage.load(RULES_KEY)
    return data.get('rules', [])


def save_rules(rules: List[Dict]):
    """Save rules to storage"""
    storage.save(RULES_KEY, {"rules": rules})


def get_active_rules() -> List[Dict]:
    """Get only active rules"""
    all_rules = load_rules()
    active = [r for r in all_rules if r.get('is_active', True)]
    print(f"📋 Active rules: {len(active)}/{len(all_rules)}")
    return active


def evaluate_condition(row: Dict, condition: Dict) -> bool:
    """
    Evaluate single condition against a row
    
    Client-Specified Operators:
    
    Numeric operators:
    1. Equal to / equal to
    2. Not equal to / not equal to
    3. Less than / less than
    4. Greater than / greater than
    5. Less than equal to / less than equal to
    6. Greater than equal to / greater than equal to
    7. Between / between
    
    Text operators:
    1. Equal to (Exact words) / equal to
    2. Not equal to / not equal to
    3. Contains / contains
    4. Starts with / starts with
    5. Ends with / ends with
    
    Args:
        row: Data row to evaluate
        condition: Condition dict with column, operator, value (and value2 for between)
    
    Returns:
        True if condition matches, False otherwise
    """
    column = condition.get('column', '')
    operator = condition.get('operator', '').lower()  # Normalize to lowercase
    value = condition.get('value', '')
    value2 = condition.get('value2', '')  # For 'between' operator
    
    # Normalize operator names (map all possible frontend formats to backend format)
    operator_map = {
        # Equality operators (used for both numeric and text)
        'equal to': 'equal_to',
        'not equal to': 'not_equal_to',
        
        # Numeric comparison operators
        'less than': 'less_than',
        'greater than': 'greater_than',
        'less than equal to': 'less_than_equal_to',
        'greater than equal to': 'greater_than_equal_to',
        'between': 'between',
        
        # Text operators
        'contains': 'contains',
        'starts with': 'starts_with',
        'ends with': 'ends_with',
        
        # Legacy format support
        'is equal to': 'equal_to',
        'is not equal to': 'not_equal_to',
        'is less than': 'less_than',
        'is greater than': 'greater_than',
        'equals': 'equal_to',
        'not_equals': 'not_equal_to',
        'not_contains': 'not_contains',
        'does not contain': 'not_contains',
        'greater_than': 'greater_than',
        'less_than': 'less_than',
        'greater_or_equal': 'greater_than_equal_to',
        'less_or_equal': 'less_than_equal_to'
    }
    
    # Map to normalized operator
    operator = operator_map.get(operator, operator)
    
    # Get row value (handle missing columns with case-insensitive lookup)
    row_value = None
    for key in row.keys():
        if key.lower() == column.lower():
            row_value = str(row[key])
            break
    
    # If column not found, use empty string
    if row_value is None:
        row_value = ''
    
    compare_value = str(value)
    
    # Text operators (case-insensitive)
    if operator == 'equal_to':
        # For text: exact match (case-insensitive)
        # For numeric: equality check
        try:
            # Try numeric comparison first
            return float(row_value) == float(compare_value)
        except (ValueError, TypeError):
            # Fall back to text comparison
            return row_value.lower() == compare_value.lower()
    
    elif operator == 'not_equal_to':
        try:
            return float(row_value) != float(compare_value)
        except (ValueError, TypeError):
            return row_value.lower() != compare_value.lower()
    
    elif operator == 'contains':
        return compare_value.lower() in row_value.lower()
    
    elif operator == 'not_contains':
        return compare_value.lower() not in row_value.lower()
    
    elif operator == 'starts_with':
        return row_value.lower().startswith(compare_value.lower())
    
    elif operator == 'ends_with':
        return row_value.lower().endswith(compare_value.lower())
    
    # Numeric operators
    elif operator == 'less_than':
        try:
            return float(row_value) < float(compare_value)
        except (ValueError, TypeError):
            return False
    
    elif operator == 'greater_than':
        try:
            return float(row_value) > float(compare_value)
        except (ValueError, TypeError):
            return False
    
    elif operator == 'less_than_equal_to':
        try:
            return float(row_value) <= float(compare_value)
        except (ValueError, TypeError):
            return False
    
    elif operator == 'greater_than_equal_to':
        try:
            return float(row_value) >= float(compare_value)
        except (ValueError, TypeError):
            return False
    
    elif operator == 'between':
        # Between operator requires value and value2
        try:
            row_num = float(row_value)
            min_val = float(compare_value)
            max_val = float(value2)
            return min_val <= row_num <= max_val
        except (ValueError, TypeError):
            return False
    
    # Unknown operator
    logger.warning(f"⚠️ Unknown operator: {condition.get('operator', '')} (normalized: {operator})")
    return False


def evaluate_rule(row: Dict, rule: Dict) -> bool:
    """
    Evaluate if a rule matches a row (should be excluded)
    
    Logic:
    - WHERE/AND conditions: ALL must match (AND logic)
    - OR conditions: If any OR matches, that branch succeeds
    - Subgroups: Nested evaluation with own logic
    
    Args:
        row: Data row to evaluate
        rule: Rule dict with conditions
    
    Returns:
        True if row should be EXCLUDED, False otherwise
    """
    conditions = rule.get('conditions', [])
    
    if not conditions:
        return False
    
    # Track current logic chain
    result = None
    current_logic = 'and'  # Default to AND logic
    
    for condition in conditions:
        condition_type = condition.get('type', 'where')
        
        # Evaluate this condition
        condition_match = evaluate_condition(row, condition)
        
        # First condition (WHERE)
        if result is None:
            result = condition_match
            current_logic = 'and'
        
        # AND logic
        elif condition_type == 'and':
            result = result and condition_match
            current_logic = 'and'
        
        # OR logic
        elif condition_type == 'or':
            result = result or condition_match
            current_logic = 'or'
        
        # WHERE (reset logic chain)
        elif condition_type == 'where':
            result = condition_match
            current_logic = 'and'
    
    return result


def apply_rules(data: List[Dict], specific_rule_ids: Optional[List[int]] = None) -> Dict:
    """
    Apply exclusion rules to filter data
    
    Args:
        data: List of data rows
        specific_rule_ids: Optional list of specific rule IDs to apply.
                          If None, applies all active rules.
                          If provided, applies only these rules (even if inactive).
    
    Returns:
        {
            "filtered_data": [...],
            "excluded_count": 123,
            "rules_applied": 2,
            "original_count": 5213
        }
    """
    # Determine which rules to apply
    if specific_rule_ids is not None:
        # Apply only specified rules (even if inactive)
        all_rules = load_rules()
        rules_to_apply = [r for r in all_rules if r.get('id') in specific_rule_ids]
        
        if not rules_to_apply:
            print(f"⚠️ No rules found with IDs: {specific_rule_ids}")
            return {
                "filtered_data": data,
                "excluded_count": 0,
                "rules_applied": 0,
                "original_count": len(data)
            }
        
        print(f"🎯 Applying {len(rules_to_apply)} specific rules: {specific_rule_ids}")
    else:
        # Apply all active rules (default behavior)
        rules_to_apply = get_active_rules()
        
        if not rules_to_apply:
            print("ℹ️ No active rules, returning all data")
            return {
                "filtered_data": data,
                "excluded_count": 0,
                "rules_applied": 0,
                "original_count": len(data)
            }
    
    filtered_data = []
    excluded_count = 0
    
    for row in data:
        should_exclude = False
        
        # Check each rule
        for rule in rules_to_apply:
            if evaluate_rule(row, rule):
                should_exclude = True
                excluded_count += 1
                break  # One rule matched, exclude this row
        
        if not should_exclude:
            filtered_data.append(row)
    
    print(f"✅ Rules applied: {len(rules_to_apply)} rules")
    print(f"📊 Original: {len(data)} rows")
    print(f"📊 Excluded: {excluded_count} rows")
    print(f"📊 Remaining: {len(filtered_data)} rows")
    
    return {
        "filtered_data": filtered_data,
        "excluded_count": excluded_count,
        "rules_applied": len(rules_to_apply),
        "original_count": len(data)
    }


def create_rule(name: str, conditions: List[Dict], is_active: bool = True) -> Dict:
    """
    Create new exclusion rule
    
    Args:
        name: Rule name
        conditions: List of condition dicts
        is_active: Whether rule is active
    
    Returns:
        Created rule dict
    """
    rules = load_rules()
    
    # Check for duplicate name
    if any(r['name'].lower() == name.lower() for r in rules):
        raise ValueError(f"Rule with name '{name}' already exists")
    
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
    
    # Log the operation with unified logging
    logging_service.add_log(
        module='rules',
        action='create',
        description=f"Created rule: {name}",
        entity_id=new_id,
        entity_name=name,
        can_revert=True,
        revert_data={'action': 'delete', 'rule_id': new_id},  # Revert by deleting
        metadata={'conditions_count': len(conditions), 'is_active': is_active}
    )
    logger.info(f"✅ Rule created: {name} (ID: {new_id})")
    
    return new_rule


def update_rule(rule_id: int, **kwargs) -> Dict:
    """
    Update existing rule
    
    Args:
        rule_id: Rule ID to update
        **kwargs: Fields to update (name, conditions, is_active)
    
    Returns:
        Updated rule dict
    """
    rules = load_rules()
    
    for rule in rules:
        if rule['id'] == rule_id:
            # Save current state for revert
            original_state = rule.copy()
            
            # Update fields
            for key, value in kwargs.items():
                if value is not None:
                    rule[key] = value
            
            rule['updated_at'] = datetime.now().isoformat()
            save_rules(rules)
            
            # Log the operation with revert capability
            updated_fields = ', '.join(kwargs.keys())
            logging_service.add_log(
                module='rules',
                action='update',
                description=f"Updated rule: {rule['name']} (fields: {updated_fields})",
                entity_id=rule_id,
                entity_name=rule['name'],
                can_revert=True,
                revert_data={'action': 'restore', 'rule_data': original_state},
                metadata={'updated_fields': list(kwargs.keys())}
            )
            logger.info(f"✅ Rule updated: {rule['name']} (ID: {rule_id})")
            
            return rule
    
    raise ValueError(f"Rule {rule_id} not found")


def delete_rule(rule_id: int):
    """
    Delete rule
    
    Args:
        rule_id: Rule ID to delete
    """
    rules = load_rules()
    
    # Find rule for logging and revert data
    deleted_rule = next((r.copy() for r in rules if r['id'] == rule_id), None)
    
    if not deleted_rule:
        raise ValueError(f"Rule {rule_id} not found")
    
    # Remove rule
    rules = [r for r in rules if r['id'] != rule_id]
    save_rules(rules)
    
    # Log the operation with revert capability
    logging_service.add_log(
        module='rules',
        action='delete',
        description=f"Deleted rule: {deleted_rule['name']}",
        entity_id=rule_id,
        entity_name=deleted_rule['name'],
        can_revert=True,
        revert_data={'action': 'restore', 'rule_data': deleted_rule},
        metadata={'conditions_count': len(deleted_rule.get('conditions', []))}
    )
    logger.info(f"🗑️ Rule deleted: {deleted_rule['name']} (ID: {rule_id})")


def toggle_rule(rule_id: int) -> Dict:
    """
    Toggle rule active status
    
    Args:
        rule_id: Rule ID to toggle
    
    Returns:
        Updated rule dict
    """
    rules = load_rules()
    
    for rule in rules:
        if rule['id'] == rule_id:
            rule['is_active'] = not rule.get('is_active', True)
            rule['updated_at'] = datetime.now().isoformat()
            save_rules(rules)
            
            status = "activated" if rule['is_active'] else "deactivated"
            print(f"🔄 Rule {status}: {rule['name']} (ID: {rule_id})")
            
            return rule
    
    raise ValueError(f"Rule {rule_id} not found")


def get_rule_by_id(rule_id: int) -> Dict:
    """
    Get single rule by ID
    
    Args:
        rule_id: Rule ID
    
    Returns:
        Rule dict
    """
    rules = load_rules()
    rule = next((r for r in rules if r['id'] == rule_id), None)
    
    if not rule:
        raise ValueError(f"Rule {rule_id} not found")
    
    return rule
