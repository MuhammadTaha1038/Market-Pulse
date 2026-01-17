#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Column Configuration Service - Admin-managed dynamic column mapping
Stores which columns to extract from Oracle and how to map them
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ColumnConfigService:
    """
    Manages dynamic column configuration for data extraction
    Admin can add/remove columns, and this affects SQL queries
    """
    
    def __init__(self, config_file_path: str = None):
        """
        Initialize column configuration service
        
        Args:
            config_file_path: Path to JSON config file
        """
        if config_file_path is None:
            base_dir = Path(__file__).parent.parent.parent.parent.parent
            config_file_path = base_dir / "column_config.json"
        
        self.config_file_path = str(config_file_path)
        self.config = self._load_config()
        logger.info(f"ColumnConfigService initialized with {len(self.config['columns'])} columns")
    
    def _load_config(self) -> dict:
        """Load column configuration from JSON file"""
        try:
            with open(self.config_file_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded column config from {self.config_file_path}")
                return config
        except FileNotFoundError:
            logger.warning("Config file not found, creating default configuration")
            return self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}, using default")
            return self._create_default_config()
    
    def _create_default_config(self) -> dict:
        """
        Create default column configuration based on current Excel structure
        This matches "Color today.xlsx" columns
        """
        default_config = {
            "version": "1.0",
            "last_updated": "2026-01-17",
            "oracle_table": "MARKET_COLORS",  # Will be configured by admin
            "columns": [
                {
                    "id": 1,
                    "oracle_name": "MESSAGE_ID",
                    "display_name": "Message ID",
                    "data_type": "INTEGER",
                    "required": True,
                    "description": "Unique message identifier"
                },
                {
                    "id": 2,
                    "oracle_name": "TICKER",
                    "display_name": "Ticker",
                    "data_type": "VARCHAR",
                    "required": True,
                    "description": "Security ticker symbol"
                },
                {
                    "id": 3,
                    "oracle_name": "SECTOR",
                    "display_name": "Sector",
                    "data_type": "VARCHAR",
                    "required": True,
                    "description": "Asset class/sector"
                },
                {
                    "id": 4,
                    "oracle_name": "CUSIP",
                    "display_name": "CUSIP",
                    "data_type": "VARCHAR",
                    "required": True,
                    "description": "CUSIP identifier"
                },
                {
                    "id": 5,
                    "oracle_name": "DATE",
                    "display_name": "Date",
                    "data_type": "DATE",
                    "required": True,
                    "description": "Trade/color date"
                },
                {
                    "id": 6,
                    "oracle_name": "PRICE_LEVEL",
                    "display_name": "Price Level",
                    "data_type": "FLOAT",
                    "required": True,
                    "description": "Price level"
                },
                {
                    "id": 7,
                    "oracle_name": "BID",
                    "display_name": "BID",
                    "data_type": "FLOAT",
                    "required": False,
                    "description": "Bid price"
                },
                {
                    "id": 8,
                    "oracle_name": "ASK",
                    "display_name": "ASK",
                    "data_type": "FLOAT",
                    "required": False,
                    "description": "Ask/Offer price"
                },
                {
                    "id": 9,
                    "oracle_name": "PX",
                    "display_name": "PX",
                    "data_type": "FLOAT",
                    "required": True,
                    "description": "Price (used for sorting)"
                },
                {
                    "id": 10,
                    "oracle_name": "SOURCE",
                    "display_name": "Source",
                    "data_type": "VARCHAR",
                    "required": True,
                    "description": "Data source/bank"
                },
                {
                    "id": 11,
                    "oracle_name": "BIAS",
                    "display_name": "Bias",
                    "data_type": "VARCHAR",
                    "required": True,
                    "description": "Color type (BID, OFFER, etc)"
                },
                {
                    "id": 12,
                    "oracle_name": "RANK",
                    "display_name": "Rank",
                    "data_type": "INTEGER",
                    "required": True,
                    "description": "Pre-calculated rank (1-6)"
                },
                {
                    "id": 13,
                    "oracle_name": "COV_PRICE",
                    "display_name": "Coverage Price",
                    "data_type": "FLOAT",
                    "required": False,
                    "description": "Coverage price reference"
                },
                {
                    "id": 14,
                    "oracle_name": "PERCENT_DIFF",
                    "display_name": "Percent Diff",
                    "data_type": "FLOAT",
                    "required": False,
                    "description": "Percentage difference"
                },
                {
                    "id": 15,
                    "oracle_name": "PRICE_DIFF",
                    "display_name": "Price Diff",
                    "data_type": "FLOAT",
                    "required": False,
                    "description": "Price difference"
                },
                {
                    "id": 16,
                    "oracle_name": "CONFIDENCE",
                    "display_name": "Confidence",
                    "data_type": "INTEGER",
                    "required": False,
                    "description": "Confidence score (0-10)"
                },
                {
                    "id": 17,
                    "oracle_name": "DATE_1",
                    "display_name": "Date 1",
                    "data_type": "DATE",
                    "required": False,
                    "description": "Secondary/fallback date"
                },
                {
                    "id": 18,
                    "oracle_name": "DIFF_STATUS",
                    "display_name": "Diff Status",
                    "data_type": "VARCHAR",
                    "required": False,
                    "description": "Difference status"
                }
            ]
        }
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: dict):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved column config to {self.config_file_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def get_all_columns(self) -> List[Dict]:
        """Get all configured columns"""
        return self.config['columns']
    
    def get_oracle_column_names(self) -> List[str]:
        """Get list of Oracle column names for SQL SELECT statement"""
        return [col['oracle_name'] for col in self.config['columns']]
    
    def get_required_columns(self) -> List[Dict]:
        """Get only required columns"""
        return [col for col in self.config['columns'] if col['required']]
    
    def get_oracle_table_name(self) -> str:
        """Get configured Oracle table name"""
        return self.config.get('oracle_table', 'MARKET_COLORS')
    
    def add_column(self, column: Dict) -> Dict:
        """
        Add new column to configuration
        
        Args:
            column: Dictionary with oracle_name, display_name, data_type, required, description
            
        Returns:
            Added column with generated ID
        """
        # Generate new ID
        max_id = max([col['id'] for col in self.config['columns']], default=0)
        column['id'] = max_id + 1
        
        # Validate required fields
        required_fields = ['oracle_name', 'display_name', 'data_type', 'required']
        for field in required_fields:
            if field not in column:
                raise ValueError(f"Missing required field: {field}")
        
        # Add column
        self.config['columns'].append(column)
        self._save_config(self.config)
        
        logger.info(f"Added new column: {column['oracle_name']}")
        return column
    
    def delete_column(self, column_id: int) -> bool:
        """
        Delete column from configuration
        
        Args:
            column_id: ID of column to delete
            
        Returns:
            True if deleted, False if not found
        """
        original_length = len(self.config['columns'])
        self.config['columns'] = [col for col in self.config['columns'] if col['id'] != column_id]
        
        if len(self.config['columns']) < original_length:
            self._save_config(self.config)
            logger.info(f"Deleted column with ID: {column_id}")
            return True
        
        logger.warning(f"Column ID {column_id} not found")
        return False
    
    def update_column(self, column_id: int, updates: Dict) -> Optional[Dict]:
        """
        Update existing column
        
        Args:
            column_id: ID of column to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated column or None if not found
        """
        for col in self.config['columns']:
            if col['id'] == column_id:
                col.update(updates)
                self._save_config(self.config)
                logger.info(f"Updated column {column_id}: {updates}")
                return col
        
        logger.warning(f"Column ID {column_id} not found")
        return None
    
    def update_oracle_table(self, table_name: str):
        """Update Oracle table name"""
        self.config['oracle_table'] = table_name
        self._save_config(self.config)
        logger.info(f"Updated Oracle table name to: {table_name}")
    
    def generate_sql_select(self, where_clause: str = "") -> str:
        """
        Generate SQL SELECT statement based on configured columns
        
        Args:
            where_clause: Optional WHERE clause (without WHERE keyword)
            
        Returns:
            Complete SQL SELECT statement
        """
        columns = ", ".join(self.get_oracle_column_names())
        table = self.get_oracle_table_name()
        
        sql = f"SELECT {columns} FROM {table}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        logger.info(f"Generated SQL: {sql}")
        return sql


# Singleton instance
_column_config_instance = None

def get_column_config() -> ColumnConfigService:
    """Get singleton column config instance"""
    global _column_config_instance
    if _column_config_instance is None:
        _column_config_instance = ColumnConfigService()
    return _column_config_instance
