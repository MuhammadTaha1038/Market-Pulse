#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database Configuration Module
Manages Oracle database connections using AWS SSM Parameter Store
Compatible with company's SSM parameter structure
"""

import os
import logging
from typing import Dict, Optional
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import based on available Oracle driver
try:
    import cx_Oracle
    ORACLE_DRIVER = "cx_Oracle"
except ImportError:
    try:
        import oracledb as cx_Oracle
        ORACLE_DRIVER = "oracledb"
    except ImportError:
        raise ImportError("Neither cx_Oracle nor oracledb is installed. Please install one of them.")

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Manages database configuration from AWS SSM Parameter Store"""
    
    def __init__(self, region_name: str = None, use_local_env: bool = False):
        """
        Initialize database configuration
        
        Args:
            region_name: AWS region name. Defaults to environment variable or 'us-east-1'
            use_local_env: If True, use local environment variables instead of SSM
        """
        self.region_name = region_name or os.environ.get('AWS_REGION', 'us-east-1')
        self.use_local_env = use_local_env
        self.ssm_client = None
        
        if not use_local_env:
            try:
                self.ssm_client = boto3.client('ssm', region_name=self.region_name)
            except Exception as e:
                logger.warning(f"Failed to initialize SSM client: {e}. Falling back to environment variables.")
                self.use_local_env = True
        
        # Company's SSM parameter structure
        self.app_prefix = os.environ.get('APP_PREFIX', 'sp-incb')
        self.env = os.environ.get('ENV', 'qa')
        self.app_name = os.environ.get('APP_NAME', 'market-pulse')
        self.param_prefix = f"/{self.app_prefix}/{self.env}/{self.app_name}"
    
    def get_parameter(self, param_name: str, decrypt: bool = True) -> Optional[str]:
        """
        Get parameter from SSM Parameter Store or environment variable
        
        Args:
            param_name: Parameter name (e.g., 'pricing.db.username')
            decrypt: Whether to decrypt SecureString parameters
            
        Returns:
            Parameter value or None if not found
        """
        if self.use_local_env:
            # Try to get from environment variables
            env_var_name = f"ORACLE_{param_name.upper().replace('/', '_').replace('ORACLE_', '')}"
            value = os.environ.get(env_var_name)
            if value:
                logger.info(f"Retrieved {param_name} from environment variable {env_var_name}")
            return value
        
        try:
            full_param_name = f"{self.param_prefix}/{param_name}"
            response = self.ssm_client.get_parameter(
                Name=full_param_name,
                WithDecryption=decrypt
            )
            value = response['Parameter']['Value']
            
            # Skip placeholder values
            if value.startswith('PLACEHOLDER'):
                logger.warning(f"Parameter {full_param_name} has placeholder value")
                return None
            
            logger.info(f"Retrieved parameter {full_param_name} from SSM")
            return value
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning(f"Parameter {full_param_name} not found in SSM")
            else:
                logger.error(f"Error retrieving parameter {full_param_name}: {e}")
            return None
    
    def get_connection_config(self) -> Dict[str, str]:
        """
        Get database connection configuration using company's SSM structure
        
        Returns:
            Dictionary with connection parameters
        """
        # Fetch from SSM (correct paths matching Terraform ssm.tf)
        host = self.get_parameter('oracle/host')
        port = self.get_parameter('oracle/port')
        service_name = self.get_parameter('oracle/service_name')
        username = self.get_parameter('oracle/username')
        password = self.get_parameter('oracle/password')
        
        # Environment-specific defaults
        if self.env == 'prod':
            default_host = 'sftprod.ihsmpricingdata.com'
            default_service = 'STFB1PD_APP.ec2.internal'
        else:
            default_host = 'sftfqa.ihsmpricingdata-dev.com'
            default_service = 'stfb2qa_app.ec2.internal'
        
        config = {
            'host': host or os.environ.get('ORACLE_HOST', default_host),
            'port': int(port or os.environ.get('ORACLE_PORT', '1521')),
            'service_name': service_name or os.environ.get('ORACLE_SERVICE_NAME', default_service),
            'username': username or os.environ.get('ORACLE_USERNAME'),
            'password': password or os.environ.get('ORACLE_PASSWORD')
        }
        
        # Validate required parameters
        required_params = ['host', 'username', 'password']
        missing = [k for k in required_params if not config.get(k)]
        
        if missing:
            raise ValueError(f"Missing required database parameters: {', '.join(missing)}")
        
        return config


class OracleDatabase:
    """Oracle Database connection manager using SQLAlchemy"""
    
    def __init__(self, config: DatabaseConfig = None):
        """
        Initialize Oracle database connection
        
        Args:
            config: DatabaseConfig instance. If None, creates a new one.
        """
        self.config = config or DatabaseConfig()
        self.engine = None
        self.Session = None
        self.connection_params = None
        
        logger.info(f"Using Oracle driver: {ORACLE_DRIVER}")
    
    def create_connection_string(self, conn_config: Dict) -> str:
        """
        Build SQLAlchemy connection string for Oracle
        
        Format: oracle+cx_oracle://user:pass@host:port/?service_name=service
        """
        username = conn_config['username']
        password = conn_config['password']
        host = conn_config['host']
        port = conn_config['port']
        service_name = conn_config['service_name']
        
        # URL encode password to handle special characters
        from urllib.parse import quote_plus
        password_encoded = quote_plus(password)
        username_encoded = quote_plus(username)
        
        connection_string = (
            f"oracle+cx_oracle://{username_encoded}:{password_encoded}@"
            f"{host}:{port}/?service_name={service_name}"
        )
        
        return connection_string
    
    def connect(self):
        """
        Establish connection to Oracle database
        
        Returns:
            SQLAlchemy engine object
        """
        try:
            conn_config = self.config.get_connection_config()
            
            # Store connection params (without password for logging)
            self.connection_params = {
                'host': conn_config['host'],
                'port': conn_config['port'],
                'service_name': conn_config['service_name'],
                'username': conn_config['username']
            }
            
            logger.info(f"Connecting to Oracle database at {conn_config['host']}:{conn_config['port']}")
            
            # Create connection string
            connection_string = self.create_connection_string(conn_config)
            
            # Create engine
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=False
            )
            
            # Create session maker
            self.Session = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM DUAL"))
            
            logger.info("Successfully connected to Oracle database")
            return self.engine
            
        except Exception as e:
            logger.error(f"Failed to connect to Oracle database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.engine:
            try:
                self.engine.dispose()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.engine = None
                self.Session = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def get_session(self):
        """
        Get a new database session
        
        Returns:
            SQLAlchemy session object
        """
        if not self.Session:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        return self.Session()
    
    def execute_query(self, query: str, params: dict = None):
        """
        Execute a SQL query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results
        """
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # Fetch results if SELECT query
                if query.strip().upper().startswith('SELECT'):
                    columns = list(result.keys())
                    rows = result.fetchall()
                    return columns, rows
                else:
                    conn.commit()
                    return None, None
                    
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def get_table_schema(self, table_name: str = None, schema: str = None):
        """
        Get table schema information
        
        Args:
            table_name: Name of the table
            schema: Schema name
            
        Returns:
            List of column information
        """
        if not table_name:
            raise ValueError("Table name not specified")
        
        query = """
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                DATA_LENGTH, 
                NULLABLE,
                DATA_DEFAULT
            FROM ALL_TAB_COLUMNS
            WHERE TABLE_NAME = :table_name
        """
        
        params = {'table_name': table_name.upper()}
        
        if schema:
            query += " AND OWNER = :schema"
            params['schema'] = schema.upper()
        
        query += " ORDER BY COLUMN_ID"
        
        columns, results = self.execute_query(query, params)
        
        return [{
            'column_name': row[0],
            'data_type': row[1],
            'data_length': row[2],
            'nullable': row[3],
            'default_value': row[4]
        } for row in results]
