#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dashboard Router - APIs for Angular frontend dashboard
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging
import os
import sys
import pandas as pd
from models.color import ColorResponse, MonthlyStatsResponse, MonthlyStats
from services.database_service import DatabaseService
from services.ranking_engine import RankingEngine
from services.output_service import get_output_service

# Import rules service for exclusion logic
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rules_service import apply_rules

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Initialize services
db_service = DatabaseService()
ranking_engine = RankingEngine()
output_service = get_output_service()


@router.get("/monthly-stats", response_model=MonthlyStatsResponse)
async def get_monthly_stats(
    asset_class: Optional[str] = Query(None, description="Filter by asset class/sector")
):
    """
    Get monthly color statistics for dashboard chart
    
    Returns last 12 months of data with color counts
    Used by Angular frontend for the bar chart
    """
    try:
        logger.info(f"Fetching monthly stats for asset_class: {asset_class}")
        
        # Fetch monthly statistics
        stats_data = db_service.fetch_monthly_stats(months=12)
        
        # Convert to Pydantic models
        stats = [MonthlyStats(**stat) for stat in stats_data]
        
        logger.info(f"Returning {len(stats)} months of statistics")
        return MonthlyStatsResponse(stats=stats)
        
    except Exception as e:
        logger.error(f"Error fetching monthly stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/colors", response_model=ColorResponse)
async def get_todays_colors(
    asset_class: Optional[str] = Query(None, description="Filter by asset class/sector"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """
    Get processed colors from output file (S3 in production)
    
    This endpoint:
    1. Reads PROCESSED colors from output Excel file
    2. Filters by asset class if specified
    3. Returns parent-child hierarchy with pagination
    
    Note: This shows FINAL processed data (after ranking, rules applied)
    Both AUTOMATED (from Oracle + cron jobs) and MANUAL uploads are included
    """
    try:
        logger.info(f"Fetching processed colors: asset_class={asset_class}, skip={skip}, limit={limit}")
        
        # Read processed colors from output file (replaces S3 in production)
        processed_records = output_service.read_processed_colors(limit=5000)  # Get recent 5000
        
        if not processed_records:
            logger.warning("No processed colors found in output file")
            return ColorResponse(
                total_count=0,
                page=1,
                page_size=limit,
                colors=[]
            )
        
        logger.info(f"Read {len(processed_records)} processed colors from output file")
        
        # Filter by asset class if specified
        if asset_class:
            processed_records = [r for r in processed_records if r.get('SECTOR') == asset_class]
            logger.info(f"Filtered to {len(processed_records)} colors for sector: {asset_class}")
        
        # Convert to ColorProcessed objects for the response
        from models.color import ColorProcessed
        processed_colors = []
        
        for record in processed_records:
            try:
                # Parse dates safely
                date_val = pd.to_datetime(record.get('DATE')) if record.get('DATE') else None
                date_1_val = pd.to_datetime(record.get('DATE_1')) if record.get('DATE_1') else date_val
                
                # Handle NaN values safely
                def safe_int(val, default=0):
                    if pd.isna(val) or val is None:
                        return default
                    return int(float(val))
                
                def safe_float(val, default=0.0):
                    if pd.isna(val) or val is None:
                        return default
                    return float(val)
                
                color = ColorProcessed(
                    message_id=safe_int(record.get('MESSAGE_ID'), 0),
                    ticker=str(record.get('TICKER', '')),
                    sector=str(record.get('SECTOR', '')),
                    cusip=str(record.get('CUSIP', '')),
                    date=date_val,
                    price_level=safe_float(record.get('PRICE_LEVEL'), 0.0),
                    bid=safe_float(record.get('BID'), 0.0),
                    ask=safe_float(record.get('ASK'), 0.0),
                    px=safe_float(record.get('PX'), 0.0),
                    source=str(record.get('SOURCE', '')),
                    bias=str(record.get('BIAS', '')),
                    rank=safe_int(record.get('RANK'), 5),
                    cov_price=safe_float(record.get('COV_PRICE'), 0.0),
                    percent_diff=safe_float(record.get('PERCENT_DIFF'), 0.0),
                    price_diff=safe_float(record.get('PRICE_DIFF'), 0.0),
                    confidence=safe_int(record.get('CONFIDENCE'), 5),
                    date_1=date_1_val,
                    diff_status=str(record.get('DIFF_STATUS', '')),
                    is_parent=bool(record.get('IS_PARENT', False)),
                    parent_message_id=safe_int(record.get('PARENT_MESSAGE_ID')) if not pd.isna(record.get('PARENT_MESSAGE_ID')) else None,
                    children_count=safe_int(record.get('CHILDREN_COUNT'), 0)
                )
                processed_colors.append(color)
            except Exception as e:
                logger.warning(f"Skipping invalid record: {e}")
                continue
        
        # Apply pagination
        total_count = len(processed_colors)
        paginated_colors = processed_colors[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_colors)} of {total_count} processed colors")
        
        return ColorResponse(
            total_count=total_count,
            page=(skip // limit) + 1,
            page_size=limit,
            colors=paginated_colors
        )
        
    except Exception as e:
        logger.error(f"Error fetching processed colors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/next-run")
async def get_next_run_time():
    """
    Get next scheduled automation run time
    
    Returns countdown timer for frontend display
    For Milestone 1: Returns mock data
    In Milestone 2: Will read from cron job schedule
    """
    try:
        # Mock data for Milestone 1
        # Will be replaced with actual cron job schedule in Milestone 2
        return {
            "next_run": "7H:52M:25S",
            "next_run_timestamp": "2026-01-16T10:00:00Z",
            "status": "scheduled"
        }
        
    except Exception as e:
        logger.error(f"Error fetching next run time: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-sectors")
async def get_available_sectors():
    """
    Get list of all available asset classes/sectors
    
    Used by frontend for filtering dropdowns
    """
    try:
        sectors = db_service.get_available_sectors()
        return {
            "sectors": sectors,
            "count": len(sectors)
        }
    except Exception as e:
        logger.error(f"Error fetching sectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/output-stats")
async def get_output_statistics():
    """
    Get statistics about processed colors in output Excel file
    
    Returns counts of automated vs manual processing, parents vs children
    """
    try:
        stats = output_service.get_processed_count()
        logger.info(f"Output stats: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error fetching output statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
