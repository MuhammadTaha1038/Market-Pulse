#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Output Service - Write processed colors to Excel file
This will be replaced with S3 integration in future milestone

TESTING MODE:
- File auto-clears if it exceeds 5 MB
- Keeps only last 100 existing records when appending
- Limits total records to 150 for fast testing
- In production with S3, these limits will be removed
"""
import pandas as pd
from typing import List
from datetime import datetime
from pathlib import Path
import logging
from models.color import ColorProcessed
import os

logger = logging.getLogger(__name__)


class OutputService:
    """
    Service for writing processed color data to output Excel file
    Future: Replace with S3 bucket integration
    """
    
    def __init__(self, output_file_path: str = None):
        """
        Initialize output service
        
        Args:
            output_file_path: Path to output Excel file
        """
        if output_file_path is None:
            # Store output in Data-main directory
            base_dir = Path(__file__).parent.parent.parent.parent.parent
            output_file_path = base_dir / "Processed_Colors_Output.xlsx"
        
        self.output_file_path = str(output_file_path)
        logger.info(f"OutputService initialized with output file: {self.output_file_path}")
        
        # Create file with headers if it doesn't exist
        self._initialize_output_file()
    
    def _initialize_output_file(self):
        """Create output file with headers if it doesn't exist or clear if too large"""
        # Check if file exists and is too large (> 5 MB)
        if os.path.exists(self.output_file_path):
            file_size_mb = os.path.getsize(self.output_file_path) / (1024 * 1024)
            if file_size_mb > 5:
                logger.warning(f"Output file is {file_size_mb:.2f} MB - creating fresh file for testing")
                os.remove(self.output_file_path)
        
        if not os.path.exists(self.output_file_path):
            logger.info("Creating new output file with headers")
            # Create empty DataFrame with all columns
            df = pd.DataFrame(columns=[
                'PROCESSED_AT',
                'PROCESSING_TYPE',
                'MESSAGE_ID',
                'TICKER',
                'SECTOR',
                'CUSIP',
                'DATE',
                'PRICE_LEVEL',
                'BID',
                'ASK',
                'PX',
                'SOURCE',
                'BIAS',
                'RANK',
                'COV_PRICE',
                'PERCENT_DIFF',
                'PRICE_DIFF',
                'CONFIDENCE',
                'DATE_1',
                'DIFF_STATUS',
                'IS_PARENT',
                'PARENT_MESSAGE_ID',
                'CHILDREN_COUNT'
            ])
            df.to_excel(self.output_file_path, index=False)
            logger.info(f"Created output file: {self.output_file_path}")
    
    def append_processed_colors(
        self, 
        colors: List[ColorProcessed], 
        processing_type: str = "AUTOMATED"
    ) -> int:
        """
        Append processed colors to output Excel file
        
        Args:
            colors: List of processed color data
            processing_type: "AUTOMATED" or "MANUAL" to track the source
            
        Returns:
            Number of records appended
        """
        if not colors:
            logger.warning("No colors to append")
            return 0
        
        logger.info(f"Appending {len(colors)} processed colors (type: {processing_type})")
        
        # Convert ColorProcessed objects to DataFrame
        records = []
        processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for color in colors:
            record = {
                'PROCESSED_AT': processed_at,
                'PROCESSING_TYPE': processing_type,
                'MESSAGE_ID': color.message_id,
                'TICKER': color.ticker,
                'SECTOR': color.sector,
                'CUSIP': color.cusip,
                'DATE': color.date.strftime("%Y-%m-%d") if color.date else None,
                'PRICE_LEVEL': color.price_level,
                'BID': color.bid,
                'ASK': color.ask,
                'PX': color.px,
                'SOURCE': color.source,
                'BIAS': color.bias,
                'RANK': color.rank,
                'COV_PRICE': color.cov_price,
                'PERCENT_DIFF': color.percent_diff,
                'PRICE_DIFF': color.price_diff,
                'CONFIDENCE': color.confidence,
                'DATE_1': color.date_1.strftime("%Y-%m-%d") if color.date_1 else None,
                'DIFF_STATUS': color.diff_status,
                'IS_PARENT': color.is_parent,
                'PARENT_MESSAGE_ID': color.parent_message_id,
                'CHILDREN_COUNT': color.children_count
            }
            records.append(record)
        
        new_df = pd.DataFrame(records)
        
        # Read existing data
        try:
            existing_df = pd.read_excel(self.output_file_path)
            logger.info(f"Existing records: {len(existing_df)}")
            
            # Keep only last 100 records for testing (prevent file bloat)
            if len(existing_df) > 100:
                logger.info(f"Keeping only last 100 records (was {len(existing_df)})")
                existing_df = existing_df.tail(100)
        except Exception as e:
            logger.warning(f"Could not read existing file: {e}. Creating new one.")
            existing_df = pd.DataFrame()
        
        # Append new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Limit to 150 total records for testing
        if len(combined_df) > 150:
            logger.info(f"Trimming to 150 records (was {len(combined_df)})")
            combined_df = combined_df.tail(150)
        
        # Write back to Excel
        combined_df.to_excel(self.output_file_path, index=False)
        
        logger.info(f"✅ Appended {len(records)} records. Total records: {len(combined_df)}")
        return len(records)
    
    def get_processed_count(self) -> dict:
        """
        Get statistics about processed data
        
        Returns:
            Dictionary with counts by processing type
        """
        try:
            df = pd.read_excel(self.output_file_path)
            
            total = len(df)
            automated = len(df[df['PROCESSING_TYPE'] == 'AUTOMATED'])
            manual = len(df[df['PROCESSING_TYPE'] == 'MANUAL'])
            parents = len(df[df['IS_PARENT'] == True])
            children = len(df[df['IS_PARENT'] == False])
            
            return {
                'total_processed': total,
                'automated': automated,
                'manual': manual,
                'parents': parents,
                'children': children,
                'output_file': self.output_file_path
            }
        except Exception as e:
            logger.error(f"Error reading output file: {e}")
            return {
                'total_processed': 0,
                'automated': 0,
                'manual': 0,
                'parents': 0,
                'children': 0,
                'output_file': self.output_file_path
            }
    
    def clear_output_file(self):
        """Clear all data from output file (keep headers)"""
        logger.warning("Clearing output file")
        self._initialize_output_file()
        logger.info("Output file cleared")
    
    def read_processed_colors(
        self, 
        processing_type: str = None,
        limit: int = None,
        cusip: str = None,
        ticker: str = None,
        message_id: int = None,
        date_from: str = None,
        date_to: str = None
    ) -> List[dict]:
        """
        Read processed colors from output Excel file (or S3 in future)
        
        **S3 MIGRATION NOTE:**
        When migrating to S3:
        1. Replace pd.read_excel() with boto3.client('s3').get_object()
        2. Use S3 Select for server-side filtering (faster)
        3. Apply same filters to S3 query for consistency
        
        Args:
            processing_type: Filter by "AUTOMATED" or "MANUAL" (None = all)
            limit: Maximum number of records to return
            cusip: Filter by specific CUSIP
            ticker: Filter by ticker symbol
            message_id: Filter by message ID
            date_from: Start date filter (YYYY-MM-DD)
            date_to: End date filter (YYYY-MM-DD)
            
        Returns:
            List of color dictionaries
        """
        try:
            # PERFORMANCE OPTIMIZATION: Only read what we need
            # If limit is small (< 100), read only a reasonable chunk
            if limit and limit < 100:
                # Read only 10x the limit to account for filtering
                # This dramatically speeds up queries for small previews
                nrows_to_read = min(limit * 10, 2000)
                logger.info(f"PERFORMANCE: Reading only {nrows_to_read} rows for limit={limit}")
                df = pd.read_excel(self.output_file_path, nrows=nrows_to_read)
            else:
                # For larger requests or no limit, read everything (slower)
                logger.info("Reading all rows from output file")
                df = pd.read_excel(self.output_file_path)
            
            if len(df) == 0:
                logger.warning("Output file is empty")
                return []
            
            logger.info(f"Initial data loaded: {len(df)} rows")
            
            # Apply filters (in S3, these would be in the query itself)
            if processing_type:
                df = df[df['PROCESSING_TYPE'] == processing_type]
                logger.info(f"After processing_type filter: {len(df)} rows")
            
            if cusip:
                df = df[df['CUSIP'].str.upper() == cusip.upper()]
                logger.info(f"After cusip filter: {len(df)} rows")
            
            if ticker:
                df = df[df['TICKER'].str.upper() == ticker.upper()]
                logger.info(f"After ticker filter: {len(df)} rows")
            
            if message_id:
                df = df[df['MESSAGE_ID'] == message_id]
                logger.info(f"After message_id filter: {len(df)} rows")
            
            # Date range filtering
            if date_from or date_to:
                df['DATE_PARSED'] = pd.to_datetime(df['DATE'], errors='coerce')
                if date_from:
                    df = df[df['DATE_PARSED'] >= pd.to_datetime(date_from)]
                if date_to:
                    df = df[df['DATE_PARSED'] <= pd.to_datetime(date_to)]
                df = df.drop('DATE_PARSED', axis=1)
                logger.info(f"After date range filter: {len(df)} rows")
            
            # Sort by most recent date first (primary), then processed time (secondary)
            if 'DATE' in df.columns:
                df['DATE_PARSED'] = pd.to_datetime(df['DATE'], errors='coerce')
                if 'PROCESSED_AT' in df.columns:
                    df['PROCESSED_AT_PARSED'] = pd.to_datetime(df['PROCESSED_AT'], errors='coerce')
                    df = df.sort_values(['DATE_PARSED', 'PROCESSED_AT_PARSED'], ascending=[False, False])
                    df = df.drop('PROCESSED_AT_PARSED', axis=1)
                else:
                    df = df.sort_values('DATE_PARSED', ascending=False)
                df = df.drop('DATE_PARSED', axis=1)
                logger.info("Sorted by DATE (most recent first)")
            elif 'PROCESSED_AT' in df.columns:
                # Fallback if DATE column missing
                df = df.sort_values('PROCESSED_AT', ascending=False)
                logger.info("Sorted by PROCESSED_AT (fallback)")
            
            # Apply limit
            if limit:
                df = df.head(limit)
            
            # Convert to list of dicts
            records = df.to_dict('records')
            
            logger.info(f"✅ Returning {len(records)} processed colors")
            return records
            
        except Exception as e:
            logger.error(f"Error reading processed colors: {e}")
            return []


# Singleton instance
_output_service_instance = None

def get_output_service() -> OutputService:
    """Get singleton output service instance"""
    global _output_service_instance
    if _output_service_instance is None:
        _output_service_instance = OutputService()
    return _output_service_instance
