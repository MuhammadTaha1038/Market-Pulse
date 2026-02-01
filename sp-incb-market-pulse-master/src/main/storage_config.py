"""
Storage configuration - SINGLE POINT to switch between JSON/S3/Oracle
When credentials are ready, just change this file
"""

import os
from json_storage import JSONStorage
# from s3_storage import S3Storage  # Uncomment when S3 credentials ready
# from oracle_storage import OracleStorage  # Uncomment when Oracle credentials ready


def get_storage():
    """
    Get storage implementation based on environment variable
    
    Environment Variables:
    - STORAGE_TYPE: 'json' (default), 's3', or 'oracle'
    
    For S3:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION
    - S3_BUCKET_NAME
    
    For Oracle:
    - ORACLE_CONFIG_HOST
    - ORACLE_CONFIG_PORT
    - ORACLE_CONFIG_SERVICE
    - ORACLE_CONFIG_USER
    - ORACLE_CONFIG_PASSWORD
    
    Returns:
        StorageInterface implementation
    """
    storage_type = os.getenv('STORAGE_TYPE', 'json').lower()
    
    print(f"🔧 Storage Type: {storage_type}")
    
    if storage_type == 's3':
        # Will implement when S3 credentials available
        # return S3Storage()
        raise NotImplementedError(
            "S3 storage not configured yet. "
            "Set S3 credentials in .env and uncomment S3Storage import."
        )
    
    elif storage_type == 'oracle':
        # Will implement when Oracle credentials available
        # return OracleStorage()
        raise NotImplementedError(
            "Oracle storage not configured yet. "
            "Set Oracle credentials in .env and uncomment OracleStorage import."
        )
    
    else:
        # Default: JSON storage (works now without any credentials)
        return JSONStorage()


# Global storage instance - used by all services
storage = get_storage()
