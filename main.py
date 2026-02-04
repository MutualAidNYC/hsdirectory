"""
HSDS API - Airtable to Open Referral

A FastAPI application that ingests data from Airtable and exposes it
through an HSDS 3.0 compliant REST API.

See: https://docs.openreferral.org/en/latest/hsds/api_reference.html
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from db.database import init_db
from airtable.sync import get_sync
from routes import root, services, organizations, taxonomies, service_at_locations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Initializes database and starts background sync on startup.
    Stops sync on shutdown.
    """
    logger.info("Starting HSDS API...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start initial sync and background sync
    sync = get_sync()
    try:
        logger.info("Running initial Airtable sync...")
        await sync.full_sync()
        logger.info("Initial sync complete")
    except Exception as e:
        logger.error(f"Initial sync failed: {e}")
    
    # Start background sync
    await sync.start_background_sync()
    
    yield
    
    # Cleanup
    logger.info("Shutting down HSDS API...")
    await sync.stop_background_sync()


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="HSDS API",
    description="Human Services Data Specification (HSDS) 3.0 Compliant API backed by Airtable",
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(root.router)
app.include_router(services.router)
app.include_router(organizations.router)
app.include_router(taxonomies.router)
app.include_router(service_at_locations.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
