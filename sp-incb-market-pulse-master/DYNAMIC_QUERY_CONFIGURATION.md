# Dynamic Query Configuration Guide

## Overview

Super admins can now configure custom SQL queries for each CLO without modifying code. This allows flexible data extraction from Oracle database with different column selections per CLO.

## Feature Workflow

### 1. **Login as Super Admin**
Access the admin panel with super admin credentials.

### 2. **Navigate to CLO Column Mapping**
Open the CLO Configuration page where you can manage queries and columns.

### 3. **Insert Custom SQL Query**
- Click "Add New Query" for a specific CLO
- Paste your SQL query (e.g., from `Final New Query US (D+E).sql`)
- Click "Test Query" to validate

### 4. **Review Available Columns**
After executing the query:
- System shows all columns returned by the query
- Displays data types for each column
- Shows sample data (first 5 rows)

### 5. **Select Columns for CLO**
- Check/uncheck columns you want to use
- Rename display names if needed
- Mark required columns
- Save configuration

### 6. **Configuration Saved**
The query and column selection are saved in `column_config.json` and used automatically when fetching data for that CLO.

---

## API Endpoints

### 1. Execute Query (Test)
**POST** `/api/admin/execute-query`

Test a SQL query and get available columns.

**Request Body:**
```json
{
  "query": "SELECT * FROM ...",
  "clo_id": "US_CLO_2.0"
}
```

**Response:**
```json
{
  "success": true,
  "query": "SELECT * FROM ...",
  "clo_id": "US_CLO_2.0",
  "total_columns": 18,
  "columns": [
    {
      "name": "MESSAGE_ID",
      "oracle_name": "MESSAGE_ID",
      "data_type": "VARCHAR2",
      "display_name": "Message ID",
      "enabled": true
    },
    {
      "name": "TICKER",
      "oracle_name": "TICKER",
      "data_type": "VARCHAR2",
      "display_name": "Ticker",
      "enabled": true
    }
  ],
  "sample_data": [
    {
      "MESSAGE_ID": "12345",
      "TICKER": "ABC 2021-1 A"
    }
  ],
  "message": "Query executed successfully. Found 18 columns."
}
```

### 2. Save Query
**POST** `/api/admin/save-query`

Save a SQL query for a specific CLO.

**Request Body:**
```json
{
  "query": "SELECT * FROM ...",
  "clo_id": "US_CLO_2.0",
  "query_name": "base_query"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Query saved successfully for CLO: US_CLO_2.0",
  "clo_id": "US_CLO_2.0",
  "query_name": "base_query"
}
```

### 3. Update CLO Columns
**POST** `/api/admin/update-clo-columns`

Update which columns are enabled for a CLO.

**Request Body:**
```json
{
  "clo_id": "US_CLO_2.0",
  "columns": [
    {
      "name": "MESSAGE_ID",
      "oracle_name": "MESSAGE_ID",
      "display_name": "Message ID",
      "data_type": "VARCHAR2",
      "enabled": true,
      "required": true
    },
    {
      "name": "TICKER",
      "oracle_name": "TICKER",
      "display_name": "Ticker Symbol",
      "data_type": "VARCHAR2",
      "enabled": true,
      "required": false
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Columns updated successfully for CLO: US_CLO_2.0",
  "clo_id": "US_CLO_2.0",
  "total_columns": 18,
  "enabled_columns": 15
}
```

---

## Configuration File Structure

### column_config.json
```json
{
  "US_CLO_2.0": {
    "name": "US CLO 2.0",
    "enabled": true,
    "queries": {
      "base_query": {
        "query": "WITH SEC_MASTER AS (SELECT ...) SELECT ...",
        "created_at": "2026-02-03 10:30:00",
        "updated_at": "2026-02-03 10:30:00"
      }
    },
    "columns": {
      "MESSAGE_ID": {
        "oracle_column_name": "MESSAGE_ID",
        "display_name": "Message ID",
        "data_type": "VARCHAR2",
        "enabled": true,
        "required": true
      },
      "TICKER": {
        "oracle_column_name": "TICKER",
        "display_name": "Ticker Symbol",
        "data_type": "VARCHAR2",
        "enabled": true,
        "required": false
      }
    },
    "updated_at": "2026-02-03 10:35:00"
  }
}
```

---

## How It Works

### Backend Query Resolution

When fetching data from Oracle, the system:

1. **Checks for Custom Query:**
   - Looks in `column_config.json` for CLO-specific query
   - If `queries.base_query` exists, uses that

2. **Falls Back to Default:**
   - If no custom query, uses default production query
   - Default query is embedded in `oracle_data_source.py`

3. **Applies Column Filtering:**
   - After fetching data, filters to only enabled columns
   - Renames columns based on `display_name` settings

### Frontend Integration

The admin UI should provide:

1. **Query Editor:**
   - Syntax-highlighted SQL editor
   - Test button to validate query
   - Save button to persist

2. **Column Selector:**
   - Checkboxes for each available column
   - Inline editing for display names
   - Drag-and-drop for column ordering

3. **CLO Selector:**
   - Dropdown to choose CLO
   - Create new CLO configuration
   - Clone configuration from another CLO

---

## Example Usage

### Scenario: Adding a New CLO Type

**Step 1:** Admin logs in and navigates to CLO Mappings

**Step 2:** Clicks "Add New CLO" → Enters "European_CLO_2025"

**Step 3:** Pastes custom SQL query for European CLOs:
```sql
SELECT 
    msg_id AS MESSAGE_ID,
    eur_ticker AS TICKER,
    cusip_eur AS CUSIP,
    date_traded AS DATE,
    price_bid AS BID,
    price_ask AS ASK
FROM EUROPEAN_CLO_DATA
WHERE currency = 'EUR'
  AND sector = 'CLO'
```

**Step 4:** Clicks "Test Query" → System returns:
- 6 columns found
- Sample data shown
- All columns enabled by default

**Step 5:** Admin adjusts:
- Unchecks "DATE" (not needed)
- Renames "MESSAGE_ID" to "Trade ID"
- Marks "CUSIP" as required

**Step 6:** Clicks "Save Configuration"

**Step 7:** System saves to `column_config.json`

**Result:** When automated jobs run or manual uploads happen for "European_CLO_2025", the system automatically uses this custom query.

---

## Benefits

### ✅ **No Code Changes Required**
Super admin can modify queries without developer intervention.

### ✅ **CLO-Specific Configuration**
Different CLOs can have different queries and column selections.

### ✅ **Validation Built-In**
Test queries before saving to prevent runtime errors.

### ✅ **Version Control**
Queries stored in JSON file can be tracked in Git.

### ✅ **Backward Compatible**
If no custom query exists, system uses default query.

---

## Security Considerations

### ⚠️ SQL Injection Protection
- All queries executed with read-only user
- Parameterized queries used where possible
- ROWNUM limit enforced on test queries

### ⚠️ Super Admin Only
- Only users with super admin role can modify queries
- Regular users cannot access query editor

### ⚠️ Audit Trail
- All query changes logged with timestamps
- `created_at` and `updated_at` tracked in config

---

## Troubleshooting

### Query Test Fails

**Error:** "Oracle error: ORA-00942: table or view does not exist"
- **Solution:** Check table names in query
- Verify Oracle user has SELECT permission

**Error:** "Syntax error in SQL query"
- **Solution:** Validate SQL in Oracle SQL Developer first
- Check for Oracle-specific syntax

### Columns Not Showing

**Issue:** Saved query but columns not appearing
- **Solution:** Check `enabled: true` in column_config.json
- Verify query actually returns data

### Data Not Loading

**Issue:** Custom query saved but data fetch fails
- **Solution:** Check `column_config.json` format
- Ensure `queries.base_query.query` exists
- Restart backend to reload configuration

---

## Next Steps

1. **Frontend Implementation:**
   - Build SQL editor component in Angular
   - Add column selector with checkboxes
   - Implement CLO management UI

2. **Enhanced Features:**
   - Query templates library
   - Query validation with dry-run
   - Column data type preview
   - Historical query versions

3. **Admin Training:**
   - Document SQL query patterns
   - Provide example queries
   - Create video tutorial

---

## Related Files

- `sp-incb-market-pulse-master/src/main/routers/admin.py` - API endpoints
- `sp-incb-market-pulse-master/src/main/services/oracle_data_source.py` - Query execution
- `column_config.json` - Configuration storage
- `Final New Query US (D+E).sql` - Example production query
