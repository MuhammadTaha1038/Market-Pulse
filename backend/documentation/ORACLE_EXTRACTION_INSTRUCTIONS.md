# Oracle Database Sample Data Extraction - Client Instructions

## Overview
This document provides step-by-step instructions for extracting sample data from the Oracle database through your VPN connection. This data is needed to design and implement the MarketPulse backend.

---

## Prerequisites

### 1. VPN Connection
- ✅ Ensure you are connected to the company VPN
- ✅ Verify you can access the Oracle database from your machine

### 2. Oracle Client Installation
You need Oracle Instant Client installed on your machine.

**Windows:**
```bash
# Download Oracle Instant Client from:
# https://www.oracle.com/database/technologies/instant-client/downloads.html

# Extract to: C:\oracle\instantclient_21_x
# Add to PATH environment variable
```

**Linux/Mac:**
```bash
# Download and extract Oracle Instant Client
# Set LD_LIBRARY_PATH (Linux) or DYLD_LIBRARY_PATH (Mac)
export LD_LIBRARY_PATH=/path/to/instantclient:$LD_LIBRARY_PATH
```

### 3. Python Environment
Requires Python 3.8 or higher

**Install required packages:**
```bash
pip install oracledb pandas
```

---

## Step 1: Configure Environment Variables

Before running the script, you need to set environment variables with your Oracle database credentials.

### Windows (PowerShell):
```powershell
# Set Oracle database credentials
$env:ORACLE_HOST = "your-oracle-host.company.com"
$env:ORACLE_PORT = "1521"
$env:ORACLE_SERVICE_NAME = "your_service_name"
$env:ORACLE_USERNAME = "your_admin_username"
$env:ORACLE_PASSWORD = "your_admin_password"
$env:ORACLE_SCHEMA = "your_schema_name"
$env:ORACLE_TABLE_NAME = "your_main_table_name"
```

### Windows (Command Prompt):
```cmd
set ORACLE_HOST=your-oracle-host.company.com
set ORACLE_PORT=1521
set ORACLE_SERVICE_NAME=your_service_name
set ORACLE_USERNAME=your_admin_username
set ORACLE_PASSWORD=your_admin_password
set ORACLE_SCHEMA=your_schema_name
set ORACLE_TABLE_NAME=your_main_table_name
```

### Linux/Mac (Bash):
```bash
export ORACLE_HOST="your-oracle-host.company.com"
export ORACLE_PORT="1521"
export ORACLE_SERVICE_NAME="your_service_name"
export ORACLE_USERNAME="your_admin_username"
export ORACLE_PASSWORD="your_admin_password"
export ORACLE_SCHEMA="your_schema_name"
export ORACLE_TABLE_NAME="your_main_table_name"
```

### Required Variables:
| Variable | Description | Example |
|----------|-------------|---------|
| `ORACLE_HOST` | Database host/IP address | `db.company.com` |
| `ORACLE_PORT` | Database port (usually 1521) | `1521` |
| `ORACLE_SERVICE_NAME` | Service name or SID | `ORCL` or `PRODDB` |
| `ORACLE_USERNAME` | Admin username | `admin_user` |
| `ORACLE_PASSWORD` | Admin password | `SecureP@ss123` |
| `ORACLE_SCHEMA` | Schema name (optional) | `MARKET_DATA` |
| `ORACLE_TABLE_NAME` | Main table for color data | `COLORS_TABLE` |

---

## Step 2: Run the Extraction Script

### Option A: List All Accessible Tables First
This helps you identify the correct table names before extraction.

```bash
python scripts/extract_sample_data.py --list-tables --output ./sample_data
```

**Expected Output:**
```
============================================================
DATABASE INFORMATION
============================================================
version: Oracle Database 19c Enterprise Edition Release 19.0.0.0.0
current_user: ADMIN_USER
database_time: 2026-01-11 10:30:45
============================================================
ACCESSIBLE TABLES
============================================================
Found 150 accessible tables
  MARKET_DATA.COLORS_TABLE (25000 rows)
  MARKET_DATA.SECURITIES_TABLE (18000 rows)
  MARKET_DATA.PRICING_DATA (50000 rows)
  ...

✓ Table list saved to ./sample_data/accessible_tables.json
```

### Option B: Extract Sample Data from Specific Table
Once you've identified the correct table, extract sample data:

```bash
python scripts/extract_sample_data.py --output ./sample_data --limit 1000
```

**Parameters:**
- `--output`: Directory where files will be saved (default: `./sample_data`)
- `--limit`: Maximum number of rows to extract (default: 1000)

**Expected Output:**
```
============================================================
DATABASE INFORMATION
============================================================
version: Oracle Database 19c Enterprise Edition
current_user: ADMIN_USER
database_time: 2026-01-11 10:30:45
✓ Saved data to ./sample_data/database_info.json

============================================================
EXTRACTING SAMPLE DATA FROM COLORS_TABLE
============================================================
✓ Table has 25 columns:
  MESSAGE_ID (VARCHAR2)
  CUSIP (VARCHAR2)
  TICKER (VARCHAR2)
  BIAS (VARCHAR2)
  SOURCE (VARCHAR2)
  BID_PRICE (NUMBER)
  MID_PRICE (NUMBER)
  ASK_PRICE (NUMBER)
  RANK (NUMBER)
  CREATED_DATE (TIMESTAMP)
  ...

✓ Extracted 1000 rows with 25 columns
✓ Saved data to ./sample_data/COLORS_TABLE_sample_20260111_103045.csv
✓ Saved data to ./sample_data/COLORS_TABLE_sample_20260111_103045.json

============================================================
EXTRACTION COMPLETE
============================================================
Output directory: C:\Users\YourName\sample_data

Next steps:
1. Review the extracted data files
2. Share the sample data with the backend development team
3. Use the schema information to design the data models
```

---

## Step 3: Generated Files

After successful extraction, you'll find these files in the output directory:

| File | Description |
|------|-------------|
| `database_info.json` | Database version, connection details, timestamp |
| `accessible_tables.json` | List of all tables you have access to |
| `{TABLE}_schema.json` | Column definitions and data types |
| `{TABLE}_sample_{timestamp}.csv` | Sample data in CSV format (Excel-compatible) |
| `{TABLE}_sample_{timestamp}.json` | First 100 rows in JSON format |

---

## Step 4: Review and Share Data

### 4.1 Verify Data Quality
Open the CSV file in Excel and verify:
- ✅ All expected columns are present
- ✅ Data looks correct (no corruption)
- ✅ Sensitive data is properly included (since this is for backend design)

### 4.2 Package for Sharing
Create a ZIP file with all extracted files:

**Windows:**
```powershell
Compress-Archive -Path .\sample_data\* -DestinationPath MarketPulse_Sample_Data.zip
```

**Linux/Mac:**
```bash
zip -r MarketPulse_Sample_Data.zip sample_data/
```

### 4.3 Share with Development Team
- Upload to secure file sharing (SharePoint, OneDrive, etc.)
- Or send via encrypted email
- **Do NOT commit to public Git repositories** (contains real data)

---

## Troubleshooting

### Error: "Neither oracledb nor cx_Oracle is installed"
**Solution:**
```bash
pip install oracledb
```

### Error: "DPI-1047: Cannot locate Oracle Client library"
**Solution:**
- Install Oracle Instant Client
- Add to PATH (Windows) or LD_LIBRARY_PATH (Linux)
- Restart terminal/PowerShell

### Error: "ORA-12541: TNS:no listener"
**Solution:**
- Verify VPN connection is active
- Check ORACLE_HOST and ORACLE_PORT are correct
- Ping the database host: `ping your-oracle-host.company.com`

### Error: "ORA-01017: invalid username/password"
**Solution:**
- Verify ORACLE_USERNAME and ORACLE_PASSWORD are correct
- Ensure account is not locked
- Check if password contains special characters (may need escaping)

### Error: "Missing required environment variables"
**Solution:**
- Ensure all required environment variables are set
- Verify no typos in variable names
- On Windows, use `$env:VAR_NAME` in PowerShell, not `%VAR_NAME%`

### No data extracted (0 rows)
**Solution:**
- Verify ORACLE_TABLE_NAME is correct (case-sensitive)
- Check if ORACLE_SCHEMA is needed
- Run with `--list-tables` to see available tables

---

## AWS SSM Parameter Store (For DevOps Team)

After getting the sample data, the DevOps team needs to populate AWS SSM Parameter Store with the credentials.

### Using AWS CLI:
```bash
# Set the environment and app details
APP_PREFIX="sp-incb"
ENV="ci"
APP_NAME="market-pulse"
REGION="us-east-1"

# Store Oracle credentials in SSM Parameter Store
aws ssm put-parameter \
    --name "/${APP_PREFIX}/${ENV}/${APP_NAME}/oracle/host" \
    --value "your-oracle-host.company.com" \
    --type "String" \
    --region $REGION

aws ssm put-parameter \
    --name "/${APP_PREFIX}/${ENV}/${APP_NAME}/oracle/port" \
    --value "1521" \
    --type "String" \
    --region $REGION

aws ssm put-parameter \
    --name "/${APP_PREFIX}/${ENV}/${APP_NAME}/oracle/service_name" \
    --value "your_service_name" \
    --type "String" \
    --region $REGION

aws ssm put-parameter \
    --name "/${APP_PREFIX}/${ENV}/${APP_NAME}/oracle/username" \
    --value "your_admin_username" \
    --type "SecureString" \
    --region $REGION

aws ssm put-parameter \
    --name "/${APP_PREFIX}/${ENV}/${APP_NAME}/oracle/password" \
    --value "your_admin_password" \
    --type "SecureString" \
    --region $REGION

aws ssm put-parameter \
    --name "/${APP_PREFIX}/${ENV}/${APP_NAME}/oracle/schema" \
    --value "your_schema_name" \
    --type "String" \
    --region $REGION

aws ssm put-parameter \
    --name "/${APP_PREFIX}/${ENV}/${APP_NAME}/oracle/table_name" \
    --value "your_main_table_name" \
    --type "String" \
    --region $REGION
```

### Using Terraform (Recommended):
After initial `terraform apply`, update the placeholder values:

```bash
# Navigate to infra directory
cd infra

# Apply Terraform to create SSM parameters
terraform apply

# Then update the values via AWS Console or CLI
# The lifecycle ignore_changes block prevents Terraform from overwriting manual updates
```

---

## Security Notes

⚠️ **IMPORTANT:**
1. Never commit database credentials to Git
2. Never share credentials via unencrypted channels
3. Use VPN when accessing the database
4. Delete local copies of sample data after sharing
5. Ensure sample data files are not committed to version control

---

## Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Verify VPN connection and database access
3. Contact your database administrator for credential verification
4. Reach out to the development team with error messages and logs

---

**Last Updated:** January 11, 2026  
**Script Version:** 1.0  
**Contact:** Backend Development Team
