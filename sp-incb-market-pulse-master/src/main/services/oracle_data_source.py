"""
Oracle Database Data Source Implementation.
Fetches credentials from client API and queries Oracle DB using dynamic column mapping.
"""
import os
import json
import requests
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from data_source_interface import DataSourceInterface

# Optional import - only needed when Oracle is configured
try:
    import oracledb
    ORACLE_DRIVER_AVAILABLE = True
except ImportError:
    ORACLE_DRIVER_AVAILABLE = False
    oracledb = None


class OracleDataSource(DataSourceInterface):
    """Oracle database data source implementation with dynamic column mapping."""
    
    def __init__(self):
        """Initialize Oracle data source with configuration."""
        # Load configuration from environment or config file
        self.credentials_api_url = os.getenv("ORACLE_CREDENTIALS_API_URL", "")
        self.oracle_host = os.getenv("ORACLE_HOST", "")
        self.oracle_port = int(os.getenv("ORACLE_PORT", "1521"))
        self.oracle_service = os.getenv("ORACLE_SERVICE_NAME", "")
        self.oracle_table = os.getenv("ORACLE_TABLE_NAME", "COLOR_DATA")
        
        # Cache credentials with TTL
        self._cached_credentials = None
        self._credentials_cache_time = None
        self._credentials_ttl = 3600  # 1 hour TTL
        
        # Load column mapping configuration
        self.column_config = self._load_column_config()
    
    def _load_column_config(self) -> Dict[str, Any]:
        """Load column configuration from column_config.json."""
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
            config_path = os.path.join(project_root, "column_config.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                print(f"Warning: column_config.json not found at {config_path}")
                return {}
        except Exception as e:
            print(f"Error loading column_config.json: {str(e)}")
            return {}
    
    def _check_driver_available(self):
        """Check if Oracle driver is available."""
        if not ORACLE_DRIVER_AVAILABLE:
            raise RuntimeError("Oracle driver not installed. Install with: pip install oracledb")
    
    def _fetch_credentials(self) -> Dict[str, str]:
        """
        Fetch Oracle credentials from client's API.
        Implements caching with TTL to avoid frequent API calls.
        
        Returns:
            Dict with 'username' and 'password'
        """
        # Check cache
        if self._cached_credentials and self._credentials_cache_time:
            time_since_cache = datetime.now() - self._credentials_cache_time
            if time_since_cache.total_seconds() < self._credentials_ttl:
                return self._cached_credentials
        
        # Fetch from API
        if not self.credentials_api_url:
            raise ValueError("ORACLE_CREDENTIALS_API_URL not configured")
        
        try:
            response = requests.get(self.credentials_api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract credentials using the keys provided by client
            username = data.get("eval.jdbc.user")
            password = data.get("eval.jdbc.password")
            
            if not username or not password:
                raise ValueError("Credentials not found in API response")
            
            # Cache credentials
            self._cached_credentials = {
                "username": username,
                "password": password
            }
            self._credentials_cache_time = datetime.now()
            
            return self._cached_credentials
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch credentials from API: {str(e)}")
    
    def _get_clo_column_mapping(self, clo_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get column mapping for specific CLO from column_config.json.
        
        Args:
            clo_id: CLO identifier to get mapping for
            
        Returns:
            Dict mapping standard column names to Oracle column names
        """
        if not clo_id or not self.column_config:
            # Return default mapping if no CLO specified or config not loaded
            return {
                "MESSAGE_ID": "MESSAGE_ID",
                "TICKER": "TICKER",
                "CUSIP": "CUSIP",
                "DATE": "DATE",
                "BID": "BID",
                "ASK": "ASK",
                "SOURCE": "SOURCE",
                "BIAS": "BIAS",
                "SECTOR": "SECTOR",
                "PRICE_LEVEL": "PRICE_LEVEL",
                "PX": "PX"
            }
        
        # Get CLO-specific mapping
        clo_config = self.column_config.get(clo_id, {})
        columns_config = clo_config.get("columns", {})
        
        # Build mapping: standard_name -> oracle_column_name
        column_mapping = {}
        for col_key, col_info in columns_config.items():
            if isinstance(col_info, dict) and col_info.get("enabled", False):
                display_name = col_info.get("display_name", col_key).upper()
                oracle_name = col_info.get("oracle_column_name", display_name)
                column_mapping[display_name] = oracle_name
        
        return column_mapping
    
    def _build_query(self, clo_id: Optional[str] = None) -> str:
        """
        Build SQL query using dynamic column mapping.
        
        Args:
            clo_id: CLO identifier for column mapping
            
        Returns:
            SQL query string
        """
        column_mapping = self._get_clo_column_mapping(clo_id)
        
        # Build SELECT clause with aliasing
        select_clauses = []
        for standard_name, oracle_name in column_mapping.items():
            if standard_name == oracle_name:
                select_clauses.append(oracle_name)
            else:
                select_clauses.append(f"{oracle_name} AS {standard_name}")
        
        select_clause = ", ".join(select_clauses)
        
        # Build WHERE clause
        where_clause = ""
        if clo_id:
            where_clause = f" WHERE CLO_ID = '{clo_id}'"
        
        # Build complete query
        query = f"""
            SELECT {select_clause}
            FROM {self.oracle_table}
            {where_clause}
            ORDER BY DATE DESC
        """
        
        return query
    
    def fetch_data(self, clo_id: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch data from Oracle database using dynamic column mapping.
        
        Args:
        self._check_driver_available()
        
            clo_id: Optional CLO identifier to filter data and determine column mapping
            
        Returns:
            DataFrame with standardized column names
        """
        if not all([self.oracle_host, self.oracle_port, self.oracle_service]):
            raise ValueError("Oracle connection details not configured")
        
        # Fetch credentials
        credentials = self._fetch_credentials()
        
        # Build connection string
        dsn = oracledb.makedsn(
            self.oracle_host,
            self.oracle_port,
            service_name=self.oracle_service
        )
        
        # Connect and query
        connection = None
        try:
            connection = oracledb.connect(
                user=credentials["username"],
                password=credentials["password"],
                dsn=dsn
            )
            
            # Build query with dynamic column mapping
            query = self._build_query(clo_id)
            
            # Execute query and load into DataFrame
            df = pd.read_sql(query, connection)
            
            # Standardize column names (uppercase, strip spaces)
            df.columns = df.columns.str.strip().str.upper()
            
            return df
            
        except oracledb.Error as e:
            raise ConnectionError(f"Oracle database error: {str(e)}")
        finally:
            if connection:
                connection.close()
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Oracle database connection.
        
        Returns:
            Dict with status and message
        """
        try:
            # Check driver availability
            if not ORACLE_DRIVER_AVAILABLE:
                return {
                    "status": "error",
                    "message": "Oracle driver not installed. Install with: pip install oracledb"
                }
            
            # Check configuration
            if not self.credentials_api_url:
                return {
                    "status": "error",
                    "message": "ORACLE_CREDENTIALS_API_URL not configured"
                }
            
            if not all([self.oracle_host, self.oracle_port, self.oracle_service]):
                return {
                    "status": "error",
                    "message": "Oracle connection details incomplete (host/port/service)"
                }
            
            # Test credentials API
            credentials = self._fetch_credentials()
            
            # Test database connection
            dsn = oracledb.makedsn(
                self.oracle_host,
                self.oracle_port,
                service_name=self.oracle_service
            )
            
            connection = oracledb.connect(
                user=credentials["username"],
                password=credentials["password"],
                dsn=dsn
            )
            
            # Test query
            cursor = connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self.oracle_table}")
            row_count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            
            return {
                "status": "success",
                "message": f"Oracle connection successful. Table has {row_count} rows."
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Oracle connection failed: {str(e)}"
            }
    
    def get_source_info(self) -> Dict[str, str]:
        """
        Get information about the Oracle data source.
        
        Returns:
            Dict with source type and connection details
        """
        return {
            "type": "Oracle",
            "host": self.oracle_host,
            "port": str(self.oracle_port),
            "service": self.oracle_service,
            "table": self.oracle_table,
            "credentials_api_configured": str(bool(self.credentials_api_url))
        }
