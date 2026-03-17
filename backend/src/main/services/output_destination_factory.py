"""
Output Destination Factory - Creates appropriate output destination based on configuration.
"""
import os
from output_destination_interface import OutputDestinationInterface
from services.local_excel_destination import LocalExcelDestination
from services.s3_destination import S3Destination


def get_output_destination() -> OutputDestinationInterface:
    """
    Get configured output destination instance.
    
    Reads OUTPUT_DESTINATION environment variable to determine which destination to use:
    - "local" (default): Save to local Excel files
    - "s3": Upload to AWS S3 bucket
    - "both": Save locally AND upload to S3
    
    Returns:
        OutputDestinationInterface implementation (or list for "both")
    """
    destination_type = os.getenv("OUTPUT_DESTINATION", "local").lower()
    
    if destination_type == "s3":
        return S3Destination()
    elif destination_type == "both":
        # Return both destinations as a list
        return [LocalExcelDestination(), S3Destination()]
    else:
        # Default to local Excel
        output_dir = os.getenv("OUTPUT_DIR", "")
        return LocalExcelDestination(output_dir=output_dir)


def get_output_destination_info() -> dict:
    """
    Get information about the current output destination configuration.
    
    Returns:
        Dict with destination type and configuration details
    """
    destination = get_output_destination()
    
    if isinstance(destination, list):
        # Multiple destinations
        return {
            "mode": "multiple",
            "destinations": [d.get_destination_info() for d in destination]
        }
    else:
        return destination.get_destination_info()
