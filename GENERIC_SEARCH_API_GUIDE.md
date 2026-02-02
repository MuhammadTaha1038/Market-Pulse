# Generic Search API Documentation

## Overview

**Column-Config Driven Search API** that allows searching processed colors by **ANY field defined in `column_config.json`**.

### Key Features
✅ **Future-Proof**: Column names are configurable, not hardcoded  
✅ **S3-Ready**: Works with Excel now, easily migrates to S3  
✅ **Flexible**: Supports multiple operators and multi-field filtering  
✅ **Dynamic**: Auto-discovers available fields from column_config.json  
✅ **Performant**: Optimized for large datasets (50k+ records)

---

## API Endpoints

### 1. Get Available Search Fields

**GET** `/api/search/fields`

Returns all searchable columns defined in column_config.json with metadata.

**Response:**
```json
{
  "version": "1.0",
  "total_fields": 18,
  "fields": [
    {
      "name": "MESSAGE_ID",
      "display_name": "Message ID",
      "data_type": "INTEGER",
      "required": true,
      "description": "Unique message identifier",
      "searchable": true
    },
    {
      "name": "TICKER",
      "display_name": "Ticker",
      "data_type": "VARCHAR",
      "required": true,
      "description": "Security ticker symbol",
      "searchable": true
    },
    ...
  ],
  "supported_operators": {
    "STRING": ["equals", "contains", "starts_with"],
    "INTEGER": ["equals", "gt", "lt", "gte", "lte", "between"],
    "FLOAT": ["equals", "gt", "lt", "gte", "lte", "between"],
    "DATE": ["equals", "gt", "lt", "gte", "lte", "between"]
  }
}
```

**Example:**
```bash
curl http://localhost:3334/api/search/fields
```

---

### 2. Simple GET Search

**GET** `/api/search/simple`

Quick single-field search using GET parameters.

**Parameters:**
- `field` (required): Column name from column_config.json
- `value` (required): Value to search for
- `operator` (optional): Search operator (default: "equals")
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Max results (default: 10, max: 100)

**Supported Operators:**
- `equals` - Exact match (case-insensitive)
- `contains` - Substring match
- `starts_with` - Prefix match
- `gt`, `lt`, `gte`, `lte` - Numeric/date comparisons
- `between` - Range (requires value2)

**Examples:**

```bash
# Search by CUSIP
GET /api/search/simple?field=CUSIP&value=12345&operator=equals

# Search by TICKER
GET /api/search/simple?field=TICKER&value=AAPL

# Search by SECTOR (contains)
GET /api/search/simple?field=SECTOR&value=Tech&operator=contains&limit=20

# Search by price range
GET /api/search/simple?field=PRICE_LEVEL&value=100&operator=gte

# Search by MESSAGE_ID
GET /api/search/simple?field=MESSAGE_ID&value=50123&operator=equals
```

**PowerShell Example:**
```powershell
$result = Invoke-WebRequest -Uri "http://localhost:3334/api/search/simple?field=TICKER&value=AAPL" -UseBasicParsing | ConvertFrom-Json
Write-Host "Found: $($result.total_count) records"
```

**Response:**
```json
{
  "total_count": 4,
  "returned_count": 4,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "MESSAGE_ID": 1234,
      "TICKER": "AAPL",
      "SECTOR": "Technology",
      "CUSIP": "037833100",
      "PRICE_LEVEL": 175.50,
      ...
    }
  ],
  "available_fields": ["MESSAGE_ID", "TICKER", "SECTOR", ...]
}
```

---

### 3. Advanced POST Search

**POST** `/api/search/generic`

Powerful multi-filter search with sorting and pagination.

**Request Body:**
```json
{
  "filters": [
    {
      "field": "SECTOR",
      "operator": "equals",
      "value": "Technology"
    },
    {
      "field": "PRICE_LEVEL",
      "operator": "gte",
      "value": 100
    },
    {
      "field": "DATE",
      "operator": "between",
      "value": "2025-01-01",
      "value2": "2025-12-31"
    }
  ],
  "skip": 0,
  "limit": 10,
  "sort_by": "PRICE_LEVEL",
  "sort_order": "desc"
}
```

**Response:** Same as simple search

**Examples:**

**1. Search Technology stocks with price >= 100:**
```json
{
  "filters": [
    {"field": "SECTOR", "operator": "equals", "value": "Technology"},
    {"field": "PRICE_LEVEL", "operator": "gte", "value": 100}
  ],
  "limit": 10,
  "sort_by": "PRICE_LEVEL",
  "sort_order": "desc"
}
```

**2. Search by CUSIP and date range:**
```json
{
  "filters": [
    {"field": "CUSIP", "operator": "starts_with", "value": "037"},
    {"field": "DATE", "operator": "between", "value": "2025-01-01", "value2": "2025-12-31"}
  ],
  "limit": 50
}
```

**3. Complex multi-criteria search:**
```json
{
  "filters": [
    {"field": "SECTOR", "operator": "equals", "value": "Finance"},
    {"field": "SOURCE", "operator": "equals", "value": "Bloomberg"},
    {"field": "BIAS", "operator": "equals", "value": "BULLISH"},
    {"field": "CONFIDENCE", "operator": "gte", "value": 4}
  ],
  "skip": 0,
  "limit": 20,
  "sort_by": "DATE",
  "sort_order": "desc"
}
```

**PowerShell Example:**
```powershell
$body = @{
    filters = @(
        @{field = "TICKER"; operator = "equals"; value = "AAPL"},
        @{field = "DATE"; operator = "gte"; value = "2025-01-01"}
    )
    limit = 10
} | ConvertTo-Json -Depth 10

$result = Invoke-WebRequest -Uri "http://localhost:3334/api/search/generic" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing | ConvertFrom-Json

Write-Host "Found: $($result.total_count) records"
```

---

## Search Operators Reference

| Operator | Data Types | Description | Example |
|----------|-----------|-------------|---------|
| `equals` | All | Exact match (case-insensitive for strings) | `{"field": "TICKER", "operator": "equals", "value": "AAPL"}` |
| `contains` | STRING | Substring match | `{"field": "SECTOR", "operator": "contains", "value": "Tech"}` |
| `starts_with` | STRING | Prefix match | `{"field": "CUSIP", "operator": "starts_with", "value": "037"}` |
| `gt` | NUMBER, DATE | Greater than | `{"field": "PRICE_LEVEL", "operator": "gt", "value": 100}` |
| `lt` | NUMBER, DATE | Less than | `{"field": "PRICE_LEVEL", "operator": "lt", "value": 200}` |
| `gte` | NUMBER, DATE | Greater than or equal | `{"field": "RANK", "operator": "gte", "value": 3}` |
| `lte` | NUMBER, DATE | Less than or equal | `{"field": "CONFIDENCE", "operator": "lte", "value": 5}` |
| `between` | NUMBER, DATE | Range (inclusive) | `{"field": "PRICE_LEVEL", "operator": "between", "value": 100, "value2": 200}` |

---

## Available Search Fields

*Dynamically loaded from `column_config.json`*

| Field Name | Display Name | Data Type | Description |
|-----------|-------------|-----------|-------------|
| `MESSAGE_ID` | Message ID | INTEGER | Unique message identifier |
| `TICKER` | Ticker | VARCHAR | Security ticker symbol |
| `SECTOR` | Sector | VARCHAR | Asset class/sector |
| `CUSIP` | CUSIP | VARCHAR | CUSIP identifier |
| `DATE` | Date | DATE | Trade/color date |
| `PRICE_LEVEL` | Price Level | FLOAT | Price level |
| `BID` | Bid | FLOAT | Bid price |
| `ASK` | Ask | FLOAT | Ask price |
| `PX` | Price | FLOAT | Mid price |
| `SOURCE` | Source | VARCHAR | Data source (TRACE, BLOOMBERG, etc.) |
| `BIAS` | Bias | VARCHAR | Color bias (BUY_BIAS, SELL_BIAS, etc.) |
| `RANK` | Rank | INTEGER | Ranking score (1-5) |
| `CONFIDENCE` | Confidence | INTEGER | Confidence level (1-5) |
| `PROCESSING_TYPE` | Processing Type | VARCHAR | AUTOMATED or MANUAL |

*Note: Fields are configurable in column_config.json - this list updates automatically*

---

## Migration to S3

When migrating from Excel to S3, update only `output_service.py`:

**Current (Excel):**
```python
def read_processed_colors(self, limit=None, filters=None):
    df = pd.read_excel(self.output_file_path, nrows=limit)
    # Apply filters...
    return df.to_dict('records')
```

**Future (S3):**
```python
def read_processed_colors(self, limit=None, filters=None):
    # Read from S3
    obj = s3_client.get_object(Bucket='market-pulse', Key='processed_colors.parquet')
    df = pd.read_parquet(obj['Body'], nrows=limit)
    # Apply filters...
    return df.to_dict('records')
```

**No changes needed to search API endpoints!** 🎉

---

## Performance Tips

1. **Use specific filters** - More filters = fewer records to process
2. **Set appropriate limits** - Default 10 for preview, increase as needed
3. **Use pagination** - Use `skip` and `limit` for large result sets
4. **Filter early** - Apply filters in the query, not after fetching
5. **Index frequently searched columns** - When using S3/database

---

## Error Handling

**Invalid field name:**
```json
{
  "detail": "Invalid field 'INVALID_FIELD'. Available fields: MESSAGE_ID, TICKER, SECTOR, ..."
}
```

**Invalid operator:**
```json
{
  "detail": "Unsupported operator 'invalid_op'. Use: equals, contains, gt, lt, gte, lte, between"
}
```

**Server error:**
```json
{
  "detail": "Error processing search: [error details]"
}
```

---

## Integration Examples

### Frontend (TypeScript/Angular)

```typescript
// Simple search
async searchByTicker(ticker: string) {
  const url = `${this.apiUrl}/search/simple?field=TICKER&value=${ticker}&limit=10`;
  return this.http.get<SearchResponse>(url).toPromise();
}

// Advanced search
async advancedSearch(filters: SearchFilter[]) {
  const body = {
    filters: filters,
    skip: 0,
    limit: 20,
    sort_by: 'DATE',
    sort_order: 'desc'
  };
  return this.http.post<SearchResponse>(`${this.apiUrl}/search/generic`, body).toPromise();
}

// Get available fields for UI
async getSearchableFields() {
  return this.http.get<FieldsResponse>(`${this.apiUrl}/search/fields`).toPromise();
}
```

### Python

```python
import requests

# Simple search
response = requests.get(
    'http://localhost:3334/api/search/simple',
    params={'field': 'TICKER', 'value': 'AAPL', 'limit': 10}
)
results = response.json()

# Advanced search
body = {
    "filters": [
        {"field": "SECTOR", "operator": "equals", "value": "Technology"},
        {"field": "PRICE_LEVEL", "operator": "gte", "value": 100}
    ],
    "limit": 20
}
response = requests.post('http://localhost:3334/api/search/generic', json=body)
results = response.json()
```

---

## Testing

```bash
# Test 1: Get available fields
curl http://localhost:3334/api/search/fields

# Test 2: Simple search
curl "http://localhost:3334/api/search/simple?field=TICKER&value=AAPL"

# Test 3: Advanced search
curl -X POST http://localhost:3334/api/search/generic \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [{"field": "SECTOR", "operator": "equals", "value": "Technology"}],
    "limit": 10
  }'
```

---

## Summary

✅ **Column names** are loaded from `column_config.json` - no hardcoding  
✅ **Search any field** dynamically without code changes  
✅ **S3-ready** - just swap storage layer, API stays the same  
✅ **Flexible operators** for all data types  
✅ **Multi-filter support** with AND logic  
✅ **Sorting and pagination** built-in  
✅ **Frontend-friendly** with available fields endpoint  

**The API will automatically adapt when column names change in column_config.json!** 🚀
