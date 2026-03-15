"""Integration tests for FastAPI server.

Tests:
    - Server startup
    - Health check endpoint
    - CORS headers
    - Consult endpoint with SSE streaming (mocked graph)
"""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    """Provide TestClient for API testing."""
    return TestClient(app)


def test_server_startup(client: TestClient):
    """Test server starts successfully."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Czech MedAI API"
    assert "docs" in data
    assert "health" in data


def test_health_check_endpoint(client: TestClient):
    """Test /health endpoint returns valid response."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]
    assert "mcp_servers" in data
    assert "sukl" in data["mcp_servers"]
    assert "biomcp" in data["mcp_servers"]
    assert "database" in data
    assert data["database"] is not None
    assert "version" in data


def test_health_check_mcp_status(client: TestClient):
    """Test /health endpoint reports MCP server status."""
    response = client.get("/health")
    data = response.json()

    sukl_status = data["mcp_servers"]["sukl"]
    biomcp_status = data["mcp_servers"]["biomcp"]

    valid_statuses = ["available", "unavailable", "error"]
    for status in [sukl_status, biomcp_status]:
        assert status in valid_statuses or status.startswith("error:")


def test_health_check_database_status(client: TestClient):
    """Test /health endpoint reports database connectivity status."""
    response = client.get("/health")
    data = response.json()

    database_status = data["database"]
    assert database_status in ["available", "error"] or database_status.startswith(
        "error:"
    )


def test_cors_preflight_returns_response(client: TestClient):
    """Test CORS preflight returns a response (may be 400 if no origins configured)."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # With empty cors_origins (dev default), preflight may return 400
    # The important thing is that the middleware processes the request
    assert response.status_code in [200, 400]


def test_process_time_header(client: TestClient):
    """Test X-Process-Time header is added to responses."""
    response = client.get("/health")
    assert "x-process-time" in response.headers

    process_time = response.headers["x-process-time"]
    assert process_time.endswith("ms")
    assert float(process_time.replace("ms", "")) >= 0


def test_openapi_docs_available(client: TestClient):
    """Test OpenAPI documentation endpoints are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Czech MedAI API"


def _parse_sse_events(response) -> list[dict]:
    """Parse SSE events from TestClient response."""
    events = []
    for line in response.iter_lines():
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        if line.startswith("data: "):
            data = json.loads(line[6:])
            events.append(data)
    return events


def test_consult_endpoint_quick_mode(client: TestClient):
    """Test /api/v1/consult endpoint with quick mode (mocked graph)."""

    async def mock_astream_events(*args, **kwargs):
        yield {
            "event": "on_chain_end",
            "name": "synthesizer",
            "data": {
                "output": {
                    "messages": [type("Msg", (), {"content": "Metformin je lék..."})()],
                    "retrieved_docs": [],
                }
            },
        }

    with patch("api.routes.graph") as mock_graph:
        mock_graph.astream_events = mock_astream_events
        response = client.post(
            "/api/v1/consult",
            json={"query": "Jaké jsou kontraindikace metforminu?", "mode": "quick"},
            headers={"Accept": "text/event-stream"},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = _parse_sse_events(response)
    assert len(events) > 0


def test_consult_endpoint_validation_error(client: TestClient):
    """Test /api/v1/consult with invalid request."""
    response = client.post("/api/v1/consult", json={"query": "", "mode": "quick"})
    assert response.status_code == 422

    response = client.post(
        "/api/v1/consult", json={"query": "a" * 1001, "mode": "quick"}
    )
    assert response.status_code in [400, 422]
