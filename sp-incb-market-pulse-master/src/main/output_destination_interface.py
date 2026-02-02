"""
Output Destination Interface for output abstraction.
Supports multiple output destinations: Local Excel files, AWS S3, etc.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class OutputDestinationInterface(ABC):
    """Abstract interface for different output destinations."""
    
    @abstractmethod
    def save_output(self, df: pd.DataFrame, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save processed data to the output destination.
        
        Args:
            df: DataFrame with processed data
            filename: Name/key for the output file
            metadata: Optional metadata to attach to the output
            
        Returns:
            Dict with status, message, and location information
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the output destination.
        
        Returns:
            Dict with status and message
        """
        pass
    
    @abstractmethod
    def get_destination_info(self) -> Dict[str, str]:
        """
        Get information about the output destination.
        
        Returns:
            Dict with destination type and details
        """
        pass
