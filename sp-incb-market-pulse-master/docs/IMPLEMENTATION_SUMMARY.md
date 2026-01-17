# Oracle Database Integration - Implementation Summary

## What We've Built

A complete solution for securely connecting to Oracle database and extracting sample data for MarketPulse backend design.

---

## Files Created

### 1. Infrastructure (Terraform)
- **`infra/ssm.tf`** - AWS SSM Parameter Store configuration for Oracle credentials
  - Stores host, port, service name, username, password (encrypted)
  - Schema and table name configuration
  - Lifecycle management to prevent accidental overwrites

### 2. Backend Code
- **`src/main/db_config.py`** - Database configuration and connection module
  - Reads credentials from AWS SSM or environment variables
  - Oracle connection manager with context manager support
  - Query execution and schema inspection utilities
  - Error handling and logging

### 3. Client Scripts
- **`scripts/extract_sample_data.py`** - Standalone data extraction script
  - Lists all accessible tables
  - Extracts sample data (CSV + JSON)
  - Gets table schema and metadata
  - Comprehensive error handling

- **`scripts/setup_extraction.bat`** - Windows setup script
- **`scripts/setup_extraction.sh`** - Linux/Mac setup script
- **`scripts/requirements_extraction.txt`** - Python dependencies for extraction

### 4. Documentation
- **`docs/ORACLE_EXTRACTION_INSTRUCTIONS.md`** - Complete technical guide
  - Prerequisites and installation
  - Step-by-step instructions
  - Troubleshooting guide
  - AWS SSM setup instructions for DevOps

- **`docs/QUICK_START.md`** - Simple guide for non-technical users
  - 3-step process
  - Copy-paste commands
  - What to expect

### 5. Dependencies
- **`requirements.txt`** - Updated with Oracle database libraries
  - `oracledb>=2.0.0` - Modern Oracle driver
  - `cx_Oracle>=8.3.0` - Legacy fallback
  - `pandas>=2.0.0` - Data processing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Side (VPN)                       │
├─────────────────────────────────────────────────────────────┤
│  1. Client connects via VPN                                 │
│  2. Runs extract_sample_data.py                             │
│  3. Connects to Oracle DB with admin credentials            │
│  4. Extracts sample data → CSV/JSON                         │
│  5. Shares with development team                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Development Team                           │
├─────────────────────────────────────────────────────────────┤
│  1. Reviews sample data structure                           │
│  2. Designs backend data models                             │
│  3. Updates Terraform with actual credentials               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    AWS Infrastructure                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AWS SSM Parameter Store (Secure)                   │   │
│  │  • /sp-incb/ci/market-pulse/oracle/host            │   │
│  │  • /sp-incb/ci/market-pulse/oracle/port            │   │
│  │  • /sp-incb/ci/market-pulse/oracle/username        │   │
│  │  • /sp-incb/ci/market-pulse/oracle/password (enc)  │   │
│  │  • ... (other parameters)                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                            ↓                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AWS Lambda (FastAPI)                               │   │
│  │  • Reads credentials from SSM                       │   │
│  │  • Connects to Oracle (via VPN/PrivateLink)        │   │
│  │  • Processes data (Run Colors logic)               │   │
│  │  • Saves to S3                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Features

✅ **Credentials stored in AWS SSM Parameter Store**
- SecureString encryption for sensitive data
- IAM-based access control
- Audit logging via CloudTrail

✅ **No credentials in code**
- Environment variables or SSM only
- `.gitignore` prevents credential files from being committed

✅ **Terraform lifecycle management**
- `ignore_changes` prevents accidental credential overwrites
- Allows manual credential updates via AWS Console/CLI

✅ **Lambda IAM permissions**
- Specific SSM parameter path access
- KMS decrypt permissions for SecureString
- Least privilege principle

---

## Next Steps for Client

### Immediate Actions:
1. ✅ Install Python 3.8+ and Oracle Instant Client
2. ✅ Connect to VPN
3. ✅ Run `setup_extraction.bat` (Windows) or `setup_extraction.sh` (Linux/Mac)
4. ✅ Set environment variables with database credentials
5. ✅ Run extraction script: `python extract_sample_data.py`
6. ✅ Share generated `sample_data` folder with development team

### What to Share:
- `database_info.json` - Database version and metadata
- `accessible_tables.json` - List of all tables
- `TABLENAME_schema.json` - Column definitions
- `TABLENAME_sample_*.csv` - Sample data in CSV format
- `TABLENAME_sample_*.json` - Sample data in JSON format

---

## Next Steps for Development Team

### After Receiving Sample Data:

1. **Analyze Data Structure**
   - Review column names, data types, relationships
   - Identify primary keys, foreign keys
   - Understand the Parent-Child ranking logic
   - Map fields to SRS requirements

2. **Design Data Models**
   - Create Pydantic models for FastAPI
   - Design database query patterns
   - Plan data transformation logic

3. **Update Infrastructure**
   ```bash
   cd infra
   terraform init
   terraform apply
   ```

4. **Configure SSM Parameters**
   ```bash
   # Using AWS CLI
   aws ssm put-parameter \
       --name "/sp-incb/ci/market-pulse/oracle/host" \
       --value "actual-host.company.com" \
       --type "String" \
       --region us-east-1
   
   # Repeat for all parameters...
   ```

5. **Test Database Connection**
   ```python
   from src.main.db_config import OracleDatabase
   
   with OracleDatabase() as db:
       schema = db.get_table_schema('COLORS_TABLE')
       print(schema)
   ```

6. **Implement Business Logic**
   - Run Colors algorithm (Rank → Date → Price)
   - Exclusion rules engine
   - S3 integration
   - Cron job scheduling

---

## Technical Specifications

### Oracle Connectivity
- **Drivers:** `oracledb` (primary), `cx_Oracle` (fallback)
- **Connection:** DSN-based with service name
- **Authentication:** Username/password from SSM

### AWS Resources
- **SSM Parameters:** 7 parameters per environment
- **IAM Policy:** Custom policy for SSM and KMS access
- **Lambda Layer:** May need Oracle Instant Client layer

### Data Format
- **CSV:** Excel-compatible, UTF-8 encoded
- **JSON:** Pretty-printed, first 100 rows for quick review
- **Schema:** Complete column metadata with types

---

## Cost Considerations

### SSM Parameter Store
- **Free tier:** Up to 10,000 parameter operations/month
- **Cost:** ~$0.05 per 10,000 API calls above free tier
- **Expected:** < $1/month for this application

### Lambda Data Transfer
- **Cost:** $0.09 per GB out to internet
- **Expected:** Minimal if using VPC PrivateLink or VPN

### S3 Storage
- **Cost:** $0.023 per GB/month (standard storage)
- **Expected:** Depends on data volume

---

## Troubleshooting Reference

### Common Issues:

| Issue | Solution |
|-------|----------|
| "Cannot connect to Oracle" | Check VPN connection, verify host/port |
| "Invalid credentials" | Verify username/password, check account status |
| "Table not found" | Use `--list-tables` to see available tables |
| "Oracle client not found" | Install Oracle Instant Client, update PATH |
| "SSM parameter not found" | Run Terraform apply, or create parameters manually |
| "Permission denied" | Check Lambda IAM role has SSM read permissions |

---

## Maintenance

### Regular Tasks:
- ✅ Rotate Oracle credentials every 90 days
- ✅ Update SSM parameters when credentials change
- ✅ Monitor SSM parameter access logs
- ✅ Review IAM policies quarterly

### Credential Rotation:
1. Update password in Oracle database
2. Update SSM parameter:
   ```bash
   aws ssm put-parameter \
       --name "/sp-incb/ci/market-pulse/oracle/password" \
       --value "new_password" \
       --type "SecureString" \
       --overwrite
   ```
3. No code changes needed (reads from SSM at runtime)

---

## Questions & Support

**For Client:**
- See: `docs/QUICK_START.md`
- See: `docs/ORACLE_EXTRACTION_INSTRUCTIONS.md`

**For DevOps:**
- Review: `infra/ssm.tf`
- Review: `infra/lambda.tf` (IAM policies)

**For Developers:**
- Review: `src/main/db_config.py`
- Review: Sample data files

---

**Implementation Date:** January 11, 2026  
**Status:** Ready for client execution  
**Next Milestone:** Receive sample data and design backend data models
