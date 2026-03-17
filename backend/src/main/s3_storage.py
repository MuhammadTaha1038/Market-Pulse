"""
S3 Storage Implementation
Stores structured JSON data (rules, presets, cron config, email config, logs, etc.)
as S3 objects when OUTPUT_DESTINATION=s3 or both.

Each storage "key" becomes an S3 object:
  s3://bucket/storage/rules.json
  s3://bucket/storage/presets.json
  s3://bucket/storage/email_config.json
  ...
"""

import json
import os
import logging
from typing import Any, Optional
from storage_interface import StorageInterface

logger = logging.getLogger(__name__)

# Optional boto3 import
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed. S3 storage unavailable.")


class S3Storage(StorageInterface):
    """
    S3-backed storage for JSON data.
    Mirrors the JSONStorage API but reads/writes from AWS S3.
    """

    def __init__(
        self,
        bucket_name: str = None,
        region: str = None,
        prefix: str = "storage",
        access_key: str = None,
        secret_key: str = None,
    ):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 not installed. Run: pip install boto3")

        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME", "")
        self.region = region or os.getenv("S3_REGION", "us-east-1")
        self.prefix = prefix.rstrip("/")
        self.access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID", "")
        self.secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY", "")

        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME not configured")

        self._s3 = self._build_client()
        logger.info(f"S3Storage initialized: s3://{self.bucket_name}/{self.prefix}/")

    def _build_client(self):
        """Build boto3 S3 client."""
        if self.access_key and self.secret_key:
            return boto3.client(
                "s3",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
        return boto3.client("s3", region_name=self.region)

    def _object_key(self, key: str) -> str:
        """Convert storage key to full S3 object key."""
        return f"{self.prefix}/{key}.json"

    # ------------------------------------------------------------------ #
    #  StorageInterface implementation                                     #
    # ------------------------------------------------------------------ #

    def save(self, key: str, data: Any):
        """Serialize data as JSON and upload to S3."""
        obj_key = self._object_key(key)
        try:
            body = json.dumps(data, indent=2, default=str).encode("utf-8")
            self._s3.put_object(
                Bucket=self.bucket_name,
                Key=obj_key,
                Body=body,
                ContentType="application/json",
            )
            logger.debug(f"S3Storage saved: s3://{self.bucket_name}/{obj_key}")
        except Exception as e:
            logger.error(f"S3Storage failed to save '{key}': {e}")
            raise

    def load(self, key: str) -> Optional[Any]:
        """Download JSON object from S3 and deserialize."""
        obj_key = self._object_key(key)
        try:
            response = self._s3.get_object(Bucket=self.bucket_name, Key=obj_key)
            body = response["Body"].read().decode("utf-8")
            return json.loads(body)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return None
            logger.error(f"S3Storage failed to load '{key}': {e}")
            return None
        except Exception as e:
            logger.error(f"S3Storage failed to load '{key}': {e}")
            return None

    def exists(self, key: str) -> bool:
        """Check if S3 object exists."""
        obj_key = self._object_key(key)
        try:
            self._s3.head_object(Bucket=self.bucket_name, Key=obj_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404", "403"):
                return False
            raise

    def delete(self, key: str):
        """Delete S3 object."""
        obj_key = self._object_key(key)
        try:
            self._s3.delete_object(Bucket=self.bucket_name, Key=obj_key)
            logger.debug(f"S3Storage deleted: {obj_key}")
        except Exception as e:
            logger.error(f"S3Storage failed to delete '{key}': {e}")
            raise

    def list_keys(self, prefix: str = "") -> list:
        """List all storage keys, optionally filtered by prefix."""
        s3_prefix = f"{self.prefix}/{prefix}" if prefix else f"{self.prefix}/"
        try:
            paginator = self._s3.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=s3_prefix):
                for obj in page.get("Contents", []):
                    # Strip prefix and .json extension to get the storage key
                    raw = obj["Key"]
                    key_part = raw[len(self.prefix) + 1:]  # remove "prefix/"
                    if key_part.endswith(".json"):
                        key_part = key_part[:-5]  # remove .json
                    if not prefix or key_part.startswith(prefix):
                        keys.append(key_part)
            return keys
        except Exception as e:
            logger.error(f"S3Storage failed to list keys: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  Extra helpers                                                       #
    # ------------------------------------------------------------------ #

    def upload_raw_file(self, local_path: str, s3_key: str) -> str:
        """
        Upload a raw file (e.g. Excel) to S3.

        Args:
            local_path: Local filesystem path to the file
            s3_key: Full S3 object key (relative to bucket root)

        Returns:
            S3 URI of the uploaded file
        """
        try:
            self._s3.upload_file(local_path, self.bucket_name, s3_key)
            uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Uploaded raw file: {local_path} → {uri}")
            return uri
        except Exception as e:
            logger.error(f"Failed to upload raw file '{local_path}': {e}")
            raise

    def upload_bytes(self, data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes to S3."""
        try:
            self._s3.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                ContentType=content_type,
            )
            uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Uploaded bytes to {uri}")
            return uri
        except Exception as e:
            logger.error(f"Failed to upload bytes to '{s3_key}': {e}")
            raise

    def download_bytes(self, s3_key: str) -> bytes:
        """Download raw object bytes from S3 key."""
        try:
            response = self._s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to download bytes from '{s3_key}': {e}")
            raise

    def delete_raw_file(self, s3_key: str):
        """Delete raw (non-JSON) object from S3 by full key."""
        try:
            self._s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted raw S3 object: s3://{self.bucket_name}/{s3_key}")
        except Exception as e:
            logger.error(f"Failed to delete raw S3 object '{s3_key}': {e}")
            raise

    @staticmethod
    def is_configured() -> bool:
        """Check if S3 is properly configured (bucket name set)."""
        return bool(os.getenv("S3_BUCKET_NAME", ""))
