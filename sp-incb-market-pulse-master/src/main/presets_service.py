"""
Presets Service
Manage saved filter presets for quick rule application
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
PRESETS_FILE = os.path.join(DATA_DIR, 'presets.json')


def _ensure_file():
    """Ensure presets file exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(PRESETS_FILE):
        with open(PRESETS_FILE, 'w') as f:
            json.dump([], f, indent=2)


def _get_next_id(presets: List[Dict]) -> int:
    """Get next available preset ID"""
    if not presets:
        return 1
    return max(preset['id'] for preset in presets) + 1


def load_presets() -> List[Dict]:
    """Load all presets from storage"""
    _ensure_file()
    try:
        with open(PRESETS_FILE, 'r') as f:
            presets = json.load(f)
        return presets
    except Exception as e:
        logger.error(f"Error loading presets: {e}")
        return []


def save_presets(presets: List[Dict]) -> None:
    """Save presets to storage"""
    _ensure_file()
    try:
        with open(PRESETS_FILE, 'w') as f:
            json.dump(presets, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving presets: {e}")
        raise


def get_preset_by_id(preset_id: int) -> Dict:
    """
    Get single preset by ID
    
    Args:
        preset_id: Preset ID
        
    Returns:
        Preset dict
        
    Raises:
        ValueError: If preset not found
    """
    presets = load_presets()
    preset = next((p for p in presets if p['id'] == preset_id), None)
    
    if not preset:
        raise ValueError(f"Preset with ID {preset_id} not found")
    
    return preset


def create_preset(
    name: str,
    conditions: List[Dict],
    description: Optional[str] = None,
    performed_by: str = "admin"
) -> Dict:
    """
    Create new preset
    
    Args:
        name: Preset name (e.g., "Select 102 bank securities")
        conditions: List of filter conditions
        description: Optional description
        performed_by: User who created preset
        
    Returns:
        Created preset dict
    """
    presets = load_presets()
    
    # Validate conditions
    if not conditions or not isinstance(conditions, list):
        raise ValueError("Conditions must be a non-empty list")
    
    for condition in conditions:
        if 'column' not in condition or 'operator' not in condition or 'value' not in condition:
            raise ValueError("Each condition must have column, operator, and value")
    
    new_preset = {
        "id": _get_next_id(presets),
        "name": name,
        "description": description or "",
        "conditions": conditions,
        "created_at": datetime.now().isoformat(),
        "created_by": performed_by,
        "updated_at": datetime.now().isoformat()
    }
    
    presets.append(new_preset)
    save_presets(presets)
    
    logger.info(f"Created preset: {name} (ID: {new_preset['id']})")
    return new_preset


def update_preset(
    preset_id: int,
    name: Optional[str] = None,
    conditions: Optional[List[Dict]] = None,
    description: Optional[str] = None,
    performed_by: str = "admin"
) -> Dict:
    """
    Update existing preset
    
    Args:
        preset_id: Preset ID to update
        name: New name (optional)
        conditions: New conditions (optional)
        description: New description (optional)
        performed_by: User who updated preset
        
    Returns:
        Updated preset dict
    """
    presets = load_presets()
    preset = next((p for p in presets if p['id'] == preset_id), None)
    
    if not preset:
        raise ValueError(f"Preset with ID {preset_id} not found")
    
    # Update fields
    if name is not None:
        preset['name'] = name
    if conditions is not None:
        if not conditions or not isinstance(conditions, list):
            raise ValueError("Conditions must be a non-empty list")
        preset['conditions'] = conditions
    if description is not None:
        preset['description'] = description
    
    preset['updated_at'] = datetime.now().isoformat()
    
    save_presets(presets)
    
    logger.info(f"Updated preset ID {preset_id}")
    return preset


def delete_preset(preset_id: int, performed_by: str = "admin") -> None:
    """
    Delete preset
    
    Args:
        preset_id: Preset ID to delete
        performed_by: User who deleted preset
    """
    presets = load_presets()
    preset = next((p for p in presets if p['id'] == preset_id), None)
    
    if not preset:
        raise ValueError(f"Preset with ID {preset_id} not found")
    
    # Remove preset
    presets = [p for p in presets if p['id'] != preset_id]
    save_presets(presets)
    
    logger.info(f"Deleted preset: {preset['name']} (ID: {preset_id})")


def apply_preset(preset_id: int, data: List[Dict]) -> List[Dict]:
    """
    Apply preset filters to data
    
    Args:
        preset_id: Preset ID to apply
        data: List of data rows to filter
        
    Returns:
        Filtered data based on preset conditions
    """
    preset = get_preset_by_id(preset_id)
    conditions = preset['conditions']
    
    # Debug: Log first row to see actual column names
    if data:
        logger.info(f"🔍 Sample data row keys: {list(data[0].keys())}")
        logger.info(f"🔍 Preset conditions: {conditions}")
    
    # Import rules evaluation logic
    from rules_service import evaluate_condition
    
    filtered_data = []
    for row in data:
        # If row matches ALL preset conditions, include it
        matches_all = all(evaluate_condition(row, condition) for condition in conditions)
        if matches_all:
            filtered_data.append(row)
    
    return filtered_data


def get_preset_stats() -> Dict:
    """
    Get preset statistics
    
    Returns:
        {
            "total_presets": 5,
            "most_recent": {...}
        }
    """
    presets = load_presets()
    
    most_recent = None
    if presets:
        most_recent = max(presets, key=lambda p: p.get('created_at', ''))
    
    return {
        "total_presets": len(presets),
        "most_recent": most_recent
    }
