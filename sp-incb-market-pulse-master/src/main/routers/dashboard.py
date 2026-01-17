#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dashboard Router - APIs for Angular frontend dashboard
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging
from models.color import ColorResponse, MonthlyStatsResponse, MonthlyStats
from services.database_service import DatabaseService
from services.ranking_engine import RankingEngine
from services.output_service import get_output_service

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
    Get today's colors with parent-child hierarchy
    
    This endpoint:
    1. Fetches raw colors from database
    2. Applies ranking algorithm (DATE > RANK > PX)
    3. Returns parent-child hierarchy
    
    Used by Angular frontend to display the main data table
    """
    try:
        logger.info(f"Fetching colors: asset_class={asset_class}, skip={skip}, limit={limit}")
        
        # Fetch raw colors from database
        asset_classes = [asset_class] if asset_class else None
        raw_colors = db_service.fetch_all_colors(asset_classes=asset_classes)
        
        if not raw_colors:
            logger.warning("No colors found")
            return ColorResponse(
                total_count=0,
                page=1,
                page_size=limit,
                colors=[]
            )
        
        # Apply ranking algorithm
        logger.info(f"Applying ranking engine to {len(raw_colors)} colors")
        processed_colors = ranking_engine.run_colors(raw_colors)
        
        # Save processed colors to output Excel (AUTOMATED type)
        logger.info("Saving processed colors to output file")
        saved_count = output_service.append_processed_colors(processed_colors, processing_type="AUTOMATED")
        logger.info(f"✅ Saved {saved_count} processed colors to Excel")
        
        # Apply pagination
        total_count = len(processed_colors)
        paginated_colors = processed_colors[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_colors)} of {total_count} colors")
        
        return ColorResponse(
            total_count=total_count,
            page=(skip // limit) + 1,
            page_size=limit,
            colors=paginated_colors
        )
        
    except Exception as e:
        logger.error(f"Error fetching colors: {e}")
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
