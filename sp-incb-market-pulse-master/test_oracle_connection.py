"""
Simple Oracle Database Connection Test Script

This script tests the connection to an Oracle database using credentials from the .env file.
It verifies that the database is reachable and authentication is successful.

Usage:
    python test_oracle_connection.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def fetch_oracle_credentials(api_url):
    """Fetch Oracle credentials from the API"""
    try:
        print(f"Fetching credentials from API: {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        username = data.get('eval.jdbc.user')
        password = data.get('eval.jdbc.password')
        
        if username and password:
            print("✓ Successfully fetched credentials from API")
            return username, password
        else:
            print("✗ API response missing required keys: 'eval.jdbc.user' or 'eval.jdbc.password'")
            return None, None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching credentials from API: {str(e)}")
        return None, None
    except Exception as e:
        print(f"✗ Unexpected error parsing API response: {str(e)}")
        return None, None

def test_oracle_connection():
    """Test Oracle database connection with credentials from API and .env file"""
    
    print("=" * 60)
    print("Oracle Database Connection Test")
    print("=" * 60)
    
    # Check if oracledb is installed
    try:
        import oracledb
        print("✓ oracledb library is installed")
        
        # Initialize thick mode for encryption support
        try:
            oracledb.init_oracle_client()
            print("✓ Oracle thick mode initialized (encryption supported)")
        except Exception as e:
            print(f"⚠ Could not initialize thick mode: {str(e)}")
            print("  Attempting to use thin mode (limited encryption support)")
            
    except ImportError:
        print("✗ oracledb library is NOT installed")
        print("\nTo install, run:")
        print("  pip install oracledb")
        return False
    
    # Read configuration from .env file
    print("\n" + "-" * 60)
    print("Reading configuration from .env file...")
    print("-" * 60)
    
    oracle_credentials_api = os.getenv('ORACLE_CREDENTIALS_API_URL')
    oracle_host = os.getenv('ORACLE_HOST')
    oracle_port = os.getenv('ORACLE_PORT', '1521')
    oracle_service = os.getenv('ORACLE_SERVICE_NAME')
    oracle_table = os.getenv('ORACLE_TABLE_NAME', 'COLOR_DATA')
    
    # Try to get credentials from API first, fallback to .env
    oracle_user = None
    oracle_password = None
    
    if oracle_credentials_api:
        print("\n" + "-" * 60)
        print("Fetching credentials from Oracle API...")
        print("-" * 60)
        oracle_user, oracle_password = fetch_oracle_credentials(oracle_credentials_api)
    
    # Fallback to .env file if API fetch failed
    if not oracle_user or not oracle_password:
        print("\nFalling back to credentials from .env file...")
        oracle_user = os.getenv('ORACLE_USERNAME')
        oracle_password = os.getenv('ORACLE_PASSWORD')
        if oracle_user and oracle_password:
            print("✓ Using credentials from .env file")
    
    # Display configuration (hide password)
    print("\n" + "-" * 60)
    print("Connection Details:")
    print("-" * 60)
    if oracle_credentials_api:
        print(f"ORACLE_CREDENTIALS_API_URL: {oracle_credentials_api}")
    print(f"ORACLE_HOST: {oracle_host or '(not set)'}")
    print(f"ORACLE_PORT: {oracle_port}")
    print(f"ORACLE_SERVICE_NAME: {oracle_service or '(not set)'}")
    print(f"ORACLE_USERNAME: {oracle_user or '(not set)'}")
    print(f"ORACLE_PASSWORD: {'*' * len(oracle_password) if oracle_password else '(not set)'}")
    print(f"ORACLE_TABLE_NAME: {oracle_table}")
    
    # Validate required fields
    print("\n" + "-" * 60)
    print("Validating configuration...")
    print("-" * 60)
    
    missing_fields = []
    if not oracle_host:
        missing_fields.append("ORACLE_HOST")
    if not oracle_service:
        missing_fields.append("ORACLE_SERVICE_NAME")
    if not oracle_user:
        missing_fields.append("ORACLE_USERNAME")
    if not oracle_password:
        missing_fields.append("ORACLE_PASSWORD")
    
    if missing_fields:
        print("✗ Missing required configuration:")
        for field in missing_fields:
            print(f"  - {field}")
        print("\nPlease update your .env file with Oracle credentials.")
        return False
    
    print("✓ All required configuration fields are present")
    
    # Attempt connection
    print("\n" + "-" * 60)
    print("Attempting database connection...")
    print("-" * 60)
    
    try:
        # Create DSN (Data Source Name)
        dsn = oracledb.makedsn(
            host=oracle_host,
            port=int(oracle_port),
            service_name=oracle_service
        )
        
        print(f"DSN: {dsn}")
        
        # Connect to database
        connection = oracledb.connect(
            user=oracle_user,
            password=oracle_password,
            dsn=dsn
        )
        
        print("✓ Successfully connected to Oracle database!")
        
        # Test query - Get database version
        print("\n" + "-" * 60)
        print("Testing database query...")
        print("-" * 60)
        
        cursor = connection.cursor()
        
        # Get Oracle version
        cursor.execute("SELECT banner FROM v$version WHERE rownum = 1")
        version = cursor.fetchone()
        if version:
            print(f"Database Version: {version[0]}")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM user_tables 
            WHERE table_name = :table_name
        """, {"table_name": oracle_table.upper()})
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print(f"✓ Table '{oracle_table}' exists")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {oracle_table}")
            row_count = cursor.fetchone()[0]
            print(f"  Row count: {row_count:,}")
            
            # Get column information
            cursor.execute(f"""
                SELECT column_name, data_type, data_length
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
            """, {"table_name": oracle_table.upper()})
            
            columns = cursor.fetchall()
            print(f"  Columns ({len(columns)}):")
            for col_name, col_type, col_length in columns[:10]:  # Show first 10
                print(f"    - {col_name}: {col_type}({col_length})")
            if len(columns) > 10:
                print(f"    ... and {len(columns) - 10} more columns")
        else:
            print(f"✗ Table '{oracle_table}' does NOT exist")
            print("\nAvailable tables:")
            cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
            tables = cursor.fetchall()
            for i, (table_name,) in enumerate(tables[:10], 1):
                print(f"  {i}. {table_name}")
            if len(tables) > 10:
                print(f"  ... and {len(tables) - 10} more tables")
        
        # Close connection
        cursor.close()
        connection.close()
        print("\n" + "=" * 60)
        print("✓ CONNECTION TEST SUCCESSFUL")
        print("=" * 60)
        return True
        
    except oracledb.Error as e:
        error_obj, = e.args
        print(f"✗ Oracle Error: {error_obj.message}")
        print(f"  Code: {error_obj.code}")
        
        # Check for encryption error
        if "DPY-3001" in str(error_obj.message) or "Network Encryption" in str(error_obj.message):
            print("\n  ⚠ This database requires Oracle Network Encryption (thick mode)")
            print("\n  To fix this, install Oracle Instant Client:")
            print("  1. Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html")
            print("  2. Extract to: C:\\oracle\\instantclient_21_x")
            print("  3. Add to PATH or set lib_dir in init_oracle_client()")
            print("\n  Example:")
            print('    oracledb.init_oracle_client(lib_dir=r"C:\\oracle\\instantclient_21_13")')
        elif error_obj.code == 1017:
            print("\n  Likely cause: Invalid username/password")
        elif error_obj.code == 12541:
            print("\n  Likely cause: TNS:no listener (Check host/port/service name)")
        elif error_obj.code == 12170:
            print("\n  Likely cause: Connection timeout (Check network/firewall)")
        
        print("\n" + "=" * 60)
        print("✗ CONNECTION TEST FAILED")
        print("=" * 60)
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        print("\n" + "=" * 60)
        print("✗ CONNECTION TEST FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_oracle_connection()
    sys.exit(0 if success else 1)
