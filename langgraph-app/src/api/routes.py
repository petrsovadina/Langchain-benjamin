"""API endpointy pro Czech MedAI.

Endpointy:
    - GET /health - Kontrola stavu systému
    - POST /api/v1/consult - Lékařská konzultace (připraveno)
"""

import logging
from typing import Dict

from fastapi import APIRouter

from agent.utils.guidelines_storage import get_pool
from api.schemas import HealthCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Zdraví"],
    summary="Kontrola stavu systému",
    description="Ověřuje dostupnost API serveru, MCP serverů a databázového připojení.",
)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint.

    Verifies:
        - API server is running
        - MCP servers (SÚKL, BioMCP) are available
        - Database connectivity (future)

    Returns:
        HealthCheckResponse: Health status with component details.

    Example:
        >>> response = await health_check()
        >>> assert response.status == "healthy"
        >>> assert response.mcp_servers["sukl"] == "available"
    """
    mcp_status: Dict[str, str] = {}
    overall_status = "healthy"

    # Check SÚKL MCP client
    try:
        from agent.graph import _sukl_client

        if _sukl_client is not None:
            mcp_status["sukl"] = "available"
            logger.debug("SÚKL MCP client: available")
        else:
            mcp_status["sukl"] = "unavailable"
            overall_status = "degraded"
            logger.warning("SÚKL MCP client: unavailable")
    except Exception as e:
        mcp_status["sukl"] = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error(f"SÚKL MCP client check failed: {e}")

    # Check BioMCP client
    try:
        from agent.graph import _biomcp_client

        if _biomcp_client is not None:
            mcp_status["biomcp"] = "available"
            logger.debug("BioMCP client: available")
        else:
            mcp_status["biomcp"] = "unavailable"
            overall_status = "degraded"
            logger.warning("BioMCP client: unavailable")
    except Exception as e:
        mcp_status["biomcp"] = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error(f"BioMCP client check failed: {e}")

    # Database connectivity check
    database_status = "available"
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        logger.debug("Database: available")
    except Exception as e:
        database_status = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error(f"Database check failed: {e}")

    return HealthCheckResponse(
        status=overall_status,
        mcp_servers=mcp_status,
        database=database_status,
        version="0.1.0",
    )
