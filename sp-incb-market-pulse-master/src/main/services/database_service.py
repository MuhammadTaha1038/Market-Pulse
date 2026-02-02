#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database Service - Data fetching abstraction layer

FULLY ABSTRACTED - Configuration-based switching:
==================================================
Input Source (RAW data):
- Excel: Set DATA_SOURCE=excel in .env
- Oracle: Set DATA_SOURCE=oracle in .env

This service now uses the data_source_factory pattern for complete abstraction.
No code changes needed - just update .env file!
==================================================
"""
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
from models.color import ColorRaw
from services.column_config_service import get_column_config
from services.data_source_factory import get_data_source

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Database operations for RAW color data (input source)
    Uses data_source_factory for abstraction - configured via .env
    """
    
    def __init__(self, clo_id: Optional[str] = None):
        """
        Initialize database service with abstracted data source
        
        Args:
            clo_id: Optional CLO identifier for column mapping
        """
        # Column configuration service
        self.column_config = get_column_config()
        
        # Get configured data source (Excel or Oracle based on .env)
        self.data_source = get_data_source()
        self.clo_id = clo_id
        
        # Data cache (for Excel mode performance)
        self._data_cache = None
        
        source_info = self.data_source.get_source_info()
        logger.info(f"DatabaseService initialized with {source_info['type']} data source")
    
    def _load_data(self) -> pd.DataFrame:
        """
        Load RAW data from configured source (Excel or Oracle)
        Uses abstraction layer for automatic source selection
        """
        source_info = self.data_source.get_source_info()
        
        # Use caching for Excel, fresh data for Oracle
        if source_info['type'] == 'Excel':
            if self._data_cache is None:
                logger.info("Fetching data from Excel data source")
                self._data_cache = self.data_source.fetch_data(clo_id=self.clo_id)
                logger.info(f"✅ Loaded {len(self._data_cache)} records from Excel (cached)")
            return self._data_cache
        else:
            # Oracle or other sources - always fetch fresh
            logger.info("Fetching fresh data from Oracle data source")
            df = self.data_source.fetch_data(clo_id=self.clo_id)
            logger.info(f"✅ Loaded {len(df)} records from Oracle")
            return df
    
    def fetch_all_colors(self, asset_classes: Optional[List[str]] = None) -> List[ColorRaw]:
        """
        Fetch all colors, optionally filtered by asset classes
        
        Args:
            asset_classes: List of sectors to filter (e.g., ['MM-CLO', '2.0_Mezz'])
            
        Returns:
            List of ColorRaw objects
        """
        df = self._load_data()
        
        # Filter by asset classes if provided
        if asset_classes:
            df = df[df['SECTOR'].isin(asset_classes)]
            logger.info(f"Filtered to {len(df)} records for sectors: {asset_classes}")
        
        # Convert to ColorRaw objects
        colors = []
        for _, row in df.iterrows():
            try:
                color = ColorRaw(
                    message_id=int(row['MESSAGE_ID']),
                    ticker=str(row['TICKER']),
                    sector=str(row['SECTOR']),
                    cusip=str(row['CUSIP']),
                    date=pd.to_datetime(row['DATE']),
                    price_level=float(row['PRICE_LEVEL']),
                    bid=float(row['BID']),
                    ask=float(row['ASK']),
                    px=float(row['PX']),
                    source=str(row['SOURCE']),
                    bias=str(row['BIAS']),
                    rank=int(row['RANK']),
                    cov_price=float(row['COV_PRICE']),
                    percent_diff=float(row['PERCENT_DIFF']),
                    price_diff=float(row['PRICE_DIFF']),
                    confidence=int(row['CONFIDENCE']),
                    date_1=pd.to_datetime(row['DATE_1']),
                    diff_status=str(row['DIFF_STATUS'])
                )
                colors.append(color)
            except Exception as e:
                logger.error(f"Error converting row {row.get('MESSAGE_ID')}: {e}")
                continue
        
        logger.info(f"Converted {len(colors)} records to ColorRaw objects")
        return colors
    
    def fetch_colors_by_cusip(self, cusip_list: List[str]) -> List[ColorRaw]:
        """
        Fetch colors for specific CUSIPs
        
        Args:
            cusip_list: List of CUSIP identifiers
            
        Returns:
            List of ColorRaw objects
        """
        df = self._load_data()
        df_filtered = df[df['CUSIP'].isin(cusip_list)]
        
        logger.info(f"Found {len(df_filtered)} colors for {len(cusip_list)} CUSIPs")
        
        colors = []
        for _, row in df_filtered.iterrows():
            try:
                color = ColorRaw(
                    message_id=int(row['MESSAGE_ID']),
                    ticker=str(row['TICKER']),
                    sector=str(row['SECTOR']),
                    cusip=str(row['CUSIP']),
                    date=pd.to_datetime(row['DATE']),
                    price_level=float(row['PRICE_LEVEL']),
                    bid=float(row['BID']),
                    ask=float(row['ASK']),
                    px=float(row['PX']),
                    source=str(row['SOURCE']),
                    bias=str(row['BIAS']),
                    rank=int(row['RANK']),
                    cov_price=float(row['COV_PRICE']),
                    percent_diff=float(row['PERCENT_DIFF']),
                    price_diff=float(row['PRICE_DIFF']),
                    confidence=int(row['CONFIDENCE']),
                    date_1=pd.to_datetime(row['DATE_1']),
                    diff_status=str(row['DIFF_STATUS'])
                )
                colors.append(color)
            except Exception as e:
                logger.error(f"Error converting row: {e}")
                continue
        
        return colors
    
    def fetch_colors_by_message_id(self, message_ids: List[int]) -> List[ColorRaw]:
        """
        Fetch colors by message IDs
        
        Args:
            message_ids: List of message IDs
            
        Returns:
            List of ColorRaw objects
        """
        df = self._load_data()
        df_filtered = df[df['MESSAGE_ID'].isin(message_ids)]
        
        logger.info(f"Found {len(df_filtered)} colors for {len(message_ids)} message IDs")
        
        colors = []
        for _, row in df_filtered.iterrows():
            try:
                color = ColorRaw(
                    message_id=int(row['MESSAGE_ID']),
                    ticker=str(row['TICKER']),
                    sector=str(row['SECTOR']),
                    cusip=str(row['CUSIP']),
                    date=pd.to_datetime(row['DATE']),
                    price_level=float(row['PRICE_LEVEL']),
                    bid=float(row['BID']),
                    ask=float(row['ASK']),
                    px=float(row['PX']),
                    source=str(row['SOURCE']),
                    bias=str(row['BIAS']),
                    rank=int(row['RANK']),
                    cov_price=float(row['COV_PRICE']),
                    percent_diff=float(row['PERCENT_DIFF']),
                    price_diff=float(row['PRICE_DIFF']),
                    confidence=int(row['CONFIDENCE']),
                    date_1=pd.to_datetime(row['DATE_1']),
                    diff_status=str(row['DIFF_STATUS'])
                )
                colors.append(color)
            except Exception as e:
                logger.error(f"Error converting row: {e}")
                continue
        
        return colors
    
    def fetch_monthly_stats(self, months: int = 12) -> List[dict]:
        """
        Get color count by month for dashboard chart from PROCESSED output data
        Reads from configured destination (local Excel or S3)
        
        Args:
            months: Number of months to look back
            
        Returns:
            List of {"month": "2026-01", "count": 1234}
        """
        try:
            # Read from PROCESSED data (using abstraction for local or S3)
            from services.processed_data_reader import get_processed_data_reader
            reader = get_processed_data_reader()
            
            # Read ALL processed colors to count by month
            df_output = reader.read_processed_data()
            
            if len(df_output) == 0:
                logger.warning("No data in processed output for monthly stats")
                return []
            
            logger.info(f"Computing monthly stats from {len(df_output)} processed records")
            
            # Use PROCESSED_AT or DATE column for grouping
            date_column = 'PROCESSED_AT' if 'PROCESSED_AT' in df_output.columns else 'DATE'
            
            # Convert to datetime and extract month
            df_output['month'] = pd.to_datetime(df_output[date_column], errors='coerce').dt.strftime('%Y-%m')
            
            # Group by month and count
            monthly_counts = df_output.groupby('month').size().reset_index(name='count')
            monthly_counts = monthly_counts.sort_values('month')
            
            # Get last N months
            if len(monthly_counts) > months:
                monthly_counts = monthly_counts.tail(months)
            
            # Convert to list of dicts
            result = []
            for _, row in monthly_counts.iterrows():
                if pd.notna(row['month']):  # Skip null months
                    result.append({
                        "month": str(row['month']),
                        "count": int(row['count'])
                    })
            
            logger.info(f"Returning {len(result)} months of stats")
            return result
            
        except Exception as e:
            logger.error(f"Error computing monthly stats: {e}")
            return []
    
    def get_available_sectors(self) -> List[str]:
        """
        Get list of all available sectors/asset classes
        
        Returns:
            List of sector names
        """
        df = self._load_data()
        sectors = df['SECTOR'].unique().tolist()
        logger.info(f"Found {len(sectors)} sectors: {sectors}")
        return sectors
    
    def enable_oracle(self, oracle_config: dict):
        """
        Switch from Excel to Oracle mode
        
        Args:
            oracle_config: Dictionary with host, port, service_name, user, password
        """
        if not ORACLE_AVAILABLE:
            raise RuntimeError("Oracle driver not installed. Install: pip install oracledb")
        
        logger.info("Switching to Oracle mode")
        self.oracle_config = oracle_config
        self.use_oracle = True
        self._data_cache = None  # Clear Excel cache
        
        # Test connection
        try:
            connection = self._get_oracle_connection()
            connection.close()
            logger.info("✅ Oracle mode enabled successfully")
        except Exception as e:
            self.use_oracle = False
            logger.error(f"❌ Failed to enable Oracle: {e}")
            raise
    
    def test_oracle_connection(self) -> dict:
        """
        Test Oracle database connection
        
        Returns:
            Dictionary with connection status and details
        """
        if not ORACLE_AVAILABLE:
            return {
                "success": False,
                "message": "Oracle driver not installed",
                "details": "Install with: pip install oracledb"
            }
        
        try:
            connection = self._get_oracle_connection()
            
            # Test query
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "message": "Oracle connection successful",
                "host": self.oracle_config['host'],
                "service_name": self.oracle_config['service_name'],
                "test_query_result": result[0] if result else None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Oracle connection failed: {str(e)}",
                "host": self.oracle_config.get('host'),
                "error": str(e)
            }
    
    def get_connection_info(self) -> dict:
        """Get current connection information"""
        return {
            "mode": "Oracle" if self.use_oracle else "Excel",
            "oracle_available": ORACLE_AVAILABLE,
            "oracle_enabled": ORACLE_ENABLED,
            "oracle_config": {
                "host": self.oracle_config.get('host'),
                "port": self.oracle_config.get('port'),
                "service_name": self.oracle_config.get('service_name'),
                "user": self.oracle_config.get('user')
            } if self.use_oracle else None,
            "excel_file": self.data_file_path if not self.use_oracle else None,
            "column_count": len(self.column_config.get_all_columns())
        }
