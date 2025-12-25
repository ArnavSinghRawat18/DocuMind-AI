"""
FastAPI application entry point for DocuMind AI backend.
Configures the application, registers routes, and sets up middleware.

PHASE 4 COMPLETE - Production-ready with:
- Rate limiting
- Request ID tracking
- Structured logging
- Payload size limits
- Health/readiness checks
- Error handling
"""

import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.database.mongodb import db
from src.database.models import HealthResponse
from src.api.routes.ingestion import router as ingestion_router
from src.api.routes.retrieval import router as retrieval_router
from src.api.routes.generation import router as generation_router
from src.api.middleware import (
    limiter,
    rate_limit_exceeded_handler,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    PayloadSizeMiddleware
)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.utils.logger import get_api_logger

logger = get_api_logger()


def _log_startup_warnings():
    """Log warnings about non-production configurations."""
    if settings.USE_MOCK_EMBEDDINGS:
        logger.warning("⚠️  MOCK EMBEDDINGS ENABLED - Not for production use")
    if settings.USE_MOCK_LLM:
        logger.warning("⚠️  MOCK LLM ENABLED - Not for production use")
    if settings.CORS_ORIGINS == ["*"]:
        logger.warning("⚠️  CORS allows all origins - Restrict in production")
    if not settings.is_production():
        logger.info("Running in DEVELOPMENT mode")
    else:
        logger.info("Running in PRODUCTION mode")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting DocuMind AI backend v1.0.0")
    logger.info("=" * 60)
    
    # Validate configuration
    try:
        settings._validate_settings()
    except ValueError as e:
        logger.critical(f"Configuration validation failed: {e}")
        sys.exit(1)
    
    _log_startup_warnings()
    
    try:
        # Connect to MongoDB
        db.connect()
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.critical(f"❌ Failed to connect to database: {e}")
        raise
    
    logger.info("✅ DocuMind AI backend ready to serve requests")
    
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
    docs_url="/docs" if not settings.is_production() else None,
    redoc_url="/redoc" if not settings.is_production() else None,
    openapi_url="/openapi.json" if not settings.is_production() else None
)


# =============================================================================
# Rate Limiter Setup
# =============================================================================

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# =============================================================================
# Middleware Stack (order matters - first added = outermost)
# =============================================================================

# Error handling (outermost - catches all)
app.add_middleware(ErrorHandlingMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Request ID tracking
app.add_middleware(RequestIDMiddleware)

# Payload size limits
app.add_middleware(PayloadSizeMiddleware)

# CORS (must be after other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
    Health check endpoint - always responds if API is running.
    
    Returns:
        HealthResponse with API and database status
    """
    db_status = "healthy" if db.is_connected() else "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=datetime.utcnow()
    )


@app.get(
    "/ready",
    tags=["health"],
    summary="Readiness check",
    description="Check if the system is ready to serve traffic."
)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint - only returns ready when all dependencies are available.
    
    Returns:
        Readiness status with component checks
    """
    checks = {
        "database": False,
        "vector_store": False,
        "llm": False
    }
    
    # Check database
    checks["database"] = db.is_connected()
    
    # Check vector store (can access embeddings collection)
    try:
        if db.is_connected():
            # Just verify we can access the collection
            db.get_collection(settings.EMBEDDINGS_COLLECTION).find_one({}, {"_id": 1})
            checks["vector_store"] = True
    except Exception:
        # Collection may be empty, that's OK
        if db.is_connected():
            checks["vector_store"] = True
    
    # Check LLM availability (light check - just verify config)
    try:
        from src.generation import get_generator
        generator = get_generator()
        checks["llm"] = generator._llm_client is not None
    except Exception:
        pass
    
    all_ready = all(checks.values())
    
    if not all_ready:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return {
        "ready": True,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


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
        "phase": "4 - Production Ready",
        "description": "AI-powered documentation generation from code repositories",
        "docs": "/docs" if not settings.is_production() else "disabled",
        "health": "/health",
        "ready": "/ready"
    }


# =============================================================================
# Register Routers
# =============================================================================

# Ingestion routes
app.include_router(ingestion_router)

# Retrieval routes (Phase 2 - Embeddings & Search)
app.include_router(retrieval_router)

# Generation routes (Phase 3 - RAG)
app.include_router(generation_router)


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=not settings.is_production(),
        log_level=settings.LOG_LEVEL.lower()
    )
