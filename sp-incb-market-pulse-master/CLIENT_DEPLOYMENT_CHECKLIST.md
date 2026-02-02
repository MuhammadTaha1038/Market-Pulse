# Client Deployment Checklist & System Verification

## 🎯 Quick Setup (10 Minutes)

### Prerequisites
- Python 3.8+ installed
- Oracle Instant Client installed (for Network Encryption support)
- VPN access to Oracle database
- AWS credentials (if using S3 output)

---

## ⚙️ Step 1: Initial Configuration (5 minutes)

### 1.1 Install Dependencies
```bash
cd sp-incb-market-pulse-master
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install oracledb boto3  # For Oracle and S3 support
```

### 1.2 Configure Environment
Edit `.env` file with your credentials:

```env
# STEP 1: Change from Excel to Oracle
DATA_SOURCE=oracle  # Change from "excel" to "oracle"

# STEP 2: Add Oracle credentials
ORACLE_CREDENTIALS_API_URL=https://your-credentials-api-url.com/getParameters?module=mdppull
ORACLE_HOST=your-oracle-host.com
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=YOUR_SERVICE_NAME
ORACLE_TABLE_NAME=COLOR_DATA

# STEP 3: Configure Output (optional - use S3 or keep local)
OUTPUT_DESTINATION=local  # Options: local, s3, both
```

### 1.3 Test Oracle Connection
```bash
cd sp-incb-market-pulse-master
python test_oracle_connection.py
```

**Expected Output:**
```
✓ Oracle thick mode initialized (encryption supported)
✓ Successfully fetched credentials from API
✓ All required configuration fields are present
✓ Successfully connected to Oracle database!
✓ Table 'COLOR_DATA' exists
  Row count: X,XXX
```

---

## 🔧 Step 2: Configure Oracle Query (CLO Mapping) (3 minutes)

### 2.1 Start Backend & Frontend
```bash
# Terminal 1 - Backend
cd sp-incb-market-pulse-master\src\main
python handler.py

# Terminal 2 - Frontend
cd market-pulse-main
npm start
```

### 2.2 Configure Query in UI
1. Open browser: `http://localhost:4200`
2. Login as Super Admin
3. Navigate to: **SUPER ADMIN → CLO Mappings**
4. Select a CLO from the tree (e.g., "US CLO")
5. In **Oracle Query Configuration** section:
   - Paste your SQL query (from `Final New Query US (D+E).sql`)
   - Click **"Run Query & Fetch Columns"** to test
   - Click **"Save Query"** to save for automated runs

### 2.3 Select Visible Columns
- After running query, all discovered columns appear below
- Check/uncheck columns to control visibility
- Click **"Save Configuration"**

---

## ✅ Step 3: System Verification (2 minutes)

### 3.1 Test System Status
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:3334/api/admin/system-status"
```

**Expected Response:**
```json
{
  "overall_status": "ready",
  "data_source": {
    "info": {
      "type": "Oracle",
      "host": "your-host.com",
      "thick_mode": "enabled"
    },
    "connection_test": {
      "status": "success"
    },
    "ready": true
  },
  "integrations": {
    "oracle": {
      "configured": true,
      "ready": true
    }
  }
}
```

### 3.2 Test Data Fetch
Navigate to **Dashboard** page and verify:
- Monthly stats load correctly
- Recent colors display (last 50 rows)
- All data comes from Oracle (not Excel)

### 3.3 Test Automation
1. Go to **Color Process** page
2. Click **"Run Automation"**
3. Verify:
   - Data fetched from Oracle using your saved query
   - Processing applies rules
   - Output saved to configured destination

---

## 🔄 System Flow Verification

### Data Flow When DATA_SOURCE=oracle

```
┌─────────────────────────────────────────────────┐
│ 1. User Action (Automation/Manual/Cron)        │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 2. database_service.py                          │
│    → Calls get_data_source()                    │
│    → Returns OracleDataSource instance          │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 3. oracle_data_source.py                        │
│    → Fetches credentials from API               │
│    → Loads custom query from column_config.json │
│    → Connects to Oracle with thick mode         │
│    → Executes query, returns DataFrame          │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 4. ranking_engine.py                            │
│    → Applies business logic                     │
│    → Ranks and filters data                     │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 5. rules_service.py                             │
│    → Applies configured rules                   │
│    → Transforms data                            │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│ 6. output_service.py                            │
│    → Saves to configured destination            │
│    → Local Excel or S3 based on OUTPUT_DESTINATION│
└─────────────────────────────────────────────────┘
```

---

## 🔍 Testing Scenarios

### Scenario 1: Excel → Oracle Transition
**Action:** Change `.env` from `DATA_SOURCE=excel` to `DATA_SOURCE=oracle`

**Expected Behavior:**
- ✅ System status shows Oracle as data source
- ✅ Dashboard loads data from Oracle
- ✅ Automation runs fetch from Oracle
- ✅ Cron jobs use Oracle
- ✅ Manual upload still works (reads user Excel files)

### Scenario 2: Query Update by Super Admin
**Action:** Update query in CLO Mappings page

**Expected Behavior:**
- ✅ Query saved to `column_config.json`
- ✅ Next automation run uses new query
- ✅ New columns appear in configuration
- ✅ Historical data unchanged

### Scenario 3: Column Visibility Change
**Action:** Enable/disable columns in CLO Mappings

**Expected Behavior:**
- ✅ Dashboard shows only enabled columns
- ✅ Security Search respects column visibility
- ✅ Manual color page shows enabled columns
- ✅ Data fetch unchanged (still gets all columns)

### Scenario 4: Cron Job Execution
**Action:** Wait for scheduled cron job or trigger manually

**Expected Behavior:**
- ✅ Fetches data from Oracle using saved query
- ✅ Processes data through rules engine
- ✅ Saves to configured output destination
- ✅ Execution logged in cron logs

---

## 🐛 Common Issues & Solutions

### Issue 1: "Oracle driver not installed"
**Solution:**
```bash
pip install oracledb
```

### Issue 2: "DPY-3001: Network Encryption only supported in thick mode"
**Solution:**
- Download Oracle Instant Client from Oracle website
- Extract to `C:\oracle\instantclient_21_13`
- Add to Windows PATH environment variable
- Restart terminal and backend

### Issue 3: "Oracle connection failed: TNS:no listener"
**Solution:**
- Verify `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME` are correct
- Test network connectivity: `Test-NetConnection -ComputerName YOUR_HOST -Port 1521`
- Ensure VPN is connected

### Issue 4: "Credentials not found in API response"
**Solution:**
- Verify `ORACLE_CREDENTIALS_API_URL` is correct
- Test API manually: `Invoke-RestMethod -Uri "YOUR_API_URL"`
- Check API returns `eval.jdbc.user` and `eval.jdbc.password` keys

### Issue 5: Query returns no columns
**Solution:**
- Verify query syntax is valid Oracle SQL
- Test query directly in Oracle SQL Developer
- Check query has `SELECT *` or explicit column list
- Ensure user has SELECT permissions on tables

---

## 📊 Critical Files Reference

### Configuration Files
| File | Purpose | Location |
|------|---------|----------|
| `.env` | System configuration | `sp-incb-market-pulse-master/.env` |
| `column_config.json` | CLO queries & column mapping | Project root |
| `requirements.txt` | Python dependencies | `sp-incb-market-pulse-master/` |

### Abstraction Layer Files
| File | Purpose |
|------|---------|
| `services/data_source_factory.py` | Creates appropriate data source |
| `services/oracle_data_source.py` | Oracle connection & query execution |
| `services/excel_data_source.py` | Excel file reading |
| `services/database_service.py` | Main data fetching service |

### Key Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/system-status` | GET | Check configuration |
| `/api/admin/oracle/execute-query` | POST | Test Oracle query |
| `/api/admin/oracle/save-query` | POST | Save query to config |
| `/api/admin/clo-mappings` | GET | Get CLO hierarchy |
| `/api/admin/clo-mappings/{id}/columns` | PUT | Update column visibility |

---

## 🚀 Production Deployment

### Pre-Deployment Checklist
- [ ] Test Oracle connection successful
- [ ] Test query execution in CLO Mappings
- [ ] Verify dashboard loads Oracle data
- [ ] Run full automation cycle successfully
- [ ] Test cron job execution
- [ ] Verify output destination (S3 or local)
- [ ] Test manual upload still works
- [ ] Backup existing data
- [ ] Document query for each CLO

### Deployment Steps
1. Set `ENVIRONMENT=production` in `.env`
2. Update `LOG_LEVEL=INFO` (not DEBUG)
3. Configure AWS S3 if using: `OUTPUT_DESTINATION=s3`
4. Set up cron schedule: `CRON_SCHEDULE=0 8,10,12,14,16,18 * * *`
5. Deploy backend to server (Azure/AWS/GCP)
6. Deploy frontend to static hosting
7. Update frontend API URL in `environment.ts`

---

## 📞 Support

If you encounter issues:

1. **Check Logs:** `sp-incb-market-pulse-master/src/main/logs/`
2. **System Status:** `GET /api/admin/system-status`
3. **Test Connection:** Run `test_oracle_connection.py`
4. **Verify Query:** Test in Oracle SQL Developer first

---

## ✨ Key Features Enabled

### ✅ Dynamic Query Configuration
- Super Admin can change Oracle query without code changes
- Each CLO can have different query
- Query saved in `column_config.json`

### ✅ Column Visibility Control
- Super Admin controls which columns users see
- Per-CLO column configuration
- UI automatically adapts

### ✅ Zero-Code Switching
- Change `.env` file from Excel to Oracle
- Restart backend - system transforms
- No code deployment needed

### ✅ Thick Mode Support
- Automatic Oracle thick mode initialization
- Network Encryption support
- Graceful fallback to thin mode

---

## 🎉 Success Criteria

System is production-ready when:
- ✅ System status shows `"overall_status": "ready"`
- ✅ Oracle connection test passes
- ✅ Query execution returns columns
- ✅ Dashboard loads Oracle data
- ✅ Automation runs successfully
- ✅ Output saved to destination
- ✅ Cron jobs execute on schedule
- ✅ Manual upload still functional
- ✅ Security search works with Oracle data
- ✅ All column visibility rules respected

---

**Last Updated:** February 3, 2026  
**Version:** 2.0 (Oracle Integration)
