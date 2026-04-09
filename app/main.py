"""
Main FastAPI application
Entry point for the Erie Otters Stats Dashboard
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
from app.database import create_db_and_tables
from app.routers import pages, debug

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"

# Create FastAPI app
app = FastAPI(
    title="Erie Otters Stats Dashboard",
    description="Learning-friendly hockey stats dashboard for Erie Otters",
    version="1.0.0"
)

# Create database tables
create_db_and_tables()

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"Static files mounted from {STATIC_DIR}")

# Setup Jinja2 templates
if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    logger.info(f"Templates loaded from {TEMPLATES_DIR}")
else:
    logger.warning(f"Templates directory not found at {TEMPLATES_DIR}")
    templates = None

# Include routers
app.include_router(pages.router)
app.include_router(debug.router)

# ==================== CUSTOM ERROR HANDLERS ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors with friendly page"""
    return HTMLResponse(
        """
        <html>
        <head>
            <title>Not Found</title>
            <link rel="stylesheet" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h1 style="color: #0b1f41;">404 - Page Not Found</h1>
                <p>The page you're looking for doesn't exist.</p>
                <a href="/" class="btn">Go Home</a>
            </div>
        </body>
        </html>
        """,
        status_code=404
    )

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "app": "Erie Otters Stats Dashboard"}

# ==================== STARTUP/SHUTDOWN EVENTS ====================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🏒 Erie Otters Stats Dashboard starting up...")
    logger.info(f"Templates directory: {TEMPLATES_DIR}")
    logger.info(f"Static files directory: {STATIC_DIR}")
    logger.info(f"Database location: {BASE_DIR}/erie_otters.db")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("🏒 Erie Otters Stats Dashboard shutting down...")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
