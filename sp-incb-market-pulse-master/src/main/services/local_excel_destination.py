"""
Local Excel Output Destination Implementation.
Saves processed data to local Excel files.
"""
import os
import pandas as pd
from typing import Dict, Any, Optional
from output_destination_interface import OutputDestinationInterface


class LocalExcelDestination(OutputDestinationInterface):
    """Local Excel file output destination implementation."""
    
    def __init__(self, output_dir: str = ""):
        """
        Initialize local Excel output destination.
        
        Args:
            output_dir: Directory to save Excel files (default: project root)
        """
        if not output_dir:
            # Default to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            self.output_dir = project_root
        else:
            self.output_dir = output_dir
        
        # Ensure directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_output(self, df: pd.DataFrame, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save DataFrame to local Excel file.
        
        Args:
            df: DataFrame to save
            filename: Excel filename (e.g., "Processed_Colors_Output.xlsx")
            metadata: Optional metadata (not used for local Excel)
            
        Returns:
            Dict with status, message, and file path
        """
        try:
            # Ensure filename has .xlsx extension
            if not filename.endswith('.xlsx'):
                filename = f"{filename}.xlsx"
            
            file_path = os.path.join(self.output_dir, filename)
            
            # Save to Excel
            df.to_excel(file_path, index=False, engine='openpyxl')
            
            return {
                "status": "success",
                "message": f"Saved to local Excel: {filename}",
                "location": file_path,
                "type": "local_excel"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save Excel file: {str(e)}",
                "location": None,
                "type": "local_excel"
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test if output directory is writable.
        
        Returns:
            Dict with status and message
        """
        try:
            # Check if directory exists
            if not os.path.exists(self.output_dir):
                return {
                    "status": "error",
                    "message": f"Output directory does not exist: {self.output_dir}"
                }
            
            # Check if directory is writable
            test_file = os.path.join(self.output_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            return {
                "status": "success",
                "message": f"Local Excel output directory is writable: {self.output_dir}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Output directory not writable: {str(e)}"
            }
    
    def get_destination_info(self) -> Dict[str, str]:
        """
        Get information about the local Excel destination.
        
        Returns:
            Dict with destination type and directory
        """
        return {
            "type": "Local Excel",
            "output_dir": self.output_dir,
            "exists": str(os.path.exists(self.output_dir))
        }
