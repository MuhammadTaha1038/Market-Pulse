#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLO Mapping Router - APIs for managing CLO-column mappings
Super admin can configure which columns each CLO type sees
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from models.clo_mapping import (
    CLOMappingResponse,
    UpdateCLOMappingRequest,
    CLOHierarchyResponse
)
from services.clo_mapping_service import get_clo_mapping_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/clo-mappings", tags=["CLO Mappings"])

clo_service = get_clo_mapping_service()


@router.get("/hierarchy", response_model=dict)
async def get_clo_hierarchy():
    """
    **Get CLO Hierarchy Structure**
    
    Returns the complete CLO type hierarchy:
    - Main CLOs (EURO ABS, CLO, USABS)
    - Sub CLOs under each main CLO
    
    Used by frontend to build the CLO selection tree.
    
    **Returns:**
    ```json
    {
      "main_clos": [
        {
          "id": "EURO_ABS",
          "name": "EURO_ABS",
          "display_name": "Euro ABS",
          "sub_clos": [...]
        }
      ],
      "total_main_clos": 3,
      "total_sub_clos": 39
    }
    ```
    """
    try:
        hierarchy = clo_service.get_clo_hierarchy()
        
        # Count totals
        total_main = len(hierarchy.get('main_clos', []))
        total_sub = sum(len(main['sub_clos']) for main in hierarchy.get('main_clos', []))
        
        return {
            **hierarchy,
            "total_main_clos": total_main,
            "total_sub_clos": total_sub
        }
        
    except Exception as e:
        logger.error(f"Error getting CLO hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mappings", response_model=List[dict])
async def get_all_clo_mappings():
    """
    **Get All CLO-Column Mappings**
    
    Returns column visibility configuration for all CLO types.
    
    **Returns:** List of mappings with visible/hidden columns for each CLO.
    """
    try:
        mappings = clo_service.get_all_mappings()
        logger.info(f"Returning {len(mappings)} CLO mappings")
        return mappings
        
    except Exception as e:
        logger.error(f"Error getting CLO mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mappings/{clo_id}", response_model=CLOMappingResponse)
async def get_clo_mapping(clo_id: str):
    """
    **Get Column Mapping for Specific CLO**
    
    Returns full column details (visible/hidden) for a CLO type.
    
    **Args:**
    - `clo_id`: CLO identifier (e.g., 'EURO_ABS', 'CLO_US_CLO')
    
    **Returns:**
    ```json
    {
      "clo_id": "EURO_ABS",
      "clo_name": "Euro ABS",
      "clo_type": "main",
      "visible_columns": [
        {
          "oracle_name": "MESSAGE_ID",
          "display_name": "Message ID",
          "data_type": "INTEGER",
          ...
        }
      ],
      "hidden_columns": [],
      "total_columns": 18
    }
    ```
    """
    try:
        mapping = clo_service.get_mapping_with_column_details(clo_id)
        
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"CLO mapping not found for: {clo_id}"
            )
        
        logger.info(f"Returning mapping for CLO: {clo_id}")
        return mapping
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting CLO mapping for {clo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mappings/{clo_id}", response_model=dict)
async def update_clo_mapping(
    clo_id: str,
    request: UpdateCLOMappingRequest,
    updated_by: str = Query("admin", description="Username of admin making the change")
):
    """
    **Update Column Visibility for CLO**
    
    Super admin can configure which columns a CLO type can see.
    
    **Args:**
    - `clo_id`: CLO identifier
    - `request`: List of column oracle_names to make visible
    - `updated_by`: Admin username (from Microsoft SSO)
    
    **Request Body:**
    ```json
    {
      "clo_id": "EURO_ABS",
      "clo_type": "main",
      "visible_columns": ["MESSAGE_ID", "TICKER", "SECTOR", "CUSIP"]
    }
    ```
    
    **Returns:** Updated mapping
    """
    try:
        # Validate CLO exists
        clo_details = clo_service.get_clo_details(clo_id)
        if not clo_details:
            raise HTTPException(
                status_code=404,
                detail=f"CLO not found: {clo_id}"
            )
        
        # Update mapping
        updated_mapping = clo_service.update_clo_mapping(
            clo_id=clo_id,
            visible_columns=request.visible_columns,
            updated_by=updated_by
        )
        
        logger.info(f"Updated CLO mapping for {clo_id} by {updated_by}")
        
        return {
            "success": True,
            "message": f"Updated column mapping for {clo_details.get('display_name', clo_id)}",
            "clo_id": clo_id,
            "visible_columns_count": len(request.visible_columns),
            "updated_by": updated_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating CLO mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-columns/{clo_id}", response_model=dict)
async def get_user_columns(clo_id: str):
    """
    **Get Columns Visible to User Based on CLO Type**
    
    This endpoint will be called by the frontend after Microsoft SSO
    to determine which columns the user can see.
    
    **Args:**
    - `clo_id`: User's CLO type from SSO (e.g., 'EURO_ABS_AUTO_LEASE')
    
    **Returns:**
    ```json
    {
      "clo_id": "EURO_ABS_AUTO_LEASE",
      "clo_name": "Auto Lease",
      "visible_columns": ["MESSAGE_ID", "TICKER", ...],
      "column_count": 15
    }
    ```
    """
    try:
        columns = clo_service.get_visible_columns_for_clo(clo_id)
        clo_details = clo_service.get_clo_details(clo_id)
        
        if not clo_details:
            raise HTTPException(
                status_code=404,
                detail=f"CLO type not found: {clo_id}"
            )
        
        logger.info(f"User with CLO {clo_id} can see {len(columns)} columns")
        
        return {
            "clo_id": clo_id,
            "clo_name": clo_details.get('display_name', clo_details.get('name')),
            "clo_type": clo_details.get('clo_type'),
            "parent_clo": clo_details.get('parent_clo'),
            "visible_columns": columns,
            "column_count": len(columns)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset/{clo_id}", response_model=dict)
async def reset_clo_mapping(
    clo_id: str,
    updated_by: str = Query("admin", description="Username of admin")
):
    """
    **Reset CLO Mapping to Default (All Columns Visible)**
    
    Resets a CLO's column visibility to show all columns.
    
    **Args:**
    - `clo_id`: CLO identifier
    - `updated_by`: Admin username
    
    **Returns:** Success message
    """
    try:
        from services.column_config_service import get_column_config
        column_config = get_column_config()
        all_columns = [col['oracle_name'] for col in column_config.config['columns']]
        
        updated_mapping = clo_service.update_clo_mapping(
            clo_id=clo_id,
            visible_columns=all_columns,
            updated_by=updated_by
        )
        
        logger.info(f"Reset CLO mapping for {clo_id} to all columns visible")
        
        return {
            "success": True,
            "message": f"Reset {clo_id} to show all columns",
            "visible_columns_count": len(all_columns)
        }
        
    except Exception as e:
        logger.error(f"Error resetting CLO mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))
