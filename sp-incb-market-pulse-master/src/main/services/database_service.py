#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database Service - Data fetching from Excel/Oracle

IMPORTANT FOR CLIENT:
======================
Current Mode: EXCEL (temporary for demo)
Production Mode: ORACLE (via Lambda + Terraform)

To enable Oracle:
1. Lambda function will extract data from Oracle
2. Terraform will manage infrastructure
3. GitLab pipeline will deploy
4. Set ORACLE_ENABLED = True
5. Configure AWS credentials in SSM Parameter Store
6. Admin API will handle connection management

This file is ready for Oracle integration once infrastructure is deployed.
======================
"""
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
from models.color import ColorRaw
from services.column_config_service import get_column_config

logger = logging.getLogger(__name__)

# Oracle connection flag - Client will enable this after AWS setup
ORACLE_ENABLED = False

try:
    import oracledb
    ORACLE_AVAILABLE = True
    logger.info("Oracle driver (oracledb) is available")
except ImportError:
    ORACLE_AVAILABLE = False
    logger.warning("Oracle driver not installed. Run: pip install oracledb")


class DatabaseService:
    """
    Database operations for color data
    Supports Excel (temporary) and Oracle (production) with dynamic columns
    """
    
    def __init__(
        self, 
        data_file_path: str = None,
        oracle_config: dict = None,
        use_oracle: bool = False
    ):
        """
        Initialize database service
        
        Args:
            data_file_path: Path to Excel file (fallback)
            oracle_config: Oracle connection config (host, port, service_name, user, password)
            use_oracle: Whether to use Oracle (requires ORACLE_ENABLED=True)
        """
        # Column configuration service
        self.column_config = get_column_config()
        
        # Excel fallback
        if data_file_path is None:
            base_dir = Path(__file__).parent.parent.parent.parent.parent
            data_file_path = base_dir / "Color today.xlsx"
        self.data_file_path = str(data_file_path)
        
        # Oracle configuration
        self.oracle_config = oracle_config or self._get_default_oracle_config()
        self.use_oracle = use_oracle and ORACLE_ENABLED and ORACLE_AVAILABLE
        
        # Data cache
        self._data_cache = None
        
        if self.use_oracle:
            logger.info("DatabaseService initialized with ORACLE connection")
            logger.info(f"Oracle host: {self.oracle_config.get('host')}")
        else:
            logger.info(f"DatabaseService initialized with EXCEL fallback: {self.data_file_path}")
    
    def _get_default_oracle_config(self) -> dict:
        """
        Get default Oracle configuration
        In production, load from AWS SSM Parameter Store or environment variables
        """
        return {
            'host': 'oracle-db.example.com',  # To be configured
            'port': 1521,
            'service_name': 'ORCL',  # To be configured
            'user': 'market_pulse_user',  # To be configured from AWS
            'password': 'PLACEHOLDER',  # Load from AWS SSM/Secrets Manager
            'encoding': 'UTF-8'
        }
    
    def _get_oracle_connection(self):
        """
        Create Oracle database connection
        Uses oracledb (python-oracledb) driver
        """
        if not ORACLE_AVAILABLE:
            raise RuntimeError("Oracle driver not installed. Install: pip install oracledb")
        
        try:
            dsn = oracledb.makedsn(
                self.oracle_config['host'],
                self.oracle_config['port'],
                service_name=self.oracle_config['service_name']
            )
            
            connection = oracledb.connect(
                user=self.oracle_config['user'],
                password=self.oracle_config['password'],
                dsn=dsn,
                encoding=self.oracle_config.get('encoding', 'UTF-8')
            )
            
            logger.info("✅ Oracle connection established")
            return connection
            
        except Exception as e:
            logger.error(f"❌ Oracle connection failed: {e}")
            raise
    
    def _load_data_from_oracle(self, where_clause: str = "") -> pd.DataFrame:
        """
        Load data from Oracle using dynamic column configuration
        
        Args:
            where_clause: Optional SQL WHERE clause
            
        Returns:
            DataFrame with data from Oracle
        """
        logger.info("Loading data from Oracle database")
        
        # Generate SQL using column config
        sql = self.column_config.generate_sql_select(where_clause)
        
        # Execute query
        connection = self._get_oracle_connection()
        try:
            df = pd.read_sql(sql, connection)
            logger.info(f"✅ Loaded {len(df)} records from Oracle")
            return df
        finally:
            connection.close()
            logger.info("Oracle connection closed")
    
    def _load_data(self) -> pd.DataFrame:
        """
        Load data from either Oracle or Excel based on configuration
        Uses caching for Excel mode
        """
        if self.use_oracle:
            # Oracle mode: no caching, always fetch fresh data
            return self._load_data_from_oracle()
        else:
            # Excel mode: cache data for performance
            if self._data_cache is None:
                logger.info(f"Loading data from Excel: {self.data_file_path}")
                self._data_cache = pd.read_excel(self.data_file_path)
                logger.info(f"✅ Loaded {len(self._data_cache)} records from Excel")
            return self._data_cache
    
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
        Get color count by month for dashboard chart
        
        Args:
            months: Number of months to look back
            
        Returns:
            List of {"month": "2026-01", "count": 1234}
        """
        df = self._load_data()
        
        # For sample data (single date), generate mock monthly stats
        # In production, this will query actual date ranges
        logger.info("Generating monthly stats (mock data for sample)")
        
        # Get unique month from data
        df['month'] = pd.to_datetime(df['DATE']).dt.strftime('%Y-%m')
        monthly_counts = df.groupby('month').size().reset_index(name='count')
        
        # If only one month, generate mock historical data for chart
        if len(monthly_counts) == 1:
            current_month = monthly_counts.iloc[0]['month']
            current_count = monthly_counts.iloc[0]['count']
            
            # Generate 11 previous months with varying counts
            stats = []
            base_date = datetime.strptime(current_month, '%Y-%m')
            
            for i in range(11, -1, -1):
                month_date = base_date - timedelta(days=30 * i)
                month_str = month_date.strftime('%Y-%m')
                
                # Mock data with alternating pattern (like frontend expects)
                if i == 0:
                    count = current_count
                else:
                    count = 1200 if i % 2 == 0 else 2100
                
                stats.append({"month": month_str, "count": count})
            
            return stats
        
        # Real data with multiple months
        result = []
        for _, row in monthly_counts.iterrows():
            result.append({
                "month": row['month'],
                "count": int(row['count'])
            })
        
        return result
    
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
