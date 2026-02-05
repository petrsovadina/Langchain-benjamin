"""Integration tests for FastAPI server.

Tests:
    - Server startup
    - Health check endpoint
    - CORS headers
"""

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

    assert sukl_status in ["available", "unavailable"] or sukl_status.startswith("error:")
    assert biomcp_status in ["available", "unavailable"] or biomcp_status.startswith("error:")


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
