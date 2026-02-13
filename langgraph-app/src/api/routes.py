"""API endpointy pro Czech MedAI.

Endpointy:
    - GET /health - Kontrola stavu systému
    - POST /api/v1/consult - Lékařská konzultace (připraveno)
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from agent.graph import Context, graph
from agent.utils.guidelines_storage import get_pool
from api.cache import get_cached_response, set_cached_response
from api.dependencies import transform_documents
from api.schemas import ConsultRequest, ErrorResponse, HealthCheckResponse

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

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
    mcp_status: dict[str, str] = {}
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
    except (ImportError, AttributeError) as e:
        mcp_status["sukl"] = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error("SÚKL MCP client check failed: %s", e)

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
    except (ImportError, AttributeError) as e:
        mcp_status["biomcp"] = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error("BioMCP client check failed: %s", e)

    # Database connectivity check
    database_status = "available"
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        logger.debug("Database: available")
    except (OSError, ConnectionRefusedError, asyncio.TimeoutError) as e:
        database_status = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error("Database check failed: %s", e)
    except Exception as e:
        database_status = f"error: {str(e)}"
        overall_status = "degraded"
        logger.error("Unexpected database check error: %s", e)

    return HealthCheckResponse(
        status=overall_status,
        mcp_servers=mcp_status,
        database=database_status,
        version="0.1.0",
    )


async def consult_stream_generator_with_cache(
    query: str,
    mode: str,
    user_id: str | None,
) -> AsyncGenerator[str, None]:
    """Generate SSE events with caching support.

    Wrapper around consult_stream_generator that caches quick mode responses.

    Args:
        query: User query text.
        mode: Execution mode ("quick" or "deep").
        user_id: Optional user identifier.

    Yields:
        SSE-formatted strings with caching metadata.
    """
    # Capture final response for caching
    final_response_data = None

    async for event in consult_stream_generator(query, mode, user_id):
        # Intercept final response for caching
        if "event: message" in event and "type" in event:
            try:
                # Extract data from SSE event
                lines = event.split("\n")
                for line in lines:
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "final":
                            final_response_data = data
            except (json.JSONDecodeError, KeyError):
                pass

        yield event

    # Cache final response (quick mode only)
    if mode == "quick" and final_response_data:
        await set_cached_response(query, mode, final_response_data)


async def consult_stream_generator(
    query: str,
    mode: str,
    user_id: str | None,
) -> AsyncGenerator[str, None]:
    r"""Generate SSE events for consult endpoint.

    Streams graph execution events in Server-Sent Events format.

    Args:
        query: User query text.
        mode: Execution mode ("quick" or "deep").
        user_id: Optional user identifier.

    Yields:
        SSE-formatted strings (event: ...\ndata: ...\n\n).

    Example SSE events:
        event: message
        data: {"type": "agent_start", "agent": "drug_agent"}

        event: message
        data: {"type": "final", "answer": "...", "retrieved_docs": [...]}

        event: done
        data: {}
    """
    start_time = time.time()

    try:
        # Get MCP clients from module-level instances
        from agent.graph import _biomcp_client, _sukl_client

        # Build context with all required fields including MCP clients
        context: Context = {
            "model_name": "claude-sonnet-4-5-20250929",
            "temperature": 0.0,
            "mode": mode,
            "user_id": user_id,
            "sukl_mcp_client": _sukl_client,
            "biomcp_client": _biomcp_client,
        }

        # Wrap graph execution in timeout (30s)
        final_state = None
        try:
            async with asyncio.timeout(30.0):  # Python 3.11+
                # Stream graph execution
                async for event in graph.astream_events(
                    {"messages": [{"role": "user", "content": query}]},
                    config={"configurable": context},
                    version="v2",
                ):
                    event_type = event.get("event")

                    # Agent start event
                    if event_type == "on_chain_start":
                        node_name = event.get("name", "")
                        if node_name in [
                            "drug_agent",
                            "pubmed_agent",
                            "guidelines_agent",
                            "supervisor",
                            "synthesizer",
                        ]:
                            yield "event: message\n"
                            yield f"data: {json.dumps({'type': 'agent_start', 'agent': node_name})}\n\n"

                    # Agent complete event
                    elif event_type == "on_chain_end":
                        node_name = event.get("name", "")
                        if node_name in [
                            "drug_agent",
                            "pubmed_agent",
                            "guidelines_agent",
                        ]:
                            yield "event: message\n"
                            yield f"data: {json.dumps({'type': 'agent_complete', 'agent': node_name})}\n\n"

                        # Capture final state from synthesizer
                        if node_name == "synthesizer":
                            final_state = event.get("data", {}).get("output", {})

        except asyncio.TimeoutError:
            # Timeout error (30s)
            error_response = {
                "type": "error",
                "error": "timeout",
                "detail": "Request timed out after 30 seconds",
            }
            yield "event: error\n"
            yield f"data: {json.dumps(error_response)}\n\n"
            return

        # If no final state captured, invoke graph normally (fallback) with timeout
        if final_state is None:
            try:
                async with asyncio.timeout(30.0):  # Python 3.11+
                    final_state = await graph.ainvoke(
                        {"messages": [{"role": "user", "content": query}]},
                        config={"configurable": context},
                    )
            except asyncio.TimeoutError:
                # Timeout error in fallback
                error_response = {
                    "type": "error",
                    "error": "timeout",
                    "detail": "Request timed out after 30 seconds",
                }
                yield "event: error\n"
                yield f"data: {json.dumps(error_response)}\n\n"
                return

        # Extract answer from final state
        messages = final_state.get("messages", [])
        answer = ""
        if messages:
            last_msg = messages[-1]
            answer = (
                last_msg.get("content", "")
                if isinstance(last_msg, dict)
                else last_msg.content
            )

        # Transform retrieved_docs
        retrieved_docs = final_state.get("retrieved_docs", [])
        retrieved_docs_json = [
            (
                doc.dict()
                if hasattr(doc, "dict")
                else transform_documents([doc])[0].dict()
            )
            for doc in retrieved_docs
        ]

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Send final response
        final_response = {
            "type": "final",
            "answer": answer,
            "retrieved_docs": retrieved_docs_json,
            "confidence": 0.0,  # Default confidence (TODO: Implement confidence scoring)
            "latency_ms": latency_ms,
        }

        yield "event: message\n"
        yield f"data: {json.dumps(final_response)}\n\n"

        # Send done event
        yield "event: done\n"
        yield "data: {}\n\n"

    except Exception as e:
        # Internal error
        logger.error(f"Consult stream error: {e}", exc_info=True)
        error_response = {
            "type": "error",
            "error": "internal_error",
            "detail": str(e),
        }
        yield "event: error\n"
        yield f"data: {json.dumps(error_response)}\n\n"


@router.post(
    "/api/v1/consult",
    tags=["Konzultace"],
    summary="Lékařská konzultace s AI asistentem",
    description="""
Odešle lékařský dotaz do multi-agent systému a vrátí odpověď s citacemi zdrojů.

**SSE Event Types:**
- `agent_start` - Agent začíná zpracování
- `agent_complete` - Agent dokončil zpracování
- `final` - Finální odpověď s citacemi
- `done` - Stream ukončen
- `error` - Chyba během zpracování

**Rate Limiting:** 10 requests per minute per IP address.

**Timeout:** 30 seconds maximum execution time.
    """,
    responses={
        200: {
            "description": "SSE stream s real-time updates agentů",
            "content": {
                "text/event-stream": {
                    "schema": {
                        "type": "string",
                        "format": "event-stream",
                        "description": (
                            "Server-Sent Events stream. Každý event má formát:\n\n"
                            "```\nevent: message|done|error\ndata: <JSON>\n\n```\n\n"
                            "**Event typy:**\n"
                            "- `agent_start` — agent zahájil zpracování\n"
                            "- `agent_complete` — agent dokončil zpracování\n"
                            "- `cache_hit` — odpověď z Redis cache (jen quick mode)\n"
                            "- `final` — finální odpověď s citacemi (viz ConsultResponse schéma)\n"
                            "- `done` — stream ukončen\n"
                            "- `error` — chyba (viz ErrorResponse schéma)"
                        ),
                    },
                    "examples": {
                        "agent_start": {
                            "summary": "Agent Start",
                            "value": 'event: message\ndata: {"type": "agent_start", "agent": "drug_agent"}\n\n',
                        },
                        "final_response": {
                            "summary": "Finální odpověď",
                            "value": (
                                'event: message\n'
                                'data: {"type": "final", "answer": "Metformin je kontraindikován při eGFR <30 [1].", '
                                '"retrieved_docs": [{"page_content": "...", "metadata": {"source": "sukl"}}], '
                                '"confidence": 0.92, "latency_ms": 2340}\n\n'
                            ),
                        },
                        "cache_hit": {
                            "summary": "Cache Hit (jen quick mode)",
                            "value": 'event: message\ndata: {"type": "cache_hit"}\n\n',
                        },
                        "done": {
                            "summary": "Stream dokončen",
                            "value": "event: done\ndata: {}\n\n",
                        },
                        "error": {
                            "summary": "Chyba",
                            "value": 'event: error\ndata: {"type": "error", "error": "timeout", "detail": "Request timed out after 30 seconds"}\n\n',
                        },
                    },
                }
            },
        },
        400: {
            "description": "Chyba validace (dotaz příliš dlouhý nebo neplatný)",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "validation_error",
                        "detail": "Query too long (max 1000 characters)",
                    }
                }
            },
        },
        429: {
            "description": "Překročen rate limit (10 požadavků/minutu)",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "rate_limit_exceeded",
                        "detail": "Rate limit 10/minute exceeded. Zkuste to znovu za chvíli.",
                    }
                }
            },
        },
        500: {
            "description": "Interní chyba serveru",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "internal_error",
                        "detail": "An unexpected error occurred",
                    }
                }
            },
        },
        504: {
            "description": "Timeout (zpracování trvalo déle než 30 sekund)",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "timeout",
                        "detail": "Request timed out after 30 seconds",
                    }
                }
            },
        },
    },
)
@limiter.limit("10/minute")
async def consult_endpoint(
    request: Request,
    consult_request: ConsultRequest,
) -> StreamingResponse:
    """Consult endpoint with SSE streaming and Redis caching.

    Processes medical query through LangGraph multi-agent system and
    streams execution events in real-time. Caches quick mode responses.

    Args:
        request: FastAPI Request (for rate limiting).
        consult_request: Validated ConsultRequest with query and mode.

    Returns:
        StreamingResponse with text/event-stream content type.

    Raises:
        HTTPException: 400 for validation errors, 429 for rate limit.

    Example:
        >>> response = await client.post(
        ...     "/api/v1/consult",
        ...     json={"query": "Jaké jsou kontraindikace metforminu?", "mode": "quick"}
        ... )
        >>> # SSE stream with events: agent_start, agent_complete, final, done
    """
    # Log request
    logger.info("Processing consult request", extra={
        "request_id": getattr(request.state, "request_id", "unknown"),
        "query_length": len(consult_request.query),
        "mode": consult_request.mode,
    })

    # Check cache first (only for quick mode)
    if consult_request.mode == "quick":
        cached = await get_cached_response(
            consult_request.query,
            consult_request.mode,
        )
        if cached:
            # Return cached response as SSE stream
            async def cached_stream():
                yield "event: message\n"
                yield f"data: {json.dumps({'type': 'cache_hit'})}\n\n"
                yield "event: message\n"
                yield f"data: {json.dumps(cached)}\n\n"
                yield "event: done\n"
                yield "data: {}\n\n"

            return StreamingResponse(
                cached_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "X-Cache": "HIT",
                },
            )

    # Create SSE stream with caching
    return StreamingResponse(
        consult_stream_generator_with_cache(
            query=consult_request.query,
            mode=consult_request.mode,
            user_id=consult_request.user_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Cache": "MISS",
        },
    )
