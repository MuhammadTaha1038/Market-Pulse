#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Output Service - Write processed colors to Excel file
This will be replaced with S3 integration in future milestone
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
        """Create output file with headers if it doesn't exist"""
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
        except Exception as e:
            logger.warning(f"Could not read existing file: {e}. Creating new one.")
            existing_df = pd.DataFrame()
        
        # Append new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
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


# Singleton instance
_output_service_instance = None

def get_output_service() -> OutputService:
    """Get singleton output service instance"""
    global _output_service_instance
    if _output_service_instance is None:
        _output_service_instance = OutputService()
    return _output_service_instance
