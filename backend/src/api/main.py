"""
FastAPI application entry point for DocuMind AI backend.
Configures the application, registers routes, and sets up middleware.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database.mongodb import db
from src.database.models import HealthResponse
from src.api.routes.ingestion import router as ingestion_router
from src.api.routes.retrieval import router as retrieval_router
from src.utils.logger import get_api_logger

logger = get_api_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    logger.info("Starting DocuMind AI backend...")
    
    try:
        # Connect to MongoDB
        db.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down DocuMind AI backend...")
    db.close()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title="DocuMind AI",
    description="AI-powered documentation generation from code repositories",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Check if the API and database are healthy."
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse with API and database status
    """
    # Check database connection
    db_status = "healthy" if db.is_connected() else "unhealthy"
    
    return HealthResponse(
        status="healthy",
        database=db_status,
        timestamp=datetime.utcnow()
    )


@app.get(
    "/",
    tags=["health"],
    summary="Root endpoint",
    description="Welcome message and API information."
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DocuMind AI",
        "version": "1.0.0",
        "description": "AI-powered documentation generation from code repositories",
        "docs": "/docs",
        "health": "/health"
    }


# =============================================================================
# Register Routers
# =============================================================================

# Ingestion routes
app.include_router(ingestion_router)

# Retrieval routes (Phase 2 - Embeddings & Search)
app.include_router(retrieval_router)


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
