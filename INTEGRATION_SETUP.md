# Integration Setup Guide

## Quick Setup: Oracle + S3

### Prerequisites
```bash
pip install oracledb boto3
```

---

## 1. Oracle Database Integration

### Step 1: Edit `.env` file
```env
# Switch to Oracle
DATA_SOURCE=oracle

# Credentials API (provided by client)
ORACLE_CREDENTIALS_API_URL=https://your-api.com/credentials

# Connection details
ORACLE_HOST=oracle-server.company.com
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_TABLE_NAME=COLOR_DATA
```

### Step 2: Restart server
```bash
python src/main/handler.py
```

### Step 3: Verify
```bash
curl http://localhost:3334/api/admin/system-status
```
Look for `"data_source": {"ready": true}`

---

## 2. S3 Integration

### Step 1: Edit `.env` file
```env
# Choose destination
OUTPUT_DESTINATION=s3        # S3 only
OUTPUT_DESTINATION=both      # Local + S3 (recommended)

# S3 Configuration
S3_BUCKET_NAME=market-pulse-processed
S3_REGION=us-east-1
S3_PREFIX=processed_colors/
S3_FILE_FORMAT=xlsx          # or csv, parquet

# AWS Credentials
AWS_ACCESS_KEY_ID=AKIAXXXXX
AWS_SECRET_ACCESS_KEY=xxxxx
```

### Step 2: Verify
```bash
curl http://localhost:3334/api/admin/system-status
```
Look for `"output_destination": {"ready": true}`

---

## 3. Column Mapping (If Oracle Column Names Change)

### File Location
```
sp-incb-market-pulse-master/column_config.json
```

### Example: Map Oracle columns to system columns
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
        "display_name": "Ticker",
        "oracle_column_name": "STOCK_SYMBOL"
      },
      "CUSIP": {
        "enabled": true,
        "display_name": "CUSIP",
        "oracle_column_name": "CUSIP_NUMBER"
      }
    }
  }
}
```

### How It Works
- System always uses standard names internally (`MESSAGE_ID`, `TICKER`)
- Oracle queries use mapped names (`MSG_ID`, `STOCK_SYMBOL`)
- Frontend never affected by Oracle column changes
- Each CLO can have different Oracle column names

### When Oracle Columns Change
1. Open `column_config.json`
2. Update `oracle_column_name` for changed columns
3. Restart server
4. Done! (No code changes)

---

## 4. Testing

### Test Oracle Connection
```bash
curl http://localhost:3334/api/admin/system-status
```

### Test Data Fetch
```bash
curl http://localhost:3334/api/dashboard/colors?limit=10
```

### Test S3 Upload
1. Click "Run Automation" in UI
2. Check S3 bucket: `s3://your-bucket/processed_colors/`

---

## 5. Production Checklist

- [ ] Oracle credentials API accessible
- [ ] Oracle connection details verified
- [ ] S3 bucket created and permissions set
- [ ] AWS credentials configured (IAM role preferred)
- [ ] Column mapping configured for each CLO
- [ ] Test data flow: Oracle → Processing → S3
- [ ] Verify dashboard reads from S3
- [ ] Test scheduled automation (cron jobs)

---

## Troubleshooting

### Oracle Connection Failed
```bash
# Check credentials API
curl https://your-api.com/credentials

# Check Oracle connectivity
telnet oracle-server.com 1521
```

### S3 Upload Failed
```bash
# Test AWS credentials
aws s3 ls s3://your-bucket/

# Check bucket policy allows PutObject
```

### Column Not Found
- Update `column_config.json` with correct Oracle column name
- Restart server

---

## Configuration Time
- Oracle setup: **5 minutes**
- S3 setup: **3 minutes**
- Column mapping: **2 minutes per CLO**

**Total: ~10 minutes** ✅
