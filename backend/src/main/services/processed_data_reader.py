"""
Processed Data Reader - Abstraction for reading processed output data.

This is SEPARATE from data_source (RAW input) - this reads PROCESSED output.
Configured via OUTPUT_DESTINATION in .env to read from local Excel or AWS S3.
"""
import os
import io
import pandas as pd
from typing import Optional
import logging

# Optional import - only needed when S3 is configured
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception

logger = logging.getLogger(__name__)


class ProcessedDataReader:
    """Read processed color data from configured output destination."""
    
    def __init__(self):
        """Initialize reader with configuration from environment."""
        self.output_destination = os.getenv("OUTPUT_DESTINATION", "local").lower()
        
        # Local Excel configuration
        self.local_file_path = self._get_local_output_path()
        
        # S3 configuration
        self.s3_bucket = os.getenv("S3_BUCKET_NAME", "")
        self.s3_region = os.getenv("S3_REGION", "us-east-1")
        self.s3_prefix = os.getenv("S3_PREFIX", "processed_colors/")
        self.s3_file_format = os.getenv("S3_FILE_FORMAT", "xlsx")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        
        self._s3_client = None
        
        logger.info(f"ProcessedDataReader initialized for: {self.output_destination}")
    
    def _get_local_output_path(self) -> str:
        """Get local output file path. Respects OUTPUT_DIR env var if set."""
        from pathlib import Path
        output_dir = os.getenv("OUTPUT_DIR", "").strip()
        if output_dir:
            return str(Path(output_dir) / "Processed_Colors_Output.xlsx")
        base_dir = Path(__file__).parent.parent.parent.parent.parent
        return str(base_dir / "Processed_Colors_Output.xlsx")
    
    def _get_s3_client(self):
        """Get or create S3 client."""
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 not installed. Install with: pip install boto3")
        
        if self._s3_client is None:
            if self.aws_access_key and self.aws_secret_key:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.s3_region
                )
            else:
                # Use IAM role or default credentials
                self._s3_client = boto3.client('s3', region_name=self.s3_region)
        return self._s3_client
    
    def read_processed_data(self, nrows: Optional[int] = None) -> pd.DataFrame:
        """
        Read processed color data from configured destination.
        
        Args:
            nrows: Optional limit on number of rows to read
            
        Returns:
            DataFrame with processed color data
        """
        # Determine source based on configuration
        if self.output_destination == "s3":
            return self._read_from_s3(nrows)
        elif self.output_destination == "both":
            # When both are configured, prioritize S3 for reading
            try:
                return self._read_from_s3(nrows)
            except Exception as e:
                logger.warning(f"Failed to read from S3, falling back to local: {e}")
                return self._read_from_local(nrows)
        else:
            # Default to local
            return self._read_from_local(nrows)
    
    def _read_from_local(self, nrows: Optional[int] = None) -> pd.DataFrame:
        """Read from local Excel file."""
        try:
            if not os.path.exists(self.local_file_path):
                logger.warning(f"Local file not found: {self.local_file_path}")
                return pd.DataFrame()
            
            if nrows:
                df = pd.read_excel(self.local_file_path, nrows=nrows)
                logger.info(f"Read {len(df)} rows (limited) from local Excel")
            else:
                df = pd.read_excel(self.local_file_path)
                logger.info(f"Read {len(df)} rows from local Excel")
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading from local Excel: {e}")
            return pd.DataFrame()
    
    def _read_from_s3(self, nrows: Optional[int] = None) -> pd.DataFrame:
        """
        Read all per-sector accumulated files from S3.

        Each sector has exactly ONE file:
          {S3_PREFIX}{SECTOR}/Processed_Colors_{SECTOR}.{format}

        Data is already deduped at write time (newest MESSAGE_ID wins) so no
        dedup step is needed here.  Reading is fast: one file per sector,
        typically 5-20 files total regardless of how many runs have happened.
        """
        try:
            if not self.s3_bucket:
                raise ValueError("S3_BUCKET_NAME not configured")

            s3_client = self._get_s3_client()
            prefix = self.s3_prefix.lstrip('/')
            fmt = self.s3_file_format
            ext = f'.{fmt}'

            # List only Processed_Colors_*.{ext} sector files
            paginator = s3_client.get_paginator('list_objects_v2')
            keys = []
            for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    fname = key.split('/')[-1]
                    if fname.startswith('Processed_Colors_') and key.endswith(ext):
                        keys.append(key)

            if not keys:
                logger.warning(f"No sector files found in S3 under '{prefix}'")
                return pd.DataFrame()

            logger.info(f"Reading {len(keys)} sector file(s) from S3")

            dfs = []
            for key in keys:
                try:
                    response = s3_client.get_object(Bucket=self.s3_bucket, Key=key)
                    body = response['Body'].read()
                    if fmt == 'csv':
                        df = pd.read_csv(io.BytesIO(body))
                    elif fmt == 'parquet':
                        df = pd.read_parquet(io.BytesIO(body), engine='pyarrow')
                    else:
                        df = pd.read_excel(io.BytesIO(body), engine='openpyxl')
                    dfs.append(df)
                    logger.info(f"  {key}: {len(df)} row(s)")
                except Exception as e:
                    logger.error(f"  Failed to read {key}: {e} — skipping")

            if not dfs:
                return pd.DataFrame()

            combined = pd.concat(dfs, ignore_index=True)

            if nrows:
                combined = combined.head(nrows)

            logger.info(f"✅ S3 read complete: {len(combined)} row(s) from {len(dfs)} sector file(s)")
            return combined

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Error reading from S3: {e}")
            raise
    
    def get_recent_colors(self, limit: int = 50, sort_by_date: bool = True) -> pd.DataFrame:
        """
        Get most recent processed colors.
        
        Args:
            limit: Number of recent records to return
            sort_by_date: Whether to sort by date descending
            
        Returns:
            DataFrame with recent processed colors
        """
        # Read data
        df = self.read_processed_data()
        
        if df.empty:
            return df
        
        # Sort by date if requested
        if sort_by_date and 'DATE' in df.columns:
            df['DATE_PARSED'] = pd.to_datetime(df['DATE'], errors='coerce')
            df = df.sort_values('DATE_PARSED', ascending=False)
            df = df.drop('DATE_PARSED', axis=1)
        elif sort_by_date and 'PROCESSED_AT' in df.columns:
            # Fallback to PROCESSED_AT if DATE not available
            df['PROCESSED_AT_PARSED'] = pd.to_datetime(df['PROCESSED_AT'], errors='coerce')
            df = df.sort_values('PROCESSED_AT_PARSED', ascending=False)
            df = df.drop('PROCESSED_AT_PARSED', axis=1)
        
        # Return limited results
        return df.head(limit)


def get_processed_data_reader() -> ProcessedDataReader:
    """Factory function to get processed data reader instance."""
    return ProcessedDataReader()
