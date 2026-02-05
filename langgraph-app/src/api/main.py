"""FastAPI application for Czech MedAI.

Production-ready API server with CORS, error handling, and health checks.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup/shutdown events.

    Startup:
        - Log server start
        - Verify MCP clients (graceful degradation if unavailable)

    Shutdown:
        - Log server shutdown
        - Cleanup resources (future: close DB connections)
    """
    # Startup
    logger.info("🚀 Czech MedAI API server starting...")
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

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
