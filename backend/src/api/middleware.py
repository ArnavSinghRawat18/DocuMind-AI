"""
Middleware module for DocuMind AI backend.
Provides rate limiting, request ID tracking, and error handling.
"""

import uuid
import time
from typing import Callable
from contextvars import ContextVar

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("documind.middleware")

# Context variable for request ID (thread-safe)
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_var.get()


# =============================================================================
# Rate Limiter Configuration
# =============================================================================

def _get_client_ip(request: Request) -> str:
    """Get client IP, respecting X-Forwarded-For header."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Initialize rate limiter
limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    logger.warning(
        f"Rate limit exceeded for {_get_client_ip(request)} on {request.url.path}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail.split("per")[1].strip() if "per" in str(exc.detail) else "60 seconds"
        },
        headers={"Retry-After": "60"}
    )


# =============================================================================
# Request ID Middleware
# =============================================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request_id_var.set(request_id)
        
        # Store on request state for easy access
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


# =============================================================================
# Request Logging Middleware
# =============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Skip logging for health checks in production
        if settings.is_production() and request.url.path in ["/health", "/ready", "/"]:
            return await call_next(request)
        
        # Get request ID
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request (only in non-production or for non-trivial endpoints)
        if not settings.is_production() or request.url.path not in ["/health", "/ready"]:
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - Started"
            )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        log_level = "warning" if response.status_code >= 400 else "info"
        getattr(logger, log_level)(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"{response.status_code} ({duration_ms:.2f}ms)"
        )
        
        return response


# =============================================================================
# Error Handling Middleware
# =============================================================================

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            
            # Log the error
            logger.exception(f"[{request_id}] Unhandled exception: {e}")
            
            # In production, hide stack traces
            if settings.is_production():
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "An internal error occurred. Please try again later.",
                        "request_id": request_id
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": str(e),
                        "type": type(e).__name__,
                        "request_id": request_id
                    }
                )


# =============================================================================
# Payload Size Middleware
# =============================================================================

# Maximum request body sizes (bytes)
MAX_BODY_SIZE = 1024 * 1024  # 1MB default
ENDPOINT_BODY_LIMITS = {
    "/generate": 64 * 1024,      # 64KB for generation
    "/api/v1/ingest": 4 * 1024,  # 4KB for ingestion (just URL)
    "/api/v1/retrieve": 32 * 1024,  # 32KB for retrieval
}


class PayloadSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce request body size limits."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            
            if content_length:
                content_length = int(content_length)
                
                # Get limit for this endpoint
                limit = MAX_BODY_SIZE
                for path, path_limit in ENDPOINT_BODY_LIMITS.items():
                    if request.url.path.startswith(path):
                        limit = path_limit
                        break
                
                if content_length > limit:
                    logger.warning(
                        f"Payload too large for {request.url.path}: "
                        f"{content_length} > {limit} bytes"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body too large. Maximum: {limit // 1024}KB"
                        }
                    )
        
        return await call_next(request)
