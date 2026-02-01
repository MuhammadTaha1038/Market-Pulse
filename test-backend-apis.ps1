# Quick Backend API Test Script
# Test all the new APIs to ensure they're working

Write-Host "🧪 Testing MarketPulse Backend APIs" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

$baseUrl = "http://127.0.0.1:3334"

# Test 1: Health Check
Write-Host "1️⃣ Testing Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    Write-Host "✅ Health Check: $response" -ForegroundColor Green
} catch {
    Write-Host "❌ Health Check Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Get All Rules
Write-Host "2️⃣ Testing Rules API - GET /api/rules..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/rules" -Method Get -ContentType "application/json"
    Write-Host "✅ Rules API Response:" -ForegroundColor Green
    Write-Host "   Total Rules: $($response.count)" -ForegroundColor Cyan
    if ($response.count -gt 0) {
        Write-Host "   First Rule: $($response.rules[0].name)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Rules API Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: Get Operators List
Write-Host "3️⃣ Testing Rules API - GET /api/rules/operators/list..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/rules/operators/list" -Method Get -ContentType "application/json"
    Write-Host "✅ Operators List Response:" -ForegroundColor Green
    Write-Host "   Total Operators: $($response.operators.Count)" -ForegroundColor Cyan
    if ($response.operators.Count -gt 0) {
        Write-Host "   First Operator: $($response.operators[0].label)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Operators API Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Get All Cron Jobs
Write-Host "4️⃣ Testing Cron Jobs API - GET /api/cron/jobs..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cron/jobs" -Method Get -ContentType "application/json"
    Write-Host "✅ Cron Jobs API Response:" -ForegroundColor Green
    Write-Host "   Total Jobs: $($response.count)" -ForegroundColor Cyan
    if ($response.count -gt 0) {
        Write-Host "   First Job: $($response.jobs[0].name)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Cron Jobs API Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Get Cron Execution Logs
Write-Host "5️⃣ Testing Cron Logs API - GET /api/cron/logs..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/cron/logs" -Method Get -ContentType "application/json"
    Write-Host "✅ Cron Logs API Response:" -ForegroundColor Green
    Write-Host "   Total Logs: $($response.count)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Cron Logs API Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Get Manual Upload History
Write-Host "6️⃣ Testing Manual Upload API - GET /api/manual-upload/history..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/manual-upload/history" -Method Get -ContentType "application/json"
    Write-Host "✅ Manual Upload API Response:" -ForegroundColor Green
    Write-Host "   Total Uploads: $($response.count)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Manual Upload API Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 7: Get Backup History
Write-Host "7️⃣ Testing Backup API - GET /api/backup/history..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/backup/history" -Method Get -ContentType "application/json"
    Write-Host "✅ Backup API Response:" -ForegroundColor Green
    Write-Host "   Total Backups: $($response.count)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Backup API Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Test 8: Create a Test Rule
Write-Host "8️⃣ Testing Rules API - POST /api/rules (Create Rule)..." -ForegroundColor Yellow
$testRule = @{
    name = "Frontend Test Rule - $(Get-Date -Format 'HH:mm:ss')"
    conditions = @(
        @{
            type = "where"
            column = "BWIC_COVER"
            operator = "equals"
            value = "TEST_BANK"
        }
    )
    is_active = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/rules" -Method Post -Body $testRule -ContentType "application/json"
    Write-Host "✅ Create Rule Response:" -ForegroundColor Green
    Write-Host "   Message: $($response.message)" -ForegroundColor Cyan
    Write-Host "   Rule ID: $($response.rule.id)" -ForegroundColor Cyan
    Write-Host "   Rule Name: $($response.rule.name)" -ForegroundColor Cyan
    
    # Store the rule ID for cleanup
    $testRuleId = $response.rule.id
    
    # Test 9: Delete the Test Rule
    Write-Host ""
    Write-Host "9️⃣ Testing Rules API - DELETE /api/rules/$testRuleId (Cleanup)..." -ForegroundColor Yellow
    try {
        $deleteResponse = Invoke-RestMethod -Uri "$baseUrl/api/rules/$testRuleId" -Method Delete -ContentType "application/json"
        Write-Host "✅ Delete Rule Response:" -ForegroundColor Green
        Write-Host "   Message: $($deleteResponse.message)" -ForegroundColor Cyan
    } catch {
        Write-Host "❌ Delete Rule Failed: $_" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Create Rule Failed: $_" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "====================================" -ForegroundColor Green
Write-Host "🎉 Backend API Testing Complete!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. If all tests passed, start the Angular frontend" -ForegroundColor White
Write-Host "2. Navigate to Settings page" -ForegroundColor White
Write-Host "3. Check if Rules section loads real data" -ForegroundColor White
Write-Host "4. Try creating a new rule" -ForegroundColor White
Write-Host "5. Check browser DevTools Network tab for API calls" -ForegroundColor White
Write-Host ""
