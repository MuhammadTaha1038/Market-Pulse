# MarketPulse - Bond Trading Color Processing System

## Overview

MarketPulse processes bond market price quotes ("colors") from multiple brokers and banks, automatically ranking them to help traders identify the best available prices. The system handles thousands of colors daily, applying intelligent algorithms to surface the most relevant quotes.

**Version:** 1.0 | **Status:** Production-Ready | **Technology:** Python 3.11 + FastAPI

---

## What This System Does

In bond trading, brokers send price quotes called "colors." Traders receive hundreds of these daily and need to quickly find the best prices. This system:

1. Ingests color data from Excel (demo) or Oracle database (production)
2. Ranks colors by: **DATE → RANK → PRICE**
3. Groups colors by security (CUSIP), showing best quote first
4. Outputs processed results for frontend consumption
5. Tracks automated vs manual processing

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Backend Server
```bash
cd src/main
python handler.py
```

Server runs on: **http://127.0.0.1:3334**

### 3. Access API Documentation
Open browser: **http://127.0.0.1:3334/docs**

---

## API Endpoints

### Dashboard APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/colors` | GET | Fetch processed colors (paginated) |
| `/api/dashboard/monthly-stats` | GET | Get color counts by month |
| `/api/dashboard/available-sectors` | GET | List all asset classes |
| `/api/dashboard/next-run` | GET | Next automation run time |
| `/api/dashboard/output-stats` | GET | Processing statistics |

**Example:**
```bash
curl "http://localhost:3334/api/dashboard/colors?limit=10"
```

### Manual Color APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/manual/upload-excel` | POST | Upload Excel file for manual processing |
| `/api/manual/process-manual-colors` | POST | Process selected colors |
| `/api/manual/clear-output` | POST | Clear output file |

**Example:**
```bash
curl -X POST http://localhost:3334/api/manual/upload-excel \
  -F "file=@colors.xlsx"
```

### Admin APIs (Column Configuration)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/columns` | GET | View all columns |
| `/api/admin/columns` | POST | Add new column |
| `/api/admin/columns/{id}` | PUT | Update column |
| `/api/admin/columns/{id}` | DELETE | Remove column |
| `/api/admin/oracle-table` | PUT | Set Oracle table name |
| `/api/admin/sql-preview` | GET | Preview SQL query |
| `/api/admin/oracle/test-connection` | POST | Test Oracle connectivity |
| `/api/admin/oracle/enable` | POST | Enable Oracle mode |

---

## Project Structure

```
sp-incb-market-pulse-master/
├── src/main/
│   ├── handler.py                    # FastAPI entry point
│   ├── models/color.py               # Data models
│   ├── services/
│   │   ├── database_service.py       # Excel/Oracle data loading
│   │   ├── ranking_engine.py         # Core ranking algorithm
│   │   ├── output_service.py         # Excel output writer
│   │   └── column_config_service.py  # Dynamic column config
│   └── routers/
│       ├── dashboard.py              # Dashboard endpoints
│       ├── manual_colors.py          # Manual processing
│       └── admin.py                  # Admin configuration
├── infra/                            # Terraform (AWS deployment)
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## Ranking Algorithm

**Sorting Priority:** DATE (newest) → RANK (1-6, lower better) → PX (lower price better)

**Example:**
```
Security: WDMNT 2022-9A (CUSIP: 97988RBL5)

Row 1: DATE=2026-01-11, RANK=1, PX=101.5  ← PARENT (best)
Row 2: DATE=2026-01-11, RANK=2, PX=101.7  ← Child (lower rank)
Row 3: DATE=2026-01-10, RANK=1, PX=101.4  ← Child (older date)
Row 4: DATE=2026-01-11, RANK=1, PX=102.0  ← Child (higher price)
```

Frontend shows only Row 1 (parent) by default. Trader can expand to see children.

---

## Oracle Database Integration

### Current Mode
✅ **Excel** (demo mode) - Using `Color today.xlsx` (5,213 sample records)

### Production Mode (Oracle)
The system is **ready for Oracle** but needs your configuration.

#### Step 1: Install Oracle Driver
```bash
pip install oracledb
```

#### Step 2: Enable Oracle Mode
Edit `src/main/services/database_service.py`, line 30:
```python
ORACLE_ENABLED = True  # Change from False
```

#### Step 3: Configure Oracle Table
```bash
curl -X PUT http://localhost:3334/api/admin/oracle-table \
  -H "Content-Type: application/json" \
  -d '{"table_name": "YOUR_TABLE_NAME"}'
```

#### Step 4: Test Connection
```bash
curl -X POST http://localhost:3334/api/admin/oracle/enable \
  -H "Content-Type: application/json" \
  -d '{
    "host": "your-oracle-host.aws.com",
    "port": 1521,
    "service_name": "ORCL",
    "user": "your_user",
    "password": "your_password"
  }'
```

#### Step 5: Verify
```bash
curl -X POST http://localhost:3334/api/admin/oracle/test-connection
```

### Expected Oracle Table Columns

| Column | Type | Required | Used For |
|--------|------|----------|----------|
| MESSAGE_ID | INTEGER | Yes | Unique identifier |
| TICKER | VARCHAR | Yes | Security symbol |
| CUSIP | VARCHAR | Yes | Grouping key |
| DATE | DATE | Yes | Ranking (primary) |
| RANK | INTEGER | Yes | Ranking (secondary) |
| PX | FLOAT | Yes | Ranking (tertiary) |
| SECTOR | VARCHAR | Yes | Filtering |
| SOURCE | VARCHAR | Yes | Display |
| BIAS | VARCHAR | Yes | Quote type |
| BID | FLOAT | No | Price info |
| ASK | FLOAT | No | Price info |

**Note:** Admin can add/remove columns via API without code changes.

---

## Data Flow

### Automated Processing
```
Excel/Oracle → Load Data → Ranking Engine → Group by CUSIP → 
Output Excel → API → Frontend
```

### Manual Processing
```
User Upload Excel → API Parses → Frontend Review → User Selects → 
Ranking Engine → Output Excel (marked MANUAL)
```

---

## Output Files

### Processed_Colors_Output.xlsx
Location: `Data-main/Processed_Colors_Output.xlsx`

Contains:
- **PROCESSED_AT:** Timestamp
- **PROCESSING_TYPE:** AUTOMATED or MANUAL
- All 18 data columns
- **IS_PARENT:** True for best quote per CUSIP
- **PARENT_MESSAGE_ID:** Link to parent
- **CHILDREN_COUNT:** Number of alternative quotes

**Future:** Will be replaced with S3 bucket (code ready).

---

## Column Configuration

Admin can modify which columns to extract from Oracle.

### View Columns
```bash
curl http://localhost:3334/api/admin/columns
```

### Add Column
```bash
curl -X POST http://localhost:3334/api/admin/columns \
  -H "Content-Type: application/json" \
  -d '{
    "oracle_name": "TRADER_NAME",
    "display_name": "Trader",
    "data_type": "VARCHAR",
    "required": false,
    "description": "Trader who submitted quote"
  }'
```

### Preview SQL
```bash
curl "http://localhost:3334/api/admin/sql-preview?where_clause=DATE>SYSDATE-1"
```

Response:
```json
{
  "sql_query": "SELECT MESSAGE_ID, TICKER, ... FROM MARKET_COLORS WHERE DATE>SYSDATE-1",
  "column_count": 18
}
```

---

## AWS Deployment

### Using Terraform (Already Configured)

1. **Package Lambda**
```bash
./package.sh
```

2. **Deploy Infrastructure**
```bash
cd infra
terraform init
terraform apply -var-file=variables-prod.tfvars
```

3. **Set Environment Variables**
Configure in AWS Lambda:
- `ORACLE_HOST`
- `ORACLE_USER`
- `ORACLE_PASSWORD` (use AWS Secrets Manager)
- `ORACLE_SERVICE`

### GitLab CI/CD
Pipeline file: `.gitlab-ci.yml` (already configured)

Stages:
1. Build → Package Lambda
2. Test → Run unit tests
3. Deploy → Terraform apply

---

## Troubleshooting

### "Oracle driver not installed"
**This is a warning, not an error.** System runs in Excel mode.

To enable Oracle:
```bash
pip install oracledb
```

### "python-multipart required"
```bash
pip install python-multipart
```

### Backend won't start
1. Check Python version: `python --version` (need 3.11+)
2. Install dependencies: `pip install -r requirements.txt`
3. Verify `Color today.xlsx` exists in `Data-main/` folder

### Port 3334 already in use
Change port in `handler.py`:
```python
uvicorn.run(app, host="127.0.0.1", port=8000)  # Use 8000 instead
```

---

## Client Checklist

### What You Have
- ✅ Complete backend system (FastAPI)
- ✅ Sample data (5,213 colors in Excel)
- ✅ Ranking engine (production-ready)
- ✅ Output management
- ✅ Admin APIs for configuration
- ✅ Terraform infrastructure files
- ✅ Oracle integration code (ready)

### What You Need to Provide
- [ ] Oracle database host and credentials
- [ ] Oracle table name
- [ ] Column list (if different from sample)
- [ ] AWS account access for deployment

### Next Steps
1. Test system with Excel data
2. Provide Oracle connection details
3. We enable Oracle mode
4. Test with live Oracle data
5. Deploy to AWS Lambda
6. Go live

---

## Support

**System Status:** ✅ Production-Ready (Demo Mode)  
**Oracle Integration:** Ready (needs your credentials)  
**Deployment:** Terraform configured, ready to deploy

**Contact backend developer for:**
- Oracle connection setup
- Column configuration
- AWS deployment assistance
- Production support

---

**Last Updated:** January 17, 2026  
**Version:** 1.0
