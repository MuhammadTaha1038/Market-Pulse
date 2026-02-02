"""
Presets API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import presets_service
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/presets", tags=["Presets"])


class PresetCondition(BaseModel):
    """Single condition in a preset"""
    column: str
    operator: str
    value: str
    value2: Optional[str] = None  # For 'between' operator


class PresetCreate(BaseModel):
    """Create preset request"""
    name: str
    conditions: List[Dict]
    description: Optional[str] = None


class PresetUpdate(BaseModel):
    """Update preset request"""
    name: Optional[str] = None
    conditions: Optional[List[Dict]] = None
    description: Optional[str] = None


class PresetApply(BaseModel):
    """Apply preset to data"""
    data: List[Dict]


@router.get("")
async def get_all_presets():
    """
    Get all presets
    
    Returns:
        {
            "presets": [
                {
                    "id": 1,
                    "name": "Select 102 bank securities",
                    "description": "Filter bank securities",
                    "conditions": [...],
                    "created_at": "2026-02-02T...",
                    "created_by": "admin"
                }
            ],
            "count": 2
        }
    """
    presets = presets_service.load_presets()
    return {
        "presets": presets,
        "count": len(presets)
    }


@router.get("/stats")
async def get_preset_stats():
    """
    Get preset statistics
    
    Returns:
        {
            "total_presets": 5,
            "most_recent": {...}
        }
    """
    stats = presets_service.get_preset_stats()
    return stats


@router.get("/{preset_id}")
async def get_preset(preset_id: int):
    """
    Get single preset by ID
    
    Args:
        preset_id: Preset ID
    
    Returns:
        {"preset": {...}}
    """
    try:
        preset = presets_service.get_preset_by_id(preset_id)
        return {"preset": preset}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("")
async def create_preset(preset: PresetCreate):
    """
    Create new preset
    
    Request body:
        {
            "name": "Select 102 bank securities",
            "description": "Bank securities filter",
            "conditions": [
                {
                    "column": "BWIC_COVER",
                    "operator": "equals",
                    "value": "Bank"
                }
            ]
        }
    
    Returns:
        {
            "message": "Preset created successfully",
            "preset": {...}
        }
    """
    try:
        new_preset = presets_service.create_preset(
            name=preset.name,
            conditions=preset.conditions,
            description=preset.description
        )
        return {
            "message": "Preset created successfully",
            "preset": new_preset
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{preset_id}")
async def update_preset(preset_id: int, preset: PresetUpdate):
    """
    Update existing preset
    
    Args:
        preset_id: Preset ID to update
    
    Request body:
        {
            "name": "Updated name",
            "conditions": [...],
            "description": "New description"
        }
    
    Returns:
        {
            "message": "Preset updated successfully",
            "preset": {...}
        }
    """
    try:
        updated = presets_service.update_preset(
            preset_id=preset_id,
            name=preset.name,
            conditions=preset.conditions,
            description=preset.description
        )
        return {
            "message": "Preset updated successfully",
            "preset": updated
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{preset_id}")
async def delete_preset(preset_id: int):
    """
    Delete preset
    
    Args:
        preset_id: Preset ID to delete
    
    Returns:
        {"message": "Preset deleted successfully"}
    """
    try:
        presets_service.delete_preset(preset_id)
        return {"message": "Preset deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{preset_id}/apply")
async def apply_preset(preset_id: int, request: PresetApply):
    """
    Apply preset filters to data
    
    Args:
        preset_id: Preset ID to apply
    
    Request body:
        {
            "data": [
                {"CUSIP": "123", "BWIC_COVER": "Bank", ...},
                {"CUSIP": "456", "BWIC_COVER": "Other", ...}
            ]
        }
    
    Returns:
        {
            "total_rows": 100,
            "filtered_rows": 25,
            "data": [...]
        }
    """
    try:
        logger.info(f"🎯 Applying preset {preset_id} to {len(request.data)} rows")
        
        if len(request.data) == 0:
            logger.warning(f"⚠️ Empty data array received for preset {preset_id}")
            return {
                "total_rows": 0,
                "filtered_rows": 0,
                "data": []
            }
        
        filtered_data = presets_service.apply_preset(preset_id, request.data)
        
        logger.info(f"✅ Preset {preset_id} applied: {len(filtered_data)}/{len(request.data)} rows match")
        
        return {
            "total_rows": len(request.data),
            "filtered_rows": len(filtered_data),
            "data": filtered_data
        }
    except ValueError as e:
        logger.error(f"❌ Preset {preset_id} not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error applying preset {preset_id}: {type(e).__name__}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@router.get("/health/check")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "presets",
        "presets_count": len(presets_service.load_presets())
    }
