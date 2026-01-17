"""Pytest fixtures for Czech MedAI foundation tests."""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agent.graph import State, Context, graph
from src.agent.models.drug_models import (
    DrugQuery,
    DrugResult,
    DrugDetails,
    QueryType,
    ReimbursementInfo,
    ReimbursementCategory,
    AvailabilityInfo,
)
from src.agent.mcp import MCPResponse


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure asyncio backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
def sample_state():
    """Provide a valid State instance for testing.

    Returns:
        State: Sample state with user message and default fields.
    """
    return State(
        messages=[{"role": "user", "content": "test message"}],
        next="placeholder",
        retrieved_docs=[]
    )


@pytest.fixture
def mock_runtime():
    """Provide a mock Runtime with complete context.

    Returns:
        MockRuntime: Runtime-like object with all Context fields.
    """
    class MockRuntime:
        def __init__(self):
            self.context = {
                # Core fields
                "model_name": "test-model",
                "temperature": 0.0,
                "langsmith_project": "test-project",
                "user_id": None,

                # MCP clients (None in foundation - implemented in Feature 002)
                "sukl_mcp_client": None,
                "biomcp_client": None,

                # Conversation persistence (None - implemented in Feature 013)
                "conversation_context": None,

                # Workflow mode (default: quick)
                "mode": "quick"
            }

    return MockRuntime()


@pytest.fixture
def test_graph():
    """Provide the compiled graph for integration tests.

    Returns:
        CompiledGraph: Czech MedAI Foundation graph instance.
    """
    return graph


# =============================================================================
# Feature 003: SÚKL Drug Agent Fixtures
# =============================================================================


@pytest.fixture
def mock_sukl_response() -> MCPResponse:
    """Provide a mock SÚKL MCP response for drug search.

    Returns:
        MCPResponse: Successful response with sample drug data.
    """
    return MCPResponse(
        success=True,
        data={
            "drugs": [
                {
                    "name": "Ibalgin 400",
                    "atc_code": "M01AE01",
                    "registration_number": "58/123/01-C",
                    "manufacturer": "Zentiva",
                },
                {
                    "name": "Ibalgin 200",
                    "atc_code": "M01AE01",
                    "registration_number": "58/124/01-C",
                    "manufacturer": "Zentiva",
                },
            ]
        },
        metadata={
            "latency_ms": 150,
            "server_url": "http://localhost:3000",
            "tool_name": "search_drugs",
        },
    )


@pytest.fixture
def mock_sukl_details_response() -> MCPResponse:
    """Provide a mock SÚKL MCP response for drug details.

    Returns:
        MCPResponse: Successful response with detailed drug information.
    """
    return MCPResponse(
        success=True,
        data={
            "registration_number": "58/123/01-C",
            "name": "Ibalgin 400",
            "active_ingredient": "ibuprofenum",
            "composition": ["ibuprofenum 400 mg", "pomocné látky"],
            "indications": [
                "Bolest hlavy",
                "Bolest zubů",
                "Bolesti svalů a kloubů",
            ],
            "contraindications": [
                "Přecitlivělost na ibuprofen",
                "Vředová choroba",
            ],
            "dosage": "1-2 tablety 3x denně po jídle",
            "side_effects": ["Nauzea", "Bolest žaludku"],
            "pharmaceutical_form": "Potahované tablety",
            "atc_code": "M01AE01",
        },
        metadata={"latency_ms": 200},
    )


@pytest.fixture
def mock_sukl_client(
    mock_sukl_response: MCPResponse, mock_sukl_details_response: MCPResponse
) -> MagicMock:
    """Provide a mock SUKLMCPClient for testing.

    Args:
        mock_sukl_response: Response for search queries.
        mock_sukl_details_response: Response for detail queries.

    Returns:
        MagicMock: Mock client with preconfigured responses.
    """
    client = MagicMock()
    client.call_tool = AsyncMock()

    # Configure responses based on tool_name
    async def call_tool_side_effect(
        tool_name: str, parameters: Dict[str, Any], retry_config: Any = None
    ) -> MCPResponse:
        if tool_name == "search_drugs":
            return mock_sukl_response
        elif tool_name == "get_drug_details":
            return mock_sukl_details_response
        elif tool_name == "get_reimbursement":
            return MCPResponse(
                success=True,
                data={
                    "registration_number": parameters.get("registration_number"),
                    "category": "B",
                    "copay_amount": 45.0,
                    "prescription_required": True,
                    "conditions": ["Pro chronickou bolest"],
                },
            )
        elif tool_name == "check_availability":
            return MCPResponse(
                success=True,
                data={
                    "registration_number": parameters.get("registration_number"),
                    "is_available": True,
                    "alternatives": [],
                },
            )
        else:
            return MCPResponse(success=False, error=f"Unknown tool: {tool_name}")

    client.call_tool.side_effect = call_tool_side_effect
    return client


@pytest.fixture
def sample_drug_query() -> DrugQuery:
    """Provide a sample DrugQuery for testing.

    Returns:
        DrugQuery: Search query for "Ibalgin".
    """
    return DrugQuery(
        query_text="Ibalgin",
        query_type=QueryType.SEARCH,
        limit=10,
    )


@pytest.fixture
def sample_drug_result() -> DrugResult:
    """Provide a sample DrugResult for testing.

    Returns:
        DrugResult: Sample drug search result.
    """
    return DrugResult(
        name="Ibalgin 400",
        atc_code="M01AE01",
        registration_number="58/123/01-C",
        manufacturer="Zentiva",
        match_score=0.95,
    )


@pytest.fixture
def sample_drug_details() -> DrugDetails:
    """Provide sample DrugDetails for testing.

    Returns:
        DrugDetails: Complete drug information.
    """
    return DrugDetails(
        registration_number="58/123/01-C",
        name="Ibalgin 400",
        active_ingredient="ibuprofenum",
        composition=["ibuprofenum 400 mg"],
        indications=["Bolest hlavy", "Bolest zubů"],
        contraindications=["Přecitlivělost na ibuprofen"],
        dosage="1-2 tablety 3x denně",
        atc_code="M01AE01",
    )
