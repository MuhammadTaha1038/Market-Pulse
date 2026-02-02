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
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=500, description="Number of records to return (default 10 for performance, max 500 for filtering)"),
    
    # CLO-based column filtering
    clo_id: Optional[str] = Query(None, description="CLO ID for column visibility filtering"),
    
    # Search filters - All optional for flexible searching
    cusip: Optional[str] = Query(None, description="Filter by CUSIP (exact match)"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol (exact match)"),
    message_id: Optional[int] = Query(None, description="Filter by message ID"),
    asset_class: Optional[str] = Query(None, description="Filter by asset class/sector"),
    source: Optional[str] = Query(None, description="Filter by source (e.g., TRACE, BLOOMBERG)"),
    bias: Optional[str] = Query(None, description="Filter by bias (e.g., BUY_BIAS, SELL_BIAS)"),
    processing_type: Optional[str] = Query(None, description="Filter by processing type (AUTOMATED or MANUAL)"),
    
    # Date range filters
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    **Advanced Search API for Processed Colors**
    
    **Storage:** Currently Excel, will migrate to Oracle database in production
    
    **Search by any combination of:**
    - CUSIP (exact match)
    - Ticker (exact match)  
    - Message ID (exact match)
    - Asset Class/Sector
    - Source (TRACE, BLOOMBERG, etc.)
    - Bias (BUY_BIAS, SELL_BIAS, etc.)
    - Processing Type (AUTOMATED or MANUAL)
    - Date Range (from/to)
    
    **Performance:** Default limit=10 for fast preview. Use pagination for larger datasets.
    
    **Oracle Ready:** Column filtering at query level for production.
    Currently reads from Excel, will migrate to Oracle SELECT with visible columns.
    
    **Returns:** Paginated list of processed colors with total count
    """
    try:
        # Get visible columns for CLO if provided (for Oracle query compatibility)
        visible_columns = None
        if clo_id:
            from services.clo_mapping_service import CLOMappingService
            clo_service = CLOMappingService()
            user_columns = clo_service.get_user_columns(clo_id)
            if user_columns:
                visible_columns = user_columns.get('visible_columns', [])
                logger.info(f"CLO '{clo_id}' visible columns: {visible_columns}")
        
        # Build filter dictionary for logging
        filters = {
            "clo_id": clo_id,
            "cusip": cusip,
            "ticker": ticker,
            "message_id": message_id,
            "asset_class": asset_class,
            "source": source,
            "bias": bias,
            "processing_type": processing_type,
            "date_from": date_from,
            "date_to": date_to
        }
        active_filters = {k: v for k, v in filters.items() if v is not None}
        logger.info(f"Search request: skip={skip}, limit={limit}, filters={active_filters}")
        
        # Read data with performance optimization
        # In production with Oracle, this will be:
        # ----------------------------------------------------------------
        # if visible_columns:
        #     columns_sql = ', '.join(visible_columns)
        # else:
        #     columns_sql = '*'
        # 
        # query = f"""
        #     SELECT {columns_sql}, IS_PARENT, PARENT_MESSAGE_ID, CHILDREN_COUNT
        #     FROM MARKET_COLORS 
        #     WHERE 1=1
        #     {'AND CUSIP = :cusip' if cusip else ''}
        #     {'AND TICKER = :ticker' if ticker else ''}
        #     {'AND SOURCE = :source' if source else ''}
        #     ORDER BY DATE DESC
        #     OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY
        # """
        # ----------------------------------------------------------------
        max_read = min(limit * 10, 1000)  # Read buffer for filtering
        processed_records = output_service.read_processed_colors(
            limit=max_read,
            processing_type=processing_type,
            cusip=cusip
        )
        
        if not processed_records:
            logger.warning("No processed colors found in output file")
            return ColorResponse(
                total_count=0,
                page=1,
                page_size=limit,
                colors=[]
            )
        
        logger.info(f"Read {len(processed_records)} records from output file/S3")
        
        # Apply additional filters
        # When migrating to S3, move these filters to S3 query for better performance
        if ticker:
            processed_records = [r for r in processed_records if r.get('TICKER', '').upper() == ticker.upper()]
            logger.info(f"Filtered by ticker '{ticker}': {len(processed_records)} records")
        
        if message_id:
            processed_records = [r for r in processed_records if r.get('MESSAGE_ID') == message_id]
            logger.info(f"Filtered by message_id {message_id}: {len(processed_records)} records")
        
        if asset_class:
            processed_records = [r for r in processed_records if r.get('SECTOR', '').upper() == asset_class.upper()]
            logger.info(f"Filtered by asset_class '{asset_class}': {len(processed_records)} records")
        
        if source:
            processed_records = [r for r in processed_records if r.get('SOURCE', '').upper() == source.upper()]
            logger.info(f"Filtered by source '{source}': {len(processed_records)} records")
        
        if bias:
            processed_records = [r for r in processed_records if r.get('BIAS', '').upper() == bias.upper()]
            logger.info(f"Filtered by bias '{bias}': {len(processed_records)} records")
        
        # Date range filtering
        if date_from or date_to:
            filtered = []
            for r in processed_records:
                try:
                    record_date = pd.to_datetime(r.get('DATE'))
                    include = True
                    if date_from:
                        include = include and record_date >= pd.to_datetime(date_from)
                    if date_to:
                        include = include and record_date <= pd.to_datetime(date_to)
                    if include:
                        filtered.append(r)
                except:
                    continue
            processed_records = filtered
            logger.info(f"Filtered by date range: {len(processed_records)} records")
        
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
                
                # Build color object - only include visible columns if CLO filter is active
                # This simulates: SELECT [visible_columns] FROM table
                color_data = {
                    'message_id': safe_int(record.get('MESSAGE_ID'), 0),
                    'ticker': str(record.get('TICKER', '')),
                    'sector': str(record.get('SECTOR', '')),
                    'cusip': str(record.get('CUSIP', '')),
                    'date': date_val,
                    'price_level': safe_float(record.get('PRICE_LEVEL'), 0.0),
                    'bid': safe_float(record.get('BID'), 0.0),
                    'ask': safe_float(record.get('ASK'), 0.0),
                    'px': safe_float(record.get('PX'), 0.0),
                    'source': str(record.get('SOURCE', '')),
                    'bias': str(record.get('BIAS', '')),
                    'rank': safe_int(record.get('RANK'), 5),
                    'cov_price': safe_float(record.get('COV_PRICE'), 0.0),
                    'percent_diff': safe_float(record.get('PERCENT_DIFF'), 0.0),
                    'price_diff': safe_float(record.get('PRICE_DIFF'), 0.0),
                    'confidence': safe_int(record.get('CONFIDENCE'), 5),
                    'date_1': date_1_val,
                    'diff_status': str(record.get('DIFF_STATUS', '')),
                    'is_parent': bool(record.get('IS_PARENT', False)),
                    'parent_message_id': safe_int(record.get('PARENT_MESSAGE_ID')) if not pd.isna(record.get('PARENT_MESSAGE_ID')) else None,
                    'children_count': safe_int(record.get('CHILDREN_COUNT'), 0)
                }
                
                # Filter columns if CLO visibility is active (simulates Oracle column filtering)
                if visible_columns:
                    # Only include columns that are in visible_columns list
                    # Map frontend column names to model field names
                    column_mapping = {
                        'MESSAGE_ID': 'message_id',
                        'TICKER': 'ticker',
                        'SECTOR': 'sector',
                        'CUSIP': 'cusip',
                        'DATE': 'date',
                        'PRICE_LEVEL': 'price_level',
                        'BID': 'bid',
                        'ASK': 'ask',
                        'PX': 'px',
                        'SOURCE': 'source',
                        'BIAS': 'bias',
                        'RANK': 'rank',
                        'COV_PRICE': 'cov_price',
                        'PERCENT_DIFF': 'percent_diff',
                        'PRICE_DIFF': 'price_diff',
                        'CONFIDENCE': 'confidence',
                        'DATE_1': 'date_1',
                        'DIFF_STATUS': 'diff_status'
                    }
                    
                    # Build filtered data - only visible columns
                    filtered_data = {}
                    for oracle_col in visible_columns:
                        model_field = column_mapping.get(oracle_col)
                        if model_field and model_field in color_data:
                            filtered_data[model_field] = color_data[model_field]
                    
                    # Always include system fields for table functionality
                    filtered_data['is_parent'] = color_data['is_parent']
                    filtered_data['parent_message_id'] = color_data['parent_message_id']
                    filtered_data['children_count'] = color_data['children_count']
                    
                    color_data = filtered_data
                
                color = ColorProcessed(**color_data)
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
