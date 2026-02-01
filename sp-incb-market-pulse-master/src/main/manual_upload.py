#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manual Upload Router - APIs for manual Excel file uploads
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
import logging
import sys
import os

# Import manual upload service
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from manual_upload_service import (
    process_manual_upload,
    get_upload_history,
    get_upload_by_id,
    delete_upload_history
)
from services.column_config_service import get_column_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manual-upload", tags=["Manual Upload"])


# Response Models
class UploadResponse(BaseModel):
    success: bool
    upload_id: int
    filename: Optional[str] = None
    rows_uploaded: Optional[int] = None
    rows_valid: Optional[int] = None
    rows_processed: Optional[int] = None
    parsing_errors: Optional[List[str]] = None
    validation_errors: Optional[List[str]] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


class UploadHistoryItem(BaseModel):
    id: int
    filename: str
    uploaded_by: str
    upload_time: str
    processing_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str
    rows_uploaded: int
    rows_valid: Optional[int] = None
    rows_processed: Optional[int] = None
    parsing_errors_count: Optional[int] = None
    error: Optional[str] = None


class UploadHistoryResponse(BaseModel):
    uploads: List[UploadHistoryItem]
    count: int


# API Endpoints

@router.post("/upload", response_model=UploadResponse)
async def upload_manual_excel(
    file: UploadFile = File(...),
    uploaded_by: str = Form("admin")
):
    """
    Upload Excel file with manual colors
    
    Steps:
    1. Validate Excel structure
    2. Parse to ColorRaw objects
    3. Apply ranking engine
    4. Save to output file (marked as MANUAL)
    5. Record in upload history
    
    Returns detailed upload statistics and any errors
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Only Excel files (.xlsx, .xls) are allowed"
            )
        
        logger.info(f"📤 Uploading manual Excel: {file.filename} by {uploaded_by}")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Process upload
        result = process_manual_upload(
            file_content=file_content,
            filename=file.filename,
            uploaded_by=uploaded_by
        )
        
        return UploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading manual Excel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=UploadHistoryResponse)
async def get_history(limit: int = 50):
    """
    Get manual upload history
    
    Returns list of all manual uploads with their status and statistics
    """
    try:
        history = get_upload_history()
        
        # Limit results
        history = history[:limit]
        
        return UploadHistoryResponse(
            uploads=[UploadHistoryItem(**upload) for upload in history],
            count=len(history)
        )
    except Exception as e:
        logger.error(f"Error fetching upload history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{upload_id}", response_model=UploadHistoryItem)
async def get_upload_details(upload_id: int):
    """Get details of a specific upload"""
    try:
        upload = get_upload_by_id(upload_id)
        
        if not upload:
            raise HTTPException(
                status_code=404, 
                detail=f"Upload with ID {upload_id} not found"
            )
        
        return UploadHistoryItem(**upload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching upload {upload_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{upload_id}", response_model=dict)
async def delete_upload(upload_id: int):
    """
    Delete upload from history and remove uploaded file
    
    Note: This only removes the history record and uploaded file,
    not the processed data that was already saved to output
    """
    try:
        upload = get_upload_by_id(upload_id)
        
        if not upload:
            raise HTTPException(
                status_code=404, 
                detail=f"Upload with ID {upload_id} not found"
            )
        
        success = delete_upload_history(upload_id)
        
        if success:
            return {
                "message": "Upload history deleted successfully",
                "upload_id": upload_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete upload")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting upload {upload_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_upload_stats():
    """
    Get statistics about manual uploads
    
    Returns summary of all uploads (success rate, total rows, etc.)
    """
    try:
        history = get_upload_history()
        
        if not history:
            return {
                "total_uploads": 0,
                "successful_uploads": 0,
                "failed_uploads": 0,
                "success_rate": 0.0,
                "total_rows_uploaded": 0,
                "total_rows_processed": 0
            }
        
        successful = [u for u in history if u["status"] == "success"]
        failed = [u for u in history if u["status"] == "failed"]
        
        total_rows_uploaded = sum(u.get("rows_uploaded", 0) for u in successful)
        total_rows_processed = sum(u.get("rows_processed", 0) for u in successful)
        
        return {
            "total_uploads": len(history),
            "successful_uploads": len(successful),
            "failed_uploads": len(failed),
            "success_rate": (len(successful) / len(history)) * 100 if history else 0.0,
            "total_rows_uploaded": total_rows_uploaded,
            "total_rows_processed": total_rows_processed,
            "recent_uploads": [
                {
                    "id": u["id"],
                    "filename": u["filename"],
                    "upload_time": u["upload_time"],
                    "status": u["status"],
                    "rows_processed": u.get("rows_processed", 0)
                }
                for u in history[:5]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching upload stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template-info", response_model=dict)
async def get_template_info():
    """
    Get information about the required Excel template structure
    
    Returns column names and validation rules for frontend
    Uses dynamic column configuration
    """
    try:
        column_config = get_column_config()
        all_columns = column_config.get_all_columns()
        
        required_cols = [col for col in all_columns if col['required']]
        optional_cols = [col for col in all_columns if not col['required']]
        
        # Build column types dict
        column_types = {col['oracle_name']: col['data_type'].lower() for col in all_columns}
        
        # Build validation rules
        validation_rules = {}
        for col in required_cols:
            if col['oracle_name'] == 'MESSAGE_ID':
                validation_rules[col['oracle_name']] = "Must be a positive integer"
            elif col['oracle_name'] == 'CUSIP':
                validation_rules[col['oracle_name']] = "Must be 9 characters"
            elif col['oracle_name'] == 'DATE':
                validation_rules[col['oracle_name']] = "Must be a valid date (YYYY-MM-DD)"
            elif col['oracle_name'] == 'PX':
                validation_rules[col['oracle_name']] = "Must be a positive number"
            elif col['oracle_name'] == 'RANK':
                validation_rules[col['oracle_name']] = "Must be an integer between 1-5"
        
        return {
            "required_columns": [col['oracle_name'] for col in required_cols],
            "optional_columns": [col['oracle_name'] for col in optional_cols],
            "column_types": column_types,
            "validation_rules": validation_rules,
            "notes": [
                "Excel file must have .xlsx or .xls extension",
                "First row must contain column headers",
                "At least one data row is required",
                "Missing optional columns will be filled with default values",
                "Invalid rows will be skipped with error messages"
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching template info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
