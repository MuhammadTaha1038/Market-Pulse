"""
Data Source Factory - Creates appropriate data source based on configuration.
"""
import os
from data_source_interface import DataSourceInterface
from services.excel_data_source import ExcelDataSource
from services.oracle_data_source import OracleDataSource


def get_data_source() -> DataSourceInterface:
    """
    Get configured data source instance.
    
    Reads DATA_SOURCE environment variable to determine which source to use:
    - "excel" (default): Use Excel file data source
    - "oracle": Use Oracle database data source
    
    Returns:
        DataSourceInterface implementation
    """
    source_type = os.getenv("DATA_SOURCE", "excel").lower()
    
    if source_type == "oracle":
        return OracleDataSource()
    else:
        # Default to Excel
        excel_file = os.getenv("EXCEL_INPUT_FILE", "Color today.xlsx")
        return ExcelDataSource(file_path=excel_file)


def get_data_source_info() -> dict:
    """
    Get information about the current data source configuration.
    
    Returns:
        Dict with source type and configuration details
    """
    source = get_data_source()
    return source.get_source_info()
