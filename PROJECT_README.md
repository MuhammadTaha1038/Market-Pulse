# MarketPulse - CLO Colors Data Processing System

**Version:** 2.0 - Integration Ready  
**Status:** Fully Abstracted - Ready for Oracle & S3 Integration  
**Date:** February 2, 2026

## 📋 Table of Contents
- [Overview](#overview)
- [What's New - Integration Ready](#whats-new---integration-ready)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Features](#features)
- [API Documentation](#api-documentation)
- [Integration Configuration](#integration-configuration)
- [Deployment](#deployment)
- [Future Integrations](#future-integrations)

---

## 🎯 Overview

MarketPulse is a comprehensive CLO (Collateralized Loan Obligation) color data processing system that automates the collection, processing, and delivery of market data to traders and analysts.

### Key Capabilities
- **Automated Color Processing**: Daily scheduled extraction and processing of color data
- **Manual Upload Workflow**: Step-by-step manual processing with real-time preview
- **CLO-Based Column Filtering**: Role-based column visibility for different user types
- **Rules Engine**: Configurable exclusion rules for data filtering
- **Preset Filters**: Save and apply custom filter combinations
- **Security Search**: Advanced search and export functionality
- **Comprehensive Logging**: Track all operations with detailed logs
- **🆕 Pluggable Data Sources**: Switch between Excel and Oracle with configuration
- **🆕 Flexible Output Destinations**: Save to local Excel, AWS S3, or both

---

## 🆕 What's New - Integration Ready

The system is now **fully abstracted** for plug-and-play integration:

### ✅ **Oracle Database Integration**
- Abstracted data source layer
- Fetches credentials from client API
- Dynamic column mapping using column_config.json
- **Configure in 10 minutes** - no code changes needed

### ✅ **AWS S3 Integration**
- Abstracted output destination layer
- Multiple file format support (Excel, CSV, Parquet)
- Save locally AND/OR to S3
- **Configure in 10 minutes** - no code changes needed

### 🔧 **Configuration-Based Setup**
- All settings in `.env` file
- Switch data sources: `DATA_SOURCE=excel` or `DATA_SOURCE=oracle`
- Switch outputs: `OUTPUT_DESTINATION=local`, `s3`, or `both`
- Test connections via API: `/api/admin/system-status`

**See:** [INTEGRATION_CONFIGURATION_GUIDE.md](sp-incb-market-pulse-master/documentation/INTEGRATION_CONFIGURATION_GUIDE.md) for complete setup instructions.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Angular 20)                    │
│  - Dashboard / Security Search                               │
│  - Color Processing Page (Manual Upload)                     │
│  - Settings (Rules, Presets, Cron Jobs, Logs)               │
│  - CLO Mappings Configuration                                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────┴────────────────────────────────────────┐
│                  Backend (FastAPI Python 3.13)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Core Services:                                       │   │
│  │  • RankingEngine - Parent-child hierarchy sorting   │   │
│  │  • OutputService - Excel/S3 output management       │   │
│  │  • RulesService - Exclusion logic                   │   │
│  │  • 🆕 DataSourceFactory - Excel/Oracle input        │   │
│  │  • 🆕 OutputDestinationFactory - Local/S3 output    │   │
│  │  • PresetsService - Filter combinations             │   │
│  │  • CronJobsService - Task scheduling                │   │
│  │  • CLOMappingService - Column visibility control    │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         │                          │
    ┌────┴─────┐            ┌──────┴──────┐
    │  Excel   │            │   Oracle    │
    │   OR     │            │  Database   │
    │  Oracle  │            │  (Future)   │
    └──────────┘            └─────────────┘
   🆕 Pluggable               Configuration
    Input Sources            via column_config.json
         │
         └─────────┬──────────────┐
                   │              │
            ┌──────┴──────┐  ┌────┴────┐
            │ Local Excel │  │  AWS S3 │
            │   Output    │  │  Output │
            └─────────────┘  └─────────┘
            🆕 Configurable Output Destinations

```

### Current Data Flow
1. **Input**: `Color today.xlsx` OR Oracle Database (configurable)
2. **Processing**: Backend applies ranking algorithm + rules
3. **Output**: `Processed_Colors_Output.xlsx` (21 columns with hierarchy info)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- pip and npm installed

### Backend Setup (FastAPI)
```bash
cd sp-incb-market-pulse-master
pip install -r requirements.txt
cd src/main
python handler.py
```
**Backend URL**: http://127.0.0.1:3334

### Frontend Setup (Angular)
```bash
cd market-pulse-main
npm install
npm start
```
**Frontend URL**: http://localhost:4200

### Default Login
- Navigate to http://localhost:4200
- Select CLO: **US CLO**, **EURO ABS AUTO LOAN**, or **EURO CLO**
- No authentication required (dev mode)

---

## ✨ Features

### 1. Automated Color Processing
- **Scheduled Execution**: Runs daily at configured time
- **Buffer System**: Upload Excel file to buffer
- **Auto-Trigger**: Click "Run Automation" or wait for scheduled run
- **Override Option**: Force immediate run regardless of schedule

### 2. Manual Color Processing
Complete workflow on "Color Process" page:
1. **Import**: Upload Excel file (auto-validates 18 columns)
2. **Preview**: See top 50 rows sorted by ranking algorithm
3. **Apply Rules**: Filter data using configured exclusion rules
4. **Delete Rows**: Manually remove unwanted entries
5. **Save to Output**: Append to `Processed_Colors_Output.xlsx` with MANUAL type

### 3. Security Search / Dashboard
- **Search by Column**: MESSAGE_ID, CUSIP, TICKER, SECTOR, SOURCE, BIAS
- **Preset Filters**: Apply saved filter combinations
- **Export**: Download filtered results as CSV
- **Most Recent Data**: Sorted by DATE DESC
- **CLO-Based Columns**: Shows only columns permitted for user's CLO type

### 4. Settings Management

#### Rules Engine
- Create exclusion rules with conditions (equal to, contains, greater than, etc.)
- Apply to automated and manual processing
- Track rule applications in logs

#### Presets
- Save filter combinations for quick reuse
- Apply to Security Search results
- Shareable across users (same CLO type)

#### Cron Jobs
- Schedule automated processing
- Configure time, frequency, enabled status
- View next run time and history

#### Logs
- Rules application logs
- Cron job execution logs
- Manual upload history
- Backup/restore activity

---

## 📡 API Documentation

### Base URL
```
http://127.0.0.1:3334
```

### Key Endpoints

#### Dashboard
```
GET  /api/dashboard/colors          # Get processed colors with filters
GET  /api/dashboard/monthly-stats   # Get monthly color statistics
GET  /api/dashboard/next-run        # Get next scheduled run time
```

#### Manual Color Processing
```
POST /api/manual-color/import       # Import Excel and get sorted preview
POST /api/manual-color/apply-rules  # Apply rules to session data
POST /api/manual-color/delete-rows  # Delete specific rows
POST /api/manual-color/save         # Save processed colors to output
```

#### Rules
```
GET    /api/rules                   # Get all rules
POST   /api/rules                   # Create new rule
PUT    /api/rules/{id}              # Update rule
DELETE /api/rules/{id}              # Delete rule
```

#### Presets
```
GET    /api/presets                 # Get all presets
POST   /api/presets                 # Create new preset
POST   /api/presets/{id}/apply      # Apply preset to data
DELETE /api/presets/{id}            # Delete preset
```

#### Cron Jobs
```
GET  /api/cron/jobs                 # Get all scheduled jobs
PUT  /api/cron/jobs/{id}            # Update job configuration
POST /api/cron/jobs/{id}/trigger    # Manually trigger job
GET  /api/cron/logs                 # Get execution history
```

#### CLO Mappings
```
GET /api/clo-mappings/user-columns/{clo_id}  # Get visible columns for CLO
GET /api/clo-mappings/structure              # Get full CLO hierarchy
```

**Full API Documentation**: See [documentation/API_DOCUMENTATION.md](sp-incb-market-pulse-master/documentation/API_DOCUMENTATION.md)

---

## 📦 Deployment

### Production Checklist
- [ ] Update `environment.ts` with production backend URL
- [ ] Configure Oracle database credentials (see Oracle Integration below)
- [ ] Set up S3 bucket and credentials (see S3 Integration below)
- [ ] Update CORS settings in `handler.py`
- [ ] Set up SSL certificates
- [ ] Configure email SMTP settings
- [ ] Deploy backend to cloud server (AWS/Azure/GCP)
- [ ] Build frontend: `npm run build`
- [ ] Deploy frontend to CDN/static hosting

**Detailed Deployment Guide**: See [documentation/DEPLOYMENT_CHECKLIST.md](sp-incb-market-pulse-master/documentation/DEPLOYMENT_CHECKLIST.md)

---

## 🔮 Future Integrations

### 1. Oracle Database Integration
**Status**: Ready for client credentials  
**Purpose**: Replace `Color today.xlsx` input with direct Oracle extraction

**Implementation**:
- Install: `pip install oracledb`
- Configure in `src/main/db_config.py`
- Update `src/main/services/database_service.py` to use Oracle queries
- Migration guide: [documentation/ORACLE_EXTRACTION_INSTRUCTIONS.md](sp-incb-market-pulse-master/documentation/ORACLE_EXTRACTION_INSTRUCTIONS.md)

### 2. S3 Integration
**Status**: Ready for client credentials  
**Purpose**: Replace `Processed_Colors_Output.xlsx` with S3 storage

**Implementation**:
- Install: `pip install boto3`
- Configure AWS credentials in environment variables
- Update `src/main/services/output_service.py` to use S3
- Migration guide: [documentation/S3_INTEGRATION_GUIDE.md](sp-incb-market-pulse-master/documentation/S3_INTEGRATION_GUIDE.md)

### 3. Email Notifications
**Status**: Pending SMTP configuration  
**Purpose**: Send processed colors to trader distribution lists

**Requirements**:
- SMTP server details
- Email templates
- Distribution lists per CLO type

---

## 📁 Project Structure

```
Data-main/
├── PROJECT_README.md                    # This file
├── column_config.json                   # Column definitions (18 columns)
├── Color today.xlsx                     # Sample input file
├── Processed_Colors_Output.xlsx         # Sample output file
│
├── market-pulse-main/                   # Angular Frontend
│   ├── src/app/
│   │   ├── components/
│   │   │   ├── home/                    # Dashboard / Security Search
│   │   │   ├── color-selection/         # Buffer Upload + Automation
│   │   │   ├── manual-color/            # Manual Processing Workflow
│   │   │   └── settings/                # Rules, Presets, Cron, Logs
│   │   ├── services/                    # API services
│   │   └── utils/                       # Column definitions, helpers
│   └── angular.json
│
└── sp-incb-market-pulse-master/         # FastAPI Backend
    ├── requirements.txt
    ├── src/main/
    │   ├── handler.py                   # Main FastAPI app
    │   ├── routers/                     # API endpoints
    │   ├── services/                    # Business logic
    │   ├── models/                      # Pydantic models
    │   └── data/                        # JSON storage (temp)
    └── documentation/                   # Consolidated docs
        ├── BACKEND_README.md
        ├── API_DOCUMENTATION.md
        ├── DEPLOYMENT_CHECKLIST.md
        ├── ORACLE_EXTRACTION_INSTRUCTIONS.md
        └── S3_INTEGRATION_GUIDE.md
```

---

## 🧪 Testing

### Manual Testing Steps
1. **Upload Buffer File**: Go to "Automated Cleaning" page
2. **Trigger Automation**: Click "Run Automation" with override option
3. **Verify Output**: Check `Processed_Colors_Output.xlsx` for new rows
4. **Manual Processing**: Go to "Color Process" page and upload file
5. **Apply Rules**: Test rule filtering
6. **Security Search**: Search by different columns and apply presets
7. **Export**: Download CSV and verify all columns present

### Backend Health Check
```bash
curl http://127.0.0.1:3334/api/health
# Expected: "healthy"

# Check integration status
curl http://127.0.0.1:3334/api/admin/system-status
# Shows data source and output destination configuration
```

---

## 🔧 Integration Configuration

The system is ready for Oracle and S3 integration. See complete setup guide:
**[INTEGRATION_CONFIGURATION_GUIDE.md](sp-incb-market-pulse-master/documentation/INTEGRATION_CONFIGURATION_GUIDE.md)**

### Quick Oracle Setup
```bash
# 1. Edit .env file
DATA_SOURCE=oracle
ORACLE_CREDENTIALS_API_URL=https://client-api.com/credentials
ORACLE_HOST=oracle-server.com
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_TABLE_NAME=COLOR_DATA

# 2. Install dependency
pip install oracledb requests

# 3. Restart server and test
curl http://localhost:3334/api/admin/system-status
```

### Quick S3 Setup
```bash
# 1. Edit .env file
OUTPUT_DESTINATION=s3
S3_BUCKET_NAME=market-pulse-processed
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# 2. Install dependency
pip install boto3

# 3. Restart server and test
curl http://localhost:3334/api/admin/system-status
```

**Configuration time: ~10 minutes each**  
**No code changes required!**

---

## 📞 Support & Contact

**Project**: MarketPulse CLO Colors System  
**Version**: 2.0 - Integration Ready  
**Client**: [Client Name]  
**Developed by**: [Your Team]  
**Date**: February 2, 2026

### Key Documentation
- **Integration Setup**: `documentation/INTEGRATION_CONFIGURATION_GUIDE.md` 🆕
- **System Abstraction**: `SYSTEM_ABSTRACTION_SUMMARY.md` 🆕
- Backend API: `documentation/API_DOCUMENTATION.md`
- Deployment: `documentation/DEPLOYMENT_CHECKLIST.md`
- Oracle Setup: `documentation/ORACLE_EXTRACTION_INSTRUCTIONS.md`
- S3 Setup: `documentation/S3_INTEGRATION_GUIDE.md`

---

## 🔒 Security Notes

**Current Demo Mode:**
- No authentication required
- All CLO types accessible
- Local file storage only

**Production Requirements:**
- Implement OAuth/JWT authentication
- Role-based access control (RBAC)
- Encrypt sensitive data
- Use environment variables for credentials
- Enable HTTPS only
- Implement rate limiting
- Add input validation and sanitization

---

## 📝 Change Log

### Version 1.0 (February 2, 2026)
- ✅ Complete automated color processing workflow
- ✅ Manual processing with ranking engine
- ✅ Rules and presets system
- ✅ CLO-based column filtering
- ✅ Security Search with advanced filters
- ✅ Comprehensive logging
- ✅ Cron job scheduling
- ✅ Excel input/output (Oracle-ready format)
- ⏳ Oracle database integration (pending credentials)
- ⏳ S3 storage integration (pending credentials)
- ⏳ Email notifications (pending SMTP config)

---

## 🎯 Next Steps for Client

1. **Review & Demo**: Test the system with provided Excel files
2. **Provide Credentials**:
   - Oracle database connection details
   - AWS S3 bucket and IAM credentials
   - SMTP server for email notifications
3. **Configuration**:
   - Confirm CLO structure and column mappings
   - Define exclusion rules
   - Set up cron job schedules
4. **Deployment**: Choose hosting environment (AWS/Azure/GCP)
5. **Go Live**: Final testing and production deployment

---

**Ready for Production** ✨  
All core features complete. Only pending: External integrations (Oracle, S3, Email) requiring client credentials.
