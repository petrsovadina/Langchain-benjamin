"""FastAPI application for Czech MedAI.

Production-ready API server with CORS, error handling, and health checks.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.config import settings
from api.logging_config import setup_logging
from api.routes import limiter, router

logger = logging.getLogger(__name__)

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup/shutdown events.

    Startup:
        - Setup structured logging
        - Log server start
        - Verify MCP clients (graceful degradation if unavailable)

    Shutdown:
        - Log server shutdown
        - Cleanup resources (future: close DB connections)
    """
    # Setup structured logging
    setup_logging()

    # Startup
    logger.info("🚀 Czech MedAI API server starting...", extra={
        "environment": settings.environment,
        "workers": settings.api_workers,
    })
    logger.info("📊 LangGraph multi-agent system ready")

    # Verify MCP clients (non-blocking)
    try:
        from agent.graph import _biomcp_client, _sukl_client

        if _sukl_client:
            logger.info("✅ SÚKL MCP client available")
        else:
            logger.warning("⚠️  SÚKL MCP client unavailable (graceful degradation)")

        if _biomcp_client:
            logger.info("✅ BioMCP client available")
        else:
            logger.warning("⚠️  BioMCP client unavailable (graceful degradation)")
    except Exception as e:
        logger.error(f"❌ MCP client verification failed: {e}")

    yield

    # Shutdown
    logger.info("🛑 Czech MedAI API server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Czech MedAI API",
    description=(
        "AI asistent pro české lékaře - klinická rozhodovací podpora "
        "založená na důkazech z českých i mezinárodních zdrojů."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    # Add to request state
    request.state.request_id = request_id

    # Process request
    response = await call_next(request)

    # Add to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses.

    Headers:
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY
        - X-XSS-Protection: 1; mode=block
        - Strict-Transport-Security: HSTS for HTTPS
        - Content-Security-Policy: Restrict resource loading
    """
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HSTS (only for HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    # CSP (Content Security Policy)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'"
    )

    return response


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # Convert to ms
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions with proper logging."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Czech MedAI API",
        "version": "0.1.0",
        "description": "AI asistent pro české lékaře",
        "docs": "/docs",
        "health": "/health",
    }
