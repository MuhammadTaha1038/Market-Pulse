#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
S3 Service - Future integration for storing processed colors in AWS S3

SETUP INSTRUCTIONS FOR CLIENT:
================================
1. Install boto3: pip install boto3
2. Configure AWS credentials:
   - Set AWS_ACCESS_KEY_ID in environment
   - Set AWS_SECRET_ACCESS_KEY in environment
   - Or use AWS IAM roles (recommended for Lambda)
3. Create S3 bucket: market-pulse-processed-colors
4. Set S3_BUCKET_NAME in environment or use default
5. Enable this service by setting USE_S3=true

This service will replace OutputService when ready.
================================
"""
import os
import json
import logging
from typing import List, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

# Check if boto3 is available
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("boto3 not installed. Run: pip install boto3")


class S3Service:
    """
    S3 Service for storing and retrieving processed colors
    
    **Features:**
    - Store processed colors as CSV/Parquet in S3
    - Search with multiple filters
    - Pagination support
    - Date range queries
    - S3 Select for server-side filtering (fast!)
    
    **File Structure in S3:**
    s3://bucket-name/
        processed_colors/
            year=2026/
                month=01/
                    colors_2026-01-15.csv
                    colors_2026-01-16.csv
                month=02/
                    colors_2026-02-01.csv
    """
    
    def __init__(
        self,
        bucket_name: str = None,
        region: str = None,
        prefix: str = "processed_colors"
    ):
        """
        Initialize S3 service
        
        Args:
            bucket_name: S3 bucket name (default from env)
            region: AWS region (default from env or us-east-1)
            prefix: S3 prefix/folder for processed colors
        """
        if not S3_AVAILABLE:
            raise ImportError("boto3 not installed. Run: pip install boto3")
        
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME", "market-pulse-processed-colors")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.prefix = prefix
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=self.region)
        
        logger.info(f"S3Service initialized: bucket={self.bucket_name}, region={self.region}")
        
        # Verify bucket exists
        self._verify_bucket()
    
    def _verify_bucket(self):
        """Verify S3 bucket exists and is accessible"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ S3 bucket '{self.bucket_name}' is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.warning(f"S3 bucket '{self.bucket_name}' does not exist. Creating...")
                self._create_bucket()
            else:
                logger.error(f"Error accessing S3 bucket: {e}")
                raise
    
    def _create_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            logger.info(f"✅ Created S3 bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    def _get_s3_key(self, date: datetime = None) -> str:
        """
        Generate S3 key with partitioning by year/month
        
        Args:
            date: Date for partitioning (default: today)
            
        Returns:
            S3 key like: processed_colors/year=2026/month=02/colors_2026-02-02.csv
        """
        if date is None:
            date = datetime.now()
        
        year = date.strftime("%Y")
        month = date.strftime("%m")
        day_str = date.strftime("%Y-%m-%d")
        
        return f"{self.prefix}/year={year}/month={month}/colors_{day_str}.csv"
    
    def upload_processed_colors(
        self,
        colors: List[dict],
        processing_type: str = "AUTOMATED",
        date: datetime = None
    ) -> str:
        """
        Upload processed colors to S3 as CSV
        
        Args:
            colors: List of color dictionaries
            processing_type: AUTOMATED or MANUAL
            date: Date for partitioning (default: today)
            
        Returns:
            S3 key where data was uploaded
        """
        if not colors:
            logger.warning("No colors to upload")
            return ""
        
        # Convert to DataFrame
        df = pd.DataFrame(colors)
        
        # Add metadata
        df['PROCESSING_TYPE'] = processing_type
        df['UPLOADED_AT'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate S3 key
        s3_key = self._get_s3_key(date)
        
        # Convert to CSV
        csv_buffer = df.to_csv(index=False)
        
        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_buffer,
                ContentType='text/csv',
                Metadata={
                    'processing_type': processing_type,
                    'record_count': str(len(colors)),
                    'uploaded_at': datetime.now().isoformat()
                }
            )
            logger.info(f"✅ Uploaded {len(colors)} colors to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    def search_processed_colors(
        self,
        cusip: str = None,
        ticker: str = None,
        message_id: int = None,
        asset_class: str = None,
        source: str = None,
        bias: str = None,
        processing_type: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[dict]:
        """
        Search processed colors in S3 with filters
        
        **Performance:** Uses S3 Select for server-side filtering (fast!)
        
        Args:
            cusip: Filter by CUSIP
            ticker: Filter by ticker
            message_id: Filter by message ID
            asset_class: Filter by sector
            source: Filter by source
            bias: Filter by bias
            processing_type: AUTOMATED or MANUAL
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            limit: Max records to return
            skip: Number of records to skip (pagination)
            
        Returns:
            List of color dictionaries matching filters
        """
        logger.info(f"Searching S3 with filters: cusip={cusip}, ticker={ticker}, limit={limit}")
        
        # Build SQL query for S3 Select
        where_clauses = []
        
        if cusip:
            where_clauses.append(f"s.CUSIP = '{cusip}'")
        if ticker:
            where_clauses.append(f"s.TICKER = '{ticker}'")
        if message_id:
            where_clauses.append(f"s.MESSAGE_ID = {message_id}")
        if asset_class:
            where_clauses.append(f"s.SECTOR = '{asset_class}'")
        if source:
            where_clauses.append(f"s.SOURCE = '{source}'")
        if bias:
            where_clauses.append(f"s.BIAS = '{bias}'")
        if processing_type:
            where_clauses.append(f"s.PROCESSING_TYPE = '{processing_type}'")
        
        # Build SQL query
        sql = "SELECT * FROM S3Object s"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        # List all CSV files in S3 (with date filtering if needed)
        s3_keys = self._list_files(date_from, date_to)
        
        # Query each file with S3 Select
        all_results = []
        for s3_key in s3_keys:
            try:
                response = self.s3_client.select_object_content(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    ExpressionType='SQL',
                    Expression=sql,
                    InputSerialization={'CSV': {'FileHeaderInfo': 'USE'}},
                    OutputSerialization={'JSON': {}}
                )
                
                # Parse results
                for event in response['Payload']:
                    if 'Records' in event:
                        records = event['Records']['Payload'].decode('utf-8')
                        for line in records.strip().split('\n'):
                            if line:
                                all_results.append(json.loads(line))
                
            except ClientError as e:
                logger.warning(f"Error querying {s3_key}: {e}")
                continue
        
        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[skip:skip + limit]
        
        logger.info(f"✅ Found {total} results, returning {len(paginated_results)}")
        return paginated_results
    
    def _list_files(self, date_from: str = None, date_to: str = None) -> List[str]:
        """
        List all CSV files in S3, optionally filtered by date range
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            
        Returns:
            List of S3 keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            keys = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if key.endswith('.csv'):
                        # TODO: Filter by date range if needed
                        keys.append(key)
            
            logger.info(f"Found {len(keys)} files in S3")
            return keys
            
        except ClientError as e:
            logger.error(f"Error listing S3 files: {e}")
            return []
    
    def get_statistics(self) -> dict:
        """
        Get statistics about stored data in S3
        
        Returns:
            Dictionary with counts and storage info
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            total_files = 0
            total_size = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    total_files += 1
                    total_size += obj['Size']
            
            return {
                'bucket': self.bucket_name,
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'prefix': self.prefix
            }
            
        except ClientError as e:
            logger.error(f"Error getting S3 statistics: {e}")
            return {}


# Singleton instance
_s3_service_instance = None

def get_s3_service() -> S3Service:
    """Get singleton S3 service instance"""
    global _s3_service_instance
    if _s3_service_instance is None:
        _s3_service_instance = S3Service()
    return _s3_service_instance


# Helper function to check if S3 is enabled
def is_s3_enabled() -> bool:
    """Check if S3 integration is enabled"""
    return S3_AVAILABLE and os.getenv("USE_S3", "false").lower() == "true"
