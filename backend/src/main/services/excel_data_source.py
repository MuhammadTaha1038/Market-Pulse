"""
Excel Data Source Implementation.
Current implementation for reading from Excel files.
"""
import os
import pandas as pd
from typing import Dict, Any, Optional
from data_source_interface import DataSourceInterface


class ExcelDataSource(DataSourceInterface):
    """Excel file data source implementation."""
    
    def __init__(self, file_path: str = "Color today.xlsx"):
        """
        Initialize Excel data source.
        
        Args:
            file_path: Path to the Excel file (default: "Color today.xlsx")
        """
        self.file_path = file_path
        # Try to resolve absolute path from project root
        if not os.path.isabs(file_path):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            self.file_path = os.path.join(project_root, file_path)
    
    def fetch_data(self, clo_id: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch data from Excel file.
        
        Args:
            clo_id: Optional CLO identifier (not used for Excel, filtering done later)
            
        Returns:
            DataFrame with raw data
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")
        
        df = pd.read_excel(self.file_path)
        
        # Standardize column names (uppercase, strip spaces)
        df.columns = df.columns.str.strip().str.upper()
        
        return df
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test if Excel file exists and is readable.
        
        Returns:
            Dict with status and message
        """
        try:
            if not os.path.exists(self.file_path):
                return {
                    "status": "error",
                    "message": f"Excel file not found: {self.file_path}"
                }
            
            # Try to read the file
            df = pd.read_excel(self.file_path)
            row_count = len(df)
            
            return {
                "status": "success",
                "message": f"Excel file accessible with {row_count} rows"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read Excel file: {str(e)}"
            }
    
    def get_source_info(self) -> Dict[str, str]:
        """
        Get information about the Excel data source.
        
        Returns:
            Dict with source type and file path
        """
        return {
            "type": "Excel",
            "file_path": self.file_path,
            "exists": str(os.path.exists(self.file_path))
        }
