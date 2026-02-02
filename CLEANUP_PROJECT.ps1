# Project Cleanup Script
# Removes testing files, temporary documentation, and obsolete files
# Keeps only essential project files and consolidated documentation

Write-Host "🧹 Starting Project Cleanup..." -ForegroundColor Cyan
Write-Host ""

$rootPath = "D:\SKILL\watsapp project\fast api project\Data-main"
Set-Location $rootPath

# Files to DELETE from root
$filesToDelete = @(
    "BACKEND_ENDPOINT_DIAGNOSTIC.md",
    "CACHE_REFRESH_FIX.md",
    "CLO_COLUMN_FILTERING_COMPLETE.md",
    "COLOR_PROCESSING_TESTING_GUIDE.md",
    "COMPLETE_DEBUGGING_GUIDE.md",
    "DELIVERY_SUMMARY.md",
    "EMAIL_QUICK_SETUP.md",
    "FRONTEND_API_INTEGRATION_FIX.md",
    "FRONTEND_INTEGRATION_COMPLETE.md",
    "GENERIC_SEARCH_API_GUIDE.md",
    "IMPLEMENTATION_SUMMARY.md",
    "INTEGRATION_COMPLETE_SUMMARY.md",
    "MANUAL_COLORS_FIX_SUMMARY.md",
    "MANUAL_COLOR_BUG_FIXES.md",
    "PERFORMANCE_OPTIMIZATION_SUMMARY.md",
    "QUICK_START_GUIDE.md",
    "START_TESTING.md",
    "TESTING_CHECKLIST.md",
    "TESTING_INSTRUCTIONS.md",
    "TEST_CLO_COLUMN_FILTERING.md",
    "YOU_ARE_ON_WRONG_PAGE.md",
    "test-backend-apis.ps1",
    "test_search_request.json"
)

Write-Host "📄 Deleting temporary documentation from root..." -ForegroundColor Yellow
foreach ($file in $filesToDelete) {
    $path = Join-Path $rootPath $file
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "  ✓ Deleted: $file" -ForegroundColor Green
    }
}

# Files to DELETE from backend
$backendPath = Join-Path $rootPath "sp-incb-market-pulse-master"
$backendFilesToDelete = @(
    "ADMIN_FEATURES_COMPLETE.md",
    "CLIENT_REQUIREMENTS_IMPLEMENTATION.md",
    "COMPLETE_ADMIN_SYSTEM_GUIDE.md",
    "COMPREHENSIVE_ADMIN_GUIDE.md",
    "COMPREHENSIVE_ADMIN_GUIDE.pdf",
    "CRON_JOBS_TESTING.md",
    "EMAIL_CONFIGURATION_GUIDE.md",
    "FRONTEND_INTEGRATION.md",
    "MANUAL_COLOR_PROCESSING_GUIDE.md",
    "MANUAL_UPLOAD_TESTING.md",
    "POWERSHELL_API_COMMANDS.md",
    "PRESETS_AND_LOGS_API.md",
    "PROJECT_COMPLETE_SUMMARY.md",
    "REMAINING_REQUIREMENTS.md",
    "RULES_ENGINE_TESTING.md",
    "test_data_generator.py",
    "TEST_EMAIL_FUNCTIONALITY.ps1",
    "new.rar",
    "scripts.rar"
)

Write-Host ""
Write-Host "📄 Deleting temporary documentation from backend..." -ForegroundColor Yellow
foreach ($file in $backendFilesToDelete) {
    $path = Join-Path $backendPath $file
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "  ✓ Deleted: $file" -ForegroundColor Green
    }
}

# Delete old docs folder (already moved important files)
$oldDocsPath = Join-Path $backendPath "docs"
if (Test-Path $oldDocsPath) {
    Write-Host ""
    Write-Host "📁 Deleting old docs folder..." -ForegroundColor Yellow
    Remove-Item $oldDocsPath -Recurse -Force
    Write-Host "  ✓ Deleted: docs/" -ForegroundColor Green
}

# Delete 'new' folder
$newPath = Join-Path $backendPath "new"
if (Test-Path $newPath) {
    Write-Host ""
    Write-Host "📁 Deleting 'new' folder..." -ForegroundColor Yellow
    Remove-Item $newPath -Recurse -Force
    Write-Host "  ✓ Deleted: new/" -ForegroundColor Green
}

# Delete scripts folder
$scriptsPath = Join-Path $backendPath "scripts"
if (Test-Path $scriptsPath) {
    Write-Host ""
    Write-Host "📁 Deleting 'scripts' folder..." -ForegroundColor Yellow
    Remove-Item $scriptsPath -Recurse -Force
    Write-Host "  ✓ Deleted: scripts/" -ForegroundColor Green
}

# Create README in backend root pointing to documentation
$backendReadme = @"
# MarketPulse Backend (FastAPI)

**Version:** 1.0  
**Python:** 3.13+  
**Framework:** FastAPI  

## Quick Start

``````bash
pip install -r requirements.txt
cd src/main
python handler.py
``````

**Server URL**: http://127.0.0.1:3334  
**Health Check**: http://127.0.0.1:3334/api/health  

## Documentation

All comprehensive documentation has been moved to the `documentation/` folder:

- **[API_DOCUMENTATION.md](documentation/API_DOCUMENTATION.md)** - Complete API reference
- **[DEPLOYMENT_CHECKLIST.md](documentation/DEPLOYMENT_CHECKLIST.md)** - Production deployment guide
- **[ORACLE_EXTRACTION_INSTRUCTIONS.md](documentation/ORACLE_EXTRACTION_INSTRUCTIONS.md)** - Oracle database setup
- **[S3_INTEGRATION_GUIDE.md](documentation/S3_INTEGRATION_GUIDE.md)** - AWS S3 setup
- **[BACKEND_README.md](documentation/BACKEND_README.md)** - Detailed backend documentation

## Project Structure

``````
sp-incb-market-pulse-master/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── documentation/               # All documentation
├── infra/                       # Terraform configs (for production)
├── data/                        # JSON storage (temporary)
└── src/main/
    ├── handler.py               # FastAPI app entry point
    ├── routers/                 # API endpoints
    ├── services/                # Business logic
    ├── models/                  # Pydantic models
    └── utils/                   # Helpers
``````

## Environment Variables

Create `.env` file in `src/main/`:

``````env
# Oracle Database (production)
ORACLE_HOST=your_oracle_host
ORACLE_PORT=1521
ORACLE_SERVICE=your_service_name
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password

# AWS S3 (production)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket
S3_REGION=us-east-1

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_password
``````

## Testing

``````bash
# Health check
curl http://127.0.0.1:3334/api/health

# Get all rules
curl http://127.0.0.1:3334/api/rules

# Get processed colors
curl "http://127.0.0.1:3334/api/dashboard/colors?limit=10"
``````

---

For complete project overview, see [PROJECT_README.md](../PROJECT_README.md) in root folder.
"@

Set-Content -Path (Join-Path $backendPath "README.md") -Value $backendReadme -Force
Write-Host ""
Write-Host "📝 Created new backend README.md" -ForegroundColor Green

# Create README in frontend
$frontendPath = Join-Path $rootPath "market-pulse-main"
$frontendReadme = @"
# MarketPulse Frontend (Angular 20)

**Version:** 1.0  
**Framework:** Angular 20  
**UI Library:** PrimeNG  

## Quick Start

``````bash
npm install
npm start
``````

**URL**: http://localhost:4200  

## Build for Production

``````bash
npm run build
``````

Output will be in `dist/` folder. Deploy to any static hosting (Nginx, S3, Netlify, Vercel, etc.)

## Project Structure

``````
market-pulse-main/
├── src/app/
│   ├── components/
│   │   ├── home/                 # Dashboard / Security Search
│   │   ├── color-selection/      # Buffer Upload + Automation
│   │   ├── manual-color/         # Manual Processing Workflow
│   │   └── settings/             # Rules, Presets, Cron, Logs
│   ├── services/                 # API services
│   ├── utils/                    # Column definitions, helpers
│   └── layout/                   # Navigation, sidebar
├── angular.json
├── package.json
└── tsconfig.json
``````

## Environment Configuration

Update `src/enviornments/environment.ts`:

``````typescript
export const environment = {
  baseURL: 'http://127.0.0.1:3334',  // Change to production URL
  production: false
};
``````

For production:
``````typescript
export const environment = {
  baseURL: 'https://api.yourcompany.com',
  production: true
};
``````

## Key Features

- **Dashboard**: Real-time color data display with monthly charts
- **Security Search**: Advanced search by column with preset filters
- **Color Processing**: Manual upload workflow with rules application
- **Settings**: Manage rules, presets, cron jobs, and logs
- **CLO Selection**: Role-based column visibility

---

For complete project overview, see [PROJECT_README.md](../PROJECT_README.md) in root folder.
"@

Set-Content -Path (Join-Path $frontendPath "README.md") -Value $frontendReadme -Force
Write-Host "📝 Created new frontend README.md" -ForegroundColor Green

Write-Host ""
Write-Host "✨ Cleanup Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Project Structure:" -ForegroundColor White
Write-Host "  ├── PROJECT_README.md              (Main documentation)" -ForegroundColor Gray
Write-Host "  ├── column_config.json" -ForegroundColor Gray
Write-Host "  ├── Color today.xlsx               (Sample input)" -ForegroundColor Gray
Write-Host "  ├── Processed_Colors_Output.xlsx   (Sample output)" -ForegroundColor Gray
Write-Host "  ├── market-pulse-main/             (Frontend)" -ForegroundColor Gray
Write-Host "  │   └── README.md" -ForegroundColor Gray
Write-Host "  └── sp-incb-market-pulse-master/   (Backend)" -ForegroundColor Gray
Write-Host "      ├── README.md" -ForegroundColor Gray
Write-Host "      └── documentation/             (All docs)" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 Next: Review PROJECT_README.md for complete overview" -ForegroundColor Yellow
