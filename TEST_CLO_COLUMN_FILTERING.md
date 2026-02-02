# CLO Column Filtering - Test Guide

## Changes Made

### Backend (Oracle-Ready)

**1. Dashboard API (`routers/dashboard.py`)**
- Added `clo_id` parameter to `/api/dashboard/colors` endpoint
- Fetches visible columns from CLO mapping service
- Filters response data to only include visible columns
- **Oracle SQL equivalent documented in code comments**

**2. Color Model (`models/color.py`)**
- Made all `ColorProcessed` fields Optional
- Allows partial column returns based on CLO mapping
- System fields (is_parent, parent_message_id, children_count) always included

### Frontend

**1. API Service (`api.service.ts`)**
- Added `cloId` parameter to `getColors()` method
- Passes CLO ID to backend for column filtering

**2. Home Component (`home.ts`)**
- Passes user's CLO ID when fetching colors data
- Logs CLO ID for debugging

## Oracle Production Implementation

When migrating to Oracle database, the column filtering will work like this:

```python
# Get visible columns from CLO mapping
visible_columns = ['MESSAGE_ID', 'TICKER', 'CUSIP', 'DATE', 'BID', 'ASK']

# Build SQL query with only visible columns
columns_sql = ', '.join(visible_columns)

query = f"""
    SELECT {columns_sql}, 
           IS_PARENT, 
           PARENT_MESSAGE_ID, 
           CHILDREN_COUNT
    FROM MARKET_COLORS 
    WHERE CUSIP = :cusip
      AND DATE >= :date_from
      AND DATE <= :date_to
    ORDER BY DATE DESC
    OFFSET :skip ROWS 
    FETCH NEXT :limit ROWS ONLY
"""

# Execute with parameters
cursor.execute(query, {
    'cusip': cusip,
    'date_from': date_from,
    'date_to': date_to,
    'skip': skip,
    'limit': limit
})
```

## Testing Steps

### 1. Start Backend
```bash
cd "d:\SKILL\watsapp project\fast api project\Data-main\sp-incb-market-pulse-master\src\main"
python handler.py
```

### 2. Test CLO Mapping Configuration
```bash
# View EURO_ABS_AUTO_LEASE mapping
curl http://127.0.0.1:3334/api/clo-mappings/user-columns/EURO_ABS_AUTO_LEASE

# Expected response:
{
  "clo_id": "EURO_ABS_AUTO_LEASE",
  "clo_name": "Auto Lease",
  "clo_type": "EURO_ABS",
  "parent_clo": "EURO ABS",
  "visible_columns": ["MESSAGE_ID", "TICKER", "SECTOR", ...],
  "column_count": 18
}
```

### 3. Disable Some Columns via Super Admin
1. Navigate to `/clo-mappings` in the frontend
2. Select "EURO_ABS_AUTO_LEASE" (or any CLO)
3. Toggle OFF some columns (e.g., disable BID, ASK, PERCENT_DIFF)
4. Click "Update CLO Mapping"

### 4. Test Backend Column Filtering
```bash
# Get colors WITH CLO filtering
curl "http://127.0.0.1:3334/api/dashboard/colors?limit=2&clo_id=EURO_ABS_AUTO_LEASE"

# Get colors WITHOUT CLO filtering (all columns)
curl "http://127.0.0.1:3334/api/dashboard/colors?limit=2"
```

### 5. Test Frontend Integration
1. Login to the application
2. Select "EURO ABS" → "Auto Lease" in CLO selector
3. Go to Dashboard
4. Check browser console for log: "📊 CLO ID sent: EURO_ABS_AUTO_LEASE"
5. Verify data table shows only visible columns
6. Check Network tab → API call should include `clo_id` parameter

### 6. Verify Column Filtering Logic
```bash
# Check logs for column filtering
# Should see: "CLO 'EURO_ABS_AUTO_LEASE' visible columns: ['MESSAGE_ID', 'TICKER', ...]"
```

## Expected Behavior

### When CLO has disabled columns:
- ✅ API returns only visible columns' data
- ✅ Frontend table shows only visible columns
- ✅ Empty/null values for disabled columns
- ✅ All enabled columns show proper data
- ✅ System fields (is_parent, etc.) always included

### When NO CLO filter applied:
- ✅ API returns all 18 columns
- ✅ Full data set returned

## Troubleshooting

### Issue: Table shows empty data
**Cause:** Backend is filtering columns but frontend is looking for wrong field names

**Solution:** Check column mapping in `dashboard.py`:
```python
column_mapping = {
    'MESSAGE_ID': 'message_id',
    'TICKER': 'ticker',
    # ... must match ColorProcessed model fields
}
```

### Issue: All columns still showing
**Cause 1:** CLO ID not being passed to backend
- Check browser console logs for "📊 CLO ID sent: ..."
- Check Network tab for `clo_id` parameter

**Cause 2:** CLO mapping service not loading correctly
- Check backend logs for "CLO 'xxx' visible columns: [...]"
- Test `/api/clo-mappings/user-columns/{clo_id}` endpoint directly

### Issue: Error "field required"
**Cause:** ColorProcessed model fields not optional
- Verify `models/color.py` has `Optional[...]` for all data fields
- System fields must have defaults

## Oracle Migration Checklist

When migrating to Oracle:

- [ ] Replace `output_service.read_processed_colors()` with Oracle query
- [ ] Use the SQL template from code comments
- [ ] Map `visible_columns` to SELECT clause
- [ ] Add proper WHERE clause for filters
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Add OFFSET/FETCH for pagination (Oracle 12c+)
- [ ] Handle NULL values in Oracle results
- [ ] Add connection pooling
- [ ] Implement query caching for frequently accessed CLOs
- [ ] Add query execution time logging
- [ ] Test with large datasets (1M+ rows)

## Performance Benefits

### Oracle Production:
1. **Query Optimization:** Only requested columns fetched from database
2. **Network Efficiency:** Smaller payload sent to frontend
3. **Memory Savings:** Less data held in memory
4. **Index Usage:** Column-specific indexes can be utilized
5. **Caching:** Smaller cached result sets

### Example:
```
Full query (18 columns): 500 KB response, 120ms
Filtered query (5 columns): 140 KB response, 45ms
Savings: 72% smaller, 62% faster
```

## Security Notes

- Column filtering prevents data leakage
- Users only see columns authorized for their CLO type
- Super Admin can configure visibility per asset class
- Audit log tracks column configuration changes
- Oracle row-level security can be added for additional protection
