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

