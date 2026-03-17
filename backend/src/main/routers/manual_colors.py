#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manual Color Router - APIs for manual color import and processing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging
import pandas as pd
from io import BytesIO
from models.color import ColorRaw, ColorProcessed
from services.ranking_engine import RankingEngine
from services.output_service import get_output_service
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manual", tags=["Manual Colors"])

# Initialize services
ranking_engine = RankingEngine()
output_service = get_output_service()


@router.post("/upload-excel")
async def upload_manual_colors(file: UploadFile = File(...)):
    """
    Upload Excel file with manual colors for processing
    
    Accepts Excel file, parses it, and returns the raw data for frontend review
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        logger.info(f"Uploading manual color file: {file.filename}")
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        logger.info(f"Loaded {len(df)} rows from Excel")
        
        # Convert to ColorRaw objects (basic validation)
        colors = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                color = ColorRaw(
                    message_id=int(row['MESSAGE_ID']),
                    ticker=str(row['TICKER']),
                    sector=str(row['SECTOR']),
                    cusip=str(row['CUSIP']),
                    date=pd.to_datetime(row['DATE']),
                    price_level=float(row['PRICE_LEVEL']),
                    bid=float(row['BID']) if pd.notna(row['BID']) else 0.0,
                    ask=float(row['ASK']) if pd.notna(row['ASK']) else 0.0,
                    px=float(row['PX']),
                    source=str(row['SOURCE']),
                    bias=str(row['BIAS']),
                    rank=int(row['RANK']),
                    cov_price=float(row['COV_PRICE']) if pd.notna(row['COV_PRICE']) else 0.0,
                    percent_diff=float(row['PERCENT_DIFF']) if pd.notna(row['PERCENT_DIFF']) else 0.0,
                    price_diff=float(row['PRICE_DIFF']) if pd.notna(row['PRICE_DIFF']) else 0.0,
                    confidence=int(row.get('CONFIDENCE', 5)),
                    date_1=pd.to_datetime(row['DATE']) if 'DATE_1' not in row else pd.to_datetime(row['DATE_1']),
                    diff_status=str(row.get('DIFF_STATUS', ''))
                )
                colors.append(color)
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        if errors:
            logger.warning(f"Parsing errors: {errors[:5]}")  # Log first 5 errors
        
        logger.info(f"✅ Parsed {len(colors)} valid colors")
        
        return {
            "success": True,
            "filename": file.filename,
            "total_rows": len(df),
            "valid_colors": len(colors),
            "errors_count": len(errors),
            "errors": errors[:10],  # Return first 10 errors
            "colors": [color.model_dump() for color in colors]
        }
        
    except Exception as e:
        logger.error(f"Error uploading manual colors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-manual-colors")
async def process_manual_colors(colors: List[dict]):
    """
    Process manually uploaded colors through ranking engine
    
    Takes list of color objects (after user review/edit/delete)
    Applies ranking algorithm and saves to output Excel
    """
    try:
        logger.info(f"Processing {len(colors)} manual colors")
        
        # Convert dicts to ColorRaw objects
        raw_colors = []
        for color_data in colors:
            try:
                color = ColorRaw(**color_data)
                raw_colors.append(color)
            except Exception as e:
                logger.warning(f"Skipping invalid color: {e}")
        
        if not raw_colors:
            raise HTTPException(status_code=400, detail="No valid colors to process")
        
        # Apply ranking algorithm
        logger.info(f"Applying ranking engine to {len(raw_colors)} manual colors")
        processed_colors = ranking_engine.run_colors(raw_colors)
        
        # Save to output Excel with MANUAL type
        saved_count = output_service.append_processed_colors(processed_colors, processing_type="MANUAL")
        
        logger.info(f"✅ Processed and saved {saved_count} manual colors")
        
        return {
            "success": True,
            "input_count": len(colors),
            "processed_count": saved_count,
            "parents": sum(1 for c in processed_colors if c.is_parent),
            "children": sum(1 for c in processed_colors if not c.is_parent),
            "message": f"Successfully processed {saved_count} manual colors"
        }
        
    except Exception as e:
        logger.error(f"Error processing manual colors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-output")
async def clear_output_file():
    """
    Clear all processed data from output Excel file
    
    WARNING: This will delete all processed colors (both automated and manual)
    """
    try:
        logger.warning("Clearing output file - requested by user")
        output_service.clear_output_file()
        
        return {
            "success": True,
            "message": "Output file cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing output file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
