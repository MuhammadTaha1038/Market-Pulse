# Email Functionality Test Script

## Test the email endpoints

# 1. Get current email configuration
Write-Host "`n=== 1. Getting Email Configuration ===" -ForegroundColor Cyan
$response = Invoke-WebRequest -Method GET -Uri "http://127.0.0.1:3334/api/email/config"
$config = $response.Content | ConvertFrom-Json
Write-Host ($config | ConvertTo-Json -Depth 10)

# 2. Get operators list (verify new operators)
Write-Host "`n=== 2. Getting Operators List ===" -ForegroundColor Cyan
$response = Invoke-WebRequest -Method GET -Uri "http://127.0.0.1:3334/api/rules/operators/list"
$operators = $response.Content | ConvertFrom-Json
Write-Host "Total operators: $($operators.operators.Count)"
$operators.operators | Format-Table -AutoSize

# 3. Update email configuration (example)
Write-Host "`n=== 3. Update Email Configuration Example ===" -ForegroundColor Yellow
Write-Host "To configure email, edit the file:"
Write-Host "sp-incb-market-pulse-master/data/email_config.json" -ForegroundColor Green
Write-Host "`nAdd your:"
Write-Host "  1. SMTP credentials (username & password)"
Write-Host "  2. Recipient emails"
Write-Host "  3. Set is_active to true"
Write-Host "`nSee EMAIL_CONFIGURATION_GUIDE.md for details"

# 4. Test SMTP connection (will fail if not configured)
Write-Host "`n=== 4. Test SMTP Connection ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Method POST -Uri "http://127.0.0.1:3334/api/email/test"
    $testResult = $response.Content | ConvertFrom-Json
    Write-Host "SMTP Test: $($testResult.message)" -ForegroundColor $(if($testResult.success){"Green"}else{"Yellow"})
} catch {
    Write-Host "SMTP not configured yet (expected)" -ForegroundColor Yellow
}

# 5. Get email logs
Write-Host "`n=== 5. Getting Email Logs ===" -ForegroundColor Cyan
$response = Invoke-WebRequest -Method GET -Uri "http://127.0.0.1:3334/api/email/logs"
$logs = $response.Content | ConvertFrom-Json
Write-Host "Total email logs: $($logs.count)"
if ($logs.count -gt 0) {
    $logs.logs | Select-Object -First 5 | Format-Table -AutoSize
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
Write-Host "`nNext Steps:"
Write-Host "1. Edit: sp-incb-market-pulse-master/data/email_config.json"
Write-Host "2. Add your Gmail credentials (see EMAIL_CONFIGURATION_GUIDE.md)"
Write-Host "3. Run: Invoke-WebRequest -Method POST -Uri 'http://127.0.0.1:3334/api/email/test'"
Write-Host "4. Send test email: Invoke-WebRequest -Method POST -Uri 'http://127.0.0.1:3334/api/email/send' -ContentType 'application/json' -Body '{""subject"":""Test"",""body"":""<h1>Test</h1>""}'"
