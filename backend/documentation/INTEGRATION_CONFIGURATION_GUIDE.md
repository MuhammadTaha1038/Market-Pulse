# Integration Configuration Guide

## ✅ System Architecture Overview

The system is now **fully abstracted** and ready for plug-and-play integration with Oracle and S3. You only need to update configuration files - **no code changes required**.

### **Abstraction Layers**

1. **Data Source Layer** (`data_source_interface.py`)
   - Excel Input ✅ (Current)
   - Oracle Database 🔌 (Ready to configure)

2. **Output Destination Layer** (`output_destination_interface.py`)
   - Local Excel ✅ (Current)
   - AWS S3 🔌 (Ready to configure)
   - Both (Local + S3) 🔌 (Supported)

---

## 🔧 Quick Configuration Guide

### **Step 1: Copy Environment File**

```bash
cd sp-incb-market-pulse-master
copy .env.example .env
```

### **Step 2: Choose Your Configuration**

Open `.env` file and configure based on your needs:

---

## 🗄️ Oracle Database Integration

### **Prerequisites from Client**

Get these details from your client:

1. **Credentials API Endpoint** (returns JSON with credentials)
2. **Oracle Connection Details** (host, port, service name)
3. **Table/View Name** (where raw color data is stored)
4. **Column Mapping** (verify with `column_config.json`)

### **Configuration Steps**

1. **Edit `.env` file:**

```env
# Switch data source to Oracle
DATA_SOURCE=oracle

# Credentials API (provided by client)
ORACLE_CREDENTIALS_API_URL=https://client-api.com/credentials

# Oracle connection details
ORACLE_HOST=oracle-db-server.client.com
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_TABLE_NAME=COLOR_DATA
```

2. **Install Oracle dependencies:**

```bash
pip install oracledb requests
```

3. **Verify column mapping in `column_config.json`:**

The system automatically uses your CLO-specific column configurations for Oracle queries. Each CLO's configured columns will be mapped to their corresponding Oracle column names.

```json
{
  "CLO_001": {
    "name": "Sample CLO",
    "columns": {
      "MESSAGE_ID": {
        "enabled": true,
        "display_name": "Message ID",
        "oracle_column_name": "MSG_ID"  ← Oracle uses this column name
      }
    }
  }
}
```

4. **Test connection:**

```bash
# Restart backend
python src/main/handler.py

# Check status via API
curl http://localhost:3334/api/admin/system-status
```

### **How It Works**

When Oracle is configured:
- System fetches credentials from client's API using `eval.jdbc.user` and `eval.jdbc.password` keys
- Credentials are cached for 1 hour (configurable TTL)
- Queries are built dynamically using column_config.json mappings per CLO
- Same DataFrame structure returned (no downstream changes needed)

**Example Query Generation:**

```python
# For CLO_001 with custom column mapping:
SELECT 
  MSG_ID AS MESSAGE_ID,
  TICKER AS TICKER,
  CUSIP_NO AS CUSIP
FROM COLOR_DATA
WHERE CLO_ID = 'CLO_001'
ORDER BY DATE DESC
```

---

## ☁️ AWS S3 Integration

### **Prerequisites from Client**

Get these details from your client:

1. **S3 Bucket Name**
2. **AWS Region** (e.g., us-east-1)
3. **AWS Credentials** (access key + secret key) OR IAM role
4. **Folder Structure** (prefix inside bucket)
5. **File Format Preference** (Excel, CSV, or Parquet)

### **Configuration Steps**

1. **Edit `.env` file:**

```env
# Option 1: S3 only (no local file)
OUTPUT_DESTINATION=s3

# Option 2: Both local and S3
OUTPUT_DESTINATION=both

# S3 Configuration
S3_BUCKET_NAME=market-pulse-processed-data
S3_REGION=us-east-1
S3_PREFIX=processed_colors/
S3_FILE_FORMAT=xlsx

# AWS Credentials (or use IAM role)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

2. **Install S3 dependencies:**

```bash
pip install boto3
```

3. **Test connection:**

```bash
# Restart backend
python src/main/handler.py

# Check status via API
curl http://localhost:3334/api/admin/system-status
```

### **S3 File Formats**

Configure `S3_FILE_FORMAT` based on client preference:

- **xlsx** (default) - Excel format, compatible with existing workflows
- **csv** - Lightweight, universally compatible
- **parquet** - Best for big data, columnar storage, fast queries

### **S3 Folder Structure**

Files will be saved as:
```
s3://bucket-name/processed_colors/Processed_Colors_Output.xlsx
s3://bucket-name/processed_colors/Processed_Colors_2026-02-02.xlsx
```

Customize with `S3_PREFIX` in `.env` file.

---

## 🔄 Combined Configuration (Oracle + S3)

Perfect for   using Oracle input and S3 output:

```env
# Input from Oracle
DATA_SOURCE=oracle
ORACLE_CREDENTIALS_API_URL=https://client-api.com/credentials
ORACLE_HOST=oracle-server.com
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_TABLE_NAME=COLOR_DATA

# Output to both local and S3
OUTPUT_DESTINATION=both
S3_BUCKET_NAME=market-pulse-processed
S3_REGION=us-east-1
S3_PREFIX=processed_colors/
S3_FILE_FORMAT=xlsx
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

**Install both dependencies:**
```bash
pip install oracledb requests boto3
```

---

## 🧪 Testing Integration

### **Method 1: System Status API**

```bash
GET http://localhost:3334/api/admin/system-status
```

**Response includes:**
```json
{
  "success": true,
  "overall_status": "ready",
  "data_source": {
    "info": {
      "type": "Oracle",
      "host": "oracle-server.com",
      "credentials_api_configured": "True"
    },
    "connection_test": {
      "status": "success",
      "message": "Oracle connection successful. Table has 15234 rows."
    },
    "ready": true
  },
  "output_destination": {
    "info": {
      "type": "AWS S3",
      "bucket": "market-pulse-processed",
      "region": "us-east-1"
    },
    "connection_test": {
      "status": "success",
      "message": "S3 bucket accessible: market-pulse-processed"
    },
    "ready": true
  }
}
```

### **Method 2: Python Testing**

```python
# Test data source
from services.data_source_factory import get_data_source

source = get_data_source()
print(source.test_connection())

# Fetch data
df = source.fetch_data(clo_id="CLO_001")
print(f"Fetched {len(df)} rows")

# Test output destination
from services.output_destination_factory import get_output_destination

destination = get_output_destination()
print(destination.test_connection())

# Save data
result = destination.save_output(df, "test_output.xlsx")
print(result)
```

---

## 🎯 Data Flow with Integrations

### **Current Flow (Excel → Local)**
```
Excel File → manual_upload_service → Processing → output_service → Local Excel
```

### **With Oracle (Oracle → Local)**
```
Oracle DB → oracle_data_source → Processing → output_service → Local Excel
```

### **With S3 (Excel → S3)**
```
Excel File → manual_upload_service → Processing → output_service → AWS S3
```

### **Full Integration (Oracle → S3)**
```
Oracle DB → oracle_data_source → Processing → output_service → AWS S3 + Local Excel
```

---

## 📝 Column Mapping Configuration

The system uses `column_config.json` for dynamic column mapping. Each CLO can have different column names in Oracle:

**Example configuration:**
```json
{
  "CLO_001": {
    "name": "Deutsche Bank CLO",
    "columns": {
      "MESSAGE_ID": {
        "enabled": true,
        "display_name": "Message ID",
        "oracle_column_name": "MSG_ID"
      },
      "TICKER": {
        "enabled": true,
        "display_name": "Ticker Symbol",
        "oracle_column_name": "STOCK_TICKER"
      }
    }
  },
  "CLO_002": {
    "name": "Goldman Sachs CLO",
    "columns": {
      "MESSAGE_ID": {
        "enabled": true,
        "display_name": "Message ID",
        "oracle_column_name": "MESSAGE_NUMBER"
      }
    }
  }
}
```

**Oracle queries will automatically use the correct column names for each CLO.**

---

## 🔧 Troubleshooting

### **Oracle Connection Issues**

1. **Credentials API not responding:**
   - Check `ORACLE_CREDENTIALS_API_URL` is correct
   - Verify network access to client's API
   - Check API response format (must have `eval.jdbc.user` and `eval.jdbc.password` keys)

2. **Database connection timeout:**
   - Verify `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME`
   - Check firewall rules
   - Test connection from server: `tnsping ORCL`

3. **Column not found errors:**
   - Review `column_config.json` mappings
   - Verify Oracle column names match configuration
   - Check table permissions

### **S3 Upload Issues**

1. **Access denied:**
   - Verify AWS credentials are correct
   - Check IAM permissions (s3:PutObject, s3:GetObject)
   - Verify bucket policy allows access

2. **Bucket not found:**
   - Check `S3_BUCKET_NAME` spelling
   - Verify bucket exists in specified region
   - Check `S3_REGION` matches bucket region

3. **File format errors:**
   - Ensure `S3_FILE_FORMAT` is valid (xlsx, csv, parquet)
   - For parquet, install: `pip install pyarrow`

---

## 📦 Deployment Checklist

### **Before Client Meeting:**
- [x] System abstracted for plug-and-play configuration
- [x] .env.example created with all variables
- [x] Documentation complete
- [x] Test endpoints available

### **After Client Provides Details:**
- [ ] Copy .env.example to .env
- [ ] Fill in Oracle credentials API URL
- [ ] Fill in Oracle connection details
- [ ] Fill in S3 bucket configuration
- [ ] Install required dependencies (`oracledb`, `boto3`)
- [ ] Test connections via `/api/admin/system-status`
- [ ] Verify column mappings in column_config.json
- [ ] Run end-to-end test
- [ ] Deploy to production

---

## 🎉 Summary

### **What's Ready:**
✅ Complete abstraction layer for data sources
✅ Complete abstraction layer for output destinations
✅ Dynamic column mapping using column_config.json
✅ Oracle integration with credentials API support
✅ S3 integration with multiple file formats
✅ Configuration via .env file
✅ Test endpoints for connection validation
✅ Comprehensive documentation

### **What Client Needs to Provide:**
❓ Oracle credentials API endpoint
❓ Oracle connection details (host, port, service, table)
❓ S3 bucket name and credentials
❓ Preferred file format and folder structure

### **Configuration Time: ~10 minutes**
1. Update .env file (2 min)
2. Install dependencies (3 min)
3. Test connections (2 min)
4. Verify data flow (3 min)

**No code changes needed - just configuration! 🚀**
