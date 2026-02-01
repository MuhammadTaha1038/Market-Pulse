#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manual Color Processing Router - APIs for Color Processing Page

This handles the manual color workflow (SEPARATE from admin panel buffer):
1. POST /api/manual-color/import - Import Excel and get sorted preview
2. GET /api/manual-color/preview/{session_id} - Get current preview
3. POST /api/manual-color/delete-rows - Delete selected rows
4. POST /api/manual-color/apply-rules - Apply selected rules
5. POST /api/manual-color/save - Save processed colors to output
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
import logging
import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.manual_color_service import (
    import_manual_colors,
    get_session_preview,
    delete_rows,
    apply_selected_rules,
    save_manual_colors,
    get_active_sessions,
    cleanup_old_sessions
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manual-color", tags=["Manual Color Processing"])


# Request/Response Models
class ImportResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    filename: Optional[str] = None
    rows_imported: Optional[int] = None
    rows_valid: Optional[int] = None
    parsing_errors: Optional[List[str]] = None
    sorted_preview: Optional[List[dict]] = None
    statistics: Optional[dict] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


class DeleteRowsRequest(BaseModel):
    session_id: str
    row_ids: List[int]


class ApplyRulesRequest(BaseModel):
    session_id: str
    rule_ids: List[int]


class SaveRequest(BaseModel):
    session_id: str
    user_id: int = 1


class SessionSummary(BaseModel):
    session_id: str
    created_at: Optional[str]
    updated_at: Optional[str]
    filename: Optional[str]
    status: Optional[str]
    rows_count: int


# API Endpoints

@router.post("/import", response_model=ImportResponse)
async def import_excel_for_manual_processing(
    file: UploadFile = File(...),
    user_id: int = Form(1)
):
    """
    Step 1: Import Excel file for manual color processing
    
    Flow:
    1. Upload Excel file
    2. Parse and validate
    3. Apply sorting logic (RankingEngine)
    4. Return sorted preview
    5. Create session for user to work with
    
    This is for Color Processing page, NOT admin panel buffer.
    """
    temp_file = None
    
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only Excel files (.xlsx, .xls) are allowed."
            )
        
        # Save uploaded file temporarily
        temp_dir = Path("data/temp_uploads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_file = temp_dir / f"manual_{user_id}_{file.filename}"
        
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📤 Received manual color upload: {file.filename}")
        
        # Process the file
        result = import_manual_colors(
            file_path=str(temp_file),
            filename=file.filename,
            user_id=user_id
        )
        
        return ImportResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Manual color import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if temp_file and temp_file.exists():
            temp_file.unlink()


@router.get("/preview/{session_id}")
async def get_preview(session_id: str):
    """
    Get current preview data for a session
    
    Returns the currently filtered data after any deletions or rule applications.
    """
    try:
        result = get_session_preview(session_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Session not found"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete-rows")
async def delete_selected_rows(request: DeleteRowsRequest):
    """
    Delete selected rows from preview
    
    User can select rows in UI and delete them.
    Returns updated preview data.
    """
    try:
        result = delete_rows(
            session_id=request.session_id,
            row_ids=request.row_ids
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete rows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-rules")
async def apply_rules_to_manual_data(request: ApplyRulesRequest):
    """
    Apply selected rules to manual color data
    
    Flow:
    1. User clicks "Run Rules" button in UI
    2. User selects rules from dropdown (fetched from /api/rules)
    3. Backend applies selected rules to current preview data
    4. Returns filtered data (excluded rows removed)
    
    Rules are fetched from Rules module (/api/rules).
    """
    try:
        if not request.rule_ids:
            raise HTTPException(status_code=400, detail="No rules selected")
        
        result = apply_selected_rules(
            session_id=request.session_id,
            rule_ids=request.rule_ids
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to apply rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_processed_manual_colors(request: SaveRequest):
    """
    Save processed manual colors to output file (S3 in future)
    
    Flow:
    1. User reviews preview (sorted, rules applied, rows deleted)
    2. User clicks "Run Automation" button
    3. Backend saves the final processed data to output Excel
    4. Future: Will save to S3 bucket
    
    This does NOT trigger full automation - only saves manual colors.
    """
    try:
        result = save_manual_colors(
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to save manual colors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions(user_id: Optional[int] = None):
    """
    Get list of active manual color sessions
    
    Optional filter by user_id.
    """
    try:
        sessions = get_active_sessions(user_id=user_id)
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"❌ Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_sessions(days: int = 1):
    """
    Clean up old session files
    
    Deletes sessions older than specified days (default 1 day).
    """
    try:
        deleted_count = cleanup_old_sessions(days=days)
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} old sessions"
        }
    except Exception as e:
        logger.error(f"❌ Failed to cleanup sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Manual Color Processing"
    }
