"""
Data Source Interface for input abstraction.
Supports multiple data sources: Excel files, Oracle DB, etc.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class DataSourceInterface(ABC):
    """Abstract interface for different data sources."""
    
    @abstractmethod
    def fetch_data(self, clo_id: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch raw data from the source.
        
        Args:
            clo_id: Optional CLO identifier to filter data
            
        Returns:
            DataFrame with standardized column names
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the data source.
        
        Returns:
            Dict with status and message
        """
        pass
    
    @abstractmethod
    def get_source_info(self) -> Dict[str, str]:
        """
        Get information about the data source.
        
        Returns:
            Dict with source type and details
        """
        pass
