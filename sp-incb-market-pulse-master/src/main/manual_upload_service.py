#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manual Upload Service - Handle manual Excel file uploads with validation and history

This service manages manual color uploads:
- File upload and validation
- Excel parsing
- Storage of upload history
- Merge with automated results
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime
import logging
import os
import shutil
from pathlib import Path

from storage_config import storage
from models.color import ColorRaw, ColorProcessed
from services.ranking_engine import RankingEngine
from services.output_service import get_output_service
from services.column_config_service import get_column_config

logger = logging.getLogger(__name__)

# Initialize services
ranking_engine = RankingEngine()
output_service = get_output_service()
column_config = get_column_config()

# Upload directories
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "manual_uploads")
BUFFER_DIR = os.path.join(os.path.dirname(__file__), "data", "manual_uploads_buffer")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BUFFER_DIR, exist_ok=True)


def get_upload_history() -> List[Dict]:
    """Get manual upload history"""
    try:
        history_data = storage.load("manual_upload_history")
        if history_data is None:
            return []
        return history_data.get("uploads", [])
    except FileNotFoundError:
        return []


def save_upload_history(history: List[Dict]):
    """Save upload history"""
    storage.save("manual_upload_history", {"uploads": history})


def get_next_upload_id() -> int:
    """Get next available upload ID"""
    history = get_upload_history()
    if not history:
        return 1
    return max(upload["id"] for upload in history) + 1


def get_buffered_files() -> List[Dict]:
    """Get list of buffered files waiting to be processed"""
    try:
        buffer_data = storage.load("manual_uploads_buffer")
        if buffer_data is None:
            return []
        return buffer_data.get("files", [])
    except FileNotFoundError:
        return []


def save_buffered_files(files: List[Dict]):
    """Save buffered files list"""
    storage.save("manual_uploads_buffer", {"files": files})


def add_to_buffer(file_path: str, filename: str, uploaded_by: str, upload_id: int) -> Dict:
    """Add uploaded file to buffer for processing in next cron run"""
    buffer_entry = {
        "id": upload_id,
        "filename": filename,
        "file_path": file_path,
        "uploaded_by": uploaded_by,
        "upload_time": datetime.now().isoformat(),
        "status": "pending",
        "processed_time": None
    }
    
    buffered = get_buffered_files()
    buffered.append(buffer_entry)
    save_buffered_files(buffered)
    
    logger.info(f"📥 Added to buffer: {filename} (ID: {upload_id})")
    return buffer_entry


def mark_buffer_processed(upload_id: int, success: bool, error: str = None):
    """Mark buffered file as processed and remove from buffer"""
    buffered = get_buffered_files()
    updated_buffer = [f for f in buffered if f["id"] != upload_id]
    save_buffered_files(updated_buffer)
    logger.info(f"✅ Removed from buffer: ID {upload_id}")


def validate_excel_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate Excel file structure using dynamic column configuration
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Get required columns from configuration (dynamic)
    required_column_configs = column_config.get_required_columns()
    required_columns = [col['oracle_name'] for col in required_column_configs]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Check for empty dataframe
    if len(df) == 0:
        errors.append("Excel file is empty (no data rows)")
    
    # Validate data types (if columns exist)
    if 'MESSAGE_ID' in df.columns:
        try:
            df['MESSAGE_ID'].astype(int)
        except:
            errors.append("MESSAGE_ID column must contain integers")
    
    if 'DATE' in df.columns:
        try:
            pd.to_datetime(df['DATE'])
        except:
            errors.append("DATE column must contain valid dates")
    
    if 'PX' in df.columns:
        try:
            df['PX'].astype(float)
        except:
            errors.append("PX column must contain numeric values")
    
    if 'RANK' in df.columns:
        try:
            df['RANK'].astype(int)
        except:
            errors.append("RANK column must contain integers")
    
    return (len(errors) == 0, errors)


def parse_excel_to_colors(df: pd.DataFrame) -> Tuple[List[ColorRaw], List[str]]:
    """
    Parse Excel DataFrame to ColorRaw objects
    
    Returns:
        (colors, errors)
    """
    colors = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Parse required fields
            color = ColorRaw(
                message_id=int(row['MESSAGE_ID']),
                ticker=str(row['TICKER']).strip(),
                sector=str(row['SECTOR']).strip(),
                cusip=str(row['CUSIP']).strip(),
                date=pd.to_datetime(row['DATE']),
                price_level=float(row['PRICE_LEVEL']) if pd.notna(row.get('PRICE_LEVEL')) else 0.0,
                bid=float(row['BID']) if pd.notna(row.get('BID')) else 0.0,
                ask=float(row['ASK']) if pd.notna(row.get('ASK')) else 0.0,
                px=float(row['PX']),
                source=str(row['SOURCE']).strip(),
                bias=str(row['BIAS']).strip() if pd.notna(row.get('BIAS')) else "",
                rank=int(row['RANK']),
                cov_price=float(row['COV_PRICE']) if pd.notna(row.get('COV_PRICE')) else 0.0,
                percent_diff=float(row['PERCENT_DIFF']) if pd.notna(row.get('PERCENT_DIFF')) else 0.0,
                price_diff=float(row['PRICE_DIFF']) if pd.notna(row.get('PRICE_DIFF')) else 0.0,
                confidence=int(row.get('CONFIDENCE', 5)),
                date_1=pd.to_datetime(row['DATE_1']) if 'DATE_1' in row and pd.notna(row.get('DATE_1')) else pd.to_datetime(row['DATE']),
                diff_status=str(row.get('DIFF_STATUS', '')).strip(),
                security_name=str(row.get('SECURITY_NAME', '')).strip(),
                bwic_cover=str(row.get('BWIC_COVER', '')).strip(),
                asset_class=str(row.get('ASSET_CLASS', '')).strip()
            )
            colors.append(color)
            
        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
    
    return colors, errors


def save_uploaded_file(file_content: bytes, original_filename: str, upload_id: int) -> str:
    """
    Save uploaded Excel file to storage
    
    Returns:
        Saved file path
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{upload_id}_{timestamp}_{original_filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    logger.info(f"📁 Saved uploaded file: {safe_filename}")
    return file_path


def process_manual_upload(
    file_content: bytes,
    filename: str,
    uploaded_by: str = "admin"
) -> Dict:
    """
    Save manual Excel upload to buffer for processing in next cron job
    
    Steps:
    1. Validate Excel structure
    2. Save to buffer directory
    3. Add to buffer queue
    4. Record in upload history as "pending"
    
    Processing will happen during next scheduled cron run.
    
    Returns:
        Upload result with buffer status
    """
    upload_id = get_next_upload_id()
    start_time = datetime.now()
    
    try:
        logger.info(f"📥 Buffering manual upload: {filename} (ID: {upload_id})")
        
        # Step 1: Read Excel
        df = pd.read_excel(pd.io.common.BytesIO(file_content))
        logger.info(f"📄 Loaded {len(df)} rows from Excel")
        
        # Step 2: Validate structure before buffering
        is_valid, validation_errors = validate_excel_structure(df)
        if not is_valid:
            error_msg = "; ".join(validation_errors)
            logger.error(f"❌ Validation failed: {error_msg}")
            
            # Save failed upload to history
            history_entry = {
                "id": upload_id,
                "filename": filename,
                "uploaded_by": uploaded_by,
                "upload_time": start_time.isoformat(),
                "status": "failed",
                "error": error_msg,
                "rows_uploaded": 0,
                "processing_type": "MANUAL"
            }
            history = get_upload_history()
            history.insert(0, history_entry)
            save_upload_history(history)
            
            return {
                "success": False,
                "upload_id": upload_id,
                "error": error_msg,
                "validation_errors": validation_errors
            }
        
        # Step 3: Save file to buffer directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{upload_id}_{timestamp}_{filename}"
        buffer_file_path = os.path.join(BUFFER_DIR, safe_filename)
        
        with open(buffer_file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"💾 Saved to buffer: {safe_filename}")
        
        # Step 4: Add to buffer queue
        buffer_entry = add_to_buffer(buffer_file_path, filename, uploaded_by, upload_id)
        
        # Step 5: Record in upload history as "pending"
        history_entry = {
            "id": upload_id,
            "filename": filename,
            "uploaded_by": uploaded_by,
            "upload_time": start_time.isoformat(),
            "status": "pending",
            "rows_uploaded": len(df),
            "processing_type": "MANUAL",
            "message": "File buffered and will be processed in next scheduled run"
        }
        history = get_upload_history()
        history.insert(0, history_entry)
        save_upload_history(history)
        
        logger.info(f"✅ Upload buffered successfully: {filename}")
        
        return {
            "success": True,
            "upload_id": upload_id,
            "filename": filename,
            "status": "pending",
            "rows_uploaded": len(df),
            "message": "File uploaded and buffered. Will be processed in next scheduled automation run."
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Buffer upload failed: {error_msg}")
        
        # Save failed upload to history
        history_entry = {
            "id": upload_id,
            "filename": filename,
            "uploaded_by": uploaded_by,
            "upload_time": start_time.isoformat(),
            "status": "failed",
            "error": error_msg,
            "rows_uploaded": 0,
            "processing_type": "MANUAL"
        }
        
        history = get_upload_history()
        history.insert(0, history_entry)
        save_upload_history(history)
        
        return {
            "success": False,
            "upload_id": upload_id,
            "error": error_msg
        }


def process_buffered_file(buffer_entry: Dict) -> Dict:
    """
    Process a single buffered file during cron run
    
    Steps:
    1. Read file from buffer
    2. Parse to ColorRaw objects
    3. Apply ranking
    4. Save to output
    5. Update history
    6. Remove from buffer
    
    Returns:
        Processing result
    """
    upload_id = buffer_entry["id"]
    filename = buffer_entry["filename"]
    file_path = buffer_entry["file_path"]
    uploaded_by = buffer_entry.get("uploaded_by", "admin")
    
    start_time = datetime.now()
    
    try:
        logger.info(f"🔄 Processing buffered file: {filename} (ID: {upload_id})")
        
        # Read buffered file
        df = pd.read_excel(file_path)
        logger.info(f"📥 Loaded {len(df)} rows from buffered file")
        
        # Parse to ColorRaw objects
        colors, parsing_errors = parse_excel_to_colors(df)
        
        if parsing_errors:
            logger.warning(f"⚠️ Parsing errors: {len(parsing_errors)} rows failed")
        
        if not colors:
            error_msg = "No valid rows could be parsed"
            logger.error(f"❌ {error_msg}")
            
            # Update history as failed
            history = get_upload_history()
            for h in history:
                if h["id"] == upload_id:
                    h["status"] = "failed"
                    h["error"] = error_msg
                    h["processing_time"] = start_time.isoformat()
                    break
            save_upload_history(history)
            
            # Remove from buffer
            mark_buffer_processed(upload_id, False, error_msg)
            
            return {
                "success": False,
                "upload_id": upload_id,
                "error": error_msg
            }
        
        logger.info(f"✅ Parsed {len(colors)} valid colors")
        
        # Apply ranking engine
        logger.info("📊 Applying ranking engine...")
        processed_colors = ranking_engine.run_colors(colors)
        logger.info(f"✅ Ranked {len(processed_colors)} colors")
        
        # Save to output file (marked as MANUAL)
        logger.info("💾 Saving to output file...")
        output_service.append_processed_colors(processed_colors, processing_type="MANUAL")
        logger.info(f"✅ Saved {len(processed_colors)} processed colors")
        
        # Update history as success
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        history = get_upload_history()
        for h in history:
            if h["id"] == upload_id:
                h["status"] = "success"
                h["processing_time"] = end_time.isoformat()
                h["duration_seconds"] = duration
                h["rows_processed"] = len(processed_colors)
                h["rows_valid"] = len(colors)
                h["message"] = f"Processed in scheduled run"
                break
        save_upload_history(history)
        
        # Remove from buffer
        mark_buffer_processed(upload_id, True)
        
        logger.info(f"✅ Buffered file processed successfully in {duration:.2f}s")
        
        return {
            "success": True,
            "upload_id": upload_id,
            "filename": filename,
            "rows_processed": len(processed_colors),
            "duration_seconds": duration
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Buffered file processing failed: {error_msg}")
        
        # Update history as failed
        history = get_upload_history()
        for h in history:
            if h["id"] == upload_id:
                h["status"] = "failed"
                h["error"] = error_msg
                h["processing_time"] = datetime.now().isoformat()
                break
        save_upload_history(history)
        
        # Remove from buffer
        mark_buffer_processed(upload_id, False, error_msg)
        
        return {
            "success": False,
            "upload_id": upload_id,
            "error": error_msg
        }


def get_upload_by_id(upload_id: int) -> Optional[Dict]:
    """Get single upload by ID"""
    history = get_upload_history()
    for upload in history:
        if upload["id"] == upload_id:
            return upload
    return None


def delete_upload_history(upload_id: int) -> bool:
    """Delete upload from history"""
    history = get_upload_history()
    
    # Find upload
    upload = None
    for u in history:
        if u["id"] == upload_id:
            upload = u
            break
    
    if not upload:
        return False
    
    # Delete file if exists
    if "file_path" in upload and os.path.exists(upload["file_path"]):
        try:
            os.remove(upload["file_path"])
            logger.info(f"🗑️ Deleted file: {upload['file_path']}")
        except Exception as e:
            logger.warning(f"Failed to delete file: {e}")
    
    # Remove from history
    history = [u for u in history if u["id"] != upload_id]
    save_upload_history(history)
    
    return True
