"""
Rules API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import rules_service

router = APIRouter(prefix="/api/rules", tags=["Rules"])


class RuleCondition(BaseModel):
    """Single condition in a rule"""
    type: str  # 'where', 'and', 'or'
    column: str
    operator: str
    value: str
    value2: Optional[str] = None  # For 'between' operator


class RuleCreate(BaseModel):
    """Create rule request"""
    name: str
    conditions: List[Dict]
    is_active: bool = True


class RuleUpdate(BaseModel):
    """Update rule request"""
    name: Optional[str] = None
    conditions: Optional[List[Dict]] = None
    is_active: Optional[bool] = None


class RuleTestRequest(BaseModel):
    """Test rule request"""
    rule: RuleCreate
    test_data: List[Dict]


@router.get("")
async def get_all_rules():
    """
    Get all rules
    
    Returns:
        {
            "rules": [...],
            "count": 2
        }
    """
    rules = rules_service.load_rules()
    return {
        "rules": rules,
        "count": len(rules)
    }


@router.get("/active")
async def get_active_rules():
    """
    Get only active rules
    
    Returns:
        {
            "rules": [...],
            "count": 1
        }
    """
    rules = rules_service.get_active_rules()
    return {
        "rules": rules,
        "count": len(rules)
    }


@router.get("/logs")
async def get_rule_logs(limit: int = 50):
    """
    Get rule operation logs
    
    Returns history of rule create/update/delete operations
    """
    try:
        logs = rules_service.get_rule_logs()
        logs = logs[:limit]
        
        return {
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rule_id}")
async def get_rule(rule_id: int):
    """
    Get single rule by ID
    
    Args:
        rule_id: Rule ID
    
    Returns:
        {"rule": {...}}
    """
    try:
        rule = rules_service.get_rule_by_id(rule_id)
        return {"rule": rule}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("")
async def create_rule(rule: RuleCreate):
    """
    Create new exclusion rule
    
    Request body:
        {
            "name": "Remove DZ Bank",
            "conditions": [
                {
                    "type": "where",
                    "column": "BWIC_COVER",
                    "operator": "equals",
                    "value": "DZ Bank"
                }
            ],
            "is_active": true
        }
    
    Returns:
        {
            "message": "Rule created successfully",
            "rule": {...}
        }
    """
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{rule_id}")
async def update_rule(rule_id: int, rule: RuleUpdate):
    """
    Update existing rule
    
    Args:
        rule_id: Rule ID to update
    
    Request body:
        {
            "name": "Updated name",
            "conditions": [...],
            "is_active": false
        }
    
    Returns:
        {
            "message": "Rule updated successfully",
            "rule": {...}
        }
    """
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
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{rule_id}")
async def delete_rule(rule_id: int):
    """
    Delete rule
    
    Args:
        rule_id: Rule ID to delete
    
    Returns:
        {"message": "Rule deleted successfully"}
    """
    try:
        rules_service.delete_rule(rule_id)
        return {"message": "Rule deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{rule_id}/toggle")
async def toggle_rule(rule_id: int):
    """
    Toggle rule active/inactive status
    
    Args:
        rule_id: Rule ID to toggle
    
    Returns:
        {
            "message": "Rule activated",
            "rule": {...}
        }
    """
    try:
        updated = rules_service.toggle_rule(rule_id)
        status = "activated" if updated['is_active'] else "deactivated"
        return {
            "message": f"Rule {status}",
            "rule": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_rule(request: RuleTestRequest):
    """
    Test a rule against sample data without saving
    Useful for previewing what rows will be excluded
    
    Request body:
        {
            "rule": {
                "name": "Test Rule",
                "conditions": [...]
            },
            "test_data": [
                {"column1": "value1", ...},
                {"column2": "value2", ...}
            ]
        }
    
    Returns:
        {
            "total_rows": 100,
            "excluded_count": 25,
            "included_count": 75,
            "excluded_sample": [...],
            "included_sample": [...]
        }
    """
    try:
        # Create temporary rule for testing
        temp_rule = {
            "id": -1,
            "name": request.rule.name,
            "is_active": True,
            "conditions": request.rule.conditions
        }
        
        # Test against provided data
        excluded = []
        included = []
        
        for row in request.test_data:
            if rules_service.evaluate_rule(row, temp_rule):
                excluded.append(row)
            else:
                included.append(row)
        
        return {
            "total_rows": len(request.test_data),
            "excluded_count": len(excluded),
            "included_count": len(included),
            "excluded_sample": excluded[:5],  # First 5 excluded
            "included_sample": included[:5]   # First 5 included
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/operators/list")
async def list_operators():
    """
    Get list of supported operators
    
    Returns:
        {
            "operators": [
                {
                    "value": "equals",
                    "label": "is equal to",
                    "type": "string"
                },
                ...
            ]
        }
    """
    # Client-specified operators
    operators = [
        # Numeric operators
        {"value": "equal to", "label": "Equal to", "type": "numeric"},
        {"value": "not equal to", "label": "Not equal to", "type": "numeric"},
        {"value": "less than", "label": "Less than", "type": "numeric"},
        {"value": "greater than", "label": "Greater than", "type": "numeric"},
        {"value": "less than equal to", "label": "Less than equal to", "type": "numeric"},
        {"value": "greater than equal to", "label": "Greater than equal to", "type": "numeric"},
        {"value": "between", "label": "Between", "type": "numeric"},
        
        # Text operators
        {"value": "equal to", "label": "Equal to (Exact words)", "type": "text"},
        {"value": "not equal to", "label": "Not equal to", "type": "text"},
        {"value": "contains", "label": "Contains", "type": "text"},
        {"value": "starts with", "label": "Starts with", "type": "text"},
        {"value": "ends with", "label": "Ends with", "type": "text"},
    ]
    
    return {"operators": operators}

@router.get("/logs")
async def get_rule_logs(limit: int = 50):
    """
    Get rule operation logs
    
    Returns history of rule create/update/delete operations
    """
    try:
        logs = rules_service.get_rule_logs()
        logs = logs[:limit]
        
        return {
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))