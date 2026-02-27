"""
Storage configuration - SINGLE POINT to switch between JSON/S3
When S3 credentials are configured and OUTPUT_DESTINATION=s3 (or both),
ALL structured data (rules, presets, cron config, email config, logs, etc.)
is stored in AWS S3. Otherwise uses local JSON files.
"""

import os
from json_storage import JSONStorage


def get_storage():
    """
    Get storage implementation based on configuration.

    Trigger: OUTPUT_DESTINATION = 's3' or 'both' in .env
    When triggered, ALL JSON data (rules, presets, cron jobs, email config,
    session data, logs) is stored in S3 instead of local files.

    Required env vars when S3 is active:
      - S3_BUCKET_NAME      (required)
      - AWS_ACCESS_KEY_ID   (required unless using IAM role)
      - AWS_SECRET_ACCESS_KEY (required unless using IAM role)
      - S3_REGION           (default: us-east-1)

    Returns:
        StorageInterface implementation (JSONStorage or S3Storage)
    """
    output_dest = os.getenv("OUTPUT_DESTINATION", "local").lower()
    use_s3 = output_dest in ("s3", "both")

    if use_s3 and os.getenv("S3_BUCKET_NAME", ""):
        try:
            from s3_storage import S3Storage
            storage_instance = S3Storage(prefix="storage")
            print(f"☁️  Storage Type: s3 (bucket: {os.getenv('S3_BUCKET_NAME')})")
            return storage_instance
        except Exception as e:
            print(f"⚠️  S3 storage failed to initialize ({e}), falling back to JSON")

    # Default: local JSON storage
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    print(f"🔧 Storage Type: json")
    return JSONStorage(data_dir=data_dir)


# Global storage instance - used by all services
storage = get_storage()
