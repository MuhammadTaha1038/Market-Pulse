#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle Database Sample Data Extraction Script
=============================================

This script automatically fetches Oracle credentials from AWS SSM Parameter Store
and extracts sample data. No manual configuration needed!

Requirements:
- VPN connection to Oracle database must be active
- Python 3.8+ with required packages
- AWS credentials configured (via AWS CLI or IAM role)

Usage:
    # Default extraction (uses company's SSM parameters)
    python extract_sample_data.py

    # Specify environment
    python extract_sample_data.py --env qa

    # Custom output directory
    python extract_sample_data.py --output ./my_sample_data

That's it! The script will:
1. Fetch credentials from SSM automatically
2. Connect to Oracle database
3. Extract sample data
4. Save to CSV and JSON files
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import required libraries
import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import cx_Oracle
import pandas as pd


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 70)
print("   MarketPulse - Oracle Data Extraction Tool")
print("=" * 70)
print()


class SSMParameterFetcher:
    """Automatically fetch database credentials from AWS SSM Parameter Store"""
    
    def __init__(self, app_prefix: str = "sp-incb", env: str = "qa", app_name: str = "market-pulse", region: str = "us-east-1"):
        """
        Initialize SSM parameter fetcher
        
        Args:
            app_prefix: Application prefix (default: sp-incb)
            env: Environment (qa, ci, prod)
            app_name: Application name (default: market-pulse)
            region: AWS region
        """
        self.app_prefix = app_prefix
        self.env = env
        self.app_name = app_name
        self.region = region
        
        try:
            self.ssm_client = boto3.client('ssm', region_name=region)
            logger.info(f"✓ Connected to AWS SSM in region: {region}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to AWS SSM: {e}")
            logger.error("  Make sure AWS credentials are configured (run: aws configure)")
            sys.exit(1)
    
    def get_parameter(self, param_path: str, decrypt: bool = True) -> Optional[str]:
        """Get parameter value from SSM"""
        try:
            response = self.ssm_client.get_parameter(
                Name=param_path,
                WithDecryption=decrypt
            )
            value = response['Parameter']['Value']
            logger.info(f"✓ Retrieved: {param_path}")
            return value
        except self.ssm_client.exceptions.ParameterNotFound:
            logger.warning(f"✗ Parameter not found: {param_path}")
            return None
        except Exception as e:
            logger.error(f"✗ Error retrieving {param_path}: {e}")
            return None
    
    def get_database_credentials(self) -> Dict[str, str]:
        """
        Fetch database credentials from SSM
        Uses company's standard parameter structure matching Terraform ssm.tf
        """
        logger.info("\n📥 Fetching database credentials from SSM...")
        
        # Correct SSM parameter structure (matching Terraform configuration)
        param_prefix = f"/{self.app_prefix}/{self.env}/{self.app_name}"
        
        logger.info(f"   Looking for parameters at: {param_prefix}/oracle/*")
        
        credentials = {
            'host': self.get_parameter(f"{param_prefix}/oracle/host"),
            'port': self.get_parameter(f"{param_prefix}/oracle/port"),
            'service_name': self.get_parameter(f"{param_prefix}/oracle/service_name"),
            'username': self.get_parameter(f"{param_prefix}/oracle/username"),
            'password': self.get_parameter(f"{param_prefix}/oracle/password"),
        }
        
        # If parameters not found in SSM, use defaults or environment variables
        if 'host' not in credentials or not credentials['host']:
            if self.env == 'prod':
                credentials['host'] = os.environ.get('ORACLE_HOST', 'sftprod.ihsmpricingdata.com')
                credentials['service_name'] = os.environ.get('ORACLE_SERVICE_NAME', 'STFB1PD_APP.ec2.internal')
            else:
                credentials['host'] = os.environ.get('ORACLE_HOST', 'sftfqa.ihsmpricingdata-dev.com')
                credentials['service_name'] = os.environ.get('ORACLE_SERVICE_NAME', 'stfb2qa_app.ec2.internal')
            
            logger.info(f"ℹ Using default host for {self.env}: {credentials['host']}")
        
        if not credentials.get('port'):
            credentials['port'] = os.environ.get('ORACLE_PORT', '1521')
        
        # Validate required credentials
        if not credentials.get('username') or not credentials.get('password'):
            logger.error("\n✗ ERROR: Could not retrieve database credentials from SSM")
            logger.error(f"  Expected parameter path: {param_prefix}/oracle/username")
            logger.error(f"  Expected parameter path: {param_prefix}/oracle/password")
            logger.error("\n  Please ensure:")
            logger.error("  1. You have AWS credentials configured (run: aws configure)")
            logger.error("  2. Your IAM role/user has SSM read permissions")
            logger.error("  3. SSM parameters exist at the correct path")
            logger.error("  4. OR set environment variables: ORACLE_HOST, ORACLE_USERNAME, ORACLE_PASSWORD")
            sys.exit(1)
        
        logger.info(f"✓ Successfully retrieved credentials for user: {credentials['username']}")
        return credentials


class OracleDataExtractor:
    """Extract sample data from Oracle database using SQLAlchemy"""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.engine = None
        self.session = None
        
    def create_connection_string(self) -> str:
        """Build Oracle connection string for SQLAlchemy"""
        username = self.credentials['username']
        password = self.credentials['password']
        host = self.credentials['host']
        port = self.credentials.get('port', '1521')
        service_name = self.credentials.get('service_name', 'ORCL')
        
        # SQLAlchemy connection string format
        # oracle+cx_oracle://user:pass@host:port/?service_name=service
        connection_string = (
            f"oracle+cx_oracle://{username}:{password}@"
            f"{host}:{port}/?service_name={service_name}"
        )
        
        return connection_string
    
    def connect(self):
        """Establish database connection using SQLAlchemy"""
        try:
            logger.info("\n🔌 Connecting to Oracle database...")
            logger.info(f"   Host: {self.credentials['host']}")
            logger.info(f"   Port: {self.credentials.get('port', '1521')}")
            logger.info(f"   Service: {self.credentials.get('service_name', 'N/A')}")
            
            connection_string = self.create_connection_string()
            
            # Create engine
            self.engine = create_engine(connection_string, echo=False)
            
            # Create session
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            
            # Test connection
            self.session.execute(text("SELECT 1 FROM DUAL"))
            
            logger.info("✓ Successfully connected to Oracle database!")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to connect to Oracle database: {e}")
            logger.error("\n  Troubleshooting:")
            logger.error("  1. Ensure you are connected to VPN")
            logger.error("  2. Verify database host is accessible")
            logger.error("  3. Check if credentials are correct")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        logger.info("✓ Database connection closed")
    
    def get_database_info(self) -> Dict:
        """Get basic database information"""
        try:
            # Get database version
            result = self.session.execute(text("SELECT * FROM V$VERSION WHERE ROWNUM = 1"))
            version = result.fetchone()[0]
            
            # Get current user
            result = self.session.execute(text("SELECT USER FROM DUAL"))
            current_user = result.fetchone()[0]
            
            # Get current timestamp
            result = self.session.execute(text("SELECT SYSDATE FROM DUAL"))
            db_time = result.fetchone()[0]
            
            return {
                'version': version,
                'current_user': current_user,
                'database_time': str(db_time)
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}
    
    def list_accessible_tables(self, schema: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """List accessible tables"""
        try:
            query = text("""
                SELECT 
                    OWNER,
                    TABLE_NAME,
                    NUM_ROWS,
                    TABLESPACE_NAME
                FROM ALL_TABLES
                WHERE ROWNUM <= :limit
                ORDER BY NUM_ROWS DESC NULLS LAST
            """)
            
            result = self.session.execute(query, {'limit': limit})
            
            tables = []
            for row in result:
                tables.append({
                    'schema': row[0],
                    'table_name': row[1],
                    'num_rows': row[2] or 0,
                    'tablespace': row[3]
                })
            
            return tables
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    def get_table_schema(self, table_name: str, schema: Optional[str] = None) -> List[Dict]:
        """Get table column information"""
        try:
            query_text = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    DATA_LENGTH,
                    DATA_PRECISION,
                    DATA_SCALE,
                    NULLABLE,
                    COLUMN_ID
                FROM ALL_TAB_COLUMNS
                WHERE TABLE_NAME = :table_name
            """
            
            params = {'table_name': table_name.upper()}
            
            if schema:
                query_text += " AND OWNER = :schema"
                params['schema'] = schema.upper()
            
            query_text += " ORDER BY COLUMN_ID"
            
            result = self.session.execute(text(query_text), params)
            
            columns = []
            for row in result:
                columns.append({
                    'column_name': row[0],
                    'data_type': row[1],
                    'data_length': row[2],
                    'precision': row[3],
                    'scale': row[4],
                    'nullable': row[5],
                    'column_id': row[6]
                })
            
            return columns
            
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return []
    
    def extract_sample_data(self, table_name: str, schema: Optional[str] = None, 
                           limit: int = 1000) -> tuple:
        """Extract sample data from specified table"""
        try:
            # Build query
            if schema:
                full_table_name = f"{schema.upper()}.{table_name.upper()}"
            else:
                full_table_name = table_name.upper()
            
            query_text = f"""
                SELECT * FROM {full_table_name}
                WHERE ROWNUM <= :limit
            """
            
            logger.info(f"\n📊 Extracting up to {limit} rows from {full_table_name}...")
            
            result = self.session.execute(text(query_text), {'limit': limit})
            
            # Get column names
            columns = list(result.keys())
            
            # Fetch data
            rows = result.fetchall()
            
            logger.info(f"✓ Extracted {len(rows)} rows with {len(columns)} columns")
            
            return columns, rows
            
        except Exception as e:
            logger.error(f"✗ Error extracting sample data: {e}")
            return [], []
    
    def save_to_csv(self, columns: List[str], rows: List[tuple], filepath: Path):
        """Save data to CSV file"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in rows:
                    # Convert all values to strings to handle Oracle types
                    writer.writerow([str(val) if val is not None else '' for val in row])
            
            logger.info(f"✓ Saved CSV: {filepath}")
            
        except Exception as e:
            logger.error(f"✗ Error saving CSV: {e}")
    
    def save_to_json(self, data: Dict, filepath: Path):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"✓ Saved JSON: {filepath}")
            
        except Exception as e:
            logger.error(f"✗ Error saving JSON: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract sample data from Oracle database - AUTOMATIC version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from QA environment (default)
  python extract_sample_data.py

  # Extract from production
  python extract_sample_data.py --env prod

  # List tables only
  python extract_sample_data.py --list-tables

  # Extract specific table
  python extract_sample_data.py --table MY_TABLE_NAME --schema MY_SCHEMA

Note: This script automatically fetches credentials from AWS SSM Parameter Store.
      Make sure you're connected to VPN and AWS credentials are configured.
        """
    )
    parser.add_argument(
        '--env',
        type=str,
        default='qa',
        choices=['qa', 'ci', 'ft', 'prod'],
        help='Environment to extract from (default: qa)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./sample_data',
        help='Output directory for sample data files (default: ./sample_data)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Maximum number of rows to extract (default: 1000)'
    )
    parser.add_argument(
        '--list-tables',
        action='store_true',
        help='List all accessible tables and exit'
    )
    parser.add_argument(
        '--table',
        type=str,
        help='Specific table name to extract'
    )
    parser.add_argument(
        '--schema',
        type=str,
        help='Schema name (optional)'
    )
    parser.add_argument(
        '--app-prefix',
        type=str,
        default='sp-incb',
        help='Application prefix for SSM parameters (default: sp-incb)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n🚀 Starting Oracle data extraction...")
    print(f"   Environment: {args.env}")
    print(f"   Output directory: {output_dir.absolute()}")
    print()
    
    # Step 1: Fetch credentials from SSM
    ssm_fetcher = SSMParameterFetcher(
        app_prefix=args.app_prefix,
        env=args.env,
        region=args.region
    )
    
    credentials = ssm_fetcher.get_database_credentials()
    
    # Step 2: Initialize extractor
    extractor = OracleDataExtractor(credentials)
    
    # Step 3: Connect to database
    if not extractor.connect():
        sys.exit(1)
    
    try:
        # Get database info
        logger.info("\n" + "=" * 70)
        logger.info("DATABASE INFORMATION")
        logger.info("=" * 70)
        
        db_info = extractor.get_database_info()
        for key, value in db_info.items():
            logger.info(f"  {key}: {value}")
        
        # Save database info
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_info['extraction_timestamp'] = timestamp
        db_info['environment'] = args.env
        db_info['extractor_config'] = {
            'host': credentials['host'],
            'port': credentials['port'],
            'service_name': credentials.get('service_name', 'N/A'),
            'user': credentials['username']
        }
        
        extractor.save_to_json(db_info, output_dir / 'database_info.json')
        
        # List accessible tables
        logger.info("\n" + "=" * 70)
        logger.info("ACCESSIBLE TABLES")
        logger.info("=" * 70)
        
        tables = extractor.list_accessible_tables(args.schema)
        logger.info(f"Found {len(tables)} accessible tables (showing top 50)")
        
        # Show top 50 tables
        for table in tables[:50]:
            logger.info(f"  {table['schema']}.{table['table_name']} ({table['num_rows']} rows)")
        
        extractor.save_to_json({'tables': tables}, output_dir / 'accessible_tables.json')
        
        if args.list_tables:
            logger.info(f"\n✓ Table list saved to {output_dir / 'accessible_tables.json'}")
            logger.info("\nTo extract data from a specific table, run:")
            logger.info(f"  python extract_sample_data.py --table TABLE_NAME --schema SCHEMA_NAME")
            return
        
        # Extract sample data from specified table
        table_to_extract = args.table
        schema_to_use = args.schema
        
        # If no table specified, try to find a likely candidate
        if not table_to_extract and tables:
            # Look for tables with "PRICING", "COLOR", or "MARKET" in the name
            keywords = ['PRICING', 'COLOR', 'MARKET', 'TRADE', 'SECURITY']
            for table in tables:
                if any(kw in table['table_name'].upper() for kw in keywords):
                    table_to_extract = table['table_name']
                    schema_to_use = table['schema']
                    logger.info(f"\nℹ Auto-selected table: {schema_to_use}.{table_to_extract}")
                    break
        
        if table_to_extract:
            logger.info("\n" + "=" * 70)
            logger.info(f"EXTRACTING SAMPLE DATA FROM {table_to_extract}")
            logger.info("=" * 70)
            
            # Get table schema
            schema_info = extractor.get_table_schema(table_to_extract, schema_to_use)
            
            if schema_info:
                logger.info(f"\n✓ Table has {len(schema_info)} columns:")
                for col in schema_info[:20]:  # Show first 20 columns
                    logger.info(f"  {col['column_name']:30} {col['data_type']}")
                if len(schema_info) > 20:
                    logger.info(f"  ... and {len(schema_info) - 20} more columns")
                
                extractor.save_to_json(
                    {'columns': schema_info},
                    output_dir / f'{table_to_extract}_schema.json'
                )
            
            # Extract sample data
            columns, rows = extractor.extract_sample_data(
                table_to_extract,
                schema_to_use,
                args.limit
            )
            
            if columns and rows:
                # Save as CSV
                csv_file = output_dir / f'{table_to_extract}_sample_{timestamp}.csv'
                extractor.save_to_csv(columns, rows, csv_file)
                
                # Save first 100 rows as JSON for easy inspection
                sample_json = []
                for row in rows[:100]:
                    row_dict = {}
                    for col, val in zip(columns, row):
                        row_dict[col] = str(val) if val is not None else None
                    sample_json.append(row_dict)
                
                extractor.save_to_json(
                    {'sample_data': sample_json},
                    output_dir / f'{table_to_extract}_sample_{timestamp}.json'
                )
        else:
            logger.warning("\nℹ No table specified for extraction")
            logger.info("  Use --table TABLE_NAME to extract specific table")
            logger.info("  Or use --list-tables to see all available tables")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ EXTRACTION COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"\n📁 Output directory: {output_dir.absolute()}")
        logger.info("\n📦 Generated files:")
        for file in output_dir.glob('*'):
            logger.info(f"   - {file.name}")
        
        logger.info("\n📧 Next steps:")
        logger.info("  1. Review the extracted data files")
        logger.info("  2. Create a ZIP archive:")
        if sys.platform == 'win32':
            logger.info(f"     Compress-Archive -Path {output_dir}\\* -DestinationPath MarketPulse_Data.zip")
        else:
            logger.info(f"     zip -r MarketPulse_Data.zip {output_dir}/")
        logger.info("  3. Share the ZIP file with the development team")
        logger.info("\n✨ Thank you!")
        
    finally:
        extractor.disconnect()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Extraction cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
