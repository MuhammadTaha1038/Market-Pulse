# Quick Start Guide - Oracle Data Extraction

## For Client (Non-Technical User)

### What You Need
1. ✅ VPN connection to Oracle database
2. ✅ Admin credentials for Oracle database
3. ✅ Windows/Mac/Linux computer with Python installed

---

## Simple 3-Step Process

### Step 1: Download and Setup
1. Download the `scripts` folder
2. Open PowerShell (Windows) or Terminal (Mac/Linux)
3. Navigate to the scripts folder:
   ```
   cd path/to/scripts
   ```
4. Run the setup script:
   - **Windows:** `setup_extraction.bat`
   - **Mac/Linux:** `bash setup_extraction.sh`

### Step 2: Configure Database Connection
**Copy and paste these commands into PowerShell (replace with your actual values):**

```powershell
$env:ORACLE_HOST = "your-database-host.com"
$env:ORACLE_PORT = "1521"
$env:ORACLE_SERVICE_NAME = "ORCL"
$env:ORACLE_USERNAME = "admin_user"
$env:ORACLE_PASSWORD = "your_password"
$env:ORACLE_SCHEMA = "MARKET_DATA"
$env:ORACLE_TABLE_NAME = "COLORS_TABLE"
```

**Replace these values:**
- `your-database-host.com` → Your Oracle database server address
- `admin_user` → Your admin username
- `your_password` → Your admin password
- `MARKET_DATA` → The schema name (if you know it)
- `COLORS_TABLE` → The main table name (if you know it)

### Step 3: Extract Data

**Option A - List tables first (if you don't know the table name):**
```
python extract_sample_data.py --list-tables
```

**Option B - Extract data from specific table:**
```
python extract_sample_data.py --limit 1000
```

---

## What You'll Get

After running the script, you'll have a `sample_data` folder with:
- ✅ `database_info.json` - Database version and details
- ✅ `accessible_tables.json` - List of all tables
- ✅ `TABLENAME_schema.json` - Column definitions
- ✅ `TABLENAME_sample_YYYYMMDD_HHMMSS.csv` - Sample data (Excel-compatible)
- ✅ `TABLENAME_sample_YYYYMMDD_HHMMSS.json` - Sample data (JSON format)

---

## Send to Development Team

1. Create a ZIP file of the `sample_data` folder
2. Upload to SharePoint/OneDrive or email
3. Notify the development team

**That's it! You're done!** 🎉

---

## Troubleshooting

### "Python is not installed"
→ Download and install Python from https://www.python.org/downloads/

### "Cannot connect to Oracle"
→ Make sure you're connected to VPN first

### "Invalid username/password"
→ Double-check your credentials (username and password)

### "Table not found"
→ Run with `--list-tables` to see available tables

### Need Help?
Contact: Backend Development Team

---

## For DevOps Team

After receiving the sample data:

1. Review the data structure
2. Update Terraform SSM parameters with actual credentials
3. Deploy infrastructure:
   ```bash
   cd infra
   terraform init
   terraform plan
   terraform apply
   ```

4. Verify Lambda has access to SSM parameters

---

**Document Version:** 1.0  
**Date:** January 11, 2026
