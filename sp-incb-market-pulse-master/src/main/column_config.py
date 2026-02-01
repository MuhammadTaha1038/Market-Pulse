#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Column Configuration Router - APIs for managing dynamic column configuration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import sys
import os

# Import column config service
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.column_config_service import get_column_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["Configuration"])

# Initialize column config service
column_config_service = get_column_config()


# Request/Response Models
class ColumnItem(BaseModel):
    id: Optional[int] = None
    oracle_name: str
    display_name: str
    data_type: str
    required: bool
    description: Optional[str] = None


class ColumnListResponse(BaseModel):
    columns: List[ColumnItem]
    count: int


class ColumnRequiredResponse(BaseModel):
    required_columns: List[str]
    optional_columns: List[str]


class TableConfigResponse(BaseModel):
    oracle_table: str
    version: str
    last_updated: str


# API Endpoints

@router.get("/columns", response_model=ColumnListResponse)
async def get_all_columns():
    """
    Get all configured columns
    
    Returns complete list of columns with their configuration
    """
    try:
        columns = column_config_service.get_all_columns()
        return ColumnListResponse(
            columns=[ColumnItem(**col) for col in columns],
            count=len(columns)
        )
    except Exception as e:
        logger.error(f"Error fetching columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns/required", response_model=ColumnRequiredResponse)
async def get_required_columns():
    """
    Get required vs optional column names
    
    Useful for validation - tells frontend which columns must be present in uploaded files
    """
    try:
        all_columns = column_config_service.get_all_columns()
        required_cols = [col['oracle_name'] for col in all_columns if col['required']]
        optional_cols = [col['oracle_name'] for col in all_columns if not col['required']]
        
        return ColumnRequiredResponse(
            required_columns=required_cols,
            optional_columns=optional_cols
        )
    except Exception as e:
        logger.error(f"Error fetching required columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns/{column_id}", response_model=ColumnItem)
async def get_column_by_id(column_id: int):
    """Get single column configuration by ID"""
    try:
        columns = column_config_service.get_all_columns()
        column = next((col for col in columns if col['id'] == column_id), None)
        
        if not column:
            raise HTTPException(
                status_code=404,
                detail=f"Column with ID {column_id} not found"
            )
        
        return ColumnItem(**column)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching column {column_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/columns", response_model=ColumnItem)
async def add_column(column: ColumnItem):
    """
    Add new column to configuration
    
    Admin can add new columns that will be:
    - Extracted from Oracle
    - Validated in manual uploads
    - Available in Rules Engine
    """
    try:
        column_dict = column.dict(exclude_none=True)
        added_column = column_config_service.add_column(column_dict)
        
        logger.info(f"✅ Added new column: {added_column['oracle_name']}")
        return ColumnItem(**added_column)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding column: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/columns/{column_id}", response_model=ColumnItem)
async def update_column(column_id: int, updates: ColumnItem):
    """
    Update existing column configuration
    
    Can change display name, data type, required status, description
    Note: Changing oracle_name may break existing data
    """
    try:
        update_dict = updates.dict(exclude_none=True, exclude={'id'})
        updated_column = column_config_service.update_column(column_id, update_dict)
        
        if not updated_column:
            raise HTTPException(
                status_code=404,
                detail=f"Column with ID {column_id} not found"
            )
        
        logger.info(f"✅ Updated column {column_id}")
        return ColumnItem(**updated_column)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating column {column_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/columns/{column_id}", response_model=dict)
async def delete_column(column_id: int):
    """
    Delete column from configuration
    
    Warning: This will affect:
    - Oracle data extraction
    - Manual upload validation
    - Rules Engine (if column used in rules)
    """
    try:
        success = column_config_service.delete_column(column_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Column with ID {column_id} not found"
            )
        
        return {
            "message": "Column deleted successfully",
            "column_id": column_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting column {column_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table", response_model=TableConfigResponse)
async def get_table_config():
    """
    Get Oracle table configuration
    
    Returns table name and config version info
    """
    try:
        table_name = column_config_service.get_oracle_table_name()
        config = column_config_service.config
        
        return TableConfigResponse(
            oracle_table=table_name,
            version=config.get('version', '1.0'),
            last_updated=config.get('last_updated', 'Unknown')
        )
    except Exception as e:
        logger.error(f"Error fetching table config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/table", response_model=dict)
async def update_table_config(oracle_table: str):
    """
    Update Oracle table name
    
    Changes which table is queried for color data
    """
    try:
        column_config_service.config['oracle_table'] = oracle_table
        column_config_service._save_config(column_config_service.config)
        
        logger.info(f"✅ Updated Oracle table to: {oracle_table}")
        return {
            "message": "Table name updated successfully",
            "oracle_table": oracle_table
        }
    except Exception as e:
        logger.error(f"Error updating table config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

