# CLO Column Cache Refresh Fix

## Problem Summary

**Issue**: When Super Admin updated CLO mappings (e.g., disabled MESSAGE_ID for Euro ABS → Auto Loan), users with cached selections didn't see the changes after refreshing the browser. The disabled columns still appeared in Rules and Presets dropdowns.

**Root Cause**: CLOSelectionService stored user's CLO selection (including `visibleColumns` array) in localStorage. When CLO mappings were updated in the backend, the localStorage cache became stale. Components read from this stale cache instead of fetching fresh data.

**User's Bug Report Flow**:
1. Super Admin navigates to CLO Mappings
2. Selects "Euro ABS → Auto Loan"
3. Toggles OFF "MESSAGE_ID" column
4. Clicks "Update CLO Mapping" (backend saves successfully ✅)
5. User refreshes browser tab
6. Opens Settings → Rules
7. MESSAGE_ID still appears in dropdown ❌ (should be hidden)

## Solution Implemented

### 1. Added `refreshColumnsFromBackend()` Method to CLOSelectionService

**File**: `market-pulse-main/src/app/services/clo-selection.service.ts`

**Changes Made**:
- Added HttpClient injection in constructor
- Added `baseURL` property from environment
- Implemented `refreshColumnsFromBackend()` method that:
  - Calls GET `/api/clo-mappings/user-columns/{clo_id}`
  - Updates cached `visibleColumns` with fresh data from backend
  - Saves updated selection to localStorage
  - Updates BehaviorSubject to notify all subscribers
  - Includes detailed console logging for debugging

**Code**:
```typescript
constructor(private http: HttpClient) {}

async refreshColumnsFromBackend(): Promise<void> {
  const currentSelection = this.getCurrentSelection();
  if (!currentSelection) {
    console.warn('⚠️ No CLO selection found to refresh');
    return;
  }

  try {
    console.log('🔄 Refreshing CLO columns from backend for:', currentSelection.cloId);
    
    const response: any = await this.http.get(
      `${this.baseURL}/api/clo-mappings/user-columns/${currentSelection.cloId}`
    ).toPromise();

    if (response && response.visible_columns) {
      const updatedSelection = {
        ...currentSelection,
        visibleColumns: response.visible_columns,
        selectedAt: new Date()
      };
      
      this.setSelection(updatedSelection);
      console.log('✅ CLO columns refreshed successfully:', response.visible_columns);
    }
  } catch (error) {
    console.error('❌ Failed to refresh CLO columns from backend:', error);
  }
}
```

### 2. Updated Settings Component to Refresh on Init

**File**: `market-pulse-main/src/app/components/settings/settings.ts`

**Changes Made**:
- Made `ngOnInit()` async
- Added `await this.cloSelectionService.refreshColumnsFromBackend()` before loading column options
- Ensures Settings page always shows the latest CLO configuration

**Code**:
```typescript
async ngOnInit() {
  // ... existing query params logic ...
  
  // Refresh CLO columns from backend to ensure we have the latest configuration
  await this.cloSelectionService.refreshColumnsFromBackend();
  
  // Load data from APIs
  this.loadColumnOptions();
  this.loadRules();
  this.loadCronJobs();
  // ... other loads ...
}
```

### 3. Updated Home Component to Refresh on Init

**File**: `market-pulse-main/src/app/components/home/home.ts`

**Changes Made**:
- Made `ngOnInit()` async
- Added `await this.cloSelectionService.refreshColumnsFromBackend()` before checking selection
- Ensures Dashboard shows correct columns immediately on load

**Code**:
```typescript
async ngOnInit() {
  console.log('🚀 Home component initialized - loading data from backend...');
  
  // Refresh CLO columns from backend to ensure we have the latest configuration
  await this.cloSelectionService.refreshColumnsFromBackend();
  
  // Check if user has selected CLO
  this.userCLOSelection = this.cloSelectionService.getCurrentSelection();
  
  // ... rest of initialization ...
}
```

## How It Works

### Before the Fix:
```
1. User logs in → Selects CLO → Backend returns visible_columns: [A, B, C, D]
2. CLOSelectionService saves to localStorage: {cloId: "X", visibleColumns: [A,B,C,D]}
3. Super Admin disables column B for CLO "X" in backend
4. User refreshes page → CLOSelectionService.getCurrentSelection() returns cached [A,B,C,D] ❌
5. Settings component uses stale column list → Column B still appears
```

### After the Fix:
```
1. User logs in → Selects CLO → Backend returns visible_columns: [A, B, C, D]
2. CLOSelectionService saves to localStorage: {cloId: "X", visibleColumns: [A,B,C,D]}
3. Super Admin disables column B for CLO "X" in backend
4. User refreshes page → Settings/Home ngOnInit() calls refreshColumnsFromBackend()
5. Backend returns updated visible_columns: [A, C, D] (B removed)
6. localStorage updated with fresh data: {cloId: "X", visibleColumns: [A,C,D]} ✅
7. Settings component uses fresh column list → Column B is hidden
```

## Testing Checklist

### Prerequisites
- ✅ Backend running on http://127.0.0.1:3334
- ✅ Frontend running on http://localhost:4200
- ✅ CLO mappings configured in Super Admin

### Test Scenario 1: Settings Component
1. Login to application
2. Select "Euro ABS → Auto Loan"
3. Navigate to Settings → Rules
4. Note which columns appear in dropdown (e.g., MESSAGE_ID, TICKER, SECTOR)
5. Open Super Admin → CLO Mappings
6. Select "Euro ABS → Auto Loan"
7. Disable "MESSAGE_ID" column
8. Click "Update CLO Mapping"
9. **Refresh browser tab** (F5 or Ctrl+R)
10. Navigate to Settings → Rules
11. **Expected**: MESSAGE_ID should NOT appear in dropdown ✅
12. **Check console**: Should see:
    - `🔄 Refreshing CLO columns from backend for: EURO_ABS_AUTO_LOAN`
    - `✅ CLO columns refreshed successfully: [...array without MESSAGE_ID...]`

### Test Scenario 2: Home Component (Dashboard)
1. Login to application
2. Select "USABS → Commercial"
3. Navigate to Dashboard (Home)
4. Note the columns visible in table
5. Open Super Admin → CLO Mappings
6. Select "USABS → Commercial"
7. Disable "BID" column
8. Click "Update CLO Mapping"
9. **Refresh browser tab**
10. Check Dashboard table headers
11. **Expected**: BID column should NOT appear ✅
12. **Check console**: Should see refresh logs

### Test Scenario 3: Multiple Users
1. User A logs in as "Euro ABS → Auto Loan"
2. User B logs in as "CLO → Risk Retention"
3. Super Admin disables "ASK" for "Euro ABS → Auto Loan" only
4. Both users refresh their browsers
5. **Expected**: 
   - User A should NOT see ASK column ✅
   - User B should still see ASK column ✅ (different CLO)

### Test Scenario 4: API Call Verification
1. Open browser DevTools → Network tab
2. Refresh any page (Settings or Home)
3. **Expected**: Should see HTTP GET request to:
   - `/api/clo-mappings/user-columns/{clo_id}`
   - Response: `{"clo_id": "...", "visible_columns": [...], ...}`
4. Verify response contains updated column list

## Console Logs to Monitor

When refresh works correctly, you should see:

```
🔄 Refreshing CLO columns from backend for: EURO_ABS_AUTO_LOAN
✅ CLO columns refreshed successfully: ["TICKER", "SECTOR", "BWIC_COVER", ...]
```

If there's an error:

```
❌ Failed to refresh CLO columns from backend: [error details]
```

If no selection exists:

```
⚠️ No CLO selection found to refresh
```

## Future Enhancements

### Optional: Add Cache Expiry Check
You could enhance the service to automatically refresh if cache is old:

```typescript
getCurrentSelection(): UserCLOSelection | null {
  const selection = this.selectionSubject.value;
  
  // Auto-refresh if selection is older than 5 minutes
  if (selection) {
    const ageInMinutes = (Date.now() - selection.selectedAt.getTime()) / 1000 / 60;
    if (ageInMinutes > 5) {
      console.log('🕒 Cache is stale, refreshing...');
      this.refreshColumnsFromBackend();
    }
  }
  
  return selection;
}
```

### Optional: Refresh After Mapping Update
In CLO Mappings component, after successful update:

```typescript
updateCLOMapping() {
  this.cloMappingService.updateMapping(this.selectedMapping).subscribe({
    next: () => {
      this.messageService.add({
        severity: 'success',
        summary: 'Mapping Updated',
        detail: 'Users must refresh to see changes'
      });
    }
  });
}
```

## Files Modified

1. ✅ `market-pulse-main/src/app/services/clo-selection.service.ts`
   - Added HttpClient injection
   - Added refreshColumnsFromBackend() method

2. ✅ `market-pulse-main/src/app/components/settings/settings.ts`
   - Made ngOnInit() async
   - Added refresh call before loading columns

3. ✅ `market-pulse-main/src/app/components/home/home.ts`
   - Made ngOnInit() async
   - Added refresh call before checking selection

## Backend Support

The fix relies on the existing backend endpoint:

**Endpoint**: `GET /api/clo-mappings/user-columns/{clo_id}`

**File**: `sp-incb-market-pulse-master/src/main/routers/clo_mappings.py`

**Response Format**:
```json
{
  "clo_id": "EURO_ABS_AUTO_LOAN",
  "clo_name": "Euro ABS - Auto Loan",
  "clo_type": "sub",
  "parent_clo": "EURO_ABS",
  "visible_columns": [
    "TICKER",
    "SECTOR",
    "BWIC_COVER",
    ...
  ],
  "column_count": 15
}
```

This endpoint was already implemented in the previous session and is working correctly.

## Conclusion

✅ **Cache refresh mechanism fully implemented**
✅ **Settings component always shows latest column configuration**
✅ **Home component always shows latest column configuration**
✅ **No TypeScript compilation errors**
✅ **Backend endpoint already available and tested**

The localStorage cache invalidation issue is now resolved. When Super Admin updates CLO mappings, users will see the changes after refreshing their browser, as the components now fetch fresh column configurations from the backend on initialization.
