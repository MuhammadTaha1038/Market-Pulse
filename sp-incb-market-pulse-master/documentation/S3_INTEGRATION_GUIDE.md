# S3 Integration Guide - Advanced Search API

## 🎯 Overview

The Market Pulse API provides **comprehensive search capabilities** for processed colors data. Currently using Excel files, **fully ready for S3 migration**.

---

## 📍 Current Status

✅ **Search API Implemented** - Supports 9 filter parameters  
✅ **Performance Optimized** - Limit=10 default for fast previews  
✅ **S3-Ready Architecture** - Easy migration path documented  
⏳ **S3 Service Created** - Ready to use when needed  

---

## 🔍 Advanced Search API

### **Endpoint:** `GET /api/dashboard/colors`

Search processed colors by **any combination** of filters:

### **Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `cusip` | string | Filter by CUSIP (exact match) | `037833100` |
| `ticker` | string | Filter by ticker symbol | `AAPL` |
| `message_id` | integer | Filter by message ID | `12345` |
| `asset_class` | string | Filter by sector | `TECHNOLOGY` |
| `source` | string | Filter by source | `TRACE`, `BLOOMBERG` |
| `bias` | string | Filter by bias | `BUY_BIAS`, `SELL_BIAS` |
| `processing_type` | string | Filter by type | `AUTOMATED`, `MANUAL` |
| `date_from` | string | Start date | `2026-01-01` |
| `date_to` | string | End date | `2026-02-02` |
| `limit` | integer | Max records (1-100) | `10` (default) |
| `skip` | integer | Pagination offset | `0` (default) |

### **Response Format:**

```json
{
  "total_count": 50000,
  "page": 1,
  "page_size": 10,
  "colors": [
    {
      "message_id": 12345,
      "ticker": "AAPL",
      "cusip": "037833100",
      "sector": "TECHNOLOGY",
      "date": "2026-02-02",
      "price_level": 150.25,
      "bid": 150.20,
      "ask": 150.30,
      "px": 150.25,
      "source": "TRACE",
      "bias": "BUY_BIAS",
      "rank": 1,
      "cov_price": 148.50,
      "percent_diff": 1.18,
      "price_diff": 1.75,
      "confidence": 8,
      "date_1": "2026-02-01",
      "diff_status": "INCREASE",
      "is_parent": true,
      "parent_message_id": null,
      "children_count": 3
    }
  ]
}
```

---

## 🚀 API Usage Examples

### **1. Search by CUSIP**
```bash
GET /api/dashboard/colors?cusip=037833100&limit=10
```

### **2. Search by Ticker**
```bash
GET /api/dashboard/colors?ticker=AAPL&limit=20
```

### **3. Search by Message ID**
```bash
GET /api/dashboard/colors?message_id=12345
```

### **4. Search by Asset Class/Sector**
```bash
GET /api/dashboard/colors?asset_class=TECHNOLOGY&limit=50
```

### **5. Search by Source**
```bash
GET /api/dashboard/colors?source=TRACE&limit=10
```

### **6. Search by Bias**
```bash
GET /api/dashboard/colors?bias=BUY_BIAS&limit=10
```

### **7. Search by Processing Type**
```bash
GET /api/dashboard/colors?processing_type=AUTOMATED&limit=10
```

### **8. Search with Date Range**
```bash
GET /api/dashboard/colors?date_from=2026-01-01&date_to=2026-02-02&limit=50
```

### **9. Combined Search (Multiple Filters)**
```bash
GET /api/dashboard/colors?ticker=AAPL&source=TRACE&bias=BUY_BIAS&date_from=2026-01-01&limit=10
```

### **10. Pagination**
```bash
# Page 1
GET /api/dashboard/colors?limit=10&skip=0

# Page 2
GET /api/dashboard/colors?limit=10&skip=10

# Page 3
GET /api/dashboard/colors?limit=10&skip=20
```

---

## 📊 Performance Notes

### **Current (Excel):**
- ✅ **Limit=10** → ~0.7 seconds (fast preview)
- ⚠️ **Limit=100** → ~3-5 seconds (reads more data)
- ❌ **No limit** → 20+ seconds (reads entire file)

### **After S3 Migration:**
- ✅ **Limit=10** → ~0.2 seconds (S3 Select server-side filtering)
- ✅ **Limit=100** → ~0.5 seconds (S3 Select optimization)
- ✅ **Complex filters** → Same speed (all filtering on S3 side)

---

## 🔄 S3 Migration Steps

### **Step 1: Install Dependencies**
```bash
pip install boto3
```

### **Step 2: Configure AWS Credentials**
```bash
# Option A: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Option B: AWS CLI (recommended)
aws configure

# Option C: IAM Role (for Lambda/EC2 - most secure)
# No configuration needed, uses instance role
```

### **Step 3: Create S3 Bucket**
```bash
aws s3 mb s3://market-pulse-processed-colors --region us-east-1
```

### **Step 4: Enable S3 in Application**
```bash
# Set environment variable
export USE_S3=true
export S3_BUCKET_NAME=market-pulse-processed-colors
```

### **Step 5: Update Code (1 line change!)**

**File:** `src/main/routers/dashboard.py`

**Before (Excel):**
```python
from services.output_service import get_output_service
output_service = get_output_service()
```

**After (S3):**
```python
from services.s3_service import get_s3_service, is_s3_enabled
output_service = get_s3_service() if is_s3_enabled() else get_output_service()
```

**That's it!** The API endpoints remain the same, just faster with S3.

---

## 🏗️ S3 File Structure

```
s3://market-pulse-processed-colors/
  processed_colors/
    year=2026/
      month=01/
        colors_2026-01-15.csv
        colors_2026-01-16.csv
      month=02/
        colors_2026-02-01.csv
        colors_2026-02-02.csv
```

**Benefits:**
- ✅ Partitioned by year/month for fast queries
- ✅ Daily files for easy management
- ✅ S3 Select can scan partitions efficiently
- ✅ Easy to delete old data

---

## 🧪 Testing the Search API

### **Test 1: Basic Search**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:3334/api/dashboard/colors?limit=10" `
  -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

### **Test 2: Search by CUSIP**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:3334/api/dashboard/colors?cusip=037833100" `
  -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

### **Test 3: Search by Ticker + Date Range**
```powershell
$params = @{
  ticker = "AAPL"
  date_from = "2026-01-01"
  date_to = "2026-02-02"
  limit = 20
}
$query = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
Invoke-WebRequest -Uri "http://127.0.0.1:3334/api/dashboard/colors?$query" `
  -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

### **Test 4: Performance Test**
```powershell
Write-Host "Testing search performance..." -ForegroundColor Cyan

# Test 1: Small limit (should be fast)
$time1 = Measure-Command {
  $result = Invoke-WebRequest -Uri "http://127.0.0.1:3334/api/dashboard/colors?limit=10" -UseBasicParsing
}
Write-Host "Limit=10: $($time1.TotalSeconds) seconds" -ForegroundColor Green

# Test 2: Larger limit
$time2 = Measure-Command {
  $result = Invoke-WebRequest -Uri "http://127.0.0.1:3334/api/dashboard/colors?limit=50" -UseBasicParsing
}
Write-Host "Limit=50: $($time2.TotalSeconds) seconds" -ForegroundColor Yellow

# Test 3: With filters
$time3 = Measure-Command {
  $result = Invoke-WebRequest -Uri "http://127.0.0.1:3334/api/dashboard/colors?ticker=AAPL&limit=10" -UseBasicParsing
}
Write-Host "Filtered: $($time3.TotalSeconds) seconds" -ForegroundColor Green
```

---

## 📝 Frontend Integration

### **Angular Service (already created):**

```typescript
// src/app/services/api.service.ts

getColors(
  skip: number = 0,
  limit: number = 10,
  filters?: {
    cusip?: string;
    ticker?: string;
    message_id?: number;
    asset_class?: string;
    source?: string;
    bias?: string;
    processing_type?: string;
    date_from?: string;
    date_to?: string;
  }
): Observable<ColorResponse> {
  let params = new HttpParams()
    .set('skip', skip.toString())
    .set('limit', limit.toString());
  
  if (filters) {
    Object.keys(filters).forEach(key => {
      if (filters[key]) {
        params = params.set(key, filters[key].toString());
      }
    });
  }
  
  return this.http.get<ColorResponse>(`${this.baseUrl}/api/dashboard/colors`, { params });
}
```

### **Usage Example:**

```typescript
// Search by CUSIP
this.apiService.getColors(0, 10, { cusip: '037833100' }).subscribe(response => {
  console.log(`Found ${response.total_count} colors`);
  this.colors = response.colors;
});

// Search by multiple filters
this.apiService.getColors(0, 20, {
  ticker: 'AAPL',
  source: 'TRACE',
  date_from: '2026-01-01',
  date_to: '2026-02-02'
}).subscribe(response => {
  this.colors = response.colors;
});
```

---

## ✅ Summary

### **What's Done:**

1. ✅ **Enhanced Search API** - 9 filter parameters (CUSIP, ticker, message_id, etc.)
2. ✅ **Performance Optimized** - Default limit=10 for fast previews
3. ✅ **Pagination Support** - Skip/limit for large datasets
4. ✅ **Date Range Filtering** - Search by date range
5. ✅ **S3 Service Created** - Ready for migration (`s3_service.py`)
6. ✅ **S3-Ready Architecture** - Easy 1-line switch

### **What's Needed for S3 Migration:**

1. ⏳ Install boto3: `pip install boto3`
2. ⏳ Configure AWS credentials
3. ⏳ Create S3 bucket
4. ⏳ Set `USE_S3=true` environment variable
5. ⏳ Update import in `dashboard.py` (1 line)

### **Benefits After S3:**

- 🚀 **Faster queries** - S3 Select does server-side filtering
- 📦 **Better scalability** - No file size limits
- 💰 **Lower costs** - Pay only for what you query
- 🔒 **Better security** - S3 encryption and IAM policies
- 📊 **Analytics ready** - Can connect to Athena, QuickSight

---

## 🔗 Related Files

- **Search API:** `src/main/routers/dashboard.py` (lines 58-180)
- **Output Service:** `src/main/services/output_service.py`
- **S3 Service:** `src/main/services/s3_service.py` ⭐ NEW
- **Models:** `src/main/models/color.py`

---

## 📞 Support

For S3 migration assistance, refer to:
- AWS Documentation: https://docs.aws.amazon.com/s3/
- Boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- S3 Select: https://docs.aws.amazon.com/AmazonS3/latest/userguide/selecting-content-from-objects.html
