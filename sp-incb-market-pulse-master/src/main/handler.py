import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse, JSONResponse
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from routers import dashboard, manual_colors, admin
from routers.manual_color import router as manual_color_router
from routers.search import router as search_router
from routers.clo_mappings import router as clo_mappings_router
from rules import router as rules_router
from cron_jobs import router as cron_router
from manual_upload import router as manual_upload_router
from backup_restore import router as backup_router
from column_config import router as column_config_router
from email_router import router as email_router
from unified_logs import router as logs_router
from presets import router as presets_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MarketPulse API",
    description="Backend API for MarketPulse color data processing",
    version="1.0.0"
)

PREFIX = os.environ.get('BASE_PATH', "")

# CORS configuration for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)
app.include_router(manual_colors.router)
app.include_router(admin.router)
app.include_router(search_router)  # 🆕 Generic Column-Config Driven Search
app.include_router(clo_mappings_router)  # 🆕 CLO-Column Mappings for User Access Control
app.include_router(rules_router)  # 🆕 Rules Engine APIs
app.include_router(cron_router)   # 🆕 Cron Jobs & Automation
app.include_router(manual_upload_router)  # 🆕 Manual Upload (Admin Panel Buffer)
app.include_router(manual_color_router)  # 🆕 Manual Color Processing (Color Page)
app.include_router(backup_router)  # 🆕 Backup & Restore
app.include_router(column_config_router)  # 🆕 Column Configuration
app.include_router(email_router)  # 🆕 Email Functionality
app.include_router(logs_router)  # 🆕 Unified Logging with Revert
app.include_router(presets_router)  # 🆕 Presets for Security Search

logger.info("MarketPulse API initialized successfully")


@app.get(PREFIX + "/version", response_class=PlainTextResponse)
def version_response():
    """Get API version"""
    version = os.environ.get('RELEASE_VERSION', '1.0.0')
    return version


@app.get(PREFIX + "/health", response_class=PlainTextResponse)
def health_response():
    """Health check endpoint"""
    return "Target is healthy"


@app.get(PREFIX + "/")
def root():
    """Root endpoint"""
    return {
        "service": "MarketPulse API",
        "version": os.environ.get('RELEASE_VERSION', '1.0.0'),
        "status": "running",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "health": "/health",
            "version": "/version",
            "docs": "/docs"
        }
    }


if __name__ == '__main__':
    logger.info("Starting MarketPulse API server on http://127.0.0.1:3334")
    uvicorn.run(app, host='127.0.0.1', port=3334)

