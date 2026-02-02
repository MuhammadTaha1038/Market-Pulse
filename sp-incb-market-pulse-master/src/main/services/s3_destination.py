"""
AWS S3 Output Destination Implementation.
Uploads processed data to AWS S3 bucket.
"""
import os
import io
import pandas as pd
from typing import Dict, Any, Optional
from output_destination_interface import OutputDestinationInterface

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


class S3Destination(OutputDestinationInterface):
    """AWS S3 output destination implementation."""
    
    def __init__(self):
        """Initialize S3 output destination with configuration."""
        # Load configuration from environment
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "")
        self.region = os.getenv("S3_REGION", "us-east-1")
        self.prefix = os.getenv("S3_PREFIX", "processed_colors/")  # Folder structure in S3
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        
        # File format configuration
        self.file_format = os.getenv("S3_FILE_FORMAT", "xlsx")  # xlsx, csv, parquet
        
        # Initialize S3 client (lazy initialization in save_output)
        self._s3_client = None
    
    def _get_s3_client(self):
        """Get or create S3 client."""
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 not installed. Install with: pip install boto3")
        
        if self._s3_client is None:
            if self.access_key and self.secret_key:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
            else:
                # Use IAM role or default credentials
                self._s3_client = boto3.client('s3', region_name=self.region)
        
        return self._s3_client
    
    def _prepare_file_buffer(self, df: pd.DataFrame) -> io.BytesIO:
        """
        Prepare DataFrame as file buffer based on configured format.
        
        Args:
            df: DataFrame to save
            
        Returns:
            BytesIO buffer containing the file data
        """
        buffer = io.BytesIO()
        
        if self.file_format == "csv":
            df.to_csv(buffer, index=False)
        elif self.file_format == "parquet":
            df.to_parquet(buffer, index=False, engine='pyarrow')
        else:  # Default to xlsx
            df.to_excel(buffer, index=False, engine='openpyxl')
        
        buffer.seek(0)
        return buffer
    
    def save_output(self, df: pd.DataFrame, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save DataFrame to AWS S3.
        
        Args:
            df: DataFrame to save
            filename: S3 object key/filename
            metadata: Optional metadata to attach as S3 object metadata
            
        Returns:
            Dict with status, message, and S3 location
        """
        try:
            if not self.bucket_name:
                return {
                    "status": "error",
                    "message": "S3_BUCKET_NAME not configured",
                    "location": None,
                    "type": "s3"
                }
            
            # Ensure filename has correct extension
            if not filename.endswith(f'.{self.file_format}'):
                base_name = filename.rsplit('.', 1)[0]
                filename = f"{base_name}.{self.file_format}"
            
            # Build S3 key with prefix
            s3_key = f"{self.prefix}{filename}".lstrip('/')
            
            # Prepare file buffer
            file_buffer = self._prepare_file_buffer(df)
            
            # Prepare metadata
            s3_metadata = {}
            if metadata:
                # Convert metadata values to strings (S3 requirement)
                s3_metadata = {k: str(v) for k, v in metadata.items()}
            
            # Upload to S3
            s3_client = self._get_s3_client()
            s3_client.upload_fileobj(
                file_buffer,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': s3_metadata,
                    'ContentType': self._get_content_type()
                }
            )
            
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            
            return {
                "status": "success",
                "message": f"Uploaded to S3: {s3_key}",
                "location": s3_url,
                "type": "s3",
                "bucket": self.bucket_name,
                "key": s3_key
            }
            
        except NoCredentialsError:
            return {
                "status": "error",
                "message": "AWS credentials not found. Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY",
                "location": None,
                "type": "s3"
            }
        except ClientError as e:
            return {
                "status": "error",
                "message": f"S3 upload failed: {str(e)}",
                "location": None,
                "type": "s3"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error during S3 upload: {str(e)}",
                "location": None,
                "type": "s3"
            }
    
    def _get_content_type(self) -> str:
        """Get content type based on file format."""
        content_types = {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
            "parquet": "application/octet-stream"
        }
        return content_types.get(self.file_format, "application/octet-stream")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test S3 connection and permissions.
        
        Returns:
            # Check boto3 availability
            if not BOTO3_AVAILABLE:
                return {
                    "status": "error",
                    "message": "boto3 not installed. Install with: pip install boto3"
                }
            
            Dict with status and message
        """
        try:
            if not self.bucket_name:
                return {
                    "status": "error",
                    "message": "S3_BUCKET_NAME not configured"
                }
            
            # Test credentials and bucket access
            s3_client = self._get_s3_client()
            
            # Check if bucket exists and is accessible
            s3_client.head_bucket(Bucket=self.bucket_name)
            
            return {
                "status": "success",
                "message": f"S3 bucket accessible: {self.bucket_name}"
            }
            
        except NoCredentialsError:
            return {
                "status": "error",
                "message": "AWS credentials not found"
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return {
                    "status": "error",
                    "message": f"S3 bucket not found: {self.bucket_name}"
                }
            elif error_code == '403':
                return {
                    "status": "error",
                    "message": f"Access denied to S3 bucket: {self.bucket_name}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"S3 connection error: {str(e)}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"S3 connection test failed: {str(e)}"
            }
    
    def get_destination_info(self) -> Dict[str, str]:
        """
        Get information about the S3 destination.
        
        Returns:
            Dict with destination type and configuration
        """
        return {
            "type": "AWS S3",
            "bucket": self.bucket_name,
            "region": self.region,
            "prefix": self.prefix,
            "file_format": self.file_format,
            "credentials_configured": str(bool(self.access_key and self.secret_key))
        }
