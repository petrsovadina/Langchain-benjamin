"""Integration tests for FastAPI server.

Tests:
    - Server startup
    - Health check endpoint
    - CORS headers
    - Consult endpoint with SSE streaming
"""

import json

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
    assert data["version"] == "0.1.0"
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
    assert data["version"] == "0.1.0"


def test_health_check_mcp_status(client: TestClient):
    """Test /health endpoint reports MCP server status."""
    response = client.get("/health")
    data = response.json()

    # MCP servers should be either "available" or "unavailable"
    sukl_status = data["mcp_servers"]["sukl"]
    biomcp_status = data["mcp_servers"]["biomcp"]

    assert sukl_status in ["available", "unavailable"] or sukl_status.startswith(
        "error:"
    )
    assert biomcp_status in ["available", "unavailable"] or biomcp_status.startswith(
        "error:"
    )


def test_health_check_database_status(client: TestClient):
    """Test /health endpoint reports database connectivity status."""
    response = client.get("/health")
    data = response.json()

    # Database should be either "available" or start with "error:"
    database_status = data["database"]
    assert database_status == "available" or database_status.startswith("error:")

    # If database fails, overall status should be degraded
    if database_status.startswith("error:"):
        assert data["status"] == "degraded"


def test_cors_headers(client: TestClient):
    """Test CORS headers are present."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers


def test_process_time_header(client: TestClient):
    """Test X-Process-Time header is added to responses."""
    response = client.get("/health")
    assert "x-process-time" in response.headers

    # Verify format (e.g., "12.34ms")
    process_time = response.headers["x-process-time"]
    assert process_time.endswith("ms")
    assert float(process_time.replace("ms", "")) >= 0


def test_openapi_docs_available(client: TestClient):
    """Test OpenAPI documentation endpoints are accessible."""
    # Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200

    # ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200

    # OpenAPI JSON schema
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Czech MedAI API"
    assert data["info"]["version"] == "0.1.0"


def test_consult_endpoint_quick_mode(client: TestClient):
    """Test /api/v1/consult endpoint with quick mode."""
    response = client.post(
        "/api/v1/consult",
        json={"query": "Jaké jsou kontraindikace metforminu?", "mode": "quick"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Parse SSE events
    events = []
    for line in response.iter_lines():
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data = json.loads(line[6:])  # Remove "data: " prefix
            events.append(data)

    # Verify event sequence
    assert len(events) > 0

    # Check for final event
    final_events = [e for e in events if e.get("type") == "final"]
    assert len(final_events) == 1

    final = final_events[0]
    assert "answer" in final
    assert "retrieved_docs" in final
    assert "latency_ms" in final
    assert isinstance(final["answer"], str)
    assert isinstance(final["retrieved_docs"], list)
    assert final["latency_ms"] > 0


def test_consult_endpoint_deep_mode(client: TestClient):
    """Test /api/v1/consult endpoint with deep mode."""
    response = client.post(
        "/api/v1/consult",
        json={"query": "Nejnovější studie o SGLT2 inhibitorech", "mode": "deep"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200

    # Parse events
    events = []
    for line in response.iter_lines():
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data = json.loads(line[6:])
            events.append(data)

    # Verify agent_start events
    agent_starts = [e for e in events if e.get("type") == "agent_start"]
    assert len(agent_starts) > 0  # At least supervisor + 1 agent


def test_consult_endpoint_validation_error(client: TestClient):
    """Test /api/v1/consult with invalid request."""
    # Empty query
    response = client.post("/api/v1/consult", json={"query": "", "mode": "quick"})
    assert response.status_code == 422  # Validation error

    # Query too long
    response = client.post(
        "/api/v1/consult", json={"query": "a" * 1001, "mode": "quick"}
    )
    assert response.status_code == 400  # Bad request


def test_consult_endpoint_rate_limiting(client: TestClient):
    """Test rate limiting (10 req/min)."""
    # Send 11 requests rapidly
    for i in range(11):
        response = client.post(
            "/api/v1/consult",
            json={"query": f"Test query {i}", "mode": "quick"},
        )

        if i < 10:
            assert response.status_code == 200
        else:
            # 11th request should be rate limited
            assert response.status_code == 429


def test_consult_endpoint_retrieved_docs_format(client: TestClient):
    """Test retrieved_docs are properly formatted."""
    response = client.post(
        "/api/v1/consult",
        json={"query": "Ibalgin", "mode": "quick"},
        headers={"Accept": "text/event-stream"},
    )

    # Parse final event
    events = []
    for line in response.iter_lines():
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data = json.loads(line[6:])
            events.append(data)

    final = [e for e in events if e.get("type") == "final"][0]
    docs = final["retrieved_docs"]

    # Verify document structure
    if docs:
        doc = docs[0]
        assert "page_content" in doc
        assert "metadata" in doc
        assert "source" in doc["metadata"]
