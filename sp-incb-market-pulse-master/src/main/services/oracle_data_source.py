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
    
    # Initialize thick mode for Network Encryption support
    _thick_mode_initialized = False
    try:
        oracledb.init_oracle_client()
        _thick_mode_initialized = True
    except Exception:
        # Thick mode not available, will use thin mode (limited encryption)
        pass
        
except ImportError:
    ORACLE_DRIVER_AVAILABLE = False
    oracledb = None
    _thick_mode_initialized = False


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
        Fetch Oracle credentials from client's API or .env file.
        Priority: API -> .env fallback
        Implements caching with TTL to avoid frequent API calls.
        
        Returns:
            Dict with 'username' and 'password'
        """
        # Check cache
        if self._cached_credentials and self._credentials_cache_time:
            time_since_cache = datetime.now() - self._credentials_cache_time
            if time_since_cache.total_seconds() < self._credentials_ttl:
                return self._cached_credentials
        
        username = None
        password = None
        
        # Try to fetch from API first
        if self.credentials_api_url:
            try:
                response = requests.get(self.credentials_api_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Extract credentials using the keys provided by client
                username = data.get("eval.jdbc.user")
                password = data.get("eval.jdbc.password")
                
                if username and password:
                    # Cache credentials
                    self._cached_credentials = {
                        "username": username,
                        "password": password
                    }
                    self._credentials_cache_time = datetime.now()
                    return self._cached_credentials
                    
            except requests.RequestException as e:
                print(f"Warning: Failed to fetch credentials from API: {str(e)}")
                print("Falling back to .env file credentials...")
        
        # Fallback to .env file if API failed or not configured
        if not username or not password:
            username = os.getenv("ORACLE_USERNAME")
            password = os.getenv("ORACLE_PASSWORD")
            
            if username and password:
                # Cache credentials
                self._cached_credentials = {
                    "username": username,
                    "password": password
                }
                self._credentials_cache_time = datetime.now()
                return self._cached_credentials
        
        # If we still don't have credentials, raise error
        raise ValueError("Oracle credentials not available from API or .env file")
    
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
        Build SQL query to fetch CLO color data from Oracle.
        First checks if CLO has a saved custom query in column_config.json,
        otherwise uses the default production query.
        
        Args:
            clo_id: CLO identifier - if provided, checks for custom query
            
        Returns:
            SQL query string
        """
        # Check if CLO has a saved custom query in column_config.json
        if clo_id and self.column_config:
            clo_config = self.column_config.get(clo_id, {})
            queries = clo_config.get("queries", {})
            
            # Use base_query if available
            if "base_query" in queries:
                saved_query = queries["base_query"].get("query", "")
                if saved_query:
                    print(f"Using custom query for CLO {clo_id}")
                    return saved_query
        
        # Default production query for fetching CLO color data
        query = """
WITH SEC_MASTER AS (
    SELECT MASTER.SEC_ID,
           MASTER.SEC_ID_TYPE,
           FIELD_NAME,
           CASE
               WHEN FIELD_TYPE = 'String' THEN FIELD_STRING_VALUE
               WHEN FIELD_TYPE = 'Integer' THEN TO_CHAR(FIELD_INTEGER_VALUE)
           END AS FIELD_VALUE
    FROM SECURITY_MASTER MASTER
    LEFT JOIN SEC_INDICATIVE_INFO DEAL
        ON DEAL.SEC_ID = MASTER.SEC_ID
        AND DEAL.SEC_ID_TYPE = MASTER.SEC_ID_TYPE
        AND DEAL.FIELD_NAME IN ('DealType', 'Currency', 'OriginalBestRatingScore', 'MkTicker')
    WHERE prc_config_sec_type = 'CLO'
        AND prc_CONFIG_KEY_NAME NOT IN ('All', 'CDO', 'CDO_Flat', 'TruPS', 'CRT')
        AND sec_status = 'Approved'
),
CLO_LIST AS (
    SELECT DISTINCT LIST.ROOTID,
           NVL(LIST.CUSIP, INTEX.CUSIP) AS CUSIP,
           NVL(LIST.ISIN, INTEX.ISIN) AS ISIN,
           REGEXP_SUBSTR(INFO.BBG, '^([A-Z0-9]+) ([A-Z0-9-]+) ([A-Z0-9-]+)$', 1, 1, 'i', 1) AS SHELF,
           REGEXP_SUBSTR(INFO.BBG, '^([A-Z0-9]+) ([A-Z0-9-]+) ([A-Z0-9-]+)$', 1, 1, 'i', 2) AS SERIES,
           REGEXP_SUBSTR(INFO.BBG, '^([A-Z0-9]+) ([A-Z0-9-]+) ([A-Z0-9-]+)$', 1, 1, 'i', 3) AS CLASS
    FROM (
        SELECT CONNECT_BY_ROOT ORIGID AS ROOTID,
               CASE DUPLICATETYPE
                   WHEN 'CUSIP' THEN DUPLICATEDID
                   ELSE ''
               END AS CUSIP,
               CASE DUPLICATETYPE
                   WHEN 'ISIN' THEN DUPLICATEDID
                   ELSE ''
               END AS ISIN
        FROM IDENTIFIERMAPPINGS
        START WITH ORIGID IN (SELECT SEC_ID FROM SEC_MASTER)
        CONNECT BY NOCYCLE ORIGID = PRIOR DUPLICATEDID

        UNION

        SELECT SEC_ID AS ROOTID,
               CASE SEC_ID_TYPE
                   WHEN 'CUSIP' THEN SEC_ID
                   ELSE ''
               END AS CUSIP,
               CASE SEC_ID_TYPE
                   WHEN 'ISIN' THEN SEC_ID
                   ELSE ''
               END AS ISIN
        FROM SEC_MASTER
    ) LIST
    LEFT JOIN INTEXBONDINFO INTEX
        ON INTEX.CUSIP = LIST.ROOTID
    LEFT JOIN (
        SELECT SEC_ID, FIELD_VALUE AS BBG
        FROM SEC_MASTER
        WHERE FIELD_NAME = 'MkTicker'
    ) INFO
        ON INFO.SEC_ID = LIST.ROOTID
),
TAINTED_COLOR AS (
    SELECT QUOTES.ROWID AS QUOTEID,
           QUOTES.MESSAGE_ID,
           QUOTES.CONTRIBUTOR,
           QUOTES.OWNER,
           QUOTES.PRICE_BID,
           QUOTES.PRICE_ASK,
           QUOTES.SPREAD_BID,
           QUOTES.SPREAD_ASK,
           QUOTES.BENCHMARK,
           QUOTES.WAL,
           QUOTES.PRICELEVEL,
           QUOTES.CONFIDENCE,
           CLO_LIST.ROOTID AS ROOT_CUSIP,
           QUOTES.CUSIP,
           QUOTES.ISIN,
           QUOTES.SHELF,
           QUOTES.SERIES,
           QUOTES.CLASS,
           NVL(QUOTES.BIAS, NVL2(QUOTES.PRICE_BID, 'BID', 'OFFER')) AS BIAS,
           CASE
               WHEN QUOTES.CONTRIBUTOR IN ('Aurul') THEN 1
               ELSE 0
           END AS TAINTED,
           QUOTES.TIME,
           TRUNC(QUOTES.TIME) AS MKT_DATE,
           NVL(QUOTES.PRICE_BID, QUOTES.PRICE_ASK) AS PRICE
    FROM SF_QUOTES_ABS QUOTES
    RIGHT JOIN CLO_LIST
        ON CLO_LIST.CUSIP = QUOTES.CUSIP
        OR CLO_LIST.ISIN = QUOTES.ISIN
        OR (CLO_LIST.SHELF = QUOTES.SHELF
            AND CLO_LIST.SERIES = QUOTES.SERIES
            AND CLO_LIST.CLASS = QUOTES.CLASS)
    WHERE QUOTES.OWNER <> 'DEMO'
        AND QUOTES.TIME >= TRUNC(SYSDATE) - 1
        AND (QUOTES.PRICE_BID IS NOT NULL OR QUOTES.PRICE_ASK IS NOT NULL)
        AND QUOTES.CONTRIBUTOR NOT IN ('noreply@solveadvisors.com', 'State Street ETF Group')
),
FILTERED_COLOR AS (
    SELECT *
    FROM (
        SELECT COLOR.*,
               ROW_NUMBER() OVER (
                   PARTITION BY
                       COLOR.ROOT_CUSIP,
                       COLOR.CUSIP,
                       COLOR.ISIN,
                       COLOR.SHELF,
                       COLOR.SERIES,
                       COLOR.CLASS,
                       COLOR.BIAS,
                       COLOR.PRICE_BID,
                       COLOR.PRICE_ASK,
                       COLOR.PRICELEVEL,
                       COLOR.CONFIDENCE,
                       COLOR.MKT_DATE
                   ORDER BY COLOR.TIME ASC
               ) AS RECENT
        FROM (
            SELECT TAINTED_COLOR.QUOTEID,
                   TAINTED_COLOR.MESSAGE_ID,
                   TAINTED_COLOR.CONTRIBUTOR,
                   TAINTED_COLOR.OWNER,
                   TAINTED_COLOR.PRICE_BID,
                   TAINTED_COLOR.PRICE_ASK,
                   TAINTED_COLOR.SPREAD_BID,
                   TAINTED_COLOR.SPREAD_ASK,
                   TAINTED_COLOR.BENCHMARK,
                   TAINTED_COLOR.WAL,
                   TAINTED_COLOR.PRICELEVEL,
                   TAINTED_COLOR.CONFIDENCE,
                   TAINTED_COLOR.ROOT_CUSIP,
                   TAINTED_COLOR.CUSIP,
                   TAINTED_COLOR.ISIN,
                   TAINTED_COLOR.SHELF,
                   TAINTED_COLOR.SERIES,
                   TAINTED_COLOR.CLASS,
                   TAINTED_COLOR.BIAS,
                   TAINTED_COLOR.TAINTED,
                   TAINTED_COLOR.TIME,
                   TAINTED_COLOR.MKT_DATE,
                   TAINTED_COLOR.PRICE
            FROM TAINTED_COLOR
        ) COLOR
    ) COLOR
    WHERE COLOR.RECENT = 1
),
COLOUR AS (
    SELECT SYSDATE AS TIME_QUERIED,
           COLOR.TIME AS TIME_RECEIVED,
           TO_CHAR(COLOR.MESSAGE_ID) AS MESSAGE,
           COLOR.ROOT_CUSIP,
           COLOR.CUSIP AS CUSIP_COLOR,
           COLOR.ISIN AS ISIN_COLOR,
           COLOR.SHELF || ' ' || COLOR.SERIES || ' ' || COLOR.CLASS AS TICKER,
           NVL(RTG.FIELD_VALUE, '100') AS ORIG_BEST_RATING,
           NVL(CURR.FIELD_VALUE, '') AS CURRENCY,
           COLOR.PRICE_BID,
           COLOR.PRICE_ASK,
           COLOR.SPREAD_BID,
           COLOR.SPREAD_ASK,
           COLOR.BENCHMARK,
           COLOR.WAL,
           COLOR.PRICELEVEL,
           DECODE(
               COLOR.BIAS,
               'MARKET', 'BID',
               'BUYER', 'BID',
               NULL, NVL2(COLOR.PRICE_BID, 'BID', 'OFFER'),
               COLOR.BIAS
           ) AS BIAS,
           COLOR.CONTRIBUTOR,
           COLOR.OWNER,
           NVL(COLOR.PRICE_BID, COLOR.PRICE_ASK) AS PRICE,
           COLOR.CONFIDENCE,
           COLOR.QUOTEID,
           NVL(ch.PRICEMID, ch.PRICEBID) AS COV_PRICE
    FROM FILTERED_COLOR COLOR
    LEFT JOIN SEC_MASTER RTG
        ON RTG.SEC_ID = COLOR.ROOT_CUSIP
        AND RTG.FIELD_NAME = 'OriginalBestRatingScore'
    LEFT JOIN SEC_MASTER CURR
        ON CURR.SEC_ID = COLOR.ROOT_CUSIP
        AND CURR.FIELD_NAME = 'Currency'
    LEFT JOIN coveragehist ch
        ON COLOR.ROOT_CUSIP = ch.cusip
        AND ch.ASOF >= TRUNC(SYSDATE) - 1
        AND ch.PUBLISHEDBATCH = 'N1600'
),
ACCEPTED AS (
    SELECT COLOUR.ROOT_CUSIP,
           sm.prc_config_key_name,
           CASE
               WHEN COLOUR.PRICE > 105 AND sm.prc_config_key_name IN ('1.0_Mezz', '2.0_Mezz', '2.0_Senior') THEN 1
               WHEN COLOUR.PRICE < 10 AND sm.prc_config_key_name IN ('1.0_Mezz', '2.0_Mezz', '2.0_Senior') THEN 1
               ELSE 0
           END AS REJECTED
    FROM COLOUR
    JOIN SECURITY_MASTER sm
        ON COLOUR.ROOT_CUSIP = sm.SEC_ID
    WHERE sm.SEC_STATUS = 'Approved'
        AND sm.PRC_CONFIG_SEC_TYPE = 'CLO'
)
SELECT DISTINCT
    TO_CHAR(col.MESSAGE) AS MESSAGE_ID,
    col.TICKER,
    a.prc_config_key_name AS Sector,
    col.ROOT_CUSIP AS CUSIP,
    TRUNC(SYSDATE) AS "DATE",
    NVL(col.PRICE, 0) AS PRICE_LEVEL,
    NVL(col.PRICE_BID, 0) AS Bid,
    NVL(col.PRICE_ASK, 0) AS Ask,
    NVL(col.PRICE, 0) AS Px,
    col.CONTRIBUTOR AS SOURCE,
    col.BIAS,
    DECODE(
        col.BIAS,
        'TRADE CONFIRM', 1,
        'BWIC COVER', 2,
        'BWIC REO', 3,
        'MARKET', 3,
        'BUYER', 3,
        'BID', 3,
        'COLOR', 3,
        'OFFER', 4,
        'BWIC TALK', 5,
        'VALUATION', 6,
        'DNT', 3,
        'DNT BEST', 3
    ) AS RANK,
    col.COV_PRICE,
    CASE
        WHEN col.COV_PRICE IS NOT NULL AND col.COV_PRICE <> 0 THEN
            ROUND(ABS(((NVL(col.PRICE, 0) - NVL(col.COV_PRICE, 0)) / col.COV_PRICE) * 100), 2)
        ELSE NULL
    END AS PERCENT_DIFF,
    (NVL(col.PRICE, 0) - NVL(col.COV_PRICE, 0)) AS PRICE_DIFF,
    col.CONFIDENCE,
    TRUNC(col.TIME_RECEIVED) AS DATE_1,
    CASE
        WHEN a.prc_config_key_name IN ('2.0_AAA_Mez', '2.0_AAA_Senior', '2.0_AAA_X_Senior') THEN
            CASE
                WHEN ROUND(ABS(((NVL(col.PRICE, 0) - NVL(col.COV_PRICE, 0)) / col.COV_PRICE) * 100), 2) > 2 THEN 'Significant Difference'
                ELSE 'Small Difference'
            END
        WHEN a.prc_config_key_name IN ('2.0_Mezz', '2.0_Senior', 'A_BSL', 'COMBO', 'Equity_Eur', 'European', 'European_Yield') THEN
            CASE
                WHEN ROUND(ABS(((NVL(col.PRICE, 0) - NVL(col.COV_PRICE, 0)) / col.COV_PRICE) * 100), 2) > 2 THEN 'Significant Difference'
                ELSE 'Small Difference'
            END
        WHEN a.prc_config_key_name IN ('US_Equity_2.0', 'US_MM_Equity_2.0') THEN
            CASE
                WHEN ROUND(ABS(((NVL(col.PRICE, 0) - NVL(col.COV_PRICE, 0)) / col.COV_PRICE) * 100), 2) > 5 THEN 'Significant Difference'
                ELSE 'Small Difference'
            END
        WHEN a.prc_config_key_name = 'US_Re' THEN
            CASE
                WHEN ROUND(ABS(((NVL(col.PRICE, 0) - NVL(col.COV_PRICE, 0)) / col.COV_PRICE) * 100), 2) > 2 THEN 'Significant Difference'
                ELSE 'Small Difference'
            END
        ELSE
            CASE
                WHEN ROUND(ABS(((NVL(col.PRICE, 0) - NVL(col.COV_PRICE, 0)) / NULLIF(NVL(col.COV_PRICE, 0), 0)) * 100), 2) > 2 THEN 'Significant Difference'
                ELSE 'Small Difference'
            END
    END AS DIFF_STATUS
FROM COLOUR col
JOIN ACCEPTED a
    ON col.ROOT_CUSIP = a.ROOT_CUSIP
WHERE a.REJECTED = 0
    AND col.CURRENCY = 'USD'
ORDER BY
    a.prc_config_key_name,
    col.ROOT_CUSIP,
    DATE_1 DESC,
    RANK,
    NVL(col.PRICE, 0) DESC
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
            
            # Check configuration - need either API URL or .env credentials
            has_api = bool(self.credentials_api_url)
            has_env_creds = bool(os.getenv("ORACLE_USERNAME") and os.getenv("ORACLE_PASSWORD"))
            
            if not has_api and not has_env_creds:
                return {
                    "status": "error",
                    "message": "Oracle credentials not configured. Set ORACLE_CREDENTIALS_API_URL or ORACLE_USERNAME/ORACLE_PASSWORD in .env"
                }
            
            if not all([self.oracle_host, self.oracle_port, self.oracle_service]):
                return {
                    "status": "error",
                    "message": "Oracle connection details incomplete (host/port/service)"
                }
            
            # Test credentials fetch (API or .env)
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
            
            thick_mode_status = "enabled" if _thick_mode_initialized else "disabled (thin mode)"
            cred_source = "API" if has_api else ".env file"
            
            return {
                "status": "success",
                "message": f"Oracle connection successful. Table has {row_count} rows. Thick mode: {thick_mode_status}. Credentials: {cred_source}"
            }
            
        except oracledb.Error as e:
            error_msg = str(e)
            
            # Check for encryption error
            if "DPY-3001" in error_msg or "Network Encryption" in error_msg:
                return {
                    "status": "error",
                    "message": "Oracle connection failed: Database requires Network Encryption. Please install Oracle Instant Client and ensure it's in your PATH. Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html"
                }
            
            return {
                "status": "error",
                "message": f"Oracle connection failed: {error_msg}"
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
        thick_mode_status = "enabled" if _thick_mode_initialized else "disabled"
        
        return {
            "type": "Oracle",
            "host": self.oracle_host,
            "port": str(self.oracle_port),
            "service": self.oracle_service,
            "table": self.oracle_table,
            "credentials_api_configured": str(bool(self.credentials_api_url)),
            "thick_mode": thick_mode_status
        }
